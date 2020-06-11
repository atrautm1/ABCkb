
"""
Use: python bareSourceParser.py -i <dir>/genemap2.txt \
     -c <dir>/mim2gene.txt -o <out_dir> -n omim.disease
"""

import collections
import csv
from parse_it import handle

def omim_parser(inFile, geneFile, namespace):
    """Parses the omim ontology files and yields nodes/edges"""
    omimDict = collections.defaultdict(dict)
    counter = 0
    # gene is unique, add each disease as unique too
    # geneMap2.txt, mim2gene.txt
    count = 0
    #with handle(open(inFile, 'r')) as inFile:
    with handle(inFile) as inFile:
        reader = csv.DictReader(decomment(inFile), delimiter="\t")
        for row in reader:
            try:
                symbols = row['Gene Symbols'].replace(",","").split(" ")
            except:
                print(row)
                exit(1)
            gene_name = row['Gene Name']
            gene_mim = "{}.id:{}".format(namespace, row['MIM Number'])
            try:
                disorders = row['Phenotypes'].split(";")
            except AttributeError:
                disorders = row['Phenotypes']

            omimDict[gene_mim] = {'name': gene_name, 'synonyms': symbols, 'edges': [
            ], 'labels': set(['Gene', namespace.replace('.', '_')])}  # 'def': '',
            # For disease, multiple commas, check if last element is a number
            if type(disorders) == list:
                for element in disorders:
                    get_MIM = element.split(',')
                    if len(get_MIM) > 1:
                        # Disorders can have multiple commas, check last instead of
                        # 2nd element
                        disease_Name = ''.join(get_MIM[:-1])
                        disease_mim = get_MIM[-1][:-3].strip()
                        if not disease_mim.isdigit():
                            count += 1
                            continue
                        else:
                            disease_mim = namespace + '.id:' + disease_mim
                            if disease_mim not in omimDict:
                                omimDict[disease_mim] = {
                                    'name': disease_Name, 'def': '', 'synonyms': [], 'edges': [], 'labels': set(['Phenotype', namespace.replace('.', '_')])}
                                omimDict[disease_mim]['edges'].append(
                                    ('associated_with', gene_mim))
                            else:
                                omimDict[disease_mim]['edges'].append(
                                    ('associated_with', gene_mim))
                            omimDict[gene_mim]['edges'].append(
                                ('associated_with', disease_mim))
    counter = 0
    #with handle(open(geneFile, 'r')) as edgeFile:
    with handle(geneFile) as edgeFile:
        for line in edgeFile:
            if line.startswith('#'):
                continue
            else:
                column_List = line.split('\t')
                mimType = column_List[1].strip()
                if mimType == 'gene' and column_List[2].strip() != '':
                    mimID = namespace + '.id:' + column_List[0].strip()
                    geneID = 'nih.nlm.ncbi.gene.id:' + column_List[2].strip()
                    geneSymbol = column_List[3].strip()
                    try:
                        omimDict[mimID]['edges'].append(('xref', geneID))
                    except:
                        counter += 1
                        omimDict[mimID] = {'name': geneSymbol,
                                           'def': '', 'synonyms': [], 'edges': [], 'labels': ['Gene']}
                        omimDict[mimID]['edges'].append(('xref', geneID))
    print("Gene nodes added:\t" + str(counter))
    print(count)
    return omimDict

def decomment(csvfile):
    """
    Ignores lines starting with # except for the header
    """
    for row in csvfile:
        if row.startswith("# Chromosome\t"):
            yield row
        else:
            raw = row.split('#')[0].strip()
            if raw: yield raw

if __name__ == "__main__":
    BASE_DIRECTORY = "/Users/atrautm1/Desktop/testdir/omimV05162019/"
    INFILE = BASE_DIRECTORY+"genemap2.txt"
    GENEFILE = BASE_DIRECTORY+"mim2gene.txt"
    NAMESPACE = "omim.disease"
    ODICT=omim_parser(INFILE,GENEFILE,NAMESPACE)
    for k,v in list(ODICT.items())[0:10]:
        print(k,v)