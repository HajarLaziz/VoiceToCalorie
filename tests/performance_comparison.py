# tests/performance_comparison.py
import time
import json
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.ner.spacy_ner import SpacyNERExtractor
from backend.ner.llm_ner import LLMNERExtractor

class PerformanceComparator:
    def __init__(self):
        self.spacy = SpacyNERExtractor()
        self.llm = LLMNERExtractor(None)
    
    def test_dataset(self, dataset: List[str]) -> Dict:
        results = {"spacy": [], "llm": []}
        
        for text in dataset:
            # spaCy
            start = time.time()
            _, nut_sp, t_sp = self.spacy.process(text)
            results["spacy"].append({
                "text": text,
                "time": t_sp,
                "calories": nut_sp["calories"],
                "foods": len(_["foods"])
            })
            
            # LLM
            start = time.time()
            _, nut_llm, t_llm = self.llm.process(text)
            results["llm"].append({
                "text": text,
                "time": t_llm,
                "calories": nut_llm["calories"],
                "foods": len(_["foods"] if 'foods' in _ else [])
            })
        
        return self._calculate_metrics(results)
    
    def _calculate_metrics(self, results):
        spacy_times = [r["time"] for r in results["spacy"]]
        llm_times = [r["time"] for r in results["llm"]]
        
        return {
            "spacy": {
                "avg_time": sum(spacy_times) / len(spacy_times) * 1000,
                "avg_calories": sum(r["calories"] for r in results["spacy"]) / len(results["spacy"]),
                "avg_foods": sum(r["foods"] for r in results["spacy"]) / len(results["spacy"])
            },
            "llm": {
                "avg_time": sum(llm_times) / len(llm_times) * 1000,
                "avg_calories": sum(r["calories"] for r in results["llm"]) / len(results["llm"]),
                "avg_foods": sum(r["foods"] for r in results["llm"]) / len(results["llm"])
            }
        }
    
    def print_report(self, metrics):
        print("\n" + "="*50)
        print("📊 RAPPORT COMPARAISON VOICE-TO-CALORIE")
        print("="*50)
        print(f"\n🟢 spaCy:")
        print(f"   Temps moyen: {metrics['spacy']['avg_time']:.2f} ms")
        print(f"   Calories moyennes: {metrics['spacy']['avg_calories']:.0f} kcal")
        print(f"   Aliments détectés: {metrics['spacy']['avg_foods']:.1f}")
        
        print(f"\n🔵 LLM:")
        print(f"   Temps moyen: {metrics['llm']['avg_time']:.2f} ms")
        print(f"   Calories moyennes: {metrics['llm']['avg_calories']:.0f} kcal")
        print(f"   Aliments détectés: {metrics['llm']['avg_foods']:.1f}")
        
        speedup = metrics['llm']['avg_time'] / metrics['spacy']['avg_time']
        print(f"\n⚡ spaCy est {speedup:.1f}x plus rapide que LLM")

def main():
    dataset = [
        "أكلت نصف بيتزا",
        "تناولت قليلًا من الأرز",
        "أكلت 2 بيضات و3 شرائح خبز",
        "شربت كوب حليب كبير",
        "أكلت طاجين دجاج بالزيتون",
        "تناولت كسكس باللحم",
        "أكلت حريرة مع خبز",
        "شربت عصير برتقال",
        "أكلت بطاطس مقلية",
        "تناولت ساندويتش دجاج",
    ]
    
    comparator = PerformanceComparator()
    metrics = comparator.test_dataset(dataset)
    comparator.print_report(metrics)

if __name__ == "__main__":
    main()