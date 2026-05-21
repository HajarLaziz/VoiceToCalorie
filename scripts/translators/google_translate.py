# scripts/translators/google_translate.py
import time
import json
import os
import hashlib

class FoodTranslator:
    """
    Traducteur automatique anglais -> arabe pour les aliments.
    Utilise un dictionnaire local + fallback vers googletrans si disponible.
    """
    
    def __init__(self, use_online=False):
        self.use_online = use_online
        self.cache_file = "data/translations_cache.json"
        self.cache = self.load_cache()
        self.translator = None
        
        if use_online:
            try:
                from googletrans import Translator
                self.translator = Translator()
                print("Mode online active (googletrans)")
            except ImportError:
                print("googletrans non installe. Installation: pip install googletrans==4.0.0-rc1")
                print("Utilisation du mode hors ligne")
                self.use_online = False
    
    def load_cache(self):
        """Charger le cache des traductions."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        """Sauvegarder le cache."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def translate_food_name(self, text):
        """
        Traduire un nom d'aliment de l'anglais vers l'arabe.
        """
        # Nettoyer le texte
        text = text.strip()
        if not text:
            return text
        
        # Verifier le cache
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Traductions specifiques pour les aliments courants
        specific_translations = {
            # Lait et produits laitiers
            "Cows' milk": "حليب البقر",
            "Milk skim": "حليب خالي الدسم",
            "Buttermilk": "لبن خاثر",
            "Evaporated, undiluted": "حليب مبخر غير مخفف",
            "Fortified milk": "حليب مدعم",
            "Powdered milk": "حليب بودرة",
            "Goats' milk": "حليب الماعز",
            "Ice cream": "آيس كريم",
            "Cream": "كريمة",
            "Cheese": "جبن",
            "Cheddar": "جبن شيدر",
            "Cream cheese": "جبن كريمي",
            "Swiss cheese": "جبن سويسري",
            
            # Oeufs
            "Eggs raw": "بيض نيء",
            "Eggs Scrambled": "بيض مخفوق",
            "Eggs fried": "بيض مقلي",
            "Yolks": "صفار بيض",
            
            # Matieres grasses
            "Butter": "زبدة",
            "Margarine": "مارغرين",
            "Mayonnaise": "مايونيز",
            "Olive oil": "زيت زيتون",
            "Corn oil": "زيت ذرة",
            
            # Viandes
            "Bacon": "بيكون",
            "Beef": "لحم بقر",
            "Hamburger": "هامبرغر",
            "Ground lean": "لحم مفروم قليل الدهن",
            "Roast beef": "لحم مشوي",
            "Steak": "ستيك",
            "Corned beef": "لحم محفوظ",
            "Chicken": "دجاج",
            "Fried chicken": "دجاج مقلي",
            "Roasted chicken": "دجاج مشوي",
            "Turkey": "ديك رومي",
            "Lamb": "لحم خروف",
            "Pork": "لحم خنزير",
            "Ham": "هام",
            "Sausage": "سجق",
            "Veal": "لحم عجل",
            
            # Poissons
            "Fish": "سمك",
            "Salmon": "سلمون",
            "Tuna": "تونة",
            "Shrimp": "جمبري",
            "Cod": "قد",
            "Crab": "سلطعون",
            "Lobster": "استاكوزا",
            "Oysters": "محار",
            "Sardines": "سردين",
            
            # Legumes
            "Potato": "بطاطس",
            "French-fried": "بطاطس مقلية",
            "Mashed potatoes": "بطاطس مهروسة",
            "Carrots": "جزر",
            "Tomatoes": "طماطم",
            "Lettuce": "خس",
            "Onions": "بصل",
            "Broccoli": "بروكلي",
            "Spinach": "سبانخ",
            "Corn": "ذرة",
            "Peas": "بازلاء",
            "Beans": "فاصوليا",
            
            # Fruits
            "Apple": "تفاح",
            "Banana": "موز",
            "Orange": "برتقال",
            "Strawberry": "فراولة",
            "Grapes": "عنب",
            "Watermelon": "بطيخ",
            "Cantaloupe": "شمام",
            
            # Boissons
            "Coffee": "قهوة",
            "Tea": "شاي",
            "Milk": "حليب",
            "Juice": "عصير",
            "Soda": "مشروب غازي",
            "Cola": "كولا",
            "Water": "ماء",
            
            # Fast food
            "McMuffin": "ماك مافن",
            "McGriddles": "ماك جريدلز",
            "Biscuit": "بسكويت",
            "Burger": "برغر",
            "Big Mac": "بيغ ماك",
            "Quarter Pounder": "ربع رطل",
            "Cheeseburger": "تشيز برغر",
            "Chicken McNuggets": "ناجتس الدجاج",
            "French Fries": "بطاطس مقلية",
            "Filet-O-Fish": "فيليه سمك",
            "Salad": "سلطة",
            "Wrap": "لفة",
            "Shake": "ميلك شيك",
            "Smoothie": "سموثي",
            "Latte": "لاتيه",
            "Mocha": "موكا",
            "Cappuccino": "كابتشينو",
            "Frappe": "فرابيه",
            
            # Categories
            "Breakfast": "فطور",
            "Beef & Pork": "لحم بقر وخنزير",
            "Chicken & Fish": "دجاج وسمك",
            "Salads": "سلطات",
            "Desserts": "حلويات",
            "Beverages": "مشروبات",
            "Coffee & Tea": "قهوة وشاي",
            "Smoothies & Shakes": "سموثي وميلك شيك",
            "Snacks & Sides": "وجبات خفيفة وجوانب",
            "Dairy products": "منتجات ألبان",
            "Fats, Oils, Shortenings": "دهون وزيت",
            "Meat, Poultry": "لحم ودواجن",
            "Fish, Seafood": "سمك ومأكولات بحرية",
            "Vegetables": "خضروات",
            "Fruits": "فواكه",
            "Breads, cereals, fastfood, grains": "خبز وحبوب",
            "Soups": "شوربات",
            "Desserts, sweets": "حلويات",
            "Jams, Jellies": "مربى",
            "Seeds and Nuts": "بذور ومكسرات",
            "Drinks,Alcohol, Beverages": "مشروبات وكحول",
        }
        
        # Chercher dans les traductions specifiques
        for eng, arb in specific_translations.items():
            if eng.lower() in text.lower():
                result = arb
                break
            elif text.lower() in eng.lower():
                result = arb
                break
        else:
            result = text  # Garder l'anglais si non trouve
        
        # Si mode online active, ameliorer la traduction
        if self.use_online and self.translator and result == text:
            try:
                translation = self.translator.translate(text, src='en', dest='ar')
                if translation and translation.text:
                    result = translation.text
                    time.sleep(0.3)  # Rate limiting
            except Exception as e:
                print(f"Erreur traduction online pour '{text}': {e}")
        
        # Mettre en cache
        self.cache[cache_key] = result
        self.save_cache()
        
        return result
    
    def translate_batch(self, texts):
        """
        Traduire une liste de textes.
        """
        results = {}
        total = len(texts)
        
        for i, text in enumerate(texts, 1):
            print(f"Traduction {i}/{total}: {text[:50]}...")
            results[text] = self.translate_food_name(text)
        
        return results