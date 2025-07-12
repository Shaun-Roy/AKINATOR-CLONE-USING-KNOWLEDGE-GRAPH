from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load Neo4j credentials from .env file
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_relationship_types():
    with driver.session() as session:
        result = session.run("CALL db.relationshipTypes()")
        return [record["relationshipType"] for record in result]

def get_labels():
    with driver.session() as session:
        result = session.run("CALL db.labels()")
        return [record["label"] for record in result]

def main():
    print("Fetching node labels and relationship types from Neo4j...")
    labels = get_labels()
    rel_types = get_relationship_types()
    
    print("\nNode Labels in Database:")
    for label in labels:
        print(f" - {label}")

    print("\nRelationship Types in Database:")
    for rel in rel_types:
        print(f" - {rel}")

if __name__ == "__main__":
    main()
    driver.close()
