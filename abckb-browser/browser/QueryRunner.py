#!/usr/bin/env python3

"""
Author: Aaron Trautman
Date Created: 01242020
Module: Knowledgebase
File name: QueryRunner
Credits: Aaron Trautman
"""

import os
import logging
from neo4j import GraphDatabase

class QueryRunner():

    def __init__(self,):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format='%(asctime)s [%(funcName)s] %(levelname)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

        uri = os.getenv("NEO4J_URI")
        if not uri:
            self.logger.info("Using default NEO4J_URI: bolt://localhost:7687")
            uri = "bolt://localhost:7687"

        self.driver = GraphDatabase.driver(uri)
        self.labels = []
        with self.driver.session() as sess:
            self.labels = [row["label"] for row in sess.run("CALL db.labels();")]
        self.labels.sort()

    def run_query(self, query):
        """
        Runs a query and returns a dictionary of results.
        """
        with self.driver.session() as session:
            self.logger.debug(f"Running query: {query}")
            query_results = session.run(query)
            res = {}
            n = 1
            for record in query_results:
                rec = dict(record)
                res[n] = rec
                n += 1
            return res

if __name__ == "__main__":
    QR = QueryRunner()
    RESULTS = QR.run_query("""MATCH (a:Plant)-[r]->(b:Chemical)
                                WHERE type(r) = \"text_mined\" 
                                RETURN a.source_id,b.source_id LIMIT 10""")
    for k,v in RESULTS.items():
        print(k,v)
