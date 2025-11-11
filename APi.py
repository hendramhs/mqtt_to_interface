from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import statistics
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- Konfigurasi Database MySQL ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "iot_data"
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print("❌ Gagal konek ke database:", e)
        return None

@app.route("/", methods=["GET"])
def get_summary():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "error", "message": "Koneksi database gagal"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM dht_data ORDER BY waktu DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return jsonify({"status": "error", "message": "Tidak ada data"}), 404

    suhu_list = [r["suhu"] for r in rows]
    humid_list = [r["kelembaban"] for r in rows]
    ldr_list = [r["ldr"] for r in rows]

    suhumax = max(suhu_list)
    suhumin = min(suhu_list)
    suhurata = round(statistics.mean(suhu_list), 2)

    nilai_suhu_max_humid_max = [
        {
            "idx": i + 1,
            "suhu": row["suhu"],
            "humid": row["kelembaban"],
            "kecerahan": row["ldr"],
            "timestamp": row["waktu"].strftime("%Y-%m-%d %H:%M:%S")
        }
        for i, row in enumerate(rows)
        if row["suhu"] == suhumax or row["kelembaban"] == max(humid_list)
    ]

    month_year_max = []
    for r in nilai_suhu_max_humid_max:
        ts = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
        month_year_max.append({"month_year": f"{ts.month}-{ts.year}"})

    # === Tambahan agar cocok dengan web ===
    latest = rows[0]
    result = {
        "suhu": latest["suhu"],
        "humid": latest["kelembaban"],
        "kecerahan": latest["ldr"],
        "waktu": latest["waktu"].strftime("%Y-%m-%d %H:%M:%S"),

        "suhumax": suhumax,
        "suhumin": suhumin,
        "suhurata": suhurata,
        "nilai_suhu_max_humid_max": nilai_suhu_max_humid_max,
        "month_year_max": month_year_max
    }

    return jsonify(result)

# --- Jalankan server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
