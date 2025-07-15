from flask import Flask, request, jsonify, render_template
from game_logic import AkinatorGame
from neoj4_utils import get_node_and_relations_for_visualization 

app = Flask(__name__)

game = None

@app.route('/')
def index():
    # Initial render of the HTML template. No graph data is passed at this stage.
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    global game
    game = AkinatorGame()
    # Return a JSON response indicating the game has started
    return jsonify({"message": f"Game started with {len(game.candidates)} candidates."})

@app.route('/question', methods=['GET'])
def get_question():
    if not game:
        return jsonify({"error": "Game not started"}), 400

    trait = game.choose_best_trait()
    if trait is None:
        guess = game.get_guess()
        if guess:
            # If game is done and a guess is made, return it
            return jsonify({"guess": guess, "done": True})
        else:
            # If game is done but no guess (e.g., candidates exhausted)
            return jsonify({"message": "No more questions, unable to guess.", "done": True})

    relation, target_label, value = trait
    question_text = f"Does your character have {relation.replace('HAS_', '').replace('_', ' ').lower()} '{value}'?"
    reference_link = game.get_trait_reference(relation, value)

    # Return the question details in JSON format
    return jsonify({
        "relation": relation,
        "target_label": target_label,
        "value": value,
        "question": question_text,
        "reference_link": reference_link,
        "candidates_remaining": len(game.candidates)
    })

@app.route('/answer', methods=['POST'])
def answer_question():
    if not game:
        return jsonify({"error": "Game not started"}), 400

    data = request.json
    relation = data.get("relation")
    target_label = data.get("target_label")
    value = data.get("value")
    answer = data.get("answer")  # expected: "yes" or "no"

    if not all([relation, target_label, value, answer]):
        return jsonify({"error": "Missing fields"}), 400

    keep = answer.lower() in ("yes", "y", "true", "1")
    game.filter_candidates(relation, target_label, value, keep)

    if game.is_game_over():
        guess = game.get_guess()
        graph_data = None
        if guess:
            # If a guess is made, retrieve its related graph data
            graph_data = get_node_and_relations_for_visualization(guess)

        # Return the final guess and graph data in JSON format
        return jsonify({
            "guess": guess,
            "done": True,
            "candidates_remaining": len(game.candidates),
            "graph_nodes": graph_data['nodes'] if graph_data else [],
            "graph_edges": graph_data['relationships'] if graph_data else []
        })

    # If the game is not over, return current status
    return jsonify({"candidates_remaining": len(game.candidates), "done": False})

if __name__ == '__main__':
    app.run(debug=True)
