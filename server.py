from flask import Flask, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder="landing")
socketio = SocketIO(app, cors_allowed_origins="*")

# ✅ Servir index.html desde la carpeta landing
@app.route('/')
def serve_index():
    return send_from_directory('landing', 'index.html')

# ✅ Endpoint para emociones
@app.route('/emotion_update', methods=['POST'])
def emotion_update():
    data = request.json
    socketio.emit('emotion_update', data)
    return jsonify({"status": "success"}), 200

# ✅ Endpoint para streaming de frames
@app.route('/frame_update', methods=['POST'])
def frame_update():
    try:
        data = request.json
        print("✅ Frame recibido en server.py")  # <-- log en terminal del server
        socketio.emit('frame_update', data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"❌ Error en frame_update: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    print("🚀 Servidor web iniciado en: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)
