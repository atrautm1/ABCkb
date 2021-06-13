#!/usr/bin/env python

from collections import defaultdict
import sys
import codecs
import re
import json
import csv
import argparse
import logging
from os import path
from parse_it import getTerm,parseMeshValue,parseTagValue,parseTrees,addNodeLabel,addLabel,handle
from oboParser import oboParser
import ctd
import mesh
import nal
import mondo

def converter(GENE_FILE, MONDO_FILE, namespace):
    omim2gene = defaultdict(set)    #Gene to gene
    gene2omim = defaultdict(set)    # Gene to Phene
    omim2mondo = defaultdict(set)   # Phene to Phene
    with handle(GENE_FILE) as genes:
        rows = csv.DictReader(genes, delimiter="\t")
        for row in rows:
            MID = row["#MIM number"]
            GID = row["GeneID"]
            if GID != "-":
                if row["type"] == "gene":
                    omim2gene[MID].add(f"{namespace}.id:{GID}")
                elif row["type"] == "phenotype":
                    gene2omim[f"{namespace}.id:{GID}"].add(MID)
    with handle(MONDO_FILE) as mf:
        omim_id = []
        mondo_id = ""
        is_obsolete = False
        for line in mf:
            if line.startswith("[Term]"):
                if mondo_id and omim_id and not is_obsolete:
                    for om in omim_id:
                        omim2mondo[om] = mondo_id
                    omim_id = []
                    mondo_id = ""
                is_obsolete = False
            elif line.startswith("id:"):
                mondo_id = line.strip().split("id: ")[1]
            elif line.startswith("xref: OMIM"):
                omim_id.append(line.split(" ")[1].split(":")[1])
            elif line.startswith("is_obsolete"):
                is_obsolete = True
    return omim2gene, gene2omim, omim2mondo

def geneParser(gene_info, gene2go, mimgen, mondo, namespace):
    """
    Parser function for ncbi gene file
    """
    # EDGES REQUIRE OTHER FILES, all are XREF
    # python oboParser.py -i /Users/rlinchan/Google\
    # Drive/PhD/dissert/data/EntrezGene_01042017/gene_info -c
    # /Users/rlinchan/Google\
    # Drive/PhD/dissert/data/EntrezGene_01042017/gene2go -o
    # /Users/rlinchan/Google\ Drive/PhD/dissert/data/neo4j_input/v3/ -n
    # nih.nlm.ncbi.gene
    
    organisms = {
        "9606":"Homo sapiens",
        "10116":"Rattus norvicigus",
        "10090":"Mus musculus"
    }
    def form(item):
        """
        Removes quotation marks and ; from items
        """
        chars = "'\";"
        for a in chars:
            item = item.replace(a,"")
        return item
    geneDict = defaultdict(dict)
    with handle(gene_info) as infile:
        reader = csv.DictReader(infile, delimiter='\t')
        for row in reader:
            idee = row["#tax_id"]
            # homo sapiens, rattus norvicigus, mus musculus
            if idee in organisms.keys(): #("9606","10116","10090"):
                geneID = f"{namespace}.id:{row['GeneID']}"
                symbol_list = form(row["Symbol"]).split("|")
                symbol = symbol_list[0]
                syn = set(row["Synonyms"].split("|"))
                syn.update(symbol_list)
                geneType = form(row["type_of_gene"])
                organism = organisms[idee]
                syn.update(form(row["description"]).split("|"))
                if "-" in syn:
                    syn.remove("-")
                geneDict[geneID] = {'name': symbol, "gene_type":geneType, "organism":organism,
                                    'synonyms': list(syn), 'parents': set(),
                                    'edges': [], 'labels': set(['Gene', namespace.replace('.', '_')])}
                #geneDict[geneID]['edges'].append(('xref', f'nih.nlm.ncbi.taxonomy.id:{idee}'))
    logger.info("Nodes Dict created")
    # Can also take down PubMedId
    with handle(gene2go) as edgeFile:
        reader = csv.DictReader(edgeFile, delimiter='\t')
        for row in reader:
            idee = row["#tax_id"]
            if idee in organisms.keys(): #("9606","10116","10090"):
                geneID = f"{namespace}.id:{row['GeneID']}"
                goID = row["GO_ID"]
                geneDict[geneID]['edges'].append(('xref', goID))
    logger.info(f"{len(geneDict)} edges added to Dict")

    omim2gene, gene2omim, omim2mondo = converter(mimgen, mondo, namespace)
    # Find OMIM associated phenotypes
    matches = 0
    for g in geneDict.keys():
        #geneID = g.split(":")[1]
        if g in gene2omim.keys():
            OMIM_ID = gene2omim[g]
            for oid in OMIM_ID:
                if oid in omim2mondo.keys():
                    matches += 1
                    geneDict[g]['edges'].append(('associated_with', omim2mondo[oid]))
    logger.info(f"{matches} Gene to Phenotype associations")
    return geneDict

