
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

API_URL = "http://localhost:5000/api"

st.set_page_config(layout="wide")
st.title("📂 Interface Web - Système de Partage de Fichiers")

# Charger les utilisateurs et toutes les données
st.subheader("👤 Utilisateurs disponibles")
try:
    all_data = requests.get(f"{API_URL}/all").json()
    utilisateurs = all_data.get("utilisateurs", [])

    if not utilisateurs:
        st.warning("Aucun utilisateur trouvé.")
    else:
        # Création d'un dictionnaire nom → ID
        nom_map = {u["nom"]: u.get("_id") for u in utilisateurs}
        selected_nom = st.selectbox("Sélectionnez un utilisateur :", list(nom_map.keys()))
        selected_id = nom_map[selected_nom]
        utilisateur = next(u for u in utilisateurs if u["_id"] == selected_id)

        st.markdown(f"**✦ Rôle :** `{utilisateur.get('rôle', 'Non spécifié')}`")

        # Affichage du groupe
        groupes = all_data.get("groupes", [])
        utilisateur_groupes = all_data.get("utilisateur_groupe", [])
        groupe_utilisateur = next(
            (g for g in utilisateur_groupes if g["id_utilisateur"] == selected_id), None)
        if groupe_utilisateur:
            groupe_info = next((grp for grp in groupes if grp["_id"] == groupe_utilisateur["id_groupe"]), None)
            if groupe_info:
                st.markdown(f"**✦ Groupe :** `{groupe_info['nom']}`")
            else:
                st.markdown("**✦ Groupe :** `Inconnu`")
        else:
            st.markdown("**✦ Groupe :** `Aucun groupe associé`")

        st.markdown("---")

        # Fichiers de l'utilisateur
        st.subheader(f"📁 Fichiers de {selected_nom}")
        fichiers = [f for f in all_data.get("fichiers", []) if f["id_utilisateur"] == selected_id]
        if fichiers:
            df_fichiers = pd.DataFrame(fichiers)
            st.dataframe(df_fichiers[["nom", "type", "taille", "chemin", "date_creation", "est_public"]])
        else:
            st.info("Aucun fichier trouvé.")

        # Fichiers partagés avec l'utilisateur
        st.subheader(f"🔒 Fichiers partagés avec {selected_nom}")
        partages = [p for p in all_data.get("partages", []) if p["utilisateur_dest_id"] == selected_id]
        fichiers_ids = [p["fichier_id"] for p in partages]
        fichiers_partages = [f for f in all_data.get("fichiers", []) if f["_id"] in fichiers_ids]
        if fichiers_partages:
            df_partages = pd.DataFrame(fichiers_partages)
            st.dataframe(df_partages[["nom", "type", "taille", "chemin", "date_creation", "est_public"]])
        else:
            st.info("Aucun fichier partagé trouvé.")

        # Fichiers partagés avec le groupe
        st.subheader("👥 Fichiers partagés avec le groupe")
        groupe_partages = all_data.get("groupe_partage", [])
        fichiers_all = all_data.get("fichiers", [])
        fichiers_partages_avec_groupe = []
        if groupe_utilisateur:
            fichiers_ids_groupe = [gp["id_fichier"] for gp in groupe_partages if gp["id_groupe"] == groupe_utilisateur["id_groupe"]]
            fichiers_partages_avec_groupe = [f for f in fichiers_all if f["_id"] in fichiers_ids_groupe]

        if fichiers_partages_avec_groupe:
            df_group_files = pd.DataFrame(fichiers_partages_avec_groupe)
            st.dataframe(df_group_files[["nom", "type", "taille", "chemin", "date_creation", "est_public"]])
        else:
            st.info("Aucun fichier partagé avec ce groupe.")

        # Statistiques dynamiques
        st.markdown("---")
        st.subheader("📈 Statistiques Dynamiques")

        df_fichiers_all = pd.DataFrame(all_data.get("fichiers", []))
        df_utilisateurs_all = pd.DataFrame(all_data.get("utilisateurs", []))
        df_partages_all = pd.DataFrame(all_data.get("partages", []))

        # Convertir les dates
        df_fichiers_all["date_creation"] = pd.to_datetime(df_fichiers_all["date_creation"], errors="coerce")
        df_partages_all["date_partage"] = pd.to_datetime(df_partages_all["date_partage"], errors="coerce")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📄 Nombre de fichiers par type")
            type_counts = df_fichiers_all["type"].value_counts()
            fig1, ax1 = plt.subplots()
            sns.barplot(x=type_counts.index, y=type_counts.values, ax=ax1)
            ax1.set_ylabel("Nombre")
            ax1.set_xlabel("Type")
            ax1.set_title("Fichiers par type")
            st.pyplot(fig1)

        with col2:
            st.markdown("### 💾 Espace disque utilisé par utilisateur")
            df_user_size = df_fichiers_all.groupby("id_utilisateur")["taille"].sum().reset_index()
            df_user_size = df_user_size.merge(df_utilisateurs_all[["_id", "nom"]], left_on="id_utilisateur", right_on="_id", how="left")
            fig2, ax2 = plt.subplots(figsize=(6,4))
            sns.barplot(y=df_user_size["nom"], x=df_user_size["taille"], ax=ax2)
            ax2.set_xlabel("Taille totale (Mo)")
            ax2.set_ylabel("Utilisateur")
            ax2.set_title("Espace disque utilisé")
            st.pyplot(fig2)

        col3, col4 = st.columns(2)

        with col3:
            st.markdown("### 📅 Partages par mois")
            df_partages_all["mois"] = df_partages_all["date_partage"].dt.to_period("M").astype(str)
            partages_mois = df_partages_all["mois"].value_counts().sort_index()
            fig3, ax3 = plt.subplots()
            sns.lineplot(x=partages_mois.index, y=partages_mois.values, marker="o", ax=ax3)
            ax3.set_xlabel("Mois")
            ax3.set_ylabel("Partages")
            ax3.set_title("Évolution des partages")
            plt.xticks(rotation=45)
            st.pyplot(fig3)

        with col4:
            st.markdown("### 🔓 Public vs Privé")
            if "est_public" in df_fichiers_all.columns:
                pub_count = df_fichiers_all["est_public"].value_counts(normalize=True) * 100
                labels = ["Privé", "Public"] if pub_count.index[0] == False else ["Public", "Privé"]
                fig4, ax4 = plt.subplots()
                ax4.pie(pub_count, labels=labels, autopct="%.1f%%", startangle=90)
                ax4.set_title("Répartition des fichiers")
                st.pyplot(fig4)

except Exception as e:
    st.error(f"Erreur lors de la connexion à l'API : {e}")
