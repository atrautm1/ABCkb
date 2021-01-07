#!/usr/bin/env python3

"""
Author: Aaron Trautman
Date Created: 11212019
Module: Knowledgebase
File name: QueryBuilder
Credits: Aaron Trautman
"""

import json
import logging
from django.conf import settings

# Generate Index to search
# CALL db.index.fulltext.createNodeIndex("NODE_NAMES_LWRCSE",["Plant", "Chemical","Bacteria","Gene","Pathway","Phenotype"],[tolower("name"), tolower("synonyms")])

# Search Index
# CALL db.index.fulltext.queryNodes("NODE_NAMES_LWRCSE", "glycine") YIELD node, score return node.name, node.synonyms, labels(node), score

# Pla, Che, Gen, Pat, Phe, Diet, Bac
schema = (
    (0,1,0,0,0,0,0),    # Plant
    (1,0,1,0,0,0,1),    # Chemical
    (0,1,0,1,0,0,0),    # Gene
    (0,0,1,0,1,0,0),    # Pathway
    (0,0,0,1,0,0,1),    # Phenotype
    (0,0,0,0,0,0,1),    # Diet
    (0,1,0,0,1,1,0)    # Bacteria
)

paths = {
    1: [[1],[2],[2,3],[2,3,4],[2,3,4,5],[2,7],[2,7,6]],
    2: [[2],[1],[3],[3,4],[3,4,5],[7],[7,6]],# Add [7,5]??
    3: [[3],[4],[4,5],[2],[2,1],[2,7],[2,7,6]],
    4: [[5],[3],[3,2],[3,2,1],[3,2,7],[3,2,7,6]],
    5: [[5],[4],[4,3],[4,3,2],[4,3,2,1],[7],[7,6],[4,3,2,7]], # Add [4,3,2,7,6]?
    6: [[7],[7,2],[7,5],[7,2,1]],
    7: [[2],[6],[5],[2,1],[2,3],[2,3,4],[2,3,4,5]],
}

class QueryBuilder():

    __label2num = {
        "Bacteria":7,
        "Plant":1,
        "Chemical":2,
        "Gene":3,
        "Pathway":4,
        "Phenotype":5,
        "Diet":6
    }

    __num2label = {
        7:"Bacteria",
        1:"Plant",
        2:"Chemical",
        3:"Gene",
        4:"Pathway",
        5:"Phenotype",
        6:"Diet"
    }

    def __init__(self, ):
        schem_hash = hash(schema)
        # if schem_hash != settings.SCHEMA_HASH:
        #     build_connections_list()
        logging.info("Builder Initialized")
        self.schema = schema

    def build_query(self, starts, ends, closed=False):
        queries = []
        endNode = ""
        startNode = ""
        labels = set([])
        intended_paths = [] # list of lists [[1,2],[1,2,3]...]
        nodes = []
        #Steps
        # Identify starting labels
        for item in starts: # starts = [{id:123,label:'Bacteria'}..]
            label = item["label"]
            labels.add(label) 
            nodes.append(node(label,item["id"]))
        # Identify paths to travel
        if closed or len(labels) > 1:  # Can't handle yet
            return None
        if len(labels) == 1:
            start_id = self.__label2num[list(labels)[0]]
            end_id = self.__label2num[ends]
            possible_paths = paths[start_id]
            for n in possible_paths:
                if n[-1] == end_id:
                    intended_paths.append(n)
        if not intended_paths:  # Crash, path not available yet
            return None
        # Write query
        for i in intended_paths:
            start_node = f"MATCH p=(s:{list(labels)[0]})"
            total_nodes = [start_node]
            for j in i:
                total_nodes.append(f"-[r{j}]-(n{j}:{self.__num2label[j]})")
            path_query = "".join(total_nodes)
            conditionals = [f" WHERE s.source_id='{nodes[0].node_id}'"]
            if len(nodes) > 1:
                for n in nodes[1:]: # Because we already attached the first one
                    conditionals.append(f" OR s.source_id='{n.node_id}'")
            conditional_statement = "".join(conditionals)
            return_statement = """ WITH RELATIONSHIPS(p) as r, NODES(p) as n WITH [x IN r| type(x)] as rels, [x IN n| labels(x)] as nods, [x IN n| x.name] as nodNames RETURN rels, nods, nodNames"""
            queries.append(str(path_query+conditional_statement+return_statement))
        return queries
    

class node():
    def __init__(self,label,node_id=None):
        self.label = label
        self.node_id = node_id
        

# def get_neighbors(edge_list):
#     neighbors = []
#     for n in range(0,len(edge_list)):
#         if edge_list[n] == 1:
#             neighbors.append(n)
#     return neighbors

# def build_connections_list():
#     logging.info("Building connections list")

#     paths = set([])
#     visited = [0,0,0,0,0,0,0]
#     queue = []
#     OFFSET = 1

#     class node():
#         def __init__(self, node_num, prev_node):
#             self.node_num = node_num
#             self.prev_node = prev_node
#     #start_node = node(n, None)

#     def visit(node_id, *prev_node):
#         n = node(node_id,prev_node)
#         p = n

#         while p.prev_node != None:
#             print("{} {}".format(int(p.node_num+OFFSET),"->")+"/n")

#         visited[node_id] = 1
#         for neighbor in get_neighbors(schema[node_id]):
#             if visited[neighbor] == 0:
#                 visit(neighbor, n)
#         visited[node_id] = 0
    
#     visit(0,None)
#     # while queue:
#     #     current_node = queue.pop(0)
#     #     paths.add(current_node.node_num+OFFSET)

#     #     for neighbor in get_neighbors(schema[current_node.node_num]):
#     #         # Gives a list of ints that are connected to current_node
#     #         if neighbor not in visited:
#     #             visited.append(neighbor)
#     #             queue.append(neighbor)
    
#     return paths
#     #visited_nodes = set()
#     # n is node of origin
#     # Multiple node jumps node:node:node...etc
#     #visited_nodes.add(n)
#     #paths.append("n")

if __name__ == "__main__":
    builder = QueryBuilder()
    print(builder.build_query([{'id':123,'label':'Bacteria'}],"Pathway"))