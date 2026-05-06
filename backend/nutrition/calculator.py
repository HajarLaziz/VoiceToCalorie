# backend/nutrition/calculator.py
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class NutritionCalculator:
    def __init__(self):
        try:
            from data.nutrition_db import NUTRITION_DB, QUANTITY_FACTORS
            self.nutrition_db = NUTRITION_DB
            self.quantity_factors = QUANTITY_FACTORS
        except:
            self.nutrition_db = {}
            self.quantity_factors = {}
    
    def calculate(self, foods: List[str], quantities: List[str]) -> Dict:
        total = {"calories": 0, "proteines": 0, "glucides": 0, "lipides": 0}
        
        factor = 1.0
        if quantities:
            q = quantities[0]
            factor = self.quantity_factors.get(q, float(q) if q.isdigit() else 1.0)
        
        for food in foods:
            if food in self.nutrition_db:
                nut = self.nutrition_db[food]
                total["calories"] += nut.get("calories", 0) * factor
                total["proteines"] += nut.get("proteines", 0) * factor
                total["glucides"] += nut.get("glucides", 0) * factor
                total["lipides"] += nut.get("lipides", 0) * factor
        
        return total