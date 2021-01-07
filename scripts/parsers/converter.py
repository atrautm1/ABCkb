#!/usr/bin/env python3

"""
Author: Aaron Trautman
Date Created: 08132020
Module: Knowledgebase
File name: converter.py
Credits: Aaron Trautman
"""

import logging
import csv
from collections import defaultdict
from parse_it import handle

class converter():
    __paths = {
        "GENE:OMIM:MONDO",  #Gene to phene to phene
        "OMIM:GENE",    # Gene to gene
        "OMIM:MONDO"    # Phene to phene
    }
    def __init__(self, converter_directory, path, a, b):
        pass

    def generate_conversion_files(self,):
        pass

    def convert_id(self):
        pass



if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s', 
                        datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    BASE_DIRECTORY = "docker/data"
    GENE_FILE = f"{BASE_DIRECTORY}/ncbi_gene/mim2gene_medgen.gz"
    MONDO_FILE = f"{BASE_DIRECTORY}/mondo/mondo.obo"
    CONVERTER_DIRECTORY = f"{BASE_DIRECTORY}/converter"
    
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
                    omim2gene[MID].add(GID)
                elif row["type"] == "phenotype":
                    gene2omim[GID].add(MID)
    with handle(MONDO_FILE) as mf:
        omim_id = []
        mondo_id = ""
        is_obsolete = False
        for line in mf:
            if line.startswith("[Term]"):
                if mondo_id and omim_id and not is_obsolete:
                    for om in omim_id:
                        omim2mondo[om] = mondo_id.lower()
                    omim_id = []
                    mondo_id = ""
                is_obsolete = False
            elif line.startswith("id:"):
                mondo_id = line.strip().split("id: ")[1]
            elif line.startswith("xref: OMIM"):
                omim_id.append(line.split(" ")[1].split(":")[1])
            elif line.startswith("is_obsolete"):
                is_obsolete = True
    print(len(omim2mondo))
    print("All done!")
    for k,v in list(omim2gene.items())[0:10]:
        print(k,v)

