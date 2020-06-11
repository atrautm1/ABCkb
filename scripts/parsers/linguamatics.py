#!/usr/bin/python -tt

from collections import defaultdict
import codecs
import getopt
import sys
import os
import logging
import csv
from nltk.stem.snowball import SnowballStemmer
import nltk

def convertID(object_id, line_num):
    """
    Takes an ID, checks it against a dictionary, and returns a new ID
    """

    if object_id == "":
        logging.warn(f"Empty object_id at line {line_num}")
        return None

    # Conversion/Normalization dictionary for source identifiers
    idConversion = {'nlm': '', 'chebi': 'CHEBI:', 
                    'nal_thesaurus': 'NAL:',
                    'ncbi': 'nih.nlm.ncbi.gene.id:', 'go': '',
                    'mp': '', 'hp': '', 
                    'NCBI-Taxonomy-taxid-3193': 'nih.nlm.ncbi.taxonomy.id:'}
    
    object_id_list = object_id.split(".")
    
    if "." in object_id:
        n = object_id_list[1].split("_")[0] # Steven says blame Aaron for this
    else:
        n = object_id.split("_")[0]

    if object_id_list[0] in idConversion:
        new_object_id = "".join([idConversion[object_id_list[0]],n])
        return new_object_id
    
    logging.warn(f"Unkown prefix \'{object_id_list[0]}\' at line {line_num}")
    return None

def filterPredicates(predicatePhrase):
    verb_endings = ('s', 'es', 'er', 'e', 'ed', 't', 'ur', 'rn', 'ng', 'ing', 'fy', 'in', 'nd', 'ck',
                    'ic', 'ad', 'ld', 'ar', 'lp', 'ow', 'en', 'ish', 'ply', 'ize', 'or', 'ts', 'rd', 'ry', 'rk', 'ir', 'rm')
    stemmer = SnowballStemmer("english")
    pos_pred = None
    # Predicate filters:
    # 1) Phrases split by whitespace
    text = nltk.word_tokenize(predicatePhrase)
    tagged_text = nltk.pos_tag(text, tagset="universal")
    #print(tagged_text)
    predicateList = predicatePhrase.split()
    sortedList = sorted(predicateList, key=len)
    #print(sortedList)
    
    # predicate = stemmer.stem(sortedList[-1].lower())
    predicate = ''
    # 2) Homogenize case to lower and select longest token
    # WHAT IF IT'S NOT THE LONGEST TOKEN
    pos_pred = sortedList[-1].lower()
    # 3) Ignore '-ly' suffix (commonly extracted)
    if pos_pred.endswith('ly'):
        # If '-ly' is only option, ignore
        if not len(sortedList) == 1:
            #filtered_preds.add(pos_pred)
        # If other option, test again for '-ly'
        #else:
            pos_pred = sortedList[-2].lower()
            # Check for 'ly' suffix again
            if pos_pred.endswith('ly') and len(sortedList) > 2:
                pos_pred = sortedList[-3].lower()
                # 5) Stem predicate
                predicate = stemmer.stem(pos_pred.lower())
            else:
                predicate = stemmer.stem(pos_pred.lower())
    # 4) Test for and split on '-'
    if '-' in pos_pred:
        delimited = pos_pred.split('-')
        orderDelimited = sorted(delimited, key=len)
        longest = orderDelimited[-1].lower()
        secondLong = orderDelimited[-2].lower()
        # 6) If longest token ends with verb suffix, stem and keep
        if longest.endswith(verb_endings):
            predicate = stemmer.stem(longest)
        elif not longest.endswith(verb_endings) and secondLong.endswith(verb_endings):
            predicate = stemmer.stem(secondLong)
        # Otherwise add to overall FP predicate set
        #else:
            #filtered_preds.add(pos_pred)
    # Otherwise, check if pred has verb ending and add
    elif pos_pred.endswith(verb_endings):
        predicate = stemmer.stem(pos_pred)
    elif not pos_pred.endswith(verb_endings) and len(sortedList) > 1:
        sec_pos_pred = sortedList[-2].lower()
        if sec_pos_pred.endswith(verb_endings):
            predicate = stemmer.stem(sec_pos_pred)
    #else:
        #filtered_preds.add(pos_pred)
        # Ignores blankset and filterset
    #return pos_pred, tagged_text
    return predicate, tagged_text   

