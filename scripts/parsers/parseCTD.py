#!/usr/bin/python -tt

import collections
import logging
import re
import argparse
from os import path
import csv
import parse_it

def parseMESH(inFiles):
    """
    Method creates set of 'valid' MESH IDs (conflicting versions)
    Input is array of 2, d201*.bin and c201*.bin
    """
    meshIDs = set()
    for filename in inFiles:
        logger.info(f"Working on {filename}")
        #myFile = open(filename, 'rU')
        myFile = parse_it.handle(filename)
        parse_it.getTerm(myFile)
        # Breaks when the term returned is empty, indicating end of file
        while 1:
            term = parse_it.parseMeshValue(
                parse_it.getTerm(myFile))
            # for descriptors
            if len(term) != 0:
                termID = term['UI'][0]
                meshIDs.add(termID)
            else:
                break
    logger.info(f"I found {len(meshIDs)} Mesh IDs")
    return meshIDs


def readIxns(filename):
    """
    CTD File is TSV, has #Fields:\n#Field1\tField2\tetc.
    This method parses unique file:CTD_chem_gene_ixns.tsv
    assocDict = {(startID,endID):{interaction:set(pmid)}}
    """
    # :START_ID|:TYPE|source:string|occurrence:float|articles:string[]|:END_ID
    # ID | xref | Comparative Toxicogenomics Database | len(PMID) | PMID;
    # PMID; | ID
    assocDict = collections.defaultdict(dict)
    geneFormset = set()
    #with open(filename, 'rU') as inFile:
    #    inFile = parse_it.handle(inFile)
    with parse_it.handle(filename) as inFile:
        for line in inFile:
            if line.startswith('#'):
                continue
            else:
                line = line.split('\t')
                startID = line[1]
                endID = line[4]
                # will always be one organism, based on GeneID
                organismID = line[7]
                if organismID == '9606':
                    interaction = set(
                        line[9].strip().replace('^', '_').split('|'))
                    pmid = set(line[10].strip().split('|'))
                    assocTuple = (startID, endID)
                    for ixn in interaction:
                        if assocTuple not in assocDict and ixn not in assocDict[assocTuple]:
                            assocDict[assocTuple][ixn] = pmid
                        elif assocTuple in assocDict and ixn not in assocDict[assocTuple]:
                            assocDict[assocTuple][ixn] = (pmid)
                        elif assocTuple in assocDict and ixn in assocDict[assocTuple]:
                            assocDict[assocTuple][ixn].update(pmid)
    return assocDict


def parseGenes(ctdGenesFile, entrez_gene):
    """
    creates map for ctd assigned gene symbols to entrez gene ids
    also parses set of human genes
    """
    logger.info('Parsing human genes file')
    # single column file of 59599 human(taxid:9606) gene ids from entrez gene
    #humanGenes = '/Users/rlinchan/Google Drive/PhD/dissert/data/neo4j_input/testNetwork/nodes/HumanEntrezGeneIDs.txt'
    sym2idDict = {}
    humanSet = set()
    with parse_it.handle(entrez_gene) as geneFile:
        #geneFile = parse_it.handle(geneFile)
        reader = csv.DictReader(geneFile, delimiter="\t")
        for row in reader:
            found = False
            if row["#tax_id"] != "9606" and found:
                break
            elif row["#tax_id"] == "9606":
                found = True
                humanSet.add(row["GeneID"])
    logger.info(f"I found {len(humanSet)} human genes")
    with parse_it.handle(ctdGenesFile) as inFile:
        #ctdGenesFile = parse_it.handle(ctdGenesFile)
        for line in inFile:
            if line.startswith('#'):
                continue
            else:
                line = line.split('\t')
                geneSymbol = line[0]
                geneID = line[2]
                if geneSymbol not in sym2idDict:
                    sym2idDict[geneSymbol] = geneID
    return sym2idDict, humanSet


