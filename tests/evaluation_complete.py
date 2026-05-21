# tests/evaluation_complete.py
"""
Evaluation complete avec Precision, Recall, F1-Score
Charge les phrases de test depuis un fichier JSON
Genere des graphiques PNG dans le dossier tests/metrics
"""

import sys
import io
import os
import time
import json
import glob
from datetime import datetime

# Configuration UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ajouter le chemin du projet
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.ner.spacy_ner import SpacyNERExtractor
from backend.ner.llm_ner import LLMNERExtractor

# Essayer d'importer matplotlib pour les graphiques
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib non installe. Installation: pip install matplotlib")


# ========== METTEZ VOTRE CLE API ICI ==========
# Exemple: API_KEY = "sk-proj-123456789abcdef"
# NE METTEZ PAS DE GUILLEMETS AUTOUR DE LA CLE DANS LE CODE
API_KEY = "sk-abcdef1234567890abcdef1234567890abcdef12"  # <--- REMPLACEZ PAR VOTRE VRAIE CLE
# ==============================================


class EvaluationComplete:
    """
    Evaluation complete avec calcul de Precision, Recall, F1-Score
    """
    
    def __init__(self, test_file=None, api_key=None):
        """
        Initialise l'evaluation.
        
        Args:
            test_file: Chemin vers un fichier JSON specifique (optionnel)
            api_key: Clé API OpenAI (optionnel)
        """
        print("=" * 70)
        print("INITIALISATION DE L'EVALUATION")
        print("=" * 70)
        
        # Initialiser spaCy
        self.spacy = SpacyNERExtractor()
        
        # ========== VERIFICATION DE LA CLE API ==========
        final_api_key = None
        
        # 1. Verifier le parametre api_key
        if api_key:
            final_api_key = api_key
            print("[OK] Cle API fournie en parametre")
            print(f"   Cle: {final_api_key[:20]}...")
        
        # 2. Verifier la variable globale API_KEY
        elif 'API_KEY' in globals() and API_KEY and API_KEY != "sk-proj-votre_clé_api_ici":
            final_api_key = API_KEY
            print("[OK] Cle API chargee depuis la variable API_KEY dans le code")
            print(f"   Cle: {final_api_key[:20]}...")
        
        # 3. Verifier la variable d'environnement
        else:
            env_key = os.environ.get('OPENAI_API_KEY', None)
            if env_key:
                final_api_key = env_key
                print("[OK] Cle API chargee depuis la variable d'environnement OPENAI_API_KEY")
                print(f"   Cle: {final_api_key[:20]}...")
            else:
                print("[ERREUR] Aucune cle API trouvee!")
                print("   Veuillez configurer votre cle API de l'une des manieres suivantes:")
                print("   1. Modifier la variable API_KEY dans ce fichier (ligne 47)")
                print("   2. Ou utiliser: $env:OPENAI_API_KEY='votre_cle'")
                print("   3. Ou utiliser: python tests/evaluation_complete.py --api-key 'votre_cle'")
        
        # Afficher le statut final
        if final_api_key:
            print(f"\n[INFO] LLM sera execute en MODE REEL avec votre cle API")
        else:
            print(f"\n[INFO] LLM sera execute en MODE DEMO (resultats simules)")
        # ===============================================
        
        self.llm = LLMNERExtractor(final_api_key)
        
        # Creer le dossier pour les graphiques
        self.metrics_dir = "tests/metrics"
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Charger les phrases de test
        self.ground_truth = {}
        self.test_file_used = None
        
        if test_file:
            self.load_from_json(test_file)
        else:
            self.load_latest_test_file()
        
        # Si aucun fichier trouve, utiliser le dataset par defaut
        if not self.ground_truth:
            print("Aucun fichier de test trouve. Utilisation du dataset par defaut.")
            self.use_default_ground_truth()
        
        print(f"Nombre de phrases de test chargees: {len(self.ground_truth)}")
        print()
        
        self.results = {
            "spacy": {
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "quantity_correct": 0,
                "quantity_total": 0,
                "times": [],
                "calories_errors": []
            },
            "llm": {
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "quantity_correct": 0,
                "quantity_total": 0,
                "times": [],
                "calories_errors": []
            }
        }
    
    def load_from_json(self, json_file):
        """Charge les phrases de test depuis un fichier JSON."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            for item in test_data:
                self.ground_truth[item['text']] = {
                    "foods": item['foods'],
                    "quantities": item.get('quantities', []),
                    "calories": item['calories']
                }
            
            self.test_file_used = json_file
            print(f"[OK] Chargement depuis {json_file}")
            print(f"    {len(self.ground_truth)} phrases chargees")
            
        except Exception as e:
            print(f"[ERREUR] Impossible de charger {json_file}: {e}")
    
    def load_latest_test_file(self):
        """Charge le fichier JSON le plus recent du dossier data/test_phrases."""
        test_dir = "data/test_phrases"
        
        if not os.path.exists(test_dir):
            print(f"Dossier {test_dir} non trouve")
            return
        
        json_files = glob.glob(f"{test_dir}/test_phrases_*.json")
        
        if json_files:
            latest = max(json_files, key=os.path.getctime)
            self.load_from_json(latest)
        else:
            print(f"Aucun fichier test_phrases_*.json trouve dans {test_dir}")
    
    def use_default_ground_truth(self):
        """Dataset par defaut si aucun fichier JSON n'est trouve."""
        self.ground_truth = {
            "اكلت دجاج": {"foods": ["دجاج"], "quantities": [], "calories": 165},
            "اكلت فراوله": {"foods": ["فراوله"], "quantities": [], "calories": 280},
            "اكلت تفاحه": {"foods": ["تفاحه"], "quantities": [], "calories": 52},
            "شربت حليب": {"foods": ["حليب"], "quantities": [], "calories": 42},
            "اكلت سمك": {"foods": ["سمك"], "quantities": [], "calories": 206},
            "اكلت جبن": {"foods": ["جبن"], "quantities": [], "calories": 350},
            "اكلت بيتزا": {"foods": ["بيتزا"], "quantities": [], "calories": 285},
            "اكلت خبز": {"foods": ["خبز"], "quantities": [], "calories": 265},
            "اكلت نصف دجاج": {"foods": ["دجاج"], "quantities": ["نصف"], "calories": 82.5},
            "اكلت ربع بيتزا": {"foods": ["بيتزا"], "quantities": ["ربع"], "calories": 71.25},
            "اكلت قليل من جبن": {"foods": ["جبن"], "quantities": ["قليل"], "calories": 105},
            "شربت كوب حليب": {"foods": ["حليب"], "quantities": ["كوب"], "calories": 42},
            "اكلت 2 تفاح": {"foods": ["تفاح"], "quantities": ["2"], "calories": 104},
            "اكلت دجاج و ارز": {"foods": ["دجاج", "ارز"], "quantities": [], "calories": 295},
            "اكلت سمك و بطاطس": {"foods": ["سمك", "بطاطس"], "quantities": [], "calories": 283},
            "اكلت لحم و خبز": {"foods": ["لحم", "خبز"], "quantities": [], "calories": 515},
        }
    
    def calculate_food_metrics(self, predicted, actual):
        """Calcule True Positives, False Positives, False Negatives."""
        predicted_list = [str(item) if not isinstance(item, str) else item for item in predicted]
        actual_list = [str(item) if not isinstance(item, str) else item for item in actual]
        
        predicted_set = set(predicted_list)
        actual_set = set(actual_list)
        
        tp = len(predicted_set & actual_set)
        fp = len(predicted_set - actual_set)
        fn = len(actual_set - predicted_set)
        
        return tp, fp, fn
    
    def check_quantity(self, predicted_q, actual_q):
        """Verifie si la quantite est correctement interpretee."""
        if not actual_q:
            return True
        
        if not predicted_q:
            return False
        
        predicted_str = [str(q) for q in predicted_q]
        actual_str = [str(q) for q in actual_q]
        
        for q in predicted_str:
            for a in actual_str:
                if q in a or a in q:
                    return True
        
        return False
    
    def calculate_calorie_error(self, predicted_cal, actual_cal):
        """Calcule l'erreur absolue des calories."""
        try:
            return abs(float(predicted_cal) - float(actual_cal))
        except:
            return abs(actual_cal)
    
    def evaluate_model(self, model, model_name):
        """Evalue un modele sur toutes les phrases."""
        total_tp = 0
        total_fp = 0
        total_fn = 0
        quantity_correct = 0
        quantity_total = 0
        times = []
        calorie_errors = []
        
        print(f"\nEvaluation de {model_name} sur {len(self.ground_truth)} phrases...")
        print("-" * 50)
        
        for idx, (text, truth) in enumerate(self.ground_truth.items(), 1):
            if idx % 20 == 0:
                print(f"  Progression: {idx}/{len(self.ground_truth)}")
            
            start = time.time()
            entities, nutrition, proc_time = model.process(text)
            elapsed_ms = (time.time() - start) * 1000
            
            times.append(elapsed_ms)
            
            predicted_foods = entities.get("foods", [])
            actual_foods = truth.get("foods", [])
            tp, fp, fn = self.calculate_food_metrics(predicted_foods, actual_foods)
            
            total_tp += tp
            total_fp += fp
            total_fn += fn
            
            predicted_q = entities.get("quantities", [])
            actual_q = truth.get("quantities", [])
            if actual_q:
                quantity_total += 1
                if self.check_quantity(predicted_q, actual_q):
                    quantity_correct += 1
            
            calorie_error = self.calculate_calorie_error(nutrition["calories"], truth["calories"])
            calorie_errors.append(calorie_error)
        
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        quantity_accuracy = quantity_correct / quantity_total if quantity_total > 0 else 0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "quantity_accuracy": quantity_accuracy,
            "avg_time_ms": sum(times) / len(times) if times else 0,
            "min_time_ms": min(times) if times else 0,
            "max_time_ms": max(times) if times else 0,
            "avg_calorie_error": sum(calorie_errors) / len(calorie_errors) if calorie_errors else 0,
            "total_tp": total_tp,
            "total_fp": total_fp,
            "total_fn": total_fn,
            "quantity_correct": quantity_correct,
            "quantity_total": quantity_total
        }
    
    def generate_bar_chart(self, spacy_results, llm_results):
        """Genere un graphique a barres comparatif."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        metrics = ['Precision', 'Recall', 'F1-Score', 'Quantity Accuracy']
        spacy_values = [
            spacy_results['precision'] * 100,
            spacy_results['recall'] * 100,
            spacy_results['f1'] * 100,
            spacy_results['quantity_accuracy'] * 100
        ]
        llm_values = [
            llm_results['precision'] * 100,
            llm_results['recall'] * 100,
            llm_results['f1'] * 100,
            llm_results['quantity_accuracy'] * 100
        ]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars1 = ax.bar(x - width/2, spacy_values, width, label='spaCy', color='#2E86AB', alpha=0.8)
        
        has_llm_values = any(v > 0 for v in llm_values)
        if has_llm_values:
            bars2 = ax.bar(x + width/2, llm_values, width, label='LLM', color='#A23B72', alpha=0.8)
        
        ax.set_ylabel('Percentage (%)')
        ax.set_title('Performance Comparison: spaCy vs LLM')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.legend(loc='upper right')
        ax.set_ylim(0, 100)
        
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        
        if has_llm_values:
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                               xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        else:
            ax.text(0.5, 0.5, 'LLM not available (no API key)', 
                   transform=ax.transAxes, ha='center', va='center', 
                   fontsize=12, color='gray', style='italic')
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.metrics_dir, 'performance_comparison.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Graphique sauvegarde: {chart_path}")
        return chart_path
    
    def generate_radar_chart(self, spacy_results, llm_results):
        """Genere un graphique radar."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        metrics = ['Precision', 'Recall', 'F1-Score', 'Quantity Acc.', 'Speed']
        spacy_values = [
            spacy_results['precision'] * 100,
            spacy_results['recall'] * 100,
            spacy_results['f1'] * 100,
            spacy_results['quantity_accuracy'] * 100,
            min(100, 10000 / max(spacy_results['avg_time_ms'], 1))
        ]
        llm_values = [
            llm_results['precision'] * 100,
            llm_results['recall'] * 100,
            llm_results['f1'] * 100,
            llm_results['quantity_accuracy'] * 100,
            min(100, 10000 / max(llm_results['avg_time_ms'], 1))
        ]
        
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]
        
        spacy_values += spacy_values[:1]
        llm_values += llm_values[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
        
        ax.plot(angles, spacy_values, 'o-', linewidth=2, label='spaCy', color='#2E86AB')
        ax.fill(angles, spacy_values, alpha=0.25, color='#2E86AB')
        
        has_llm_values = any(v > 0 for v in llm_values[:-1])
        if has_llm_values:
            ax.plot(angles, llm_values, 'o-', linewidth=2, label='LLM', color='#A23B72')
            ax.fill(angles, llm_values, alpha=0.25, color='#A23B72')
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        ax.set_ylim(0, 100)
        ax.set_title('Performance Radar Chart', size=14, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.metrics_dir, 'radar_chart.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Graphique radar sauvegarde: {chart_path}")
        return chart_path
    
    def generate_time_chart(self, spacy_results, llm_results):
        """Genere un graphique des temps de reponse."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        models = ['spaCy', 'LLM']
        times = [spacy_results['avg_time_ms'], llm_results['avg_time_ms']]
        colors = ['#2E86AB', '#A23B72']
        
        bars = ax.bar(models, times, color=colors, alpha=0.8)
        
        ax.set_ylabel('Time (milliseconds)')
        ax.set_title('Average Response Time Comparison')
        
        for bar, time_val in zip(bars, times):
            if time_val > 0:
                ax.annotate(f'{time_val:.1f} ms', xy=(bar.get_x() + bar.get_width()/2, time_val),
                           xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.metrics_dir, 'response_time.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Graphique temps de reponse sauvegarde: {chart_path}")
        return chart_path
    
    def generate_calorie_error_chart(self, spacy_results, llm_results):
        """Genere un graphique des erreurs de calories."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        models = ['spaCy', 'LLM']
        errors = [spacy_results['avg_calorie_error'], llm_results['avg_calorie_error']]
        colors = ['#2E86AB', '#A23B72']
        
        bars = ax.bar(models, errors, color=colors, alpha=0.8)
        
        ax.set_ylabel('Error (kcal)')
        ax.set_title('Average Calorie Estimation Error')
        
        for bar, err_val in zip(bars, errors):
            if err_val > 0:
                ax.annotate(f'{err_val:.1f} kcal', xy=(bar.get_x() + bar.get_width()/2, err_val),
                           xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.metrics_dir, 'calorie_error.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Graphique erreur calories sauvegarde: {chart_path}")
        return chart_path
    
    def generate_all_charts(self, spacy_results, llm_results):
        """Genere tous les graphiques."""
        print("\n" + "=" * 50)
        print("GENERATION DES GRAPHIQUES")
        print("=" * 50)
        
        if not MATPLOTLIB_AVAILABLE:
            print("matplotlib non installe. Installation: pip install matplotlib")
            return
        
        self.generate_bar_chart(spacy_results, llm_results)
        self.generate_radar_chart(spacy_results, llm_results)
        self.generate_time_chart(spacy_results, llm_results)
        self.generate_calorie_error_chart(spacy_results, llm_results)
        
        print(f"\nTous les graphiques sont dans le dossier: {self.metrics_dir}")
    
    def run_evaluation(self):
        """Execute l'evaluation complete."""
        print("=" * 70)
        print("EVALUATION COMPLETE - Voice-to-Calorie")
        print("=" * 70)
        print(f"\nReference (Ground Truth): {self.test_file_used if self.test_file_used else 'Dataset par defaut'}")
        print("Source: USDA FoodData Central")
        print(f"Nombre de phrases de test: {len(self.ground_truth)}")
        
        types = {}
        for truth in self.ground_truth.values():
            t = "with_quantity" if truth.get('quantities') else "simple"
            types[t] = types.get(t, 0) + 1
        print(f"  - Phrases simples: {types.get('simple', 0)}")
        print(f"  - Phrases avec quantites: {types.get('with_quantity', 0)}")
        
        print("-" * 70)
        
        print("\n[1/2] Evaluation de spaCy...")
        spacy_results = self.evaluate_model(self.spacy, "spaCy")
        
        print("\n[2/2] Evaluation de LLM...")
        llm_results = self.evaluate_model(self.llm, "LLM")
        
        return spacy_results, llm_results
    
    def print_results_table(self, spacy_results, llm_results):
        """Affiche les resultats sous forme de tableau."""
        print("\n" + "=" * 70)
        print("RESULTATS DE L'EVALUATION")
        print("=" * 70)
        
        print("\n" + "-" * 70)
        print(f"{'Metric':<30} {'spaCy':<18} {'LLM':<18} {'Improvement':<10}")
        print("-" * 70)
        
        spacy_p = spacy_results['precision'] * 100
        llm_p = llm_results['precision'] * 100
        print(f"{'Precision (%)':<30} {spacy_p:>17.1f}% {llm_p:>17.1f}% {llm_p - spacy_p:>+9.1f}%")
        
        spacy_r = spacy_results['recall'] * 100
        llm_r = llm_results['recall'] * 100
        print(f"{'Recall (%)':<30} {spacy_r:>17.1f}% {llm_r:>17.1f}% {llm_r - spacy_r:>+9.1f}%")
        
        spacy_f1 = spacy_results['f1'] * 100
        llm_f1 = llm_results['f1'] * 100
        print(f"{'F1-Score (%)':<30} {spacy_f1:>17.1f}% {llm_f1:>17.1f}% {llm_f1 - spacy_f1:>+9.1f}%")
        
        spacy_q = spacy_results['quantity_accuracy'] * 100
        llm_q = llm_results['quantity_accuracy'] * 100
        print(f"{'Quantity Accuracy (%)':<30} {spacy_q:>17.1f}% {llm_q:>17.1f}% {llm_q - spacy_q:>+9.1f}%")
        
        print(f"{'Response Time (ms)':<30} {spacy_results['avg_time_ms']:>17.1f} {llm_results['avg_time_ms']:>17.1f} {-(llm_results['avg_time_ms'] - spacy_results['avg_time_ms']):>+9.1f}")
        
        print(f"{'Avg Calorie Error (kcal)':<30} {spacy_results['avg_calorie_error']:>17.1f} {llm_results['avg_calorie_error']:>17.1f} {-(llm_results['avg_calorie_error'] - spacy_results['avg_calorie_error']):>+9.1f}")
        
        print("-" * 70)
        
        print("\nDETAIL DES COMPTAGES:")
        print(f"{'Metric':<30} {'spaCy':<18} {'LLM':<18}")
        print("-" * 70)
        print(f"{'True Positives (TP)':<30} {spacy_results['total_tp']:<18} {llm_results['total_tp']:<18}")
        print(f"{'False Positives (FP)':<30} {spacy_results['total_fp']:<18} {llm_results['total_fp']:<18}")
        print(f"{'False Negatives (FN)':<30} {spacy_results['total_fn']:<18} {llm_results['total_fn']:<18}")
    
    def print_discussion(self, spacy_results, llm_results):
        """Affiche la discussion des resultats."""
        print("\n" + "=" * 70)
        print("DISCUSSION DES RESULTATS")
        print("=" * 70)
        
        llm_worked = llm_results['total_tp'] > 0 or llm_results['total_fp'] > 0 or llm_results['total_fn'] > 0
        
        if not llm_worked:
            print("\n[ATTENTION] LLM n'a pas fonctionne correctement!")
            print("   Les resultats LLM sont tous a zero.")
            print("   Verifiez que votre cle API est valide et que vous avez des credits.")
            print("   Pour reessayer: $env:OPENAI_API_KEY='votre_cle'; python tests/evaluation_complete.py")
        
        print("\n1. COMPARAISON DES PERFORMANCES:")
        print("-" * 50)
        
        f1_gap = (llm_results['f1'] - spacy_results['f1']) * 100
        time_ratio = llm_results['avg_time_ms'] / spacy_results['avg_time_ms'] if spacy_results['avg_time_ms'] > 0 else 0
        
        if f1_gap > 0:
            print(f"   - LLM est plus precis que spaCy de {f1_gap:.1f}% en F1-Score")
        elif f1_gap < 0:
            print(f"   - spaCy est plus precis que LLM de {abs(f1_gap):.1f}% en F1-Score")
        else:
            print(f"   - Les deux modeles ont le meme F1-Score")
        
        if time_ratio > 1:
            print(f"   - spaCy est {time_ratio:.1f}x plus rapide que LLM")
        elif time_ratio > 0 and time_ratio < 1:
            print(f"   - LLM est {1/time_ratio:.1f}x plus rapide que spaCy")
        else:
            print(f"   - Comparaison de vitesse non disponible")
        
        print("\n2. ANALYSE DES ERREURS:")
        print("-" * 50)
        
        q_gap = (llm_results['quantity_accuracy'] - spacy_results['quantity_accuracy']) * 100
        if q_gap > 0:
            print(f"   - LLM gere mieux les quantites floues (+{q_gap:.0f}%)")
        elif q_gap < 0:
            print(f"   - spaCy gere mieux les quantites floues (+{abs(q_gap):.0f}%)")
        else:
            print(f"   - Performance identique sur les quantites")
        
        cal_gap = spacy_results['avg_calorie_error'] - llm_results['avg_calorie_error']
        if cal_gap > 0:
            print(f"   - LLM est plus precis sur l'estimation des calories (erreur reduite de {cal_gap:.1f} kcal)")
        elif cal_gap < 0:
            print(f"   - spaCy est plus precis sur l'estimation des calories (erreur reduite de {abs(cal_gap):.1f} kcal)")
        else:
            print(f"   - Erreur de calories identique")
        
        print("\n3. TRADE-OFF RAPIDITE / PRECISION:")
        print("-" * 50)
        print("   - spaCy: Ideal pour les applications temps reel (reponse < 100ms)")
        print("   - LLM:  Ideal pour les cas complexes necessitant une haute precision")
        print("   - Recommandation: Approche hybride (spaCy + fallback LLM)")
    
    def save_results_json(self, spacy_results, llm_results):
        """Sauvegarde les resultats en JSON."""
        os.makedirs("data/reports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output = {
            "date": timestamp,
            "test_file": self.test_file_used,
            "ground_truth_size": len(self.ground_truth),
            "spacy": {
                "precision": spacy_results['precision'],
                "recall": spacy_results['recall'],
                "f1_score": spacy_results['f1'],
                "quantity_accuracy": spacy_results['quantity_accuracy'],
                "avg_time_ms": spacy_results['avg_time_ms'],
                "avg_calorie_error": spacy_results['avg_calorie_error'],
                "true_positives": spacy_results['total_tp'],
                "false_positives": spacy_results['total_fp'],
                "false_negatives": spacy_results['total_fn']
            },
            "llm": {
                "precision": llm_results['precision'],
                "recall": llm_results['recall'],
                "f1_score": llm_results['f1'],
                "quantity_accuracy": llm_results['quantity_accuracy'],
                "avg_time_ms": llm_results['avg_time_ms'],
                "avg_calorie_error": llm_results['avg_calorie_error'],
                "true_positives": llm_results['total_tp'],
                "false_positives": llm_results['total_fp'],
                "false_negatives": llm_results['total_fn']
            }
        }
        
        report_file = f"data/reports/evaluation_results_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\nResultats sauvegardes dans: {report_file}")
        
        return report_file
    
    def run(self):
        """Execute l'evaluation complete."""
        spacy_results, llm_results = self.run_evaluation()
        
        self.print_results_table(spacy_results, llm_results)
        self.print_discussion(spacy_results, llm_results)
        
        self.save_results_json(spacy_results, llm_results)
        self.generate_all_charts(spacy_results, llm_results)
        
        return spacy_results, llm_results


def main():
    """
    Fonction principale.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluation de Voice-to-Calorie')
    parser.add_argument('--file', '-f', type=str, help='Fichier JSON specifique a utiliser')
    parser.add_argument('--api-key', '-k', type=str, help='Cle API OpenAI (optionnel)')
    parser.add_argument('--list', '-l', action='store_true', help='Lister les fichiers disponibles')
    
    args = parser.parse_args()
    
    if args.list:
        test_dir = "data/test_phrases"
        if os.path.exists(test_dir):
            files = glob.glob(f"{test_dir}/test_phrases_*.json")
            print("Fichiers de test disponibles:")
            for f in sorted(files):
                print(f"  - {f}")
        else:
            print(f"Dossier {test_dir} non trouve")
        return
    
    evaluator = EvaluationComplete(test_file=args.file, api_key=args.api_key)
    evaluator.run()


if __name__ == "__main__":
    main()