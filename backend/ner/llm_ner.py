# backend/ner/llm_ner.py
import json
import time
from typing import Dict, Tuple, Optional  # <-- CES IMPORTS SONT ESSENTIELS

class LLMNERExtractor:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'extracteur LLM.
        Supporte Groq (clé commençant par gsk_) et OpenAI (clé commençant par sk-)
        """
        self.api_key = api_key
        self.available = False
        self.client = None
        self.provider = None
        self.current_model = None
        
        print(f"[DEBUG] LLM __init__ - api_key provided: {api_key is not None}")
        
        if not api_key:
            print("[INFO] Mode demo LLM (no API key)")
            return
        
        print(f"[DEBUG] API Key starts with: {api_key[:15]}...")
        
        # Detection du type de clé
        if api_key.startswith("sk-"):
            self.provider = "openai"
            try:
                from openai import OpenAI
                
                self.client = OpenAI(
                    api_key=api_key,
                    timeout=30.0,
                    max_retries=2
                )
                self.current_model = "gpt-3.5-turbo"
                self.available = True
                print("[OK] OpenAI client initialise (mode rapide)")
                
                # Test rapide
                try:
                    test_response = self.client.chat.completions.create(
                        model=self.current_model,
                        messages=[{"role": "user", "content": "Test"}],
                        max_tokens=5
                    )
                    print("[OK] Connexion OpenAI etablie")
                except Exception as test_e:
                    print(f"[WARN] Test connexion: {test_e}")
                    
            except Exception as e:
                print(f"[ERROR] Erreur OpenAI: {e}")
                self.available = False
                
        elif api_key.startswith("gsk_"):
            self.provider = "groq"
            try:
                from openai import OpenAI
                
                self.client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=api_key,
                    timeout=30.0,
                    max_retries=2
                )
                self.current_model = "llama-3.1-8b-instant"
                self.available = True
                print("[OK] Groq client initialise")
                
            except Exception as e:
                print(f"[ERROR] Erreur Groq: {e}")
                self.available = False
        else:
            print(f"[ERROR] Format de cle API non reconnu: {api_key[:15]}...")
            print("   Les cles OpenAI commencent par 'sk-'")
            print("   Les cles Groq commencent par 'gsk_'")
            self.available = False
        
        if not self.available:
            print("[INFO] LLM fonctionnera en mode mock")
    
    def extract_entities(self, text: str) -> Dict:
        """
        Extrait les entites nutritionnelles du texte.
        """
        if not self.available or not self.client:
            print("[DEBUG] Using mock extraction (not available)")
            return self._mock_extraction(text)
        
        # Prompt pour retourner une liste de strings
        prompt = f"""Analyse ce repas en arabe et donne les aliments.

Repas: "{text}"

REPOND UNIQUEMENT PAR CE JSON (sans aucun autre texte):
{{"foods": ["aliment1", "aliment2"], "total_calories": 0}}

Exemple pour "اكلت دجاج وتفاح":
{{"foods": ["دجاج", "تفاح"], "total_calories": 217}}"""
        
        try:
            print(f"[DEBUG] Calling {self.provider} API with model: {self.current_model}")
            
            response = self.client.chat.completions.create(
                model=self.current_model,
                messages=[
                    {"role": "system", "content": "You are a nutrition expert. Respond ONLY with valid JSON. foods must be a list of strings like ['food1', 'food2']."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content
            print(f"[DEBUG] Response received")
            
            # Nettoyer la réponse
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result = json.loads(result_text)
            
            # Normalisation: s'assurer que foods est une liste de strings
            if 'foods' in result:
                if isinstance(result['foods'], list):
                    normalized_foods = []
                    for item in result['foods']:
                        if isinstance(item, dict):
                            # Si c'est un dict, prendre la valeur 'name'
                            normalized_foods.append(item.get('name', str(item)))
                        else:
                            normalized_foods.append(str(item))
                    result['foods'] = normalized_foods
                elif isinstance(result['foods'], str):
                    result['foods'] = [result['foods']]
                else:
                    result['foods'] = []
            else:
                result['foods'] = []
            
            # S'assurer que total_calories existe
            if 'total_calories' not in result:
                result['total_calories'] = 0
            
            print(f"[DEBUG] Foods found: {result['foods']}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] {self.provider} API Error: {type(e).__name__}: {e}")
            return self._mock_extraction(text)
    
    def _mock_extraction(self, text: str) -> Dict:
        """
        Extraction de secours (mock) quand l'API n'est pas disponible.
        """
        print(f"[DEBUG] Mock extraction for: {text[:30]}...")
        
        try:
            from data.nutrition_db import NUTRITION_DB
        except ImportError:
            NUTRITION_DB = {}
        
        # Retourner une LISTE DE STRINGS
        foods = []
        for food in NUTRITION_DB.keys():
            if food in text:
                foods.append(food)
        
        # Detection simple des quantites
        factor = 1.0
        if "نصف" in text:
            factor = 0.5
        elif "ربع" in text:
            factor = 0.25
        elif "ثلث" in text:
            factor = 0.33
        elif "قليل" in text or "قليلا" in text:
            factor = 0.3
        
        calories = sum(NUTRITION_DB.get(f, {}).get("calories", 0) for f in foods) * factor
        
        print(f"[DEBUG] Mock found {len(foods)} foods, {calories} calories")
        
        return {
            "foods": foods,  # Liste de strings
            "total_calories": calories,
            "total_proteines": 0,
            "total_glucides": 0,
            "total_lipides": 0
        }
    
    def calculate_nutrition(self, extraction: Dict) -> Dict:
        """
        Extrait les valeurs nutritionnelles du resultat.
        """
        return {
            "calories": extraction.get("total_calories", 0),
            "proteines": extraction.get("total_proteines", 0),
            "glucides": extraction.get("total_glucides", 0),
            "lipides": extraction.get("total_lipides", 0)
        }
    
    def process(self, text: str) -> Tuple[Dict, Dict, float]:
        """
        Processus complet: extraction + calcul.
        """
        start = time.time()
        entities = self.extract_entities(text)
        nutrition = self.calculate_nutrition(entities)
        elapsed = time.time() - start
        print(f"[DEBUG] process completed in {elapsed:.2f}s")
        return entities, nutrition, elapsed