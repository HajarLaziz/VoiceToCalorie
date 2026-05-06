# data/nutrition_db.py
# Base de données nutritionnelle complète

NUTRITION_DB = {
    # Légumes
    "سلطة خضراء": {"calories": 25, "proteines": 1.5, "glucides": 5, "lipides": 0.2},
    "سلطة طماطم وخيار": {"calories": 30, "proteines": 1, "glucides": 7, "lipides": 0.3},
    "بطاطس": {"calories": 77, "proteines": 2, "glucides": 17, "lipides": 0.1},
    "بطاطس مقلية": {"calories": 312, "proteines": 3.4, "glucides": 41, "lipides": 15},
    "خضار": {"calories": 40, "proteines": 2, "glucides": 8, "lipides": 0.3},
    "طماطم": {"calories": 18, "proteines": 0.9, "glucides": 3.9, "lipides": 0.2},
    "خيار": {"calories": 15, "proteines": 0.7, "glucides": 3.6, "lipides": 0.1},
    
    # Protéines
    "دجاج مشوي": {"calories": 165, "proteines": 31, "glucides": 0, "lipides": 3.6},
    "دجاج": {"calories": 165, "proteines": 31, "glucides": 0, "lipides": 3.6},
    "دجاج مقلي": {"calories": 250, "proteines": 25, "glucides": 8, "lipides": 13},
    "لحم مشوي": {"calories": 250, "proteines": 26, "glucides": 0, "lipides": 15},
    "لحم": {"calories": 250, "proteines": 26, "glucides": 0, "lipides": 15},
    "سمك مشوي": {"calories": 206, "proteines": 22, "glucides": 0, "lipides": 12},
    "تونة": {"calories": 184, "proteines": 30, "glucides": 0, "lipides": 6},
    "بيض": {"calories": 155, "proteines": 13, "glucides": 1.1, "lipides": 11},
    "بيضة مسلوقة": {"calories": 78, "proteines": 6.3, "glucides": 0.6, "lipides": 5.3},
    "بيضة مقلية": {"calories": 90, "proteines": 6.3, "glucides": 0.4, "lipides": 7},
    
    # Céréales
    "خبز": {"calories": 265, "proteines": 9, "glucides": 49, "lipides": 3.2},
    "شريحة خبز": {"calories": 80, "proteines": 2.7, "glucides": 15, "lipides": 1},
    "أرز": {"calories": 130, "proteines": 2.7, "glucides": 28, "lipides": 0.3},
    "كسكس": {"calories": 112, "proteines": 3.6, "glucides": 23, "lipides": 0.2},
    "معكرونة": {"calories": 131, "proteines": 5, "glucides": 25, "lipides": 0.5},
    "بيتزا": {"calories": 285, "proteines": 12, "glucides": 35, "lipides": 10},
    
    # Plats composés
    "كسكس بالخضر": {"calories": 180, "proteines": 6, "glucides": 30, "lipides": 4},
    "كسكس باللحم": {"calories": 350, "proteines": 18, "glucides": 35, "lipides": 15},
    "طاجين دجاج": {"calories": 280, "proteines": 25, "glucides": 10, "lipides": 15},
    "حريرة": {"calories": 150, "proteines": 8, "glucides": 20, "lipides": 5},
    "شوربة خضار": {"calories": 80, "proteines": 2, "glucides": 12, "lipides": 2.5},
    
    # Fruits
    "تفاحة": {"calories": 52, "proteines": 0.3, "glucides": 14, "lipides": 0.2},
    "موز": {"calories": 89, "proteines": 1.1, "glucides": 23, "lipides": 0.3},
    "تمر": {"calories": 282, "proteines": 2.5, "glucides": 75, "lipides": 0.4},
    "فاكهة": {"calories": 60, "proteines": 0.8, "glucides": 15, "lipides": 0.3},
    
    # Boissons
    "حليب": {"calories": 42, "proteines": 3.4, "glucides": 5, "lipides": 1},
    "عصير برتقال": {"calories": 45, "proteines": 0.7, "glucides": 10, "lipides": 0.2},
    "قهوة": {"calories": 2, "proteines": 0.3, "glucides": 0, "lipides": 0},
    "شاي": {"calories": 1, "proteines": 0, "glucides": 0, "lipides": 0},
    
    # Produits laitiers
    "جبن": {"calories": 350, "proteines": 25, "glucides": 2, "lipides": 27},
    "زبدة": {"calories": 717, "proteines": 0.9, "glucides": 0.1, "lipides": 81},
    "زبادي": {"calories": 61, "proteines": 3.5, "glucides": 4.7, "lipides": 3.3},
    "عسل": {"calories": 304, "proteines": 0.3, "glucides": 82, "lipides": 0},
    
    # Pâtisseries
    "كعكة": {"calories": 350, "proteines": 4, "glucides": 45, "lipides": 18},
    "بسكويت": {"calories": 500, "proteines": 6, "glucides": 65, "lipides": 24},
    "شباكية": {"calories": 420, "proteines": 5, "glucides": 55, "lipides": 20},
    "مسمن": {"calories": 280, "proteines": 6, "glucides": 35, "lipides": 12},
    
    # Sandwichs
    "شطيرة تونة": {"calories": 400, "proteines": 20, "glucides": 35, "lipides": 20},
    "شطيرة دجاج": {"calories": 380, "proteines": 22, "glucides": 35, "lipides": 17},
}

QUANTITY_FACTORS = {
    "نصف": 0.5,
    "ربع": 0.25,
    "ثلث": 0.33,
    "قليل": 0.3,
    "قليلاً": 0.3,
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