def taxParser(tsvFile, nodesFile, namespace):
    """
    Parses names.dmp and nodes.dmp files from NCBI Taxonomy to generate nodes and edges for Neo4J
    python oboParser.py -i NCBI_taxdump_9.29.16/names.dmp -c NCBI_taxdump_9.29.16/nodes.dmp -o neo4j_input/ -n nih.nlm.ncbi.taxonomy
    """
    synTitles = set(['acronym', 'blast name', 'common name', 'equivalent name', 'genbank acronym',
                     'genbank common name', 'genbank synonym', 'synonym', 'scientific name'])
    taxDict = defaultdict(dict)
    taxChildrenTree = defaultdict(set)
    files = [tsvFile, nodesFile]
    for dmp in files:
        with handle(dmp) as inFile:
            for line in inFile:
                # Can replace with map(strip, line.split('|'),
                # line.replace('\"', ''))
                line = line.replace('\"', '')
                column_List = [i.strip() for i in line.split('|')]
                if 'names.dmp' in dmp:
                    taxID = namespace + '.id:' + column_List[0]
                    name = column_List[1]
                    # needs to account for different names/synonyms
                    # scientific name is PT
                    if taxID not in taxDict:
                        taxDict[taxID] = {'name': name, 'synonyms': [name], 'edges': [
                        ], 'labels': set(['Organism', namespace.replace('.', '_')])}  # 'def': '',
                        if 'scientific name' == column_List[3]:
                            taxDict[taxID]['name'] = name
                    else:
                        taxDict[taxID]['synonyms'].append(name)
                        if 'scientific name' == column_List[3]:
                            taxDict[taxID]['name'] = name
                if 'nodes.dmp' in dmp:
                    taxID = namespace + '.id:' + column_List[0]
                    parentID = namespace + '.id:' + column_List[1]
                    taxDict[taxID]['edges'].append(('is_a', parentID))
                    if taxID not in taxChildrenTree:
                        taxChildrenTree[parentID].add(taxID)
                    if taxID in taxChildrenTree:
                        taxChildrenTree[parentID].add(taxID)
    # recursively find all children of Embryophyta to label as plant
    outDict = defaultdict(dict)
    childSet = set()
    # Add plant label
    addLabel(taxChildrenTree, childSet, 'nih.nlm.ncbi.taxonomy.id:3193')
    for child in childSet:
        outDict[child] = taxDict[child]
        outDict[child]['labels'].add('Plant')
    logger.info(f"""{len(taxDict)} total nodes\nwith {len(outDict)} labeled nodes """)
    return outDict

