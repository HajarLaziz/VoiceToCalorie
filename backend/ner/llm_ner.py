# backend/ner/llm_ner.py
import json
import time
from typing import Dict, Tuple, Optional

class LLMNERExtractor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.available = api_key is not None
        self.client = None
        
        if self.available:
            try:
                import openai
                self.client = openai.OpenAI(api_key=api_key)
                print("✅ OpenAI initialisé")
            except:
                self.available = False
        else:
            print("ℹ️ Mode démo LLM")
    
    def extract_entities(self, text: str) -> Dict:
        if not self.available:
            return self._mock_extraction(text)
        
        prompt = f"""Analyse ce repas en arabe et donne les valeurs nutritionnelles au format JSON.
Repas: "{text}"

Format réponse:
{{"foods": [{{"name": "", "quantity": 1}}], "total_calories": 0, "total_proteines": 0, "total_glucides": 0, "total_lipides": 0}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except:
            return self._mock_extraction(text)
    
    def _mock_extraction(self, text: str) -> Dict:
        try:
            from data.nutrition_db import NUTRITION_DB
        except:
            NUTRITION_DB = {}
        
        foods = []
        for food in NUTRITION_DB.keys():
            if food in text:
                foods.append({"name": food, "quantity": 1})
        
        return {
            "foods": foods,
            "total_calories": sum(NUTRITION_DB.get(f["name"], {}).get("calories", 0) for f in foods),
            "total_proteines": sum(NUTRITION_DB.get(f["name"], {}).get("proteines", 0) for f in foods),
            "total_glucides": sum(NUTRITION_DB.get(f["name"], {}).get("glucides", 0) for f in foods),
            "total_lipides": sum(NUTRITION_DB.get(f["name"], {}).get("lipides", 0) for f in foods)
        }
    
    def calculate_nutrition(self, extraction: Dict) -> Dict:
        return {
            "calories": extraction.get("total_calories", 0),
            "proteines": extraction.get("total_proteines", 0),
            "glucides": extraction.get("total_glucides", 0),
            "lipides": extraction.get("total_lipides", 0)
        }
    
    def process(self, text: str) -> Tuple[Dict, Dict, float]:
        start = time.time()
        entities = self.extract_entities(text)
        nutrition = self.calculate_nutrition(entities)
        return entities, nutrition, time.time() - start