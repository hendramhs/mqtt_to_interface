import paho.mqtt.client as mqtt
import mysql.connector
from datetime import datetime

# --- Konfigurasi MQTT ---
BROKER = "broker.hivemq.com"
PORT = 8883  # TLS port
USERNAME = ""
PASSWORD = ""
TOPIC = "hendra/sensor"

# --- Konfigurasi Database MySQL ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="iot_data"
)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS dht_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    suhu FLOAT,
    kelembaban FLOAT,
    ldr INT,
    waktu TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

def reconnect_db():
    global db, cursor
    try:
        db.ping(reconnect=True, attempts=3, delay=2)
    except:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="iot_data"
        )
        cursor = db.cursor()

# --- Callback MQTT ---
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke broker, kode:", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    reconnect_db()
    data = msg.payload.decode().strip()
    print(f"Data diterima: {data}")

    try:
        # Ambil hanya 3 nilai pertama (abaikan relay jika masih dikirim)
        parts = data.split(",")
        if len(parts) < 3:
            print("⚠️ Format data tidak lengkap, diabaikan.")
            return

        suhu = float(parts[0])
        kelembaban = float(parts[1])
        ldr = int(parts[2])

        cursor.execute(
            "INSERT INTO dht_data (suhu, kelembaban, ldr) VALUES (%s, %s, %s)",
            (suhu, kelembaban, ldr)
        )
        db.commit()

        # Tampilkan output rapi seperti contoh sebelumnya
        print("------------------------------")
        print(f"Temperature: {suhu:.2f}°C")
        print(f"Humidity:    {kelembaban:.2f}%")
        print(f"LDR Value:   {ldr}")
        print("------------------------------\n")

    except Exception as e:
        print("⚠️ Gagal simpan data:", e)

# --- Jalankan MQTT ---
client = mqtt.Client(client_id="PythonSubscriber")
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
print("Menunggu data dari HiveMQ...\n")
client.loop_forever()