def csvNodeOutput(oboDict, csvOut, namespace):
    """
    All nodes output:
    Source_ID(namespace)
    Name
    Synonyms
    Definition
    Labels

    All edges output:
    Source_ID(namespace) 1
    Label
    Source(namespace)
    Source_ID(namespace) 2


    Mined edges output:
    : START_ID
    TYPE:
    Source:
    Occurrence
    Evidence
    : END_ID
    """
    logger.info("Writing to file...")
    namespaces = set(['disbiome','disease_ontology.do', 'ebi.chebi', 'gene_ontology.go', 'human_phenotype.hpo', 'jax.mgi.mp', 'nih.nlm.mesh', 'nih.nlm.ncbi.gene',
                      'nih.nlm.ncbi.taxonomy', 'omim.disease', 'phenotypic_quality.pato', 'plant_ontology.po', 'plant_trait.to', 'usda.nal.thesaurus', 'mondo'])
    oboIDs = set(['CHEBI', 'DOID', 'GO', 'HP', 'MP', 'PATO', 'TO',
                  'PO', 'nih.nlm.ncbi.gene.id', 'nih.nlm.ncbi.taxonomy.id'])
    renameIDs = set(['OMIM', 'MESH', 'MeSH', 'MSH', 'Mesh'])
    xrefs = set()

    nodeOut = codecs.open(csvOut + namespace + '.nodes.csv', 'w', 'utf-8')
    if namespace == "nih.nlm.ncbi.gene":
        nodeOut.write(
        "source_id:ID|name:string|gene_type:string|organism:string|synonyms:string[]|:LABEL\n")
    else:    
        nodeOut.write(
        "source_id:ID|name:string|synonyms:string[]|:LABEL\n")  # definition:string|

    edgeOut = codecs.open(csvOut + namespace + '.edges.csv', 'w', 'utf-8')
    edgeOut.write(":START_ID|:TYPE|source:string|occurrence:float|:END_ID\n")

    xrefOut = codecs.open(csvOut + namespace + '.xref.edges.csv', 'w', 'utf-8')
    xrefOut.write(":START_ID|:TYPE|source:string|occurrence:float|:END_ID\n")

    for uid, attribute_Dict in oboDict.items():
        name = attribute_Dict['name']
        syns = ''
        if len(attribute_Dict['synonyms']) > 1:
            syns = ";".join(attribute_Dict['synonyms'])
        # changes ONLY for NCBI Gene (comment out)
        elif len(attribute_Dict['synonyms']) == 1:
            syns = attribute_Dict['synonyms'][0]
        # Addition of namespace, node, and all extra labels
        labels = attribute_Dict['labels']
        labelString = ''
        if len(labels) > 1:
            labelString = ";".join(labels)
        elif len(labels) == 1:
            # unpacks value from set, ie.
            # [value] = set
            [labelString] = labels
            # labelString = labelString + ';Node'
        else:
            labelString = namespace.replace('.', '_')  # + ';Node'
        #definition = attribute_Dict['def']
        # add extra label via delimiter
        # ID|name|syns|def|labels
        if namespace == "nih.nlm.ncbi.gene":
            outList = [uid, name, attribute_Dict["gene_type"],
            attribute_Dict["organism"], syns, labelString]
        else:
            outList = [uid, name, syns, labelString]  # definition,
        try:
            outString = "|".join(outList) + "\n"
        except:
            logger.error(outList)
            sys.exit(1)
        nodeOut.write(outString)
        # nodeOut.flush()
        for relationship in attribute_Dict['edges']:
            # ID1|Type|source|occurrence|ID2
            rel = relationship[0]
            ID2 = relationship[1]
            edgeList = [uid, rel, namespace, '1', ID2]
            edgeString = "|".join(edgeList) + '\n'
            prefix = ID2.split(':')[0].strip()
            if rel == 'xref' and prefix in oboIDs:
                xrefOut.write(edgeString)
                # xrefOut.flush()
            if rel == 'xref' and prefix in renameIDs:
                if prefix == 'OMIM':
                    edgeList = [uid, rel, namespace, '1',
                                'omim.disease.id:' + ID2.split(':')[1].strip()]
                    edgeString = '|'.join(edgeList) + '\n'
                    xrefOut.write(edgeString)
                else:
                    edgeList = [uid, rel, namespace,
                                '1', ID2.split(':')[1].strip()]
                    edgeString = '|'.join(edgeList) + '\n'
                    xrefOut.write(edgeString)
            if rel != 'xref':
                edgeOut.write(edgeString)
                # edgeOut.flush()
            elif rel == 'xref' and prefix not in oboIDs:
                xrefs.add(prefix)
    nodeOut.close()
    edgeOut.close()
    xrefOut.close()
    logger.info("Finished writing to file...")

