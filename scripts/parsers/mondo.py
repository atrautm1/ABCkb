#!/usr/bin/env python3

"""
Author: Aaron Trautman
Date Created: 01122020
Module: Knowledgebase
File name: mondo.py
Credits: Aaron Trautman
"""

import json
from parse_it import handle

class Parser():

    def __init__(self,):
        self.nodeDict = {}

    def parse(self,mondoFile):
        #mondo_json = json.load(mondoFile)
        n = 0
        p = 0
        labels = set(["mondo","Phenotype"])
        sources = set()
        synonyms = set()
        nodeID = ""
        name = ""
        edges = []
        linkTypes = set()
        link2id = {"mesh":"", "mp":"MP","doid":"DOID","mondo":"MONDO",
        "meddra":"MEDDRA","hp":"HP","pato":"PATO", "omim":"omim.disease.id"}
        obsolete = False
        term = False
        props = ["id","name","synonym","xref","is_a"]
        for line in mondoFile:
            if line.startswith("[Term]") and term:
                if not obsolete:
                    self.nodeDict[nodeID] = {"name":name, "synonyms":list(synonyms), "edges":edges,
                                             "labels":labels}
                edges = []
                synonyms = set()
                obsolete = False
            elif line.startswith("id"):
                term = True
                nodeID = line.strip().split("id: ")[1]
            elif line.startswith("name"):
                name = line.strip().split("name: ")[1]
            elif line.startswith("synonym"):
                synonyms.add(line.split('\"')[1])
            elif line.startswith("xref"):
                nodeOut = line.split(" ")[1]
                linkType = nodeOut.split(":")[0].lower()
                edgeType = "xref"
                #predicate = line.split('\"')
                if linkType in link2id.keys():
                    outNodeID = nodeOut.split(":")[1]
                    linkTypes.add(linkType)
                    edges.append(("xref",str(link2id[linkType]+":"+outNodeID)))
            elif line.startswith("is_a"):
                nodeOut = line.split(" ")[1]
                linkType = nodeOut.split(":")[0].lower()
                if linkType in link2id.keys():
                    outNodeID = nodeOut.split(":")[1]
                    linkTypes.add(linkType)
                    edges.append(("is_a",nodeOut))
            elif line.startswith("is_obsolete"):
                obsolete = True
        self.nodeDict[nodeID] = {"name":name, "synonyms":list(synonyms), "edges":edges,
                                             "labels":labels}
                                             
        return self.nodeDict

if __name__ == "__main__":
    mFile = "docker/data/mondo/mondo.obo"
    parser = Parser()
    parser.parse(handle(mFile))