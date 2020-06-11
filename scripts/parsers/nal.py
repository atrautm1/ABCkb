#!/usr/bin/env python

import xml.etree.ElementTree as ET 
from parse_it import handle
from treelib import Node, Tree

class Parser():

    """
    Parser class for parsing a NAL xml file
    """
    # All of the roots are coming from the TM queries
    # Other items in NAL may be considered phenotypes or chemicals
    # But are not being labelled for our purposes
    __root2label = {
        322:"Phenotype", 156:"Phenotype", 319:"Phenotype",
        7812:"Chemical", 8:"Chemical", 264:"Chemical", 
        858:"Plant"
    }

    def __init__(self, namespace="usda_nal_thesaurus"):
        self.namespace = namespace
        self.tree = Tree()
        self.tree.create_node("Root","root")
        self.name2id = {}

    def parse(self, xmlFile):
        """
        parsing function that parses an xml file
        """
        nodes = {}
        tree = ET.parse(xmlFile)
        root = tree.getroot() # THESAURUS node
        for concept in root: # Parse xml with nodes as concepts
            iden = "NAL:"+concept.find("TNR").text # node source ID
            nodes[iden], name = self.parseNode(concept) # Parse the node from xml file
            self.tree.create_node(tag=name, identifier=iden, parent='root') # create the node in the tree
            self.name2id[name] = iden # For mapping edges
        # Iterate through twice because parent/child relationships are connected via name not id
        # in xml file and file is sorted alphabetically
        for nodeID, props in nodes.items(): # Add edges to node as a list of tuples
            nodes[nodeID]["edges"] = self.parseEdges(nodeID,props)
        for node,label in self.__root2label.items(): # Add specific labels to nodes
            sub = self.tree.subtree("NAL:{}".format(node))
            for i in sub.all_nodes():
                iden = i.identifier.split(".")[0]
                nodes[iden]["labels"].add(label)
        return nodes
        
    def parseNode(self,node):
        """
        Parse each node from the xml file
        """
        labels = set()
        name = node.find("DESCRIPTOR").text
        synonyms = extractElem(node, "UF") # Used for
        parents = extractElem(node, "BT") # Broader term
        children = extractElem(node, "NT") # Narrow term
        # associated = extractElem(node,"RT") # Related term
        # categories = extractElem(node, "SC") # Subject category
        # for cat in categories:
        #     item = cat.split(" ")[0]
        #     if item in self.labels.keys():
        #         labels.add(self.labels[item])
        labels.add(self.namespace)
        return {"name": name, "synonyms": list(synonyms), "parents": parents,
                "children": children, "labels": labels}, name
    
    def parseEdges(self, nodeID, props):
        """
        Add edges to nodes.
        Some nodes have multiple parents
        """
        edges = []
        multiParent = 0
        for name in props["children"]:
            edges.append(("has_child",self.name2id[name]))
        for name in props["parents"]:
            parentID = self.name2id[name]
            if multiParent == 0:
                self.tree.move_node(nodeID,parentID)
            else:
                self.tree.create_node(tag=props["name"],identifier=nodeID+".{}".format(multiParent),parent=parentID)
            edges.append(("is_a",parentID))
            multiParent += 1
        return edges

def extractElem(node,tag):
    """
    Extracts an element
    """
    elemSet = set()
    for elem in node.findall(tag):
        elemSet.add(elem.text)
    return elemSet

if __name__ == "__main__":
    parser = Parser()
    mydict = parser.parse(handle("docker/data/nal/NAL_Thesaurus_2019_XML.zip"))
    print(mydict)
    #sub = parser.tree.subtree("usda.nal.thesaurus.id:858")
    #print(sub.all_nodes())