def readArgs():
    """Reads the arguments provided by the user."""
    desc = """
    This program parses through source data and formats it
    for use in a neo4j Knowledgebase
    """
    p = argparse.ArgumentParser(description=desc, prog="bareSourceParser")
    # Required arguments
    p.add_argument("-i", "--infiles", required=True, nargs='+',
                   help="Files with node information")
    p.add_argument("-o", "--outdir", required=True, 
                   help="Specifies the directory where the data is written.")
    p.add_argument("-n", "--namespace", required=True, 
                   help="""Namespace of the source data. Currently accepts:\n
                           usda.nal.thesaurus\n
                           plant.trait.to\n
                           plant.ontology.po\n
                           phenotypic.quality.pato\n
                           jax.mgi.mp\n
                           human.phenotype.hpo\n
                           gene.ontology.go\n
                           ebi.chebi\n
                           disease.ontology.do\n
                           omim.disease\n
                           nih.nlm.ncbi.taxonomy\n
                           nih.nlm/ncbi.gene\n
                           nih.nlm.mesh\n""")
    # Optional arguments
    p.add_argument("-v", "--verbose", default=False, help="Output verbose", action="store_true")
    args = p.parse_args()
    return args

def main():
    args = readArgs()
    INFILE = args.infiles
    OUTPUT_DIRECTORY = args.outdir
    NAMESPACE = args.namespace
    # NAMESPACE is UID prefix for:
    # gene, taxonomy, omim, nal
    # MeSH parsing
    if NAMESPACE == "nih.nlm.mesh":
        logger.info("Parsing mesh files...")
        nodeOut = open(path.join(OUTPUT_DIRECTORY,f"{NAMESPACE}.nodes.csv"), "w")
        edgeOut = open(path.join(OUTPUT_DIRECTORY,f"{NAMESPACE}.edges.csv"), "w")
        parser = mesh.Parser(nodeOut, edgeOut)
        for F in INFILE:
            parser.read(F)
        parser.writeEdges()
        nodeOut.close()
        edgeOut.close()
        sys.exit(0)
    # NCBI Taxonomy parsing
    elif NAMESPACE == "nih.nlm.ncbi.taxonomy":
        # CHEMFILE is nodes.dmp (edges)
        logger.info('Parsing NCBI Taxonomy files...')
        for F in INFILE:
            if F.endswith("names.dmp"):
                f1 = F
            else:
                f2 = F
        outDict = taxParser(f1, f2, NAMESPACE)
    # OMIM parsing
    elif NAMESPACE == "omim.disease":
        logger.info('Parsing omim files...')
        for F in INFILE:
            if F.endswith("genemap2.txt"):
                f1 = F
            else:
                f2 = F
        outDict = omim_parser(f1, f2, NAMESPACE)
    # NCBI Gene parsing
    elif NAMESPACE == "nih.nlm.ncbi.gene":
        logger.info('Parsing NCBI gene files...')
        for F in INFILE:
            if "gene_info" in F:
                gene_info = F
            elif "gene2go" in F:
                gene2go = F
            elif "mim2gene" in F:
                mimgen = F
            elif "mondo" in F:
                mon = F
            else:
                logger.error(f"I'm not sure what to do with this file!\n file:{F}")
        outDict = geneParser(gene_info, gene2go, mimgen, mon, NAMESPACE)
    # NALT parsing
    elif NAMESPACE == "usda.nal.thesaurus":
        logger.info('Parsing NAL files...')
        parser = nal.Parser()
        outDict = parser.parse(handle(INFILE[0]))
    # Parse the mondo obo file
    elif NAMESPACE == "ctd":
        for F in INFILE:
            ct = ctd.Parser(F,OUTPUT_DIRECTORY)
            ct.parse()
        exit(0)
    elif NAMESPACE == "mondo":
        logger.info("Parsing mondo ontology...")
        parser = mondo.Parser()
        outDict = parser.parse(handle(INFILE[0]))
    # Parse a different obo file
    else:
        logger.info(f"Parsing {NAMESPACE}: {INFILE[0]}...")
        outDict = oboParser(INFILE[0], NAMESPACE)
        
    logger.info(f"Writing to:\t{OUTPUT_DIRECTORY}")
    csvNodeOutput(outDict, OUTPUT_DIRECTORY, NAMESPACE)

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s', 
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    main()
