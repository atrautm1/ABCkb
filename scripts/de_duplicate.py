#!/usr/bin/env python3

"""
Author: Aaron Trautman
Date Created: 10112019
Module: Knowledgebase
File name: de_duplicate.py
Credits: Aaron Trautman
"""

import sys
import logging
import collections
from os import path, listdir

class DeDup():

    nodes = set()

    def __init__(self, directory):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
        if not check_directory(directory):
            self.logger.error("The provided directory either doesn't exist or is empty.")
            sys.exit(1)
        self.directory = directory

    def worker(self, suffix):
        files = [F for F in listdir(self.directory) if F.endswith(suffix+".csv") and F != "nih.nlm.ncbi.gene.nodes.csv"]
        self.dups = open(f"{self.directory}{suffix}.duplicates","w")
        self.comb_suff = open(f"{self.directory}{suffix}.psv","w")
        if suffix == "nodes":
            self.comb_suff.write("source_id:ID|name:string|synonyms:string[]|:LABEL\n")
        if not files:
            self.logger.error(f"I didn't find any files ending with {suffix}")
            sys.exit(1)
        print("File Lines Useful_Info Empty_Info")
        for who in files:
            arr, you = self.parse_file(path.join(self.directory, who), suffix)
            # if arr == 1:
            #     print(f"{who}: is empty")
            # elif not you == arr:
            print(who, arr, you)
        self.dups.close()
        self.comb_suff.close()

    def parse_file(self, file, suffix):
        dic = collections.defaultdict(list)
        en = 0 # Empty Nodes
        n = 0 # Line count
        x = -1 # 
        # dups = open(f"{file}.duplicates","w")
        if suffix == "nodes":
            x = 1 # Name position
        with open(file, "r") as f:
            for line in f:
                li = line.strip().split("|")
                if li[0].startswith("source_id"):
                    continue
                else:
                    if not li[0] in self.nodes and li[x]:
                        self.nodes.add(li[0])
                        self.comb_suff.write(line)
                    else:
                        self.dups.write(f"{li[0]},{li[x]},{dic[li[0]]}\n")
                        en += 1
                    #dic.update({li[0]: li[x]})
                    dic[li[0]].append(li[x])
                n += 1
        # dups.close()
        return n, en

def check_directory(directory):
    if path.exists(directory) and path.isdir(directory):
        if not listdir(directory):
            return False
        return True
    return False

if __name__ == "__main__":
    DIRECTORY = sys.argv[1]
    D = DeDup(DIRECTORY)
    D.worker("nodes")
    #D.worker("edges")




