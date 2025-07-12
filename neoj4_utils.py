from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load Neo4j credentials from .env
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def close_driver():
    driver.close()

def get_all_characters():
    """Return a list of all character names in the graph."""
    with driver.session() as session:
        query = "MATCH (c:Character) RETURN c.name AS name"
        result = session.run(query)
        return [record["name"] for record in result]

def get_trait_frequencies(candidates, relation, target_label):
    """
    Given a list of candidate character names, a relation, and target node label,
    return a dict mapping trait value to the count of candidates having that trait.
    """
    with driver.session() as session:
        query = f"""
        MATCH (c:Character)-[r:{relation}]->(t:{target_label})
        WHERE c.name IN $candidates
        RETURN t.name AS value, count(c) AS count
        """
        result = session.run(query, candidates=candidates)
        return {record["value"]: record["count"] for record in result}

def filter_characters(candidates, relation, target_label, value, keep=True):
    """
    Filter candidates based on whether they have (keep=True) or don't have (keep=False)
    the trait with given relation, target node label, and value.
    Returns the filtered list of character names.
    """
    with driver.session() as session:
        if keep:
            query = f"""
            MATCH (c:Character)-[r:{relation}]->(t:{target_label} {{name: $value}})
            WHERE c.name IN $candidates
            RETURN c.name AS name
            """
        else:
            query = f"""
            MATCH (c:Character)
            WHERE c.name IN $candidates AND NOT (c)-[:{relation}]->(:{target_label} {{name: $value}})
            RETURN c.name AS name
            """
        result = session.run(query, candidates=candidates, value=value)
        return [record["name"] for record in result]
