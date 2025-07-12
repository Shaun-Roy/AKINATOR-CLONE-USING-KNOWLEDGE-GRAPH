from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jUtils:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def get_all_characters(self):
        with self.driver.session() as session:
            result = session.run("MATCH (c:Character) RETURN c.name AS name")
            return [record["name"] for record in result]

    def get_trait_frequencies(self, candidates, relation):
        with self.driver.session() as session:
            query = f"""
            MATCH (c:Character)-[r:{relation}]->(t)
            WHERE c.name IN $candidates
            RETURN t.name AS value, count(c) AS count
            """
            result = session.run(query, candidates=candidates)
            return {record["value"]: record["count"] for record in result}

    def filter_characters(self, candidates, relation, value, keep=True):
        with self.driver.session() as session:
            if keep:
                query = f"""
                MATCH (c:Character)-[r:{relation}]->(t {{name: $value}})
                WHERE c.name IN $candidates
                RETURN c.name AS name
                """
            else:
                query = f"""
                MATCH (c:Character)
                WHERE c.name IN $candidates AND NOT EXISTS {{
                    MATCH (c)-[:{relation}]->(t {{name: $value}})
                }}
                RETURN c.name AS name
                """
            result = session.run(query, candidates=candidates, value=value)
            return [record["name"] for record in result]

class AkinatorGame:
    TRAIT_REFERENCES = {
        "HAS_INTELLIGENCE": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_STRENGTH": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_SPEED": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_DURABILITY": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_POWER": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_COMBAT": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_GENDER": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_RACE": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_ALIGNMENT": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_PUBLISHER": "akabab.github.io/superhero-api/api/glossary.html",
        "HAS_OCCUPATION": "akabab.github.io/superhero-api/api/glossary.html",
    }

    def __init__(self):
        self.neo4j = Neo4jUtils()
        self.candidates = self.neo4j.get_all_characters()
        self.asked_traits = set()

    def choose_best_trait(self):
        # List of all possible relations to ask about
        relations = [
            "HAS_GENDER", "HAS_RACE", "HAS_ALIGNMENT", "HAS_PUBLISHER", "HAS_OCCUPATION",
            "HAS_INTELLIGENCE", "HAS_STRENGTH", "HAS_SPEED", "HAS_DURABILITY",
            "HAS_POWER", "HAS_COMBAT"
        ]

        best_trait = None
        best_value = None
        best_count = 0

        # Find the trait that splits candidates best (closest to half)
        for relation in relations:
            if relation in self.asked_traits:
                continue

            freqs = self.neo4j.get_trait_frequencies(self.candidates, relation)
            total_candidates = len(self.candidates)
            for value, count in freqs.items():
                # We want to find a trait-value that splits the group about half/half
                if 0 < count < total_candidates and count > best_count:
                    best_count = count
                    best_trait = (relation, "Value", value)

        if best_trait:
            self.asked_traits.add(best_trait[0])
            return best_trait  # (relation, target_label, value)
        else:
            return None  # no more questions

    def filter_candidates(self, relation, target_label, value, keep):
        self.candidates = self.neo4j.filter_characters(self.candidates, relation, value, keep)

    def is_game_over(self):
        return len(self.candidates) <= 1

    def get_guess(self):
        if self.candidates:
            return self.candidates[0]
        return None

    def get_trait_reference(self, relation, value):
        return self.TRAIT_REFERENCES.get(relation)

    def close(self):
        self.neo4j.close()


# For manual testing
if __name__ == "__main__":
    game = AkinatorGame()
    print(f"Starting candidates: {len(game.candidates)}")
    trait = game.choose_best_trait()
    print("Best trait to ask about:", trait)
    # Simulate user answers here, etc.
    game.close()