def readTSV(filename, entrez_gene, ctd_gene, writeFile, meshIDs, goldStd):
    """
    This method reads all other CTD files listed in methods section
    Exceptions:
    OK CTD_Disease-GO_biological_process_associations.tsv MESH 2 GO FLIP edge direction
    OK CTD_Disease-GO_cellular_component_associations.tsv MESH 2 GO FLIP edge direction
    OK CTD_Disease-GO_molecular_function_associations.tsv MESH 2 GO FLIP edge direction
    OK CTD_chem_go_enriched.tsv (4,629,998) MESH 2 GO
    NA CTD_chem_pathways_enriched.tsv MESH 2 KEGG,REACT
    NA CTD_diseases_pathways.tsv FLIP edge direction MESH: or OMIM: ot KEGG,REACT
    NA CTD_genes_pathways.tsv NCBI GENE ID to KEGG,REACT
    LARGE
    MODIFY CTD_chemicals_diseases.tsv-> (4,338,326) MESH 2 MESH:,OMIM:
    MODIFY CTD_genes_diseases.tsv-> (46,613,048) NCBI GENE ID 2 MESH:,OMIM:
    """
    logger.info(f"Parsing {filename}")
    idArray = []
    source = 'Comparative Toxicogenomics Database'
    relType = 'xref'
    #ctdGeneFile = '/Users/rlinchan/Google Drive/PhD/dissert/data/assocDBs/CTD_2242015/CTD_genes.tsv'
    sym2id = {}
    humanSet = set()
    #  noPMIDDict = {startID:set(endID)}
    noPMIDDict = collections.defaultdict(set)
    gene2goDict = collections.defaultdict(set)
    mod = 0
    checkBoth = 0
    goFilter = 0
    inferredCount = 0
    directCount = 0
    if 'Disease' in filename:  # flag to flip IDs for direction of relationship
        mod = 1
        sym2id, humanSet = parseGenes(ctd_gene, entrez_gene)  # symbol to id map
    if 'chemicals' in filename:
        checkBoth = 1
    if 'genes_diseases' in filename:
        sym2id, humanSet = parseGenes(ctd_gene, entrez_gene)  # symbol to id map
    if 'chem_go' in filename:
        goFilter = 1
    with parse_it.handle(filename) as inFile:
        for line in inFile:
            if line.startswith('# Fields:'):
                line = next(inFile)
                header = line[2:].strip().split('\t')
                for column in header:  # define columns by header line
                    if column.endswith('ID'):  # 1,4 arrayPos = 0,1
                        idArray.append(header.index(column))
                    if column == 'OmimIDs':  # 8 arrayPos = 3
                        idArray.append(header.index(column))
                    if column == 'PubMedIDs':  # 9 arrayPos = 4
                        idArray.append(header.index(column))
                    if column == 'DirectEvidence':  # 5 arrayPos = 2
                        idArray.append(header.index(column))
            elif line.startswith('#'):  # skip file header
                continue
            else:  # associations
                line = line.strip().split('\t')
                startID = ''
                endID = ''
                ontology = ''
                geneID = []
                if mod == 0:  # retain original order
                    startID = line[idArray[0]]
                    endID = line[idArray[1]]
                    if goFilter == 1:
                        ontology = line[3]
                        # only include bioProc for CTD_chem_go
                        if ontology != 'Biological Process':
                            continue
                if mod == 1:  # flip order, CTD_Disease-GO*.tsv
                    startID = line[idArray[1]]  # goID
                    endID = line[idArray[0]]  # diseaseID
                    geneSym = line[5].split('|')  # gene symbols
                    for gene in geneSym:
                        if gene in sym2id:
                            geneID.append(sym2id[gene])
                    # account for non-prefixed omim
                    if endID.isdigit():
                        endID = 'omim.disease.id:' + endID
                if len(idArray) == 2:  # all other files
                    if startID in meshIDs or endID in meshIDs:  # does this ignore OMIM?
                        if startID not in noPMIDDict:
                            noPMIDDict[startID].add(endID)
                        else:
                            noPMIDDict[startID].add(endID)
                        for gene in geneID:  # adds gene to GO
                            if gene not in noPMIDDict and gene in humanSet:  # filter human genes
                                noPMIDDict[
                                    'nih.nlm.ncbi.gene.id:' + gene].add(startID)
                            if gene in noPMIDDict and gene in humanSet:  # filter human genes
                                noPMIDDict[
                                    'nih.nlm.ncbi.gene.id:' + gene].add(startID)
                elif len(idArray) == 5:
                    # chemicals_diseases.tsv = MESH to MESH: or OMIM:
                    # genes_diseases.tsv = Entrez ID to MESH: or OMIM:
                    # idArray = [0:ID,1:ID,2:DirectEvidence,3:OMIM,4:PubMedIDs]
                    omim = line[idArray[3]].strip().split('|')
                    evidence = line[idArray[2]]
                    if evidence != '':
                        directCount += 1
                    if evidence == '':
                        inferredCount += 1
                    pmids = ''  # PMID may be empty, must check
                    occurrence = '1'  # occurrence set to 1 if no pmid evidence
                    # Addition of 1 because 0 based language
                    if len(line) == idArray[4] + 1:
                        pmids = line[idArray[4]].strip().split('|')
                        # occurrence based on citation evidence
                        occurrence = str(len(pmids))
                    if startID.isdigit():  # convert to geneID
                        startID = 'nih.nlm.ncbi.gene.id:' + startID
                    if 'MESH' in endID:
                        endID = endID.split(':')[-1]
                    if 'OMIM' in endID:
                        endID = 'omim.disease.id:' + endID.split(':')[-1]
                    if checkBoth == 1:  # chemicals_diseases.tsv
                        if startID in meshIDs and endID in meshIDs:
                            lineOut = '%s|%s|%s|%s|%s|%s\n' % (
                                startID, relType, source, occurrence, ';'.join(pmids), endID)
                            if goldStd == 1 and evidence != '':
                                lineOut = '%s\t%s\n' % (startID, endID)
                                writeFile.write(lineOut)
                            if goldStd == 0:
                                writeFile.write(lineOut)
                            # when omimIDs exist, create chemical to omim
                            # relationship
                            if omim[0] != '':
                                omimIDs = set(omim)
                                for mim in omimIDs:
                                    mimOut = '%s|%s|%s|%s|%s|%s\n' % (
                                        startID, relType, source, occurrence, ';'.join(pmids), 'omim.disease.id:' + mim)
                                    if goldStd == 1 and evidence != '':
                                        writeFile.write(mimOut)
                                    if goldStd == 0:
                                        writeFile.write(mimOut)
                    elif checkBoth == 0 and endID in meshIDs:  # genes_diseases.tsv
                        geneID = startID.split(':')[1]
                        if geneID in humanSet:
                            lineOut = startID + '|' + relType + '|' + source + '|' + \
                                occurrence + '|' + \
                                ';'.join(pmids) + '|' + endID + '\n'
                            writeFile.write(lineOut)
                            # when omimIDs exist, create chemical to omim
                            # relationship
                            if omim[0] != '':
                                omimIDs = set(omim)
                                for mim in omimIDs:
                                    mimOut = startID + '|' + relType + '|' + source + '|' + \
                                        occurrence + '|' + \
                                        ';'.join(pmids) + '|' + \
                                        'omim.disease.id:' + mim + '\n'
                                    writeFile.write(mimOut)

    if len(idArray) == 2:
        return noPMIDDict
    else:
        logger.info(f"Direct Associations:{directCount}\nInferred Associations:{inferredCount}")
        writeFile.flush()
        writeFile.close()


