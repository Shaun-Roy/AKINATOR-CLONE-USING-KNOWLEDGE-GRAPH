import csv
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(dotenv_path="venv/.env")
NEO4J_URI = os.getenv("NEO4J_URI")  
NEO4J_USER = os.getenv("NEO4J_USERNAME")  # Adjusted here
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
csv_file_path = "superhero_triples.csv"

class Neo4jLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def load_triples(self, csv_file_path):
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self._merge_triple(
                    row['source_label'], row['source'], 
                    row['relation'], 
                    row['target_label'], row['target']
                )

    def _merge_triple(self, src_label, src_name, relation, tgt_label, tgt_name):
        try:
            with self.driver.session(database="neo4j") as session:  # specify database here
                session.execute_write(
                    self._create_nodes_and_relation,
                    src_label, src_name,
                    relation,
                    tgt_label, tgt_name
                )
        except Exception as e:
            print(f"Error merging triple ({src_name} -[{relation}]-> {tgt_name}): {e}")

    @staticmethod
    def _create_nodes_and_relation(tx, src_label, src_name, relation, tgt_label, tgt_name):
        query = f"""
        MERGE (a:{src_label} {{name: $src_name}})
        MERGE (b:{tgt_label} {{name: $tgt_name}})
        MERGE (a)-[r:{relation}]->(b)
        """
        tx.run(query, src_name=src_name, tgt_name=tgt_name)

if __name__ == "__main__":
    loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    print("Starting to load triples into Neo4j...")
    loader.load_triples(csv_file_path)
    loader.close()
    print("Done loading triples!")
