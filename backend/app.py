# app.py
import json
from flask import Flask, request, jsonify
from search_service.search_service import SearchService  # ✅ Direct import

app = Flask(__name__)

# Instantiate the SearchService
search_service = SearchService()

def make_reply(received_message: str, vectors_json_str: str) -> str:
    return f"dummy answer, here are the top 3 vectors: {vectors_json_str}"

@app.route("/chat", methods=["GET", "POST"])
def chat():
    # Accept message via JSON POST {"message": "..."} or GET ?message=...
    if request.method == "POST":
        data = request.get_json(silent=True)
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' in JSON body"}), 400
        message = str(data["message"])
    else:
        message = request.args.get("message")
        if message is None:
            return jsonify({"error": "Missing 'message' query parameter"}), 400

    try:
        top_k = 3
        results = search_service.search(message, top_n=top_k)
        vectors_json_str = json.dumps(results, ensure_ascii=False)
        reply = make_reply(message, vectors_json_str)
        return jsonify({"reply": reply}), 200
    except Exception as e:
        return jsonify({"error": f"Server error during search: {e}"}), 500

if __name__ == "__main__":
    # For development only — use a proper WSGI server in production.
    app.run(host="0.0.0.0", port=5000, debug=True)
