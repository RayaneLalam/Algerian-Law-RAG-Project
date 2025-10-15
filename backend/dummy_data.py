import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# === 1. Dummy data of 20 Algerian national laws (in French) ===
laws = [
    {
        "id": 1,
        "titre": "Loi sur l'organisation judiciaire",
        "texte": "Cette loi fixe la structure et les compétences des tribunaux en Algérie.",
        "categorie": "Justice",
        "date_publication": "1998-05-12"
    },
    {
        "id": 2,
        "titre": "Loi sur la protection de l'environnement",
        "texte": "La loi vise à préserver les ressources naturelles et à lutter contre la pollution.",
        "categorie": "Environnement",
        "date_publication": "2001-07-18"
    },
    {
        "id": 3,
        "titre": "Loi relative à la santé publique",
        "texte": "Elle encadre l'organisation du système de santé et la prévention des maladies.",
        "categorie": "Santé",
        "date_publication": "2003-02-25"
    },
    {
        "id": 4,
        "titre": "Loi sur l'éducation nationale",
        "texte": "Cette loi définit les principes fondamentaux du système éducatif algérien.",
        "categorie": "Éducation",
        "date_publication": "2008-04-23"
    },
    {
        "id": 5,
        "titre": "Loi sur la sécurité sociale",
        "texte": "Elle garantit la protection sociale des travailleurs et de leurs familles.",
        "categorie": "Travail",
        "date_publication": "1994-09-30"
    },
    {
        "id": 6,
        "titre": "Loi sur la liberté de la presse",
        "texte": "La loi garantit la liberté d'expression tout en encadrant les médias.",
        "categorie": "Médias",
        "date_publication": "2012-01-12"
    },
    {
        "id": 7,
        "titre": "Loi sur la protection du consommateur",
        "texte": "Elle protège les droits du consommateur face aux pratiques commerciales abusives.",
        "categorie": "Commerce",
        "date_publication": "2009-11-04"
    },
    {
        "id": 8,
        "titre": "Loi sur les collectivités locales",
        "texte": "Cette loi détermine le fonctionnement des communes et des wilayas.",
        "categorie": "Administration",
        "date_publication": "2011-06-10"
    },
    {
        "id": 9,
        "titre": "Loi sur les hydrocarbures",
        "texte": "Elle régit la recherche, l'exploitation et la commercialisation des hydrocarbures.",
        "categorie": "Énergie",
        "date_publication": "2019-12-11"
    },
    {
        "id": 10,
        "titre": "Loi sur la sécurité routière",
        "texte": "La loi vise à réduire les accidents de la route par la prévention et les sanctions.",
        "categorie": "Transport",
        "date_publication": "2016-03-08"
    },
    {
        "id": 11,
        "titre": "Loi sur la lutte contre la corruption",
        "texte": "Elle établit les mécanismes de prévention et de répression de la corruption.",
        "categorie": "Justice",
        "date_publication": "2006-02-20"
    },
    {
        "id": 12,
        "titre": "Loi sur les marchés publics",
        "texte": "Elle définit les règles applicables à la passation des marchés publics.",
        "categorie": "Économie",
        "date_publication": "2010-05-28"
    },
    {
        "id": 13,
        "titre": "Loi sur les associations",
        "texte": "La loi encadre la création et le fonctionnement des associations en Algérie.",
        "categorie": "Société civile",
        "date_publication": "2012-01-12"
    },
    {
        "id": 14,
        "titre": "Loi sur la propriété intellectuelle",
        "texte": "Elle protège les droits des auteurs, inventeurs et créateurs.",
        "categorie": "Propriété",
        "date_publication": "2003-08-18"
    },
    {
        "id": 15,
        "titre": "Loi sur les finances publiques",
        "texte": "Cette loi encadre la gestion et le contrôle des dépenses de l'État.",
        "categorie": "Finances",
        "date_publication": "2015-12-29"
    },
    {
        "id": 16,
        "titre": "Loi sur la nationalité algérienne",
        "texte": "Elle définit les conditions d'acquisition et de perte de la nationalité algérienne.",
        "categorie": "Droit civil",
        "date_publication": "1970-02-05"
    },
    {
        "id": 17,
        "titre": "Loi sur le code du travail",
        "texte": "Elle régit les relations entre employeurs et travailleurs en Algérie.",
        "categorie": "Travail",
        "date_publication": "1990-06-21"
    },
    {
        "id": 18,
        "titre": "Loi sur la protection du patrimoine culturel",
        "texte": "La loi protège les biens culturels matériels et immatériels du pays.",
        "categorie": "Culture",
        "date_publication": "1998-09-15"
    },
    {
        "id": 19,
        "titre": "Loi sur la cybersécurité",
        "texte": "Elle établit les règles de sécurité et de protection des systèmes informatiques.",
        "categorie": "Technologie",
        "date_publication": "2020-11-03"
    },
    {
        "id": 20,
        "titre": "Loi sur l'investissement",
        "texte": "Cette loi favorise l'investissement national et étranger en Algérie.",
        "categorie": "Économie",
        "date_publication": "2022-07-28"
    }
]

# === 2. Vectorization using SentenceTransformer ===
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Combine title and text for embedding
texts = [f"{law['titre']} - {law['texte']}" for law in laws]
embeddings = model.encode(texts, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# === 3. Create and save FAISS index ===
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

faiss.write_index(index, "laws.index")

# === 4. Save texts and metadata to JSON ===
with open("laws.json", "w", encoding="utf-8") as f:
    json.dump(laws, f, ensure_ascii=False, indent=4)

print("✅ FAISS index saved to 'laws.index'")
print("✅ Metadata and texts saved to 'laws.json'")
