import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "iqtestego.db"
)


# IQ ballini hisoblash
def calculate_iq(correct):
    scores = {
        8: 110,
        9: 118,
        10: 125,
        11: 130,
        12: 133,
        13: 135,
        14: 138,
        15: 140,
        16: 150,
        17: 153,
        18: 155,
        19: 158,
        20: 160
    }

    if correct in scores:
        return scores[correct]

    return 70 + correct * 3


# Ma'lumotlar bazasini yaratish
def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            age INTEGER,
            country TEXT,
            correct_answers INTEGER NOT NULL,
            iq_score INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()


# Server ishlayotganini tekshirish
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "success",
        "message": "IQTestEgo backend ishlayapti!"
    })


# Test natijasini saqlash
@app.route("/api/result", methods=["POST"])
def save_result():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    gender = str(data.get("gender", "")).strip()
    country = str(data.get("country", "")).strip()

    try:
        age = int(data.get("age", 0))
        correct = int(data.get("correct_answers", -1))
    except (ValueError, TypeError):
        return jsonify({"error": "Yosh yoki javoblar soni noto'g'ri"}), 400

    if not name or len(name) > 100:
        return jsonify({"error": "Ism-familiyani tekshiring"}), 400

    if not 1 <= age <= 120:
        return jsonify({"error": "Yosh noto'g'ri"}), 400

    if not 0 <= correct <= 20:
        return jsonify({"error": "To'g'ri javoblar soni 0-20 oralig'ida bo'lishi kerak"}), 400

    if not country or len(country) > 60:
        return jsonify({"error": "Davlatni tanlang"}), 400

    iq_score = calculate_iq(correct)
    created_at = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DATABASE)

    cursor = conn.execute("""
        INSERT INTO results
        (name, gender, age, country, correct_answers, iq_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, gender, age, country, correct, iq_score, created_at))

    result_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Natija saqlandi!",
        "id": result_id,
        "iq_score": iq_score
    }), 201


# Top 30 reyting
@app.route("/api/top30", methods=["GET"])
def get_top30():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT name, country, age, correct_answers, iq_score
        FROM results
        ORDER BY iq_score DESC, correct_answers DESC, id ASC
        LIMIT 30
    """).fetchall()

    conn.close()

    ranking = []

    for index, row in enumerate(rows, start=1):
        ranking.append({
            "rank": index,
            "name": row["name"],
            "country": row["country"],
            "age": row["age"],
            "correct_answers": row["correct_answers"],
            "iq_score": row["iq_score"]
        })

    return jsonify({
        "status": "success",
        "total": len(ranking),
        "top30": ranking
    })



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