def writeIxnEdges(assocDict, outFile):
    """
    Writes neo4j edges input for ixns CTD file ONLY
    """
    writeFile = open(outFile, 'w')
    writeFile.write(
        ':START_ID|:TYPE|source:string|occurrence:float|articles:string[]|:END_ID\n')
    source = 'Comparative Toxicogenomics Database'
    for assocTuple in assocDict:
        chemID = assocTuple[0]
        geneID = 'nih.nlm.ncbi.gene.id:' + assocTuple[1]
        for predicate in assocDict[assocTuple]:
            pmids = assocDict[assocTuple][predicate]
            occurrence = len(pmids)
            outLine = chemID + '|' + predicate + '|' + source + \
                '|' + str(occurrence) + '|' + \
                ';'.join(pmids) + '|' + geneID + '\n'
            writeFile.write(outLine)
    writeFile.flush()
    writeFile.close()


def writeEdges(assocDict, outFile):
    """
    Writes neo4j edges input for all CTD files except ixns
    """
    logger.info(f"Writing to {outFile}")
    conversionDict = {'MESH:': ''}  # Pathways-KEGG,REACT
    source = 'Comparative Toxicogenomics Database'
    writeFile = open(outFile, 'w')
    writeFile.write(':START_ID|:TYPE|source:string|occurrence:float|:END_ID\n')
    for startID in assocDict:
        for endID in assocDict[startID]:
            outLine = startID + '|xref|' + source + '|1|' + endID + '\n'
            writeFile.write(outLine)
    writeFile.flush()
    writeFile.close()


