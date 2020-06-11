#!/usr/bin/env python3

"""
Author: Aaron Trautman
Date Created: 10142019
Module: Knowledgebase
File name: ctd.py
Credits: Aaron Trautman
"""

import csv
import logging
from os import path
from parse_it import handle, check_file, check_directory

NAMESPACE = {
    "gene": "nih.nlm.ncbi.gene.id:",
    "omim": "omim.disease.id",
    "mesh": ""
}

class Parser():

    def __init__(self, file, outdir):
        """
        Class for parsing a ctd file
        takes two arguments
        1. A CTD file to parse
        2. An output directory
        """
        self.logger = logging.getLogger(__name__)
        if not check_file(file):
            self.logger.error("The provided file either doesn't exist or is empty.")
            exit(1)
        if not check_directory(outdir):
            self.logger.error("Output directory not found. Exiting...")
            exit(1)
        self.file = file
        self.nodes = None
        self.a2b = {"nodes":None, "affect":set(),"increase":set(),"decrease":set(),"xref":set(),"marker/mechanism":set(), "therapeutic":set()}
        basename = str(path.splitext(path.basename(self.file))[0].split(".")[0]+".edges.csv")
        outfile = path.join(outdir, basename)
        self.outfile = open(outfile, "w")
        self.outfile.write(":START_ID|:TYPE|source:string|predicate:string[]|articles:string[]|:END_ID\n")
        self.logger.info(f"Writing edges to: {outfile}")

    def parse(self):
        """
        Reads a file defined by the class instance and parses nodes and relationships
        """
        with handle(self.file) as infile:
            reader = csv.DictReader(decomment(infile), delimiter="\t")
            for row in reader:
                predicate = self.__check_predicate_exists(row)
                if predicate:
                    nodes = self.parse_nodes(row)
                    if self.nodes != nodes:
                        if self.nodes:
                            self.write_out()
                    self.nodes = nodes
                    # self.parse_relationship(row)
                    evidence = ""
                    if "PubMedIDs" in row.keys():
                        if row["PubMedIDs"]:
                            evidence = row["PubMedIDs"]
                    self.parse_relationship(predicate, evidence.replace("|",";"))
                    # except KeyError:
                    #     if "PubMedIDs" in row.keys():
                    #         self.a2b["xref"].add(("xref", row["PubMedIDs"].replace("|",";")))
                    #     else:
                    #         self.a2b["xref"].add(("xref", ""))
        self.write_out()
        self.outfile.close()
    
    def __check_predicate_exists(self, row):
        """
        Checks that a predicate exists
        """
        # Used by some of the files to indicate a direct connection
        if "DirectEvidence" in row.keys(): 
            return row["DirectEvidence"]
        elif "InteractionActions" in row.keys(): # [affect,increase,decrease]+predicate
            return row["InteractionActions"]
        return "xref" # chem_go_enriched does not contain a predicate

    def write_out(self):
        """
        Writes a pair of nodes with their predicates
        """
        start = self.nodes[0]
        end = self.nodes[1]
        source = "ctd"
        for item in self.a2b.keys():
            pmids = []
            preds = []
            if self.a2b[item]:
                predicates = self.a2b[item]
                for pred in predicates:
                    preds.append(pred[0])
                    pmids.append(pred[1])
                try:
                    edge = f"{start}|{item}|{source}|{';'.join(preds)}|{';'.join(pmids)}|{end}\n"
                    self.outfile.write(edge)
                except TypeError:
                    self.logger.error(f"Problem with {self.a2b}")
                    exit(1)
        for k in self.a2b:
            self.a2b[k] = set()

    def parse_nodes(self, row):
        """
        Function to parse the nodes
        !change namespaces at somepoint!
        """
        keys = row.keys()
        if "ChemicalID" in keys:
            nodeA = row["ChemicalID"]
            if "GOTermID" in keys:
                return (nodeA, row["GOTermID"])
            elif "DiseaseID" in keys:
                nodeB = row["DiseaseID"].replace("MESH:",NAMESPACE["mesh"]).replace("OMIM",NAMESPACE["omim"])
                return (nodeA, nodeB)
            elif "GeneID" in keys:
                nodeB = NAMESPACE["gene"]+row["GeneID"]
                return (nodeA, nodeB)
            else:
                self.logger.error(f"Unsure what end node is in row {row}")
                exit(1)
        elif "GeneID" in keys:
            nodeA = NAMESPACE["gene"]+row["GeneID"]
            nodeB = row["DiseaseID"].replace("MESH:",NAMESPACE["mesh"]).replace("OMIM",NAMESPACE["omim"])
            return (nodeA, nodeB)
        self.logger.error(f"Unsure what start node is in row {row}")
        exit(1)

    def parse_relationship(self,predicate,pmid):
        """
        Function to parse relationships given a predicate and a pmid
        """
        rels = predicate.split("|")
        for rel in rels:
            rex = rel.split("^")
            base = rex[0].rstrip("s")
            if base in ("affect", "increase", "decrease"):
                self.a2b[base].add((rex[1], pmid))
            else:
                self.a2b[base].add(("", pmid))

def decomment(csvfile):
    """
    Ignores lines starting with # except for the header
    """
    for row in csvfile:
        if row.startswith("# Fields:"):
            yield next(csvfile)
        else:
            raw = row.split('#')[0].strip()
            if raw: 
                yield raw

# if __name__ == "__main__":
#     logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s',
#                             datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
#     o = "/Users/atrautm1/ctd/new/"
#     files = [
#     "CTD_chem_gene_ixns.tsv.gz", #Chem to gene
#     "CTD_chem_go_enriched.tsv.gz", # chem to go
#     "CTD_chemicals_diseases.tsv.gz", # chem to disease(omim[if omim, no pmid] or mesh)
#     "CTD_genes_diseases.tsv.gz", ]# gene to disease
#     #"CTD_genes_pathways.tsv.gz"]
#     for f in files:
#         ct = ctd("/Users/atrautm1/Documents/workStuff/github/MicrobiomeKB/Knowledgebase/docker/data/ctd/"+f,o)
#         ct.parse()