#!/usr/bin/env python3

"""
Common functions
"""

import collections
import gzip
from zipfile import ZipFile
import logging
from os import path, listdir

def check_file(file):
    if path.exists(file) and path.isfile(file):
        return True
    return False

def check_directory(directory):
    if path.exists(directory) and path.isdir(directory):
        if not listdir(directory):
            return False
        return True
    return False

def handle(filehandle):
    """
    File handling method for mix of files.
    """
    logging.info("handling {}".format(filehandle))
    if filehandle.endswith(".gz"):
        return gzip.open(filehandle, mode="rt")
    elif filehandle.endswith(".zip"):
        with ZipFile(filehandle) as myzip:
            records = myzip.infolist()
            if len(records) == 1:
                return myzip.open(records[0])
            logging.error("zip fail")
    return open(filehandle, "r")

def getTerm(stream):
    """Takes file stream and forms arrays for each stanza of obo formatted file.
    Each element of the array is a line of the stanza excluding [Term] """
    # decode at this point .decode('utf-8')
    block = []
    for line in stream:
        #line = line.decode(encoding='utf-8')
        # or line.strip() == "[Typedef]":
        if line.strip() == "[Term]" or line.strip() == "[Typedef]" or line.strip() == "*NEWRECORD":
            break
        else:
            if line.strip() != "":
                block.append(line.strip())
    return block

def parseTagValue(term):
    """Generates dictionary of tags for term stanza from OBO files.
    {key=(tag):value=(value)}"""
    data = {}
    for line in term:
        tag = line.split(': ', 1)[0].strip()
        # print tag
        value = line.split(': ', 1)[1].strip()
        if not tag in data.keys():
            data[tag] = []
        data[tag].append(value)
    return data


def parseMeshValue(term):
    """Generates dictionary of tags for term stanza from MeSH flat files.
    {key=(tag):value=(value)}
    """
    data = collections.defaultdict(list)
    for line in term:
        items = line.split("= ", 1)
        tag = items[0].strip()
        try:
            value = items[1].strip()
        except:
            continue
        data[tag].append(value)
    return data


def parseTrees(F):
    """
    Parses mtrees201*.bin and returns two dictionaries:
        parentDict = {mn:set(parentMNs)}
        mn2desc = {mn:set()}
    """
    parentDict = collections.defaultdict(set)
    mn2desc = collections.defaultdict(str)  # really desc2mn?
    with handle(F) as treeFile:
        for line in treeFile:
            line = line.split(';')
            heading = line[0].strip()
            mn = line[1].strip()
            mn2desc[heading] = mn
            partialMn = mn.split('.')
            # Banking on it returning 1 if no . exists
            if len(partialMn) == 1:
                parentDict[mn] = set()
            elif len(partialMn) > 1:
                parent = '.'.join(partialMn[0:-1])
                parentDict[mn].add(parent)
    return parentDict, mn2desc

def addNodeLabel(childTree, tnr, desc2tnr, label):
    """
    recursively add label to all children of term
    Eg.- Plant node label for all Plantae
    """
    for child in childTree[tnr]['children']:
        childTree[tnr]['labels'].add(label)
        if child in desc2tnr:
            nextTnr = desc2tnr[child]
        addNodeLabel(childTree, nextTnr, desc2tnr, label)

def addLabel(taxChildrenTree, childSet, taxID):
    for child in taxChildrenTree[taxID]:
        childSet.add(child)
        addLabel(taxChildrenTree, childSet, child)