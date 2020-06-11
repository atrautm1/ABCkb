#!/usr/bin/env python3

import collections
from parse_it import getTerm, parseMeshValue, parseTagValue, handle

def oboParser(oboFile, namespace):
    # modified from http://blog.nextgenetics.net/?e=6
    GOterms = collections.defaultdict(dict)
    myFile = handle(oboFile)
    keys = set()
    relationships = ['is_a', 'disjoint_from', 'xref']
    label = ''
    if namespace == 'ebi.chebi':
        label = 'Chemical' 
    if namespace == 'gene.ontology.go':
        label = 'Pathway'
    if namespace == 'disease.ontology.do' or namespace == 'human.phenotype.hpo':
        label = 'Phenotype'
    namespace = namespace.replace('.','_')
    # skip the file header lines
    getTerm(myFile)
    # Breaks when the term returned is empty, indicating end of file
    while 1: 
        term = parseTagValue(getTerm(myFile))

        if len(term) != 0:
            #remove obsolete terms
            if 'is_obsolete' in term:
                continue
            else:
                subID = term['id'][0].split(':')
            # Finds TYPEDEF stanzas and ignores them
            if len(subID) < 2:
                continue
            termID = term['id'][0]
            termName = ""
            try:
                termName = term['name'][0]
            except:
                pass
            termDef = ""
            keys.update(list(term.keys()))  

            if 'def' in term:
                termDef = term['def'][0].replace(
                    "\"", '')
                termDef = termDef.replace('\'', '')
                termDef = termDef.replace(';', '.')
                termDef = termDef.split('[')[0].strip()
            # addition of node label for pathway
            if 'namespace' in term:
                if 'biological_process' in term['namespace']:
                    label = 'Pathway'
                else:
                    label = '' 
            if label != '':
                GOterms[termID] = {'name': termName, 'def': termDef, 'synonyms': [
                ], 'edges': [], 'labels': set([label, namespace])}
            else:
                GOterms[termID] = {'name': termName, 'def': termDef, 'synonyms': [
                ], 'edges': [], 'labels': set([namespace])}

            # iterate over all tagged information for term
            if 'synonym' in term:
                termSynonyms = term['synonym']
                # only include exact synonyms (some are broad/narrow/related)
                # BUT some related are important, like those in ChEBI
                for synonym in termSynonyms:
                    if 'EXACT' in synonym:
                        synonym = synonym.replace('\"', '')
                        synonym = synonym.split('EXACT')[0].strip()
                        GOterms[termID]['synonyms'].append(
                            synonym)
            if 'is_a' in term:
                for edge in term['is_a']:
                    anEdge = edge.split()[0]
                    GOterms[termID]['edges'].append(('is_a', anEdge))
            if 'disjoint_from' in term:
                for edge in term['disjoint_from']:
                    anEdge = edge.split()[0]
                    GOterms[termID]['edges'].append(
                        ('disjoint_from', anEdge))
            if 'xref' in term:
                for edge in term['xref']:
                    anEdge = edge.split()[0]
                    if anEdge == 'KEGG':
                        thisEdge = edge.split()
                        anEdge = thisEdge[0] + '_' + thisEdge[1]
                    GOterms[termID]['edges'].append(
                        ('xref', anEdge))
            if 'intersection_of' in term:
                for edge in term['intersection_of']:
                    anEdge = edge.split()[0]
                    if '_' in anEdge:
                        edgeList = edge.split()
                        GOterms[termID]['edges'].append(
                            (edgeList[0], edgeList[1]))
                    # cases where intersection_of: singleWord ID
                    if anEdge.isalpha() and '_' not in anEdge:
                        edgeList = edge.split()
                        GOterms[termID]['edges'].append(
                            (edgeList[0], edgeList[1]))
                    elif ':' in anEdge:
                        GOterms[termID]['edges'].append(
                            ('intersection_of', anEdge))
            if 'relationship' in term:
                for edge in term['relationship']:
                    edgeList = edge.split()
                    relationship = edgeList[0]
                    anEdge = edgeList[1]
                    GOterms[termID]['edges'].append((relationship, anEdge))
        else:
            break
    print(len(GOterms))
    return GOterms