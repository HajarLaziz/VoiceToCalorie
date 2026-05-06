# backend/ner/spacy_ner.py
import re
import time
from typing import Dict, List, Tuple, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class SpacyNERExtractor:
    def __init__(self):
        """Initialise le modèle spaCy pour l'arabe"""
        self.nlp = None
        self.available = False
        
        try:
            import spacy
            self.nlp = spacy.load("ar_core_news_sm")
            self.available = True
            print("✅ Modèle spaCy arabe chargé")
        except ImportError:
            print("⚠️ spaCy non installé - mode mots-clés")
        except Exception as e:
            print(f"⚠️ Erreur spaCy: {e}")
    
    def extract_entities(self, text: str) -> Dict:
        """Extrait les aliments et quantités"""
        try:
            from data.nutrition_db import NUTRITION_DB, QUANTITY_FACTORS
        except ImportError:
            NUTRITION_DB = {}
            QUANTITY_FACTORS = {}
        
        foods = []
        quantities = []
        
        # Détection des quantités
        quantity_patterns = [
            (r'(\d+)\s*', 'number'),
            (r'(نصف|ربع|ثلث|قليل|قليلاً|بعض|جزء|كمية قليلة|كمية كبيرة)', 'fraction'),
            (r'(طبق صغير|طبق متوسط|طبق كبير|كوب صغير|كوب كبير)', 'size'),
        ]
        
        for pattern, _ in quantity_patterns:
            matches = re.findall(pattern, text)
            quantities.extend(matches)
        
        # Détection des aliments
        if self.available and self.nlp:
            doc = self.nlp(text)
            for token in doc:
                if token.pos_ == "NOUN" and len(token.text) > 2:
                    foods.append(token.text)
        else:
            for food_name in NUTRITION_DB.keys():
                if food_name in text:
                    foods.append(food_name)
        
        return {
            "foods": list(set(foods)),
            "quantities": list(set(quantities)),
            "raw_text": text
        }
    
    def calculate_nutrition(self, extraction: Dict) -> Dict:
        """Calcule les valeurs nutritionnelles"""
        try:
            from data.nutrition_db import NUTRITION_DB, QUANTITY_FACTORS
        except ImportError:
            NUTRITION_DB = {}
            QUANTITY_FACTORS = {}
        
        total = {"calories": 0.0, "proteines": 0.0, "glucides": 0.0, "lipides": 0.0}
        
        factor = 1.0
        if extraction["quantities"]:
            q = extraction["quantities"][0]
            factor = QUANTITY_FACTORS.get(q, float(q) if q.isdigit() else 1.0)
        
        for food in extraction["foods"]:
            if food in NUTRITION_DB:
                nut = NUTRITION_DB[food]
                total["calories"] += nut.get("calories", 0) * factor
                total["proteines"] += nut.get("proteines", 0) * factor
                total["glucides"] += nut.get("glucides", 0) * factor
                total["lipides"] += nut.get("lipides", 0) * factor
        
        return total
    
    def process(self, text: str) -> Tuple[Dict, Dict, float]:
        start = time.time()
        entities = self.extract_entities(text)
        nutrition = self.calculate_nutrition(entities)
        return entities, nutrition, time.time() - start