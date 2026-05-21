# scripts/translate_and_import.py
import pandas as pd
import json
import os
import sys
import re
import shutil
from datetime import datetime

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from translators.google_translate import FoodTranslator

class CSVImporter:
    """
    Importe les fichiers CSV et les ajoute a nutrition_db.py.
    """
    
    def __init__(self, use_online_translation=False):
        self.translator = FoodTranslator(use_online=use_online_translation)
        self.nutrition_db_path = "data/nutrition_db.py"
        self.all_entries = []
        self.stats = {
            "total_processed": 0,
            "total_added": 0,
            "categories": {}
        }
    
    def process_csv_file(self, csv_path):
        """
        Traiter un fichier CSV.
        
        Args:
            csv_path: Chemin vers le fichier CSV
        
        Returns:
            Liste des entrees extraites
        """
        print(f"\nTraitement de: {csv_path}")
        print("-" * 50)
        
        # Charger le CSV
        df = pd.read_csv(csv_path)
        print(f"  Lignes: {len(df)}")
        print(f"  Colonnes: {list(df.columns)}")
        
        entries = []
        
        # Identifier les colonnes
        name_col = None
        calories_col = None
        protein_col = None
        carbs_col = None
        fat_col = None
        category_col = None
        
        # Chercher la colonne des noms
        for col in ['Item', 'Food', 'item', 'food', 'Name', 'name']:
            if col in df.columns:
                name_col = col
                break
        
        # Chercher la colonne des calories
        for col in ['Calories', 'calories', 'Energy', 'energy']:
            if col in df.columns:
                calories_col = col
                break
        
        # Chercher la colonne des proteines
        for col in ['Protein', 'protein', 'Proteins', 'proteins']:
            if col in df.columns:
                protein_col = col
                break
        
        # Chercher la colonne des glucides
        for col in ['Carbohydrates', 'carbohydrates', 'Carbs', 'carbs']:
            if col in df.columns:
                carbs_col = col
                break
        
        # Chercher la colonne des lipides
        for col in ['Fat', 'fat', 'Total Fat', 'Total fat']:
            if col in df.columns:
                fat_col = col
                break
        
        # Chercher la colonne de categorie
        for col in ['Category', 'category']:
            if col in df.columns:
                category_col = col
                break
        
        print(f"  Colonne nom: {name_col}")
        print(f"  Colonne calories: {calories_col}")
        
        if name_col is None or calories_col is None:
            print(f"  ATTENTION: Colonnes essentielles non trouvees. Ignorer ce fichier.")
            return []
        
        # Extraire les noms uniques pour traduction en batch
        unique_names = df[name_col].dropna().unique()
        print(f"  {len(unique_names)} noms uniques a traduire...")
        
        # Traduire tous les noms
        translations = self.translator.translate_batch(list(unique_names))
        
        # Parcourir chaque ligne
        for index, row in df.iterrows():
            english_name = row[name_col]
            if pd.isna(english_name):
                continue
            
            arabic_name = translations.get(english_name, english_name)
            
            # Extraire les valeurs
            calories = self.safe_float(row.get(calories_col, 0))
            proteins = self.safe_float(row.get(protein_col, 0)) if protein_col else 0
            carbs = self.safe_float(row.get(carbs_col, 0)) if carbs_col else 0
            fats = self.safe_float(row.get(fat_col, 0)) if fat_col else 0
            category = row.get(category_col, 'Autre') if category_col else 'Autre'
            
            # Nettoyer le nom arabe
            arabic_name = self.clean_arabic_name(arabic_name, english_name)
            
            # Ne garder que si calories > 0
            if calories > 0 and calories < 2000:
                entry = {
                    "name_english": english_name,
                    "name_arabic": arabic_name,
                    "calories": calories,
                    "proteines": proteins,
                    "glucides": carbs,
                    "lipides": fats,
                    "category": category,
                    "source": os.path.basename(csv_path)
                }
                entries.append(entry)
                self.stats["categories"][category] = self.stats["categories"].get(category, 0) + 1
        
        print(f"  {len(entries)} entrees extraites")
        self.all_entries.extend(entries)
        self.stats["total_processed"] += len(entries)
        
        return entries
    
    def safe_float(self, value):
        """Convertir une valeur en float."""
        try:
            if pd.isna(value):
                return 0
            if isinstance(value, str):
                # Extraire les nombres
                numbers = re.findall(r'\d+(?:\.\d+)?', value)
                if numbers:
                    return float(numbers[0])
            return float(value)
        except (ValueError, TypeError):
            return 0
    
    def clean_arabic_name(self, arabic_name, english_name):
        """Nettoyer et normaliser le nom arabe."""
        
        # Supprimer les parentheses et leur contenu
        arabic_name = re.sub(r'\([^)]*\)', '', arabic_name)
        
        # Supprimer les guillemets
        arabic_name = arabic_name.replace('"', '').replace("'", "")
        
        # Nettoyer les espaces multiples
        arabic_name = re.sub(r'\s+', ' ', arabic_name).strip()
        
        # Si le nom est vide, utiliser une version simplifiee de l'anglais
        if not arabic_name or len(arabic_name) < 2:
            # Traduction simplifiee
            simple_map = {
                "pizza": "بيتزا",
                "burger": "برغر",
                "chicken": "دجاج",
                "beef": "لحم",
                "fish": "سمك",
                "salad": "سلطة",
                "soup": "شوربة",
                "milk": "حليب",
                "coffee": "قهوة",
                "tea": "شاي",
                "juice": "عصير",
            }
            eng_lower = english_name.lower()
            for key, arb in simple_map.items():
                if key in eng_lower:
                    return arb
            return english_name[:20]
        
        return arabic_name
    
    def create_backup(self):
        """Creer une sauvegarde de nutrition_db.py."""
        os.makedirs("data/backups", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"data/backups/nutrition_db_backup_{timestamp}.py"
        
        if os.path.exists(self.nutrition_db_path):
            shutil.copy(self.nutrition_db_path, backup_file)
            print(f"\nBackup cree: {backup_file}")
            return backup_file
        return None
    
    def get_existing_foods(self):
        """Extraire les aliments deja presents dans nutrition_db.py."""
        if not os.path.exists(self.nutrition_db_path):
            return set()
        
        with open(self.nutrition_db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        pattern = r'"([^"]+)"\s*:'
        existing = set(re.findall(pattern, content))
        return existing
    
    def add_to_nutrition_db(self):
        """Ajouter les entrees a nutrition_db.py."""
        print("\nAjout a nutrition_db.py...")
        
        # Creer une sauvegarde
        self.create_backup()
        
        # Verifier les aliments existants
        existing_foods = self.get_existing_foods()
        
        # Filtrer les nouveaux aliments
        new_entries = []
        for entry in self.all_entries:
            name = entry['name_arabic']
            if name and name not in existing_foods:
                line = f'    "{name}": {{"calories": {entry["calories"]}, "proteines": {entry["proteines"]}, "glucides": {entry["glucides"]}, "lipides": {entry["lipides"]}}},'
                new_entries.append(line)
                existing_foods.add(name)
        
        if not new_entries:
            print("Aucun nouvel aliment a ajouter")
            return
        
        # Lire le fichier existant
        with open(self.nutrition_db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Trouver la fin du dictionnaire
        import re
        pattern = r'(NUTRITION_DB = \{)(.*?)(\n\})'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            section_header = "\n    # ===== DONNEES IMPORTEES DU CSV =====\n"
            new_content = content.replace(
                match.group(0),
                f'NUTRITION_DB = {{{match.group(2)}{section_header}' + '\n    '.join(new_entries) + '\n}}'
            )
        else:
            # Si la structure n'existe pas, creer le dictionnaire
            new_content = f'NUTRITION_DB = {{\n' + '\n    '.join(new_entries) + '\n}}'
        
        # Sauvegarder
        with open(self.nutrition_db_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        self.stats["total_added"] = len(new_entries)
        print(f"  {len(new_entries)} nouveaux aliments ajoutes")
        
        # Afficher quelques exemples
        print("\nExemples d'aliments ajoutes:")
        for entry in new_entries[:15]:
            name = entry.split(':')[0].strip(' "')
            print(f"     - {name}")
        
        if len(new_entries) > 15:
            print(f"     ... et {len(new_entries) - 15} autres")
    
    def generate_report(self):
        """Generer un rapport de l'import."""
        print("\n" + "=" * 60)
        print("RAPPORT D'IMPORTATION")
        print("=" * 60)
        
        print(f"\nTotal entrees traitees: {self.stats['total_processed']}")
        print(f"Nouveaux aliments ajoutes: {self.stats['total_added']}")
        
        if self.stats['categories']:
            print("\nPar categorie:")
            for cat, count in sorted(self.stats['categories'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {cat}: {count} aliments")
        
        # Sauvegarder le rapport en JSON
        report_file = "data/imported/import_report.json"
        os.makedirs("data/imported", exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "date": datetime.now().isoformat(),
                "total_processed": self.stats['total_processed'],
                "total_added": self.stats['total_added'],
                "categories": self.stats['categories']
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nRapport sauvegarde: {report_file}")
    
    def save_export(self):
        """Exporter toutes les entrees en JSON pour reference."""
        export_file = "data/imported/all_imported_foods.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_entries, f, ensure_ascii=False, indent=2)
        print(f"Export complet: {export_file}")
    
    def run(self, csv_files):
        """
        Executer l'import pour une liste de fichiers CSV.
        
        Args:
            csv_files: Liste des chemins vers les fichiers CSV
        """
        print("=" * 60)
        print("IMPORTATION DES FICHIERS CSV VERS NUTRITION_DB.PY")
        print("=" * 60)
        print(f"\n{len(csv_files)} fichier(s) a traiter")
        
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                self.process_csv_file(csv_file)
            else:
                print(f"\nFichier non trouve: {csv_file}")
        
        if self.all_entries:
            self.save_export()
            self.add_to_nutrition_db()
            self.generate_report()
        else:
            print("\nAucune donnee valide trouvee.")
        
        print("\n" + "=" * 60)
        print("IMPORTATION TERMINEE")
        print("=" * 60)


def main():
    """
    Fonction principale.
    """
    
    # Chemins vers vos fichiers CSV
    csv_files = [
        "data/imported/nutrients_csvfile.csv",
        "data/imported/menu.csv"
    ]
    
    # Verifier les fichiers
    print("Verification des fichiers:")
    for f in csv_files:
        if os.path.exists(f):
            print(f"  [OK] {f}")
        else:
            print(f"  [MANQUANT] {f}")
    
    # Demander si on veut utiliser la traduction online
    print("\nOptions de traduction:")
    print("  1. Hors ligne (dictionnaire local) - plus rapide")
    print("  2. En ligne (Google Translate) - plus precis, necessite internet")
    
    choice = input("\nChoisissez (1 ou 2): ").strip()
    use_online = (choice == "2")
    
    if use_online:
        print("\nInstallation de googletrans...")
        os.system("pip install googletrans==4.0.0-rc1")
    
    # Executer l'import
    importer = CSVImporter(use_online_translation=use_online)
    importer.run(csv_files)


if __name__ == "__main__":
    main()