def tsvParser(tsv_File, new_rel_dict):
    """
    Method input: Linguamatics TSV Result files
    Each TSV file should follow the format
        (object, predicate, subject) --> (col 1-3, col 4, col 5-7)
        followed by hit text (col7) and docID (col10)
    Method returns a relationship dictionary of format
        { predicate : { (subjID, objID) :
        [[objectTerm,subjectTerm,hitText,doc,location], ... ]}
    """
    ## file used has the object and subject reversed
    ## object (col5-7), predicate(col4), and subject(col1-3)
    ## docID (col12), hit text (col16)

    
    verb_endings = ('s', 'es', 'er', 'e', 'ed', 't', 'ur', 'rn', 'ng', 'ing', 'fy', 'in', 'nd', 'ck',
                    'ic', 'ad', 'ld', 'ar', 'lp', 'ow', 'en', 'ish', 'ply', 'ize', 'or', 'ts', 'rd', 'ry', 'rk', 'ir', 'rm')
    rel_Dict = defaultdict(dict)
    tags = []
    unfiltered_preds = set()   # Set of predicates
    filtered_preds = set()
    langs = set()   # Languages being used in the article hits
    # Possible languages from Agricola
    langCodes = set(["spa", "fre", "rus", "swe", "chi", "jpn", "afr",
                     "ger", "tur", "por", "ita", "nor", "ind", "cat", "fin", "dan"])
    otherLang = 0
    unknown_location = False
    #logging.info("Working on:\t%s" % tsv_File.split('/')[-1])
    n = 2
    with open(tsv_File, 'r') as i:
        reader = csv.DictReader(i, delimiter='\t')
        for row in reader:
            hit = row["Hit"].replace('\'', '').replace('|', '').replace("\"", '')
            hit_language = hit.split("... ")[-1]
            subjID = convertID(row["[SNID] Subject"], n)
            objID = convertID(row["[SNID] Object"], n)
            if hit_language.lower() in langCodes:   # Exclude non-english hits
                langs.add(hit_language)
                continue
            elif subjID == None or objID == None:   # Skip results with blank ids
                continue
            else:
                objectTerm = (row["[PT] Object"],row["Object"])
                subjectTerm = (row["[PT] Subject"],row["Subject"])
                try:
                    location = row["Location"]
                except:
                    if "abstract" in tsv_File.lower():
                        location = "abstract"
                    elif "title" in tsv_File.lower():
                        location = "title"
                    else:
                        unknown_location = True
                        location = "unknown"
                doc = row["Doc"]
                predicatePhrase = row["Predicate"]
                # ***** ***** Aaron made it to here.. woohoo! Jul 2 ***** *****
                # Add to overall, unfiltered set of predicates
                unfiltered_preds.add(predicatePhrase)
                # Filter the predicates
                predicate, tagged_text = filterPredicates(predicatePhrase)
                # Add filtered predicate to list
                filtered_preds.add(predicate)
                tags.append(tagged_text)

                preds = [rel["predicate"] for rel in new_rel_dict[(subjID,objID)]]

                if predicate not in preds:
                    new_rel_dict[(subjID,objID)].append({"predicate":predicate, 
                                                         "pmid":[doc], "evidence":[f"{location}:{hit}"]})
                else:
                    ind = preds.index(predicate)
                    new_rel_dict[(subjID,objID)][ind]["pmid"].append(doc)
                    new_rel_dict[(subjID,objID)][ind]["evidence"].append(f"{location}:{hit}")

                # change set for analysis of blanks
                #if predicate == '':
                #    filtered_preds.add(predicatePhrase)
                #    continue

                if predicate:
                    if predicate not in rel_Dict and (subjID, objID) not in rel_Dict[predicate]:
                        rel_Dict[predicate][(subjID, objID)] = [
                            [objectTerm, subjectTerm, predicatePhrase, hit, doc, location]]
                    elif predicate in rel_Dict and (subjID, objID) not in rel_Dict[predicate]:
                        rel_Dict[predicate][(subjID, objID)] = [
                            [objectTerm, subjectTerm, predicatePhrase, hit, doc, location]]
                    elif predicate in rel_Dict and (subjID, objID) in rel_Dict[predicate]:
                        rel_Dict[predicate][(subjID, objID)].append(
                            [objectTerm, subjectTerm, predicatePhrase, hit, doc, location])
            n += 1
    if unknown_location:
        logging.warn("Location of text mining hit undiscernable; set to unknown")
    return rel_Dict, langs, unfiltered_preds, filtered_preds, new_rel_dict