def parseMEDIC(inFile, meshIDs):
    """
    Borrows obo parsing code from bareSourceParser.py to parse the MEDIC ontology
    MEDIC maps MeSH Diseases to OMIM Diseases
    """
    # assocDict = {startID:set(endID)}
    assocDict = collections.defaultdict(set)
    #myFile = open(inFile, 'rU')
    myFile = parse_it.handle(inFile)
    parse_it.getTerm(myFile)
    # Breaks when the term returned is empty, indicating end of file
    while 1:
        term = parse_it.parseTagValue(parse_it.getTerm(myFile))

        if len(term) != 0:
            subID = term['id'][0].split(':')
            # Finds TYPEDEF stanzas and ignores them
            if len(subID) < 2:
                continue
            termID = term['id'][0].split(':')[-1]

            if 'alt_id' in term.keys() and termID in meshIDs:
                mimID = 'omim.disease.id:' + term['alt_id'][0].split(':')[-1]
                assocDict[termID].update([mimID])
        else:
            break
    logger.info(len(assocDict))
    return assocDict

def readArgs():
    """Reads the arguments provided by the user."""
    desc = """
    This program parses through source data and formats it
    for use in a neo4j Knowledgebase
    """
    p = argparse.ArgumentParser(description=desc, prog="parseCTD")
    # Required arguments
    p.add_argument("-i", "--infiles", required=True, nargs='+',
                   help="File with node information")
    p.add_argument("-o", "--outdir", required=True, 
                   help="Specifies the directory where the data is written.")
    # Optional arguments
    p.add_argument("-c", "--ctd_gene_file", required=False, help="CTD_genes.tsv file")
    p.add_argument("-e", "--entrez_file", required=False, help="gene_info file with entrez gene IDs")
    p.add_argument("-m", "--meshfiles", required=False, nargs='+', help="Directory with mesh information (mesh)")
    p.add_argument("-g", "--gold", default=False, action='store_true', 
                   required=False, help="Output Gold standard")
    p.add_argument("-v", "--verbose", default=False, help="Output verbose", action="store_true")
    args = p.parse_args()
    return args

def main():
    """ Main parsing function. """
    # Read args
    args = readArgs()
    INFILES = args.infiles
    OUTPUT_DIRECTORY = args.outdir
    GOLD = args.gold
    MESH_FILES = args.meshfiles
    GENE_INFO = args.entrez_file
    CTD_GENE = args.ctd_gene_file

    meshIDs = parseMESH(MESH_FILES)
    # Set output file name based on Gold Standard or not
    for INFILE in INFILES:
        if not GOLD:
            OUTFILE = path.join(OUTPUT_DIRECTORY,str(path.splitext(path.basename(INFILE))[0].split(".")[0]+".xref.edges.csv")) 
            #outFile = outFile + inFile.split('/')[-1][:-3] + 'xref.edges.csv'
        else:
            OUTFILE = path.join(OUTPUT_DIRECTORY,str(path.splitext(path.basename(INFILE))[0].split(".")[0]+".goldStd.csv"))
            #outFile = outFile + inFile.split('/')[-1][:-3] + 'goldStd.csv'

        logger.info(f"Output to:\t{OUTFILE}")

        # Generate valid meshIDs
        if INFILE.endswith('_ixns.tsv.gz'):
            assocDict = readIxns(INFILE)
            writeIxnEdges(assocDict, OUTFILE)
        elif INFILE.endswith('_diseases.tsv.gz'):
            writeFile = open(OUTFILE, 'w')
            if not GOLD:
                writeFile.write(
                    ':START_ID|:TYPE|source:string|occurrence:float|articles:string[]|:END_ID\n')
            else:
                writeFile.write('chemID(MeSH)\tdiseaseID(MeSH)\n')
            readTSV(INFILE, GENE_INFO, CTD_GENE, writeFile, meshIDs, GOLD)
        elif INFILE.endswith('.obo.gz'):
            idPairSet = parseMEDIC(INFILE, meshIDs)
            writeEdges(idPairSet, OUTFILE)
        else:
            idPairSet = readTSV(INFILE, GENE_INFO, CTD_GENE, 'NA', meshIDs, GOLD)
            writeEdges(idPairSet, OUTFILE)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s', 
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    main()
