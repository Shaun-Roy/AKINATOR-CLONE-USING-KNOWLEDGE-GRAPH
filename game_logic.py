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

    # --- NEW FUNCTION FOR GRAPH VISUALIZATION ---
    def get_node_and_relations(self, entity_name):
        """
        Retrieves a specific node and its immediate relationships/connected nodes
        from Neo4j, formatted for frontend visualization.
        """
        with self.driver.session() as session:
            # Query to get the central node, its direct relationships, and connected nodes
            query = """
            MATCH (n {name: $entityName})-[r]-(m)
            RETURN n, r, m
            LIMIT 50 // Limit the number of relations for better visualization performance
            """
            result = session.run(query, entityName=entity_name)

            nodes_data = []
            relationships_data = []
            seen_node_ids = set() # To track unique nodes already added

            for record in result:
                n_node = record["n"]
                m_node = record["m"]
                relationship = record["r"]

                # Add 'n' node if not already added
                if n_node.id not in seen_node_ids:
                    nodes_data.append({
                        "id": n_node.id,
                        "labels": list(n_node.labels),
                        "properties": dict(n_node)
                    })
                    seen_node_ids.add(n_node.id)

                # Add 'm' node if not already added
                if m_node.id not in seen_node_ids:
                    nodes_data.append({
                        "id": m_node.id,
                        "labels": list(m_node.labels),
                        "properties": dict(m_node)
                    })
                    seen_node_ids.add(m_node.id)

                # Add relationship
                relationships_data.append({
                    "id": relationship.id,
                    "start": relationship.start_node.id,
                    "end": relationship.end_node.id,
                    "type": relationship.type,
                    "properties": dict(relationship)
                })

            return {"nodes": nodes_data, "relationships": relationships_data}

# --- AkinatorGame Class (No changes needed in this file for AkinatorGame logic directly) ---
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

    # Example of getting graph data for a guess
    test_entity = "Superman" # Replace with an actual character in your DB
    print(f"\nGetting graph data for {test_entity}:")
    try:
        graph_data = game.neo4j.get_node_and_relations(test_entity)
        print(f"Nodes found: {len(graph_data['nodes'])}")
        print(f"Relationships found: {len(graph_data['relationships'])}")
        # print(graph_data) # Uncomment to see full raw data
    except Exception as e:
        print(f"Error getting graph data: {e}")

    game.close()