def multiFileParser(filePath, tsv_Out):
    """
    This method performs a directory walk to find sub-directories
    and files ending in .tsv (linguamatics results).
    It then creates a "global" dictionary of unique relationships
    described by their predicates
    """
    rel_Dict = defaultdict(dict)
    new_rel_dict = defaultdict(list)
    # PARSE THROUGH MULTIPLE DIRECTORIES
    fileList = []
    overall_Langs = set()
    overall_preds = set()
    filter_Preds = set()

    for root, dirs, files in os.walk(filePath):
        for name in files:
            if name.endswith(".tsv"):
                fileList.append(os.path.join(root, name))

    tot = len(fileList)
    curr = 1
    for oneFile in fileList:
        logging.info(f"Processing {curr} of {tot}:\t{oneFile.split('/')[-1]}")
        curr += 1
        parsed_File, langs, preds, filtered, new_rel_dict = tsvParser(oneFile, new_rel_dict)
        overall_Langs.update(langs)
        overall_preds.update(preds)
        filter_Preds.update(filtered)
        for predicate, nodeDict in parsed_File.items():
            for nodePair, hitList in nodeDict.items():
                if predicate not in rel_Dict and nodePair not in rel_Dict[predicate]:
                    rel_Dict[predicate][nodePair] = hitList
                elif predicate in rel_Dict and nodePair not in rel_Dict[predicate]:
                    rel_Dict[predicate][nodePair] = hitList
                elif predicate in rel_Dict and nodePair in rel_Dict[predicate]:
                    rel_Dict[predicate][nodePair] = rel_Dict[
                        predicate][nodePair] + hitList
    stats = f"""
    Languages:\n{overall_Langs}
    Number of unfiltered predicates:\t{len(overall_preds)}
    Number of filtered predicate types:\t{len(filter_Preds)}
    """
    logging.info(stats)
    predFile = codecs.open(
        tsv_Out + 'unFilteredPredsList.csv', 'w', encoding='utf-8')

    for verb in overall_preds:
        predFile.write(verb + '\n')
    predFile.close()

    return rel_Dict, new_rel_dict


def findPredicateDataThreshold(predicateTupleList, relTotal, tsv_Out, stat):
    predicateTupleList.sort(reverse=True)
    ninetyFive = codecs.open(tsv_Out + stat + "95percent", "w", "utf-8")
    five = codecs.open(tsv_Out + stat + "5percent", "w", "utf-8")
    cutoff = relTotal * .95
    countUp = 0
    for couple in predicateTupleList:
        outLine = "%d\t%s\n" % (couple[0], couple[1])
        countUp += couple[0]
        if countUp <= cutoff:
            ninetyFive.write(outLine)
        else:
            five.write(outLine)
    ninetyFive.close()
    five.close()

def check_directory(directory):
    if os.path.exists(directory) and os.path.isdir(directory):
        if not os.listdir(directory):
            return False
        return True
    return False

