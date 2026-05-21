# tests/generate_test_phrases.py
"""
Script pour generer 100 phrases de test complexes
a partir de la base de donnees nutritionnelle
"""

import sys
import os
import json
import random
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data.nutrition_db import NUTRITION_DB, QUANTITY_FACTORS

class TestPhraseGenerator:
    """
    Genere des phrases de test variees et complexes.
    """
    
    def __init__(self):
        self.nutrition_db = NUTRITION_DB
        self.quantity_factors = list(QUANTITY_FACTORS.keys())
        
        # Categoriser les aliments
        self.categories = {
            "fruits": ["تفاح", "تفاحه", "موز", "فراوله", "برتقال", "عنب", "تمر", "كمثرى", "مانجو", "أناناس"],
            "legumes": ["خضار", "سلطه", "بطاطس", "جزر", "طماطم", "خيار", "بصل", "سبانخ", "بروكلي"],
            "viandes": ["دجاج", "لحم", "سمك", "تونة", "بيض", "جبن", "لحم بقر", "ديك رومي"],
            "boissons": ["حليب", "عصير برتقال", "قهوة", "شاي", "عصير تفاح", "مشروب غازي"],
            "cereales": ["خبز", "ارز", "كسكس", "معكرونه", "بيتزا"],
            "plats": ["طاجين دجاج", "كسكس باللحم", "حريره", "شوربه خضار"],
            "desserts": ["كعكه", "بسكويت", "شباكيه", "مسمن", "عسل"]
        }
        
        # Mots de connexion
        self.connecteurs = ["و", "مع", "مع بعض", "بالإضافه الي", "بالاضافة الي"]
        
        # Verbes d'action
        self.verbes = ["اكلت", "تناولت", "شربت", "اكلت", "تذوقت"]
        
        # Toutes les phrases generees
        self.phrases = []
    
    def get_random_food(self, category=None):
        """Retourne un aliment aleatoire."""
        if category and category in self.categories:
            foods = [f for f in self.categories[category] if f in self.nutrition_db]
            if foods:
                return random.choice(foods)
        
        # Sinon, prendre un aliment aleatoire de la base
        all_foods = list(self.nutrition_db.keys())
        # Filtrer les noms trop longs ou speciaux
        valid_foods = [f for f in all_foods if len(f) < 30 and not any(c.isdigit() for c in f)]
        return random.choice(valid_foods) if valid_foods else "دجاج"
    
    def get_random_quantity(self):
        """Retourne une quantite aleatoire."""
        types = ["number", "fraction", "vague", "size"]
        choice = random.choice(types)
        
        if choice == "number":
            numbers = ["واحد", "اثنين", "ثلاثه", "اربعه", "خمسه", "1", "2", "3", "4", "5"]
            return random.choice(numbers)
        elif choice == "fraction":
            fractions = ["نصف", "ربع", "ثلث"]
            return random.choice(fractions)
        elif choice == "vague":
            vagues = ["قليل", "قليلا", "بعض", "كمية قليلة", "كمية كبيرة"]
            return random.choice(vagues)
        else:  # size
            sizes = ["كوب صغير", "كوب كبير", "طبق صغير", "طبق متوسط", "طبق كبير"]
            return random.choice(sizes)
    
    def generate_simple_phrase(self):
        """Genere une phrase simple: verbe + aliment."""
        verbe = random.choice(self.verbes)
        food = self.get_random_food()
        return f"{verbe} {food}", [food]
    
    def generate_quantity_phrase(self):
        """Genere une phrase avec quantite: verbe + quantite + aliment."""
        verbe = random.choice(self.verbes)
        quantite = self.get_random_quantity()
        food = self.get_random_food()
        return f"{verbe} {quantite} {food}", [food], [quantite]
    
    def generate_multi_food_phrase(self):
        """Genere une phrase avec plusieurs aliments."""
        verbe = random.choice(self.verbes)
        nb_foods = random.randint(2, 4)
        foods = []
        
        for i in range(nb_foods):
            category = random.choice(list(self.categories.keys()))
            food = self.get_random_food(category)
            foods.append(food)
        
        # Construire la phrase
        if len(foods) == 2:
            phrase = f"{verbe} {foods[0]} {random.choice(self.connecteurs)} {foods[1]}"
        else:
            phrase = f"{verbe} {foods[0]}"
            for i in range(1, len(foods) - 1):
                phrase += f" {random.choice(self.connecteurs)} {foods[i]}"
            phrase += f" {random.choice(self.connecteurs)} {foods[-1]}"
        
        return phrase, foods
    
    def generate_quantity_multi_phrase(self):
        """Genere une phrase avec quantites sur plusieurs aliments."""
        verbe = random.choice(self.verbes)
        nb_foods = random.randint(2, 3)
        foods = []
        quantities = []
        
        parts = [verbe]
        for i in range(nb_foods):
            quantite = self.get_random_quantity()
            food = self.get_random_food()
            parts.append(f"{quantite} {food}")
            foods.append(food)
            quantities.append(quantite)
            if i < nb_foods - 1:
                parts.append(random.choice(self.connecteurs))
        
        phrase = " ".join(parts)
        return phrase, foods, quantities
    
    def generate_complex_phrase(self):
        """Genere une phrase complexe avec plats composes."""
        verbes_plats = ["اكلت", "تناولت", "طلب", "حضرت"]
        verbe = random.choice(verbes_plats)
        
        # Plats composes specifiques
        plats_composes = ["طاجين دجاج", "كسكس باللحم", "حريره", "شوربه خضار", "بسطيله", "رفيسه"]
        plat = random.choice([p for p in plats_composes if p in self.nutrition_db])
        
        # Ajouter une quantite aleatoire
        if random.choice([True, False]):
            quantite = self.get_random_quantity()
            phrase = f"{verbe} {quantite} {plat}"
            return phrase, [plat], [quantite]
        else:
            phrase = f"{verbe} {plat}"
            return phrase, [plat]
    
    def generate_all_phrases(self, total=100):
        """Genere toutes les phrases de test."""
        
        print("Generation des phrases de test...")
        print("=" * 60)
        
        # Repartition des types de phrases
        nb_simple = int(total * 0.2)      # 20% phrases simples
        nb_quantity = int(total * 0.25)   # 25% phrases avec quantite
        nb_multi = int(total * 0.2)       # 20% phrases multi-aliments
        nb_quantity_multi = int(total * 0.2)  # 20% phrases quantite + multi
        nb_complex = int(total * 0.15)    # 15% phrases complexes
        
        phrases_data = []
        
        # 1. Phrases simples
        print(f"\nGeneration de {nb_simple} phrases simples...")
        for _ in range(nb_simple):
            phrase, foods = self.generate_simple_phrase()
            calories = self.calculate_calories(foods)
            phrases_data.append({
                "text": phrase,
                "foods": foods,
                "quantities": [],
                "calories": calories,
                "type": "simple"
            })
        
        # 2. Phrases avec quantites
        print(f"Generation de {nb_quantity} phrases avec quantites...")
        for _ in range(nb_quantity):
            phrase, foods, quantities = self.generate_quantity_phrase()
            calories = self.calculate_calories(foods, quantities)
            phrases_data.append({
                "text": phrase,
                "foods": foods,
                "quantities": quantities,
                "calories": calories,
                "type": "quantity"
            })
        
        # 3. Phrases multi-aliments
        print(f"Generation de {nb_multi} phrases multi-aliments...")
        for _ in range(nb_multi):
            phrase, foods = self.generate_multi_food_phrase()
            calories = self.calculate_calories(foods)
            phrases_data.append({
                "text": phrase,
                "foods": foods,
                "quantities": [],
                "calories": calories,
                "type": "multi"
            })
        
        # 4. Phrases quantite + multi
        print(f"Generation de {nb_quantity_multi} phrases quantite + multi...")
        for _ in range(nb_quantity_multi):
            phrase, foods, quantities = self.generate_quantity_multi_phrase()
            calories = self.calculate_calories(foods, quantities)
            phrases_data.append({
                "text": phrase,
                "foods": foods,
                "quantities": quantities,
                "calories": calories,
                "type": "quantity_multi"
            })
        
        # 5. Phrases complexes
        print(f"Generation de {nb_complex} phrases complexes...")
        for _ in range(nb_complex):
            result = self.generate_complex_phrase()
            if len(result) == 2:
                phrase, foods = result
                quantities = []
            else:
                phrase, foods, quantities = result
            calories = self.calculate_calories(foods, quantities)
            phrases_data.append({
                "text": phrase,
                "foods": foods,
                "quantities": quantities,
                "calories": calories,
                "type": "complex"
            })
        
        # Melanger les phrases
        random.shuffle(phrases_data)
        
        self.phrases = phrases_data
        print(f"\nTotal: {len(self.phrases)} phrases generees")
        
        return self.phrases
    
    def calculate_calories(self, foods, quantities=None):
        """Calcule les calories totales pour une phrase."""
        total = 0
        
        if quantities is None:
            quantities = []
        
        # Si plusieurs quantites, on les associe aux aliments
        for i, food in enumerate(foods):
            if food in self.nutrition_db:
                cal = self.nutrition_db[food]["calories"]
                
                # Appliquer la quantite correspondante si disponible
                if i < len(quantities):
                    q = quantities[i]
                    factor = self.get_quantity_factor(q)
                    total += cal * factor
                else:
                    total += cal
        
        return round(total, 1)
    
    def get_quantity_factor(self, quantity):
        """Convertit une quantite en facteur numerique."""
        # Verifier dans QUANTITY_FACTORS
        for q_word, factor in QUANTITY_FACTORS.items():
            if q_word in quantity:
                return factor
        
        # Verifier les nombres
        if quantity.isdigit():
            return float(quantity)
        
        # Mots de nombres
        number_words = {
            "واحد": 1, "واحده": 1,
            "اثنين": 2, "اثنتين": 2,
            "ثلاثه": 3, "ثلاث": 3,
            "اربعه": 4, "اربع": 4,
            "خمسه": 5, "خمس": 5,
            "سته": 6, "ست": 6,
            "سبعه": 7, "سبع": 7,
            "ثمانيه": 8, "ثمان": 8,
            "تسعه": 9, "تسع": 9,
            "عشره": 10
        }
        
        if quantity in number_words:
            return number_words[quantity]
        
        return 1.0
    
    def save_to_json(self):
        """Sauvegarde les phrases dans un fichier JSON."""
        os.makedirs("data/test_phrases", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = f"data/test_phrases/test_phrases_{timestamp}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.phrases, f, ensure_ascii=False, indent=2)
        
        print(f"\nPhrases sauvegardees dans: {output_file}")
        return output_file
    
    def save_to_text(self):
        """Sauvegarde les phrases dans un fichier texte."""
        os.makedirs("data/test_phrases", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = f"data/test_phrases/test_phrases_{timestamp}.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("PHRASES DE TEST POUR VOICE-TO-CALORIE\n")
            f.write("=" * 60 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total: {len(self.phrases)} phrases\n\n")
            
            for i, phrase_data in enumerate(self.phrases, 1):
                f.write(f"{i}. Phrase: {phrase_data['text']}\n")
                f.write(f"   Aliments: {', '.join(phrase_data['foods'])}\n")
                if phrase_data['quantities']:
                    f.write(f"   Quantites: {', '.join(phrase_data['quantities'])}\n")
                f.write(f"   Calories attendues: {phrase_data['calories']} kcal\n")
                f.write(f"   Type: {phrase_data['type']}\n")
                f.write("\n")
        
        print(f"Phrases sauvegardees dans: {output_file}")
        return output_file
    
    def print_summary(self):
        """Affiche un resume des phrases generees."""
        print("\n" + "=" * 60)
        print("RESUME DES PHRASES GENEREES")
        print("=" * 60)
        
        types_count = {}
        for p in self.phrases:
            t = p['type']
            types_count[t] = types_count.get(t, 0) + 1
        
        print("\nRepartition par type:")
        for t, count in types_count.items():
            print(f"  {t}: {count} phrases")
        
        # Exemples
        print("\nExemples de phrases:")
        for i, p in enumerate(self.phrases[:15], 1):
            print(f"  {i}. {p['text']}")
            print(f"      -> {p['calories']} kcal")
        
        if len(self.phrases) > 15:
            print(f"  ... et {len(self.phrases) - 15} autres")
    
    def generate_for_evaluation(self):
        """Genere le code Python pour integrer dans evaluation_complete.py."""
        
        print("\n" + "=" * 60)
        print("CODE A COPIER DANS evaluation_complete.py")
        print("=" * 60)
        
        print("\n# ===== PHRASES DE TEST (100 phrases) =====\n")
        print("self.ground_truth = {")
        
        for p in self.phrases:
            # Nettoyer la phrase pour l'utiliser comme cle
            phrase_key = p['text']
            foods_list = '", "'.join(p['foods'])
            quantities_list = '", "'.join(p['quantities']) if p['quantities'] else ""
            
            print(f'    "{phrase_key}": {{')
            print(f'        "foods": ["{foods_list}"],')
            if quantities_list:
                print(f'        "quantities": ["{quantities_list}"],')
            else:
                print(f'        "quantities": [],')
            print(f'        "calories": {p["calories"]}')
            print(f'    }},')
        
        print("}")
    
    def run(self, total=100):
        """Execute la generation complete."""
        self.generate_all_phrases(total)
        self.print_summary()
        self.save_to_json()
        self.save_to_text()
        self.generate_for_evaluation()
        
        return self.phrases


def main():
    """Fonction principale."""
    
    print("=" * 60)
    print("GENERATEUR DE PHRASES DE TEST")
    print("=" * 60)
    print("\nCe script va generer 100 phrases de test complexes")
    print("a partir de votre base de donnees nutritionnelle.")
    print()
    
    # Demander confirmation
    confirm = input("Voulez-vous continuer? (o/n): ").strip().lower()
    
    if confirm == 'o':
        generator = TestPhraseGenerator()
        phrases = generator.run(total=100)
        
        print("\n" + "=" * 60)
        print("GENERATION TERMINEE")
        print("=" * 60)
        print("\nFichiers crees:")
        print("  - data/test_phrases/test_phrases_*.json")
        print("  - data/test_phrases/test_phrases_*.txt")
        print("\nVous pouvez maintenant:")
        print("  1. Copier le code dans evaluation_complete.py")
        print("  2. Executer l'evaluation: python tests/evaluation_complete.py")
    else:
        print("Operation annulee.")


if __name__ == "__main__":
    main()