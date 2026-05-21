# scripts/preprocess_nutrition_db.py
"""
Data Preprocessing pour nutrition_db.py
Operations:
1. Normalisation des caracteres arabes (ة -> ه, ى -> ي, etc.)
2. Suppression des doublons
3. Nettoyage des entrees incorrectes (calories aberrantes, noms vides)
4. Verification des valeurs numeriques
5. Generation d'un rapport de nettoyage
"""

import re
import sys
import os
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class NutritionDBPreprocessor:
    """
    Classe pour nettoyer et normaliser la base de donnees nutritionnelle.
    """
    
    def __init__(self, db_path="data/nutrition_db.py"):
        self.db_path = db_path
        self.backup_path = None
        self.stats = {
            "original_count": 0,
            "final_count": 0,
            "duplicates_removed": 0,
            "invalid_entries_removed": 0,
            "normalized_names": [],
            "errors": []
        }
    
    def create_backup(self):
        """
        Cree une sauvegarde avant modification.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "data/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        self.backup_path = os.path.join(backup_dir, f"nutrition_db_backup_{timestamp}.py")
        
        import shutil
        shutil.copy(self.db_path, self.backup_path)
        print(f"Backup cree: {self.backup_path}")
        
        return self.backup_path
    
    def normalize_arabic_characters(self, text):
        """
        Normalise les caracteres arabes.
        Convertit les variantes en formes standard.
        
        Args:
            text: Texte arabe a normaliser
        
        Returns:
            Texte normalise
        """
        replacements = {
            'ة': 'ه',      # Ta marbuta -> Ha
            'ى': 'ي',      # Alif maqsura -> Ya
            'أ': 'ا',      # Alif with hamza -> Alif
            'إ': 'ا',      # Alif with hamza below -> Alif
            'آ': 'ا',      # Alif with madd -> Alif
            'ؤ': 'و',      # Waw with hamza -> Waw
            'ئ': 'ي',      # Ya with hamza -> Ya
            'ك': 'ك',      # Keef (standard)
            'ي': 'ي',      # Ya (standard)
            'ه': 'ه',      # Ha (standard)
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def is_valid_numeric_value(self, value):
        """
        Verifie si une valeur numerique est valide.
        
        Args:
            value: Valeur a verifier
        
        Returns:
            True si valide, False sinon
        """
        try:
            num = float(value)
            # Une valeur nutritionnelle raisonnable doit etre entre 0 et 2000
            if 0 <= num <= 2000:
                return True
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def is_valid_food_name(self, name):
        """
        Verifie si le nom d'un aliment est valide.
        
        Args:
            name: Nom de l'aliment
        
        Returns:
            True si valide, False sinon
        """
        if not name or not isinstance(name, str):
            return False
        
        # Supprimer les noms trop courts ou trop longs
        if len(name) < 2 or len(name) > 100:
            return False
        
        # Supprimer les noms qui ne contiennent que des chiffres ou symboles
        if re.match(r'^[\d\s\W]+$', name):
            return False
        
        return True
    
    def parse_nutrition_db(self):
        """
        Parse le fichier nutrition_db.py et extrait les donnees.
        
        Returns:
            Dictionnaire des entrees et le contenu original
        """
        with open(self.db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern pour extraire les entrees NUTRITION_DB
        pattern = r'NUTRITION_DB = \{(.*?)\n\}'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("Erreur: Structure NUTRITION_DB non trouvee")
            return {}, content
        
        db_content = match.group(1)
        
        # Pattern pour extraire chaque entree
        entry_pattern = r'"([^"]+)"\s*:\s*\{([^}]+)\}'
        entries = re.findall(entry_pattern, db_content)
        
        nutrition_data = {}
        for name, values_str in entries:
            # Extraire les valeurs
            calories_match = re.search(r'"calories":\s*([\d\.]+)', values_str)
            proteines_match = re.search(r'"proteines":\s*([\d\.]+)', values_str)
            glucides_match = re.search(r'"glucides":\s*([\d\.]+)', values_str)
            lipides_match = re.search(r'"lipides":\s*([\d\.]+)', values_str)
            
            nutrition_data[name] = {
                "calories": float(calories_match.group(1)) if calories_match else 0,
                "proteines": float(proteines_match.group(1)) if proteines_match else 0,
                "glucides": float(glucides_match.group(1)) if glucides_match else 0,
                "lipides": float(lipides_match.group(1)) if lipides_match else 0
            }
        
        self.stats["original_count"] = len(nutrition_data)
        print(f"Parse termine: {len(nutrition_data)} entrees trouvees")
        
        return nutrition_data, content
    
    def normalize_entries(self, nutrition_data):
        """
        Normalise les noms des aliments.
        
        Args:
            nutrition_data: Dictionnaire des donnees
        
        Returns:
            Dictionnaire normalise
        """
        normalized_data = {}
        
        for name, values in nutrition_data.items():
            # Normaliser le nom
            normalized_name = self.normalize_arabic_characters(name)
            
            # Supprimer les espaces multiples
            normalized_name = re.sub(r'\s+', ' ', normalized_name).strip()
            
            if normalized_name != name:
                self.stats["normalized_names"].append({
                    "original": name,
                    "normalized": normalized_name
                })
            
            # Si le nom normalise existe deja, fusionner ou garder le meilleur
            if normalized_name in normalized_data:
                # Garder l'entree avec les calories les plus raisonnables
                existing = normalized_data[normalized_name]
                if 0 < values["calories"] < 1000 and (existing["calories"] == 0 or existing["calories"] > 1000):
                    normalized_data[normalized_name] = values
            else:
                normalized_data[normalized_name] = values
        
        print(f"Normalisation: {len(self.stats['normalized_names'])} noms modifies")
        
        return normalized_data
    
    def remove_duplicates(self, nutrition_data):
        """
        Supprime les entrees en double.
        
        Args:
            nutrition_data: Dictionnaire des donnees
        
        Returns:
            Dictionnaire sans doublons
        """
        unique_data = {}
        
        for name, values in nutrition_data.items():
            # Verifier si les memes valeurs existent deja
            is_duplicate = False
            
            for existing_name, existing_values in unique_data.items():
                if (abs(existing_values["calories"] - values["calories"]) < 1 and
                    abs(existing_values["proteines"] - values["proteines"]) < 0.1 and
                    abs(existing_values["glucides"] - values["glucides"]) < 0.1 and
                    abs(existing_values["lipides"] - values["lipides"]) < 0.1):
                    
                    # Memes valeurs, garder le nom le plus court
                    if len(name) < len(existing_name):
                        del unique_data[existing_name]
                        unique_data[name] = values
                    is_duplicate = True
                    self.stats["duplicates_removed"] += 1
                    break
            
            if not is_duplicate:
                unique_data[name] = values
        
        print(f"Doublons supprimes: {self.stats['duplicates_removed']}")
        
        return unique_data
    
    def validate_entries(self, nutrition_data):
        """
        Valide et nettoie les entrees.
        Supprime les entrees avec des valeurs aberrantes.
        
        Args:
            nutrition_data: Dictionnaire des donnees
        
        Returns:
            Dictionnaire valide
        """
        valid_data = {}
        invalid_count = 0
        
        for name, values in nutrition_data.items():
            # Verifier le nom
            if not self.is_valid_food_name(name):
                self.stats["invalid_entries_removed"] += 1
                self.stats["errors"].append({
                    "name": name,
                    "reason": "Invalid food name"
                })
                continue
            
            # Verifier les calories
            if not self.is_valid_numeric_value(values["calories"]):
                self.stats["invalid_entries_removed"] += 1
                self.stats["errors"].append({
                    "name": name,
                    "reason": f"Invalid calories: {values['calories']}"
                })
                continue
            
            # Verifier les valeurs extremes
            if values["calories"] > 1500:
                self.stats["errors"].append({
                    "name": name,
                    "reason": f"High calories: {values['calories']} (may need verification)"
                })
            
            # Nettoyer les valeurs non valides pour les macros
            for key in ["proteines", "glucides", "lipides"]:
                if not self.is_valid_numeric_value(values[key]):
                    values[key] = 0.0
            
            valid_data[name] = values
        
        print(f"Entrees invalides supprimees: {self.stats['invalid_entries_removed']}")
        print(f"Erreurs signalees: {len(self.stats['errors'])}")
        
        return valid_data
    
    def generate_output_content(self, nutrition_data):
        """
        Genere le nouveau contenu du fichier nutrition_db.py.
        
        Args:
            nutrition_data: Dictionnaire des donnees nettoyees
        
        Returns:
            Contenu du fichier
        """
        # Trier par ordre alphabetique
        sorted_items = sorted(nutrition_data.items())
        
        # Generer les lignes
        lines = []
        lines.append("# data/nutrition_db.py")
        lines.append("# Base de donnees nutritionnelle nettoyee et normalisee")
        lines.append(f"# Date de nettoyage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("# Total aliments: " + str(len(sorted_items)))
        lines.append("")
        lines.append("NUTRITION_DB = {")
        
        current_category = None
        
        for name, values in sorted_items:
            # Categorisation approximative
            category = self.get_category(name)
            
            if category != current_category:
                current_category = category
                lines.append(f"")
                lines.append(f"    # {category}")
            
            line = f'    "{name}": {{"calories": {values["calories"]:.1f}, "proteines": {values["proteines"]:.1f}, "glucides": {values["glucides"]:.1f}, "lipides": {values["lipides"]:.1f}}},'
            lines.append(line)
        
        lines.append("}")
        lines.append("")
        lines.append("")
        lines.append("QUANTITY_FACTORS = {")
        
        # Ajouter les facteurs de quantite
        quantity_factors = {
            "نصف": 0.5,
            "ربع": 0.25,
            "ثلث": 0.33,
            "قليل": 0.3,
            "قليلا": 0.3,
            "بعض": 0.5,
            "كمية قليلة": 0.3,
            "كمية كبيرة": 1.5,
            "جزء": 0.7,
            "طبق صغير": 0.7,
            "طبق متوسط": 1.0,
            "طبق كبير": 1.3,
            "كوب صغير": 0.7,
            "كوب كبير": 1.3,
        }
        
        for factor_name, factor_value in sorted(quantity_factors.items()):
            lines.append(f'    "{factor_name}": {factor_value},')
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def get_category(self, food_name):
        """
        Determine la categorie d'un aliment.
        
        Args:
            food_name: Nom de l'aliment
        
        Returns:
            Categorie
        """
        categories = {
            "Legumes": ["سلطة", "خضار", "بطاطس", "طماطم", "خيار", "جزر", "بصل", "فلفل", "سبانخ", "بروكلي"],
            "Fruits": ["تفاح", "موز", "برتقال", "فراولة", "عنب", "تمر", "فاكهة", "مانجو", "أناناس"],
            "Viandes": ["دجاج", "لحم", "سمك", "تونة", "بيض", "بقر", "خروف", "هام", "سجق"],
            "Produits laitiers": ["حليب", "جبن", "زبدة", "زبادي", "كريمة", "لبن"],
            "Boissons": ["عصير", "قهوة", "شاي", "مشروب غازي", "كولا", "سبرايت"],
            "Cereales": ["خبز", "أرز", "كسكس", "معكرونة", "بيتزا", "برغر"],
            "Plats composes": ["طاجين", "حريرة", "شوربة", "باستا", "ماك مافن", "بيغ ماك"],
            "Patisseries": ["كعكة", "بسكويت", "شباكية", "مسمن", "حلويات", "آيس كريم"],
            "Autres": []
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in food_name:
                    return category
        
        return "Autres"
    
    def save_report(self):
        """
        Sauvegarde un rapport du nettoyage.
        """
        report_dir = "data/reports"
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(report_dir, f"preprocessing_report_{timestamp}.json")
        
        report = {
            "date": datetime.now().isoformat(),
            "source_file": self.db_path,
            "backup_file": self.backup_path,
            "statistics": self.stats,
            "normalized_names": self.stats["normalized_names"][:50],  # Limiter a 50
            "errors": self.stats["errors"][:50]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"Rapport sauvegarde: {report_path}")
        
        return report_path
    
    def print_summary(self):
        """
        Affiche un resume du nettoyage.
        """
        print("\n" + "=" * 60)
        print("RESUME DU NETTOYAGE")
        print("=" * 60)
        
        print(f"\nEntrees originales: {self.stats['original_count']}")
        print(f"Entrees finales: {self.stats['final_count']}")
        print(f"Doublons supprimes: {self.stats['duplicates_removed']}")
        print(f"Entrees invalides supprimees: {self.stats['invalid_entries_removed']}")
        print(f"Noms normalises: {len(self.stats['normalized_names'])}")
        
        if self.stats['errors']:
            print(f"\nErreurs detectees: {len(self.stats['errors'])}")
            print("Premieres erreurs:")
            for error in self.stats['errors'][:10]:
                print(f"  - {error['name']}: {error['reason']}")
        
        print("\n" + "=" * 60)
    
    def run(self, create_backup=True):
        """
        Execute le pipeline complet de preprocessing.
        
        Args:
            create_backup: Creer une sauvegarde avant modification
        """
        print("=" * 60)
        print("PREPROCESSING DE LA BASE DE DONNEES NUTRITIONNELLE")
        print("=" * 60)
        
        # 1. Creer une sauvegarde
        if create_backup:
            self.create_backup()
        
        # 2. Parser le fichier
        nutrition_data, original_content = self.parse_nutrition_db()
        
        if not nutrition_data:
            print("Erreur: Aucune donnee trouvee")
            return False
        
        # 3. Normaliser les noms
        normalized_data = self.normalize_entries(nutrition_data)
        
        # 4. Supprimer les doublons
        deduplicated_data = self.remove_duplicates(normalized_data)
        
        # 5. Valider les entrees
        validated_data = self.validate_entries(deduplicated_data)
        
        # 6. Mettre a jour les statistiques
        self.stats["final_count"] = len(validated_data)
        
        # 7. Generer le nouveau contenu
        new_content = self.generate_output_content(validated_data)
        
        # 8. Sauvegarder le fichier
        with open(self.db_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"\nFichier sauvegarde: {self.db_path}")
        
        # 9. Sauvegarder le rapport
        self.save_report()
        
        # 10. Afficher le resume
        self.print_summary()
        
        print("\nPREPROCESSING TERMINE AVEC SUCCES")
        
        return True


def main():
    """
    Fonction principale.
    """
    
    preprocessor = NutritionDBPreprocessor()
    
    # Demander confirmation
    print("Ce script va nettoyer et normaliser votre base de donnees.")
    print("Une sauvegarde sera creee avant modification.")
    print()
    
    confirm = input("Voulez-vous continuer? (o/n): ").strip().lower()
    
    if confirm == 'o':
        preprocessor.run(create_backup=True)
    else:
        print("Operation annulee.")


if __name__ == "__main__":
    main()