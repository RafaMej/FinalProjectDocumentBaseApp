# app.py — colócalo en la raíz de FinalProjectBDA/
import subprocess
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# Agrega src/ al path para importar los módulos existentes
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC_DIR)

from queries import (
    cosine_similarity_query,
    euclidean_distance_query,
    manhattan_distance_query,
    semantic_search,
    compare_documents,
    jaccard_similarity,
    dice_coefficient,
    inner_product,
    get_connection,
)

app = Flask(__name__)
CORS(app)  # Permite conexiones desde el simulador iOS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(BASE_DIR, "src")


# ── Setup ──────────────────────────────────────────────────────────────────

@app.route("/api/setup/init-db", methods=["POST"])
def init_db():
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(SRC_PATH, "database.py")],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
        return jsonify({"ok": True, "log": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/setup/preprocess", methods=["POST"])
def preprocess():
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(SRC_PATH, "preprocessing.py")],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
        return jsonify({"ok": True, "log": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/setup/lsi", methods=["POST"])
def generate_lsi():
    # El frontend manda el número de componentes k
    data = request.get_json(silent=True) or {}
    k = int(data.get("k", 5))

    try:
        # lsi.py pide input() interactivo, así que lo simulamos con stdin
        result = subprocess.run(
            [sys.executable, os.path.join(SRC_PATH, "lsi.py")],
            input=str(k),
            capture_output=True, text=True, cwd=BASE_DIR
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
        return jsonify({"ok": True, "k": k, "log": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Documentos ────────────────────────────────────────────────────────────

@app.route("/api/docs", methods=["GET"])
def list_docs():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM DOCUMENTS ORDER BY name")
        docs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({"documents": docs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Búsquedas ──────────────────────────────────────────────────────────────

@app.route("/api/query/search", methods=["POST"])
def search():
    data = request.get_json()
    query_text = data.get("query", "").strip()
    mode = data.get("mode", "cosine")
    top_n = int(data.get("top_n", 5))

    if not query_text:
        return jsonify({"error": "query is required"}), 400

    try:
        if mode == "cosine":
            raw = cosine_similarity_query(query_text, top_n=top_n)
        elif mode == "euclidean":
            raw = euclidean_distance_query(query_text, top_n=top_n)
        elif mode == "manhattan":
            raw = manhattan_distance_query(query_text, top_n=top_n)
        elif mode == "semantic":
            raw = semantic_search(query_text, top_n=top_n)
        else:
            return jsonify({"error": f"Unknown mode: {mode}"}), 400

        if raw is None:
            return jsonify({"error": "No results — check LSI index or query terms"}), 422

        results = [
            {"rank": i + 1, "document": doc, "score": score}
            for i, (doc, score) in enumerate(raw)
        ]
        return jsonify({"results": results, "mode": mode})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Comparación ────────────────────────────────────────────────────────────

@app.route("/api/query/compare", methods=["POST"])
def compare():
    data = request.get_json()
    doc1 = data.get("doc1", "").strip()
    doc2 = data.get("doc2", "").strip()

    if not doc1 or not doc2:
        return jsonify({"error": "doc1 and doc2 are required"}), 400
    if doc1 == doc2:
        return jsonify({"error": "Please select two different documents"}), 400

    try:
        # Cosine doc vs doc (cálculo directo en SQL, igual que compare_documents)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(f1.frequency * f2.frequency) * 1.0
                / (SQRT(SUM(f1.frequency * f1.frequency)) *
                   SQRT(SUM(f2.frequency * f2.frequency)))
            FROM FREQUENCIES f1
            JOIN FREQUENCIES f2 ON f1.term_id = f2.term_id
            WHERE f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
              AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
        """, (doc1, doc2))
        cosine_val = round(cursor.fetchone()[0] or 0.0, 6)

        cursor.execute("""
            SELECT SQRT(SUM(
                (COALESCE(f1.frequency,0) - COALESCE(f2.frequency,0)) *
                (COALESCE(f1.frequency,0) - COALESCE(f2.frequency,0))
            ))
            FROM TERMS t
            LEFT JOIN FREQUENCIES f1 ON t.id = f1.term_id
                AND f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
            LEFT JOIN FREQUENCIES f2 ON t.id = f2.term_id
                AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
        """, (doc1, doc2))
        eucl_val = round(cursor.fetchone()[0] or 0.0, 6)

        cursor.execute("""
            SELECT SUM(ABS(COALESCE(f1.frequency,0) - COALESCE(f2.frequency,0)))
            FROM TERMS t
            LEFT JOIN FREQUENCIES f1 ON t.id = f1.term_id
                AND f1.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
            LEFT JOIN FREQUENCIES f2 ON t.id = f2.term_id
                AND f2.document_id = (SELECT id FROM DOCUMENTS WHERE name = ?)
        """, (doc1, doc2))
        manh_val = round(cursor.fetchone()[0] or 0.0, 6)
        conn.close()

        jacc_val  = jaccard_similarity(doc1, doc2)
        dice_val  = dice_coefficient(doc1, doc2)
        inner_val = inner_product(doc1, doc2)

        return jsonify({
            "doc1": doc1,
            "doc2": doc2,
            "cosineSimilarity":   cosine_val,
            "jaccardCoefficient": jacc_val,
            "diceCoefficient":    dice_val,
            "innerProduct":       inner_val,
            "euclideanDistance":  eucl_val,
            "manhattanDistance":  manh_val,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Métrica individual ─────────────────────────────────────────────────────

@app.route("/api/query/metric", methods=["POST"])
def metric():
    data = request.get_json()
    metric_name = data.get("metric", "").strip()
    doc1 = data.get("doc1", "").strip()
    doc2 = data.get("doc2", "").strip()

    if not metric_name or not doc1 or not doc2:
        return jsonify({"error": "metric, doc1 and doc2 are required"}), 400
    if doc1 == doc2:
        return jsonify({"error": "Please select two different documents"}), 400

    try:
        if metric_name == "jaccard":
            score = jaccard_similarity(doc1, doc2)
        elif metric_name == "dice":
            score = dice_coefficient(doc1, doc2)
        elif metric_name == "inner":
            score = inner_product(doc1, doc2)
        else:
            return jsonify({"error": f"Unknown metric: {metric_name}"}), 400

        return jsonify({"metric": metric_name, "doc1": doc1, "doc2": doc2, "score": score})

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Historial de queries ───────────────────────────────────────────────────

@app.route("/api/query-count", methods=["GET"])
def query_count():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM QUERIES")
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Corre en todas las interfaces para que el simulador iOS lo alcance
    app.run(host="0.0.0.0", port=5001, debug=True)