def main(argv):
    tsv_In = ""
    tsv_Out = ""

    try:
        opts, args = getopt.getopt(
            argv, "hi:o:", ["help", "tsvInput=", "tsvOutput="])
    except getopt.GetoptError:
        print('python linguaResults.py -i <linguaTSVFile directory> -o <output prefix>\n')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('python linguaResults.py\
             -i <linguamatics_directory_with_tsv_outputs> -o <outputdirectory/prefix>\n\
             Example usage: python linguaResults.py\
             -i /Path/to/results/1p2c\
             -o /Path/to/results/1p2c/plant2chem_rels')
            sys.exit()
        elif opt in ("-i", "--tsvInput"):
            tsv_In = arg
            if not check_directory(tsv_In):
                logger.warn("I didn't find any text-mined files to parse...")
                sys.exit()
        elif opt in ("-o", "--tsvOutput"):
            tsv_Out = arg

    if not tsv_In or not tsv_Out:
        logger.error(f"Please provide input (-i path/to/lingua/files) and output (-o output prefix)\n\
            -i: {tsv_In} \n-o: {tsv_Out} ")
        sys.exit(2)

    logging.info(f"Source directory:\t{tsv_In}")
    # Dictionary structure: { predicate : { (subjID, objID) : [
    # [objectTerm,subjectTerm,hitText,doc,location], ... ]}
    full_List, new_rel_dict = multiFileParser(tsv_In, tsv_Out) # Generates the dict

    # include BOTH files when loading neo4j instance to test for all vs
    # filtered
    rel_file = codecs.open(
        filename=f"{tsv_Out}_collapsed_edges.psv", mode="w", encoding="utf-8"
    )

    header=":START_ID|source:string|predicate:string[]|evidence:string|:END_ID\n"
    rel_file.write(header)
    consolidated_edges = 0
    for k,v in new_rel_dict.items():
        preds = [rel["predicate"] for rel in v]
        evidences = str(v)

        sID = k[0]
        eID = k[1]
        rel_file.write(
            f"{sID}|text_mined|{';'.join(preds)}|{evidences}|{eID}\n"
        )
        consolidated_edges += 1
    graph_in = codecs.open(
        tsv_Out + 'Finaledges_mined_rels.psv', 'w', encoding='utf-8')
    graph_filtered = codecs.open(
        tsv_Out + 'Finaledges_filtered_mined_rels.psv', 'w', encoding='utf-8')
    # Header for pipe separated value file (import into Neo4j)

    neo4jEdgeHeader = ":START_ID|:TYPE|source:string|occurrence:float|articles:string[]|evidence:string[]|:END_ID\n"
    graph_in.write(neo4jEdgeHeader)
    graph_filtered.write(neo4jEdgeHeader)

    total_rels = 0
    agricolaIDs = set()
    agricola_count = set()
    pubmed_count = set()
    predCountsList = []
    locFilter = []
    locFilterTotal = 0
    source = "Text_Mined"
    locationSet = set(['Abstract', 'Other Abstract',
                       'Standard Abstract', 'Title', ' Title, Title'])

    uniqueNodePairSet = set()
    absoluteRelCount = 0
    # { predicate : { (subjID, objID) : [[objectTerm,subjectTerm,hitText,doc,location], ... ]}}
    #for predicate, rel_dict in full_List.iteritems(): not supported in py3
    for predicate, rel_dict in full_List.items():
        absolutePredicateCount = 0
        # number of predicate: nodePairs to be written as rels
        total_rels += len(rel_dict)
        for nodePair in rel_dict:
            absoluteRelCount += len(rel_dict[nodePair])
            absolutePredicateCount += len(rel_dict[nodePair])
            if (nodePair[1], nodePair[0]) not in uniqueNodePairSet:
                uniqueNodePairSet.add(nodePair)
            # create a list to write out SINGLE collapsed relationship to
            evidenceList = []
            evidenceSet = set()
            start_id = nodePair[0]
            end_id = nodePair[1]
            # perform weighting for source at this stage
            # absolOccurrence is absolute count, without weighting
            absolOccurrence = len(rel_dict[nodePair])
            occurrence = 0
            for linguaHit in rel_dict[nodePair]:
                obj = linguaHit[0][1]  # last index [0=preferred,1=actual]
                pred = linguaHit[2]
                subj = linguaHit[1][1]  # last index [0=preferred,1=actual]
                article = linguaHit[4].strip()
                location = linguaHit[5].strip()
                if 'Abstract' in location:
                    occurrence += 0.5
                if 'Title' in location:
                    occurrence += 0.75
                # Sanity check for location anomalies
                # if location not in locationSet:
                #    print "PROBLEM:\t", location + '\t' + pred
                #    print linguaHit
                text_hit = linguaHit[3]
                evidence = article + "~" + location + "~" + obj + \
                    "~" + pred + "~" + subj + "~" + text_hit
                evidenceList.append(evidence)
                evidenceSet.add(article)
                # NEEDS MODIFICATION
                # look for duplicates between pubmed and agricola
                if article.isdigit():
                    pubmed_count.add(article)
                else:
                    if article == 'Doc':  # skip column header
                        continue
                    agricola_count.add(article)
                    try:
                        if article[3].isdigit():
                            agricolaIDs.add(article[0:3])
                        else:
                            agricolaIDs.add(article[0:4])
                    except:
                        print(article)
                        print(linguaHit)
                        break
            # Filter by occurrence
            if occurrence <= 1:
                # accounts for 2 abstract hits (0.5+0.5) and above
                graph_filtered.write(start_id + '|' +
                                     predicate + '|' +
                                     source + '|' +
                                     str(occurrence) + '|' +
                                     ';'.join(evidenceSet) + '|' +
                                     ';'.join(evidenceList) + '|' +
                                     end_id + '\n')
            else:
                graph_in.write(start_id + '|' +
                               predicate + '|' +
                               source + '|' +
                               str(occurrence) + '|' +
                               ';'.join(evidenceSet) + '|' +
                               ';'.join(evidenceList) + '|' +
                               end_id + '\n')
                locFilter.append((absolutePredicateCount, predicate))
                locFilterTotal += absolutePredicateCount
        predCountsList.append((absolutePredicateCount, predicate))
    graph_in.close()
    graph_filtered.close()
    rel_file.close()
    stats = f"""
    # consolidated Predicates:\t{consolidated_edges}
    # of Unique Predicates:\t{str(len(full_List))}
    # of Unique Node Pairs:\t{str(len(uniqueNodePairSet))}
    # of Unique Triples(subj,pred,obj) aka Edges:\t{str(total_rels)}
    # of Absolute Relationship Occurrences(Unweighted):\t{str(absoluteRelCount)}
    Agricola ID-prefixes:\n {agricolaIDs}
    # of Unique Agricola articles:\t{str(len(agricola_count))}
    # of Unique Pubmed articles:\t{str(len(pubmed_count))}
    """
    logging.info(stats)
    # Find predicates accounting for 95% of data
    findPredicateDataThreshold(locFilter, locFilterTotal, tsv_Out, 'filtered')
    findPredicateDataThreshold(
        predCountsList, absoluteRelCount, tsv_Out, 'unfiltered')


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s', 
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    main(sys.argv[1:])