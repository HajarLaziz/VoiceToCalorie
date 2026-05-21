# backend/ner/spacy_ner.py
import re
import time
from typing import Dict, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class SpacyNERExtractor:
    def __init__(self):
        """Initialise l'extracteur avec la base de donnees nutritionnelle."""

        # Charger la base de donnees nutritionnelle
        self.nutrition_db = {}
        self.quantity_factors = {}

        try:
            from data.nutrition_db import NUTRITION_DB, QUANTITY_FACTORS
            self.nutrition_db = NUTRITION_DB
            self.quantity_factors = QUANTITY_FACTORS
            print(f"Base nutritionnelle chargee: {len(self.nutrition_db)} aliments")
        except ImportError as e:
            print(f"Erreur import nutrition_db: {e}")
        except Exception as e:
            print(f"Erreur chargement base: {e}")

        # Essayer spaCy (optionnel)
        self.nlp = None
        self.available = False
        try:
            import spacy
            try:
                self.nlp = spacy.load("ar_core_news_sm")
                self.available = True
                print("Mode spaCy active")
            except OSError:
                print("Mode simplifie (recherche par mots-cles)")
        except ImportError:
            print("Mode simplifie (recherche par mots-cles)")

    def extract_entities(self, text: str) -> Dict:
        """Extrait les aliments et quantites du texte."""

        foods = []
        quantities = []

        # Detection des quantites
        quantity_patterns = [
            (r'(\d+)', 'number'),
            (r'(نصف|ربع|ثلث|قليل|قليلا|بعض|جزء|كمية قليلة|كمية كبيرة)', 'fraction'),
            (r'(طبق صغير|طبق متوسط|طبق كبير|كوب صغير|كوب كبير)', 'size'),
        ]

        for pattern, _ in quantity_patterns:
            matches = re.findall(pattern, text)
            quantities.extend(matches)

        # Detection des aliments - recherche directe dans nutrition_db
        for food_name in self.nutrition_db.keys():
            if food_name in text:
                foods.append(food_name)

        # Si aucun aliment trouve, chercher par mots individuels
        if not foods:
            words = text.split()
            for word in words:
                if len(word) > 2:
                    for food_name in self.nutrition_db.keys():
                        if word in food_name or food_name in word:
                            foods.append(food_name)
                            break

        # Supprimer les doublons
        foods = list(set(foods))
        quantities = list(set(quantities))

        return {
            "foods": foods if foods else [],
            "quantities": quantities,
            "raw_text": text
        }

    def calculate_nutrition(self, extraction: Dict) -> Dict:
        """Calcule les valeurs nutritionnelles."""

        total = {"calories": 0.0, "proteines": 0.0, "glucides": 0.0, "lipides": 0.0}

        # Facteur de quantite
        factor = 1.0
        if extraction["quantities"]:
            q = extraction["quantities"][0]
            if q in self.quantity_factors:
                factor = self.quantity_factors[q]
            elif q.replace('.', '').isdigit():
                factor = float(q)

        # Limiter le facteur a une plage raisonnable
        factor = max(0.25, min(3.0, factor))

        # Calculer pour chaque aliment
        foods_found = 0
        for food in extraction["foods"]:
            if food in self.nutrition_db:
                nut = self.nutrition_db[food]
                total["calories"] += nut.get("calories", 0) * factor
                total["proteines"] += nut.get("proteines", 0) * factor
                total["glucides"] += nut.get("glucides", 0) * factor
                total["lipides"] += nut.get("lipides", 0) * factor
                foods_found += 1

        # Si aucun aliment trouve, retourner 0
        if foods_found == 0:
            total = {"calories": 0.0, "proteines": 0.0, "glucides": 0.0, "lipides": 0.0}

        # Arrondir les valeurs
        total = {k: round(v, 1) for k, v in total.items()}

        return total

    def process(self, text: str) -> Tuple[Dict, Dict, float]:
        """Processus complet d'extraction et calcul."""

        start = time.time()

        if not text or not text.strip():
            return {"foods": [], "quantities": [], "raw_text": text}, {"calories": 0, "proteines": 0, "glucides": 0,
                                                                       "lipides": 0}, 0.0

        entities = self.extract_entities(text)
        nutrition = self.calculate_nutrition(entities)
        processing_time = time.time() - start

        return entities, nutrition, processing_time