#!/usr/bin/env python3

"""
Author: Steven Blanchard
Date Created: 10092019
Module: Knowledgebase
File name: mesh.py
Credits: Aaron Trautman
"""

class Parser:
    # node label map
    __labels = {
        'B': 'Organism',
        'C': 'Phenotype',
        'D': 'Chemical',
        'B01.650': 'Plant',
        'G03.493': 'Pathway',
    }

    def __init__(self, nodeOut, edgeOut, labels=None):
        """
        Parses a mesh file and writes nodes to nodeOut and
        edges to edgeOut
        """
        self.nodeOut = nodeOut
        self.edgeOut = edgeOut
        self.tree2id = {}
        self.name2id = {}
        self.edges = {'tree': {}, 'name': {}}

        self.labels = type(self).__labels.copy()
        if labels:
            self.labels.update(labels)

        self.nodeOut.write(
            'source_id:ID|name:string|synonyms:string[]|:LABEL\n')

    def read(self, file):
        """
        File reader function
        """
        with open(file, 'rt') as fp:
            record = None
            for line in fp:
                line = line.strip()
                if line == '*NEWRECORD':
                    if record is not None:
                        self.__writeNode(record)
                        self.__storeEdges(record)
                    record = Record()
                elif line:
                    record.parse(line, self.labels)
            self.__writeNode(record)
            self.__storeEdges(record)

    def writeEdges(self):
        """
            A function that writes edges to file
        """
        self.edgeOut.write(':START_ID|:TYPE|source:string|:END_ID\n')

        for k, v in self.edges['tree'].items():
            l = {self.tree2id[i.rsplit('.', 1)[0]] for i in v}
            for mesh_id in l:
                self.__writeEdge(k, 'is_a', mesh_id)

        for k, v in self.edges['name'].items():
            l = {self.name2id[i] for i in v}
            for mesh_id in l:
                self.__writeEdge(k, 'mapped_to', mesh_id)

    def __writeNode(self, record):
        if "Chemical" in record.labels and "Phenotype" in record.labels:
            record.labels.remove("Chemical") # Used for node D065606 and others that may double label
        self.nodeOut.write(str(record))
        self.nodeOut.write('\n')

    def __writeEdge(self, start, rel, end):
        self.edgeOut.write('|'.join([start, rel, 'nih.nlm.mesh', end]))
        self.edgeOut.write('\n')

    def __storeEdges(self, record):
        self.tree2id.update({i: record.mesh_id for i in record.tree})
        self.name2id[record.name] = record.mesh_id
        if record.tree:
            self.edges['tree'][record.mesh_id] = record.tree
        if record.mapsTo:
            self.edges['name'][record.mesh_id] = record.mapsTo


class Record:
    __ns = "nih_nlm_mesh"

    def __init__(self):
        """
            Builds a mesh record 
        """
        self.mesh_id = None
        self.name = None
        self.synonyms = set()
        self.tree = set()
        self.mapsTo = set()
        self.labels = set()
        self.labels.add(type(self).__ns)

    def parse(self, line, meshLabels):
        """
            For parsing a line in a mesh file
        """
        element, data = line.split(' = ', 1)

        if element == 'UI':
            self.mesh_id = data
        elif element == 'MH' or element == 'NM':
            self.name = data
        elif element == 'ENTRY' or element == 'SY':
            self.synonyms.add(data.split('|', 1)[0])
        elif element == 'MN':
            self.tree.add(data)
            for label in meshLabels:
                if data.startswith(label):
                    self.labels.add(meshLabels[label])
        elif element == 'HM':
            data = data.split('/', 1)[0].strip('*')
            self.mapsTo.add(data)

    def __str__(self):
        """
            Redefining builtin str function to join records
        """
        return "|".join([
            self.mesh_id,
            self.name,
            ";".join(self.synonyms),
            ";".join(self.labels),
        ])
