import logging
from typing import Dict

logger = logging.getLogger(__name__)

def normalize_language(language: str) -> str:
    language = language.lower().strip()
    return 'ar' if language in ('ar', 'arabic', 'العربية') else 'fr'

def map_arabic_doc(doc: Dict) -> Dict:
    mapped = doc.copy()
    if 'texte' in doc: mapped['content'] = doc['texte']
    if 'source' in doc: mapped['article'] = doc['source']
    elif 'titre' in doc: mapped['article'] = doc['titre']
    return mapped