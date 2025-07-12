from flask import Flask, request, jsonify, render_template
from game_logic import AkinatorGame

app = Flask(__name__)

game = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    global game
    game = AkinatorGame()
    return jsonify({"message": f"Game started with {len(game.candidates)} candidates."})

@app.route('/question', methods=['GET'])
def get_question():
    if not game:
        return jsonify({"error": "Game not started"}), 400

    trait = game.choose_best_trait()
    if trait is None:
        guess = game.get_guess()
        if guess:
            return jsonify({"guess": guess, "done": True})
        else:
            return jsonify({"message": "No more questions, unable to guess.", "done": True})

    relation, target_label, value = trait
    question_text = f"Does your character have {relation.replace('HAS_', '').replace('_', ' ').lower()} '{value}'?"
    reference_link = game.get_trait_reference(relation, value)

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
        return jsonify({"guess": guess, "done": True, "candidates_remaining": len(game.candidates)})

    return jsonify({"candidates_remaining": len(game.candidates), "done": False})

if __name__ == '__main__':
    app.run(debug=True)
