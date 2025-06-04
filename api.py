
from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["Projet_Cours"]

# Fonction pour convertir les _id en string
def normalize_id(data):
    if isinstance(data, list):
        for d in data:
            if "_id" in d:
                d["_id"] = str(d["_id"])
    elif isinstance(data, dict) and "_id" in data:
        data["_id"] = str(data["_id"])
    return data

@app.route("/api/all", methods=["GET"])
def get_all():
    return jsonify({
        "utilisateurs": normalize_id(list(db.utilisateurs.find({}))),
        "fichiers": normalize_id(list(db.fichiers.find({}))),
        "partages": normalize_id(list(db.partages.find({}))),
        "groupes": normalize_id(list(db.groupes.find({}))),
        "utilisateur_groupe": normalize_id(list(db.utilisateur_groupe.find({}))),
        "groupe_partage": normalize_id(list(db.groupe_partage.find({})))
    })

@app.route("/api/utilisateurs", methods=["GET"])
def get_utilisateurs():
    utilisateurs = list(db.utilisateurs.find({}))
    return jsonify(normalize_id(utilisateurs))

@app.route("/api/fichiers/utilisateur/<id_utilisateur>", methods=["GET"])
def get_fichiers_par_utilisateur(id_utilisateur):
    fichiers = list(db.fichiers.find({"id_utilisateur": id_utilisateur}))
    return jsonify(normalize_id(fichiers))

@app.route("/api/partages/utilisateur/<id_utilisateur>", methods=["GET"])
def get_fichiers_partages(id_utilisateur):
    partages = list(db.partages.find({"utilisateur_dest_id": id_utilisateur}))
    fichiers_ids = [p["fichier_id"] for p in partages]
    fichiers = list(db.fichiers.find({"_id": {"$in": fichiers_ids}}))
    return jsonify(normalize_id(fichiers))

@app.route("/api/fichiers/groupe/<id_groupe>", methods=["GET"])
def get_fichiers_partages_groupe(id_groupe):
    liens = list(db.groupe_partage.find({"id_groupe": id_groupe}))
    ids = [l["id_fichier"] for l in liens]
    fichiers = list(db.fichiers.find({"_id": {"$in": ids}}))
    return jsonify(normalize_id(fichiers))

@app.route("/api/dataframe/fichiers", methods=["GET"])
def get_fichiers_csv():
    fichiers = list(db.fichiers.find({}))
    for f in fichiers:
        f["_id"] = str(f["_id"])
    return jsonify(fichiers)


if __name__ == "__main__":
    app.run(debug=True)
