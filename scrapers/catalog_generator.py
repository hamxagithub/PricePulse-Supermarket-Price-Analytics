"""
Comprehensive Pakistani retail product catalog generator.
Shared by Metro and Naheed scrapers to generate realistic large-scale
product datasets that mirror real Pakistani supermarket inventories.

Approach:
- Extensive brand lists per category (real Pakistani + international brands)
- Extensive product item lists per category
- Systematic size-ladder variant expansion
- City-based price variation
- Deterministic seeding for reproducibility
"""
import re
import random
import hashlib
from datetime import datetime

import numpy as np


# ═══════════════════════════════════════════════════════════════
# SIZE LADDERS — realistic size variants per unit type
# ═══════════════════════════════════════════════════════════════
SIZE_LADDERS = {
    "ML": [50, 100, 120, 150, 200, 250, 300, 350, 400, 500, 750, 1000, 1500, 2000, 2500, 4000],
    "L": [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 10],
    "G": [25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000, 1500, 2000, 5000],
    "KG": [0.25, 0.5, 1, 1.5, 2, 2.5, 3, 5, 10, 25],
    "PCS": [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 20, 24, 30, 36, 48, 60, 72, 96],
}

# Which size ladder each base unit maps to
UNIT_LADDER_MAP = {
    "ML": "ML", "L": "L", "G": "G", "KG": "KG", "PCS": "PCS",
    "LTR": "L", "GM": "G",
}


# ═══════════════════════════════════════════════════════════════
# COMPREHENSIVE PRODUCT CATALOG — Pakistani Retail
# ═══════════════════════════════════════════════════════════════
CATALOG = {
    "Dairy & Milk": {
        "brands": [
            "Olpers", "MilkPak", "Nurpur", "Haleeb", "Dairy Omung",
            "Adams", "Good Milk", "Day Fresh", "Prema", "Gourmet",
            "Pakola", "Nestle", "Fauji", "Millac", "Anmol",
        ],
        "items": [
            ("Full Cream UHT Milk", 60, 280, "L", 6),
            ("Low Fat Milk", 65, 290, "L", 6),
            ("Flavored Milk Chocolate", 30, 100, "ML", 6),
            ("Flavored Milk Strawberry", 30, 100, "ML", 6),
            ("Flavored Milk Mango", 30, 100, "ML", 6),
            ("Flavored Milk Coffee", 30, 100, "ML", 6),
            ("Fresh Yogurt Natural", 30, 160, "KG", 5),
            ("Raita", 30, 100, "ML", 5),
            ("Lassi Sweet", 25, 80, "ML", 5),
            ("Lassi Mango", 25, 80, "ML", 5),
            ("Butter Salted", 120, 500, "G", 5),
            ("Butter Unsalted", 130, 520, "G", 5),
            ("Cheese Slices Processed", 100, 420, "G", 5),
            ("Mozzarella Cheese Shredded", 150, 600, "G", 5),
            ("Cheddar Cheese Block", 200, 700, "G", 5),
            ("Cream Cheese Spread", 150, 500, "G", 5),
            ("Fresh Cream", 50, 200, "ML", 5),
            ("Whipping Cream UHT", 100, 350, "ML", 5),
            ("Condensed Milk", 80, 350, "G", 5),
            ("Evaporated Milk", 60, 200, "ML", 5),
            ("Desi Ghee Pure", 200, 800, "KG", 5),
            ("Banaspati Ghee", 150, 600, "KG", 5),
            ("Khoya", 200, 600, "G", 4),
            ("Paneer", 180, 500, "G", 4),
            ("Eggs Farm", 220, 450, "PCS", 4),
        ],
    },

    "Cooking Oil & Ghee": {
        "brands": [
            "Sufi", "Dalda", "Habib", "Eva", "Mezan", "Seasons",
            "Turkey", "Fryola", "Soya Supreme", "Canolive",
            "Olitalia", "Borges", "Golden Sun", "Pakwan", "Latif",
        ],
        "items": [
            ("Cooking Oil Canola", 150, 700, "L", 7),
            ("Sunflower Oil", 160, 720, "L", 7),
            ("Corn Oil", 170, 740, "L", 7),
            ("Olive Oil Extra Virgin", 500, 2500, "ML", 6),
            ("Olive Oil Pomace", 300, 1500, "ML", 6),
            ("Vegetable Oil", 130, 600, "L", 7),
            ("Coconut Oil", 200, 800, "ML", 5),
            ("Mustard Oil", 180, 700, "ML", 5),
            ("Soybean Oil", 140, 650, "L", 6),
            ("Rice Bran Oil", 200, 800, "ML", 5),
            ("Palm Oil", 120, 550, "L", 6),
            ("Banaspati Ghee Cooking", 130, 550, "KG", 6),
            ("Cooking Spray", 250, 500, "ML", 3),
            ("Margarine", 120, 400, "G", 5),
            ("Shortening", 150, 500, "G", 5),
        ],
    },

    "Rice Flour & Grains": {
        "brands": [
            "Guard", "Al-Karam", "Matco", "Falak", "Punjab King",
            "Kernel", "Sunrise", "Kashmir", "Dawat", "Ahmed",
            "National", "Kolson", "Sultan", "Rose", "Five Star",
        ],
        "items": [
            ("Basmati Rice Super Kernel", 200, 600, "KG", 7),
            ("Basmati Rice Sella", 150, 450, "KG", 7),
            ("Basmati Rice Broken", 80, 250, "KG", 6),
            ("Brown Rice", 180, 500, "KG", 5),
            ("White Rice Regular", 100, 300, "KG", 6),
            ("Wheat Flour Atta", 50, 180, "KG", 7),
            ("Wheat Flour Maida", 60, 200, "KG", 6),
            ("Semolina Suji", 80, 250, "KG", 5),
            ("Gram Flour Besan", 100, 350, "KG", 5),
            ("Corn Flour", 60, 200, "G", 5),
            ("Custard Powder", 80, 300, "G", 5),
            ("Baking Powder", 50, 200, "G", 5),
            ("Baking Soda", 30, 100, "G", 4),
            ("Oats Rolled", 150, 500, "G", 5),
            ("Cornflakes Cereal", 200, 600, "G", 5),
            ("Wheat Porridge Daliya", 60, 200, "G", 5),
            ("Vermicelli Seviyan", 30, 120, "G", 5),
            ("Sago Sabudana", 60, 200, "G", 4),
        ],
    },

    "Pulses & Lentils": {
        "brands": [
            "Guard", "National", "Ahmed", "Falak", "Matco",
            "Shan", "Mehran", "Sultan", "Sunrise", "Al-Karam",
            "Five Star", "Daali", "Zaika", "Rose", "Prince",
        ],
        "items": [
            ("Masoor Daal Red Lentils", 150, 350, "KG", 6),
            ("Chana Daal Bengal Gram", 140, 330, "KG", 6),
            ("Moong Daal Yellow", 160, 370, "KG", 6),
            ("Mash Daal Urad", 180, 400, "KG", 6),
            ("Toor Daal Arhar", 170, 380, "KG", 5),
            ("White Chickpeas Kabuli Chana", 200, 400, "KG", 6),
            ("Black Chickpeas Kala Chana", 180, 380, "KG", 5),
            ("Kidney Beans Rajma", 200, 450, "KG", 5),
            ("White Beans Lobia", 180, 400, "KG", 5),
            ("Green Gram Moong Whole", 170, 380, "KG", 5),
            ("Split Peas", 120, 300, "KG", 5),
            ("Mixed Daal", 160, 350, "KG", 5),
        ],
    },

    "Spices & Masala": {
        "brands": [
            "National", "Shan", "Mehran", "Ahmed", "Zaiqa",
            "Habib", "Saeed Ghani", "Guard", "Ali Baba", "Chef",
            "Youngs", "DelMonte", "Badshah", "MDH", "Laziza",
        ],
        "items": [
            ("Red Chili Powder", 60, 300, "G", 6),
            ("Turmeric Powder Haldi", 50, 250, "G", 6),
            ("Coriander Powder Ground", 50, 240, "G", 6),
            ("Cumin Powder Ground", 70, 350, "G", 6),
            ("Cumin Seeds Whole", 80, 360, "G", 5),
            ("Black Pepper Powder", 100, 450, "G", 6),
            ("Black Pepper Whole", 120, 500, "G", 5),
            ("Garam Masala Powder", 60, 300, "G", 6),
            ("Biryani Masala Mix", 30, 160, "G", 6),
            ("Chicken Masala Mix", 25, 140, "G", 6),
            ("Karahi Masala Mix", 25, 140, "G", 5),
            ("Nihari Masala Mix", 30, 160, "G", 5),
            ("Tikka Masala Mix", 25, 140, "G", 5),
            ("Qorma Masala Mix", 25, 140, "G", 5),
            ("Haleem Masala Mix", 30, 150, "G", 5),
            ("Chaat Masala", 30, 150, "G", 5),
            ("Cinnamon Sticks", 80, 350, "G", 4),
            ("Cloves Whole", 100, 450, "G", 4),
            ("Cardamom Green", 200, 800, "G", 4),
            ("Bay Leaves", 30, 150, "G", 4),
            ("Mustard Seeds", 40, 180, "G", 4),
            ("Fennel Seeds Saunf", 50, 220, "G", 4),
            ("Fenugreek Seeds Methi", 40, 180, "G", 4),
            ("Dried Red Chilies", 80, 300, "G", 5),
            ("White Pepper", 120, 500, "G", 4),
            ("Paprika Powder", 80, 350, "G", 5),
            ("Mixed Herbs Italian", 60, 250, "G", 4),
            ("Garlic Powder", 60, 250, "G", 5),
            ("Onion Powder", 50, 220, "G", 5),
            ("Salt Iodized Table", 15, 60, "G", 6),
            ("Salt Himalayan Pink", 30, 150, "G", 5),
        ],
    },

    "Sauces & Condiments": {
        "brands": [
            "National", "Mitchells", "Shangrila", "Knorr", "Shan",
            "Ahmed", "Young's", "Heinz", "OXO", "Maggi",
            "Kikkoman", "Nando's", "Kissan", "Dipitt", "Lays",
        ],
        "items": [
            ("Tomato Ketchup", 60, 320, "G", 7),
            ("Chili Garlic Sauce", 50, 280, "ML", 6),
            ("Hot Sauce", 50, 250, "ML", 5),
            ("Soya Sauce", 40, 220, "ML", 6),
            ("Vinegar White", 25, 120, "ML", 6),
            ("Apple Cider Vinegar", 200, 600, "ML", 5),
            ("Mayonnaise Original", 80, 400, "G", 6),
            ("Mayonnaise Garlic", 80, 400, "G", 5),
            ("Mustard Sauce", 60, 250, "G", 5),
            ("BBQ Sauce", 70, 300, "ML", 5),
            ("Worcestershire Sauce", 100, 350, "ML", 4),
            ("Oyster Sauce", 100, 350, "ML", 4),
            ("Mixed Fruit Jam", 80, 380, "G", 6),
            ("Strawberry Jam", 80, 380, "G", 5),
            ("Marmalade Orange", 90, 350, "G", 5),
            ("Pure Honey Natural", 200, 800, "G", 6),
            ("Peanut Butter Creamy", 200, 650, "G", 5),
            ("Peanut Butter Crunchy", 200, 650, "G", 4),
            ("Chocolate Spread Hazelnut", 300, 800, "G", 5),
            ("Mixed Pickle Achar", 60, 280, "G", 6),
            ("Mango Pickle", 60, 280, "G", 5),
            ("Lemon Pickle", 50, 250, "G", 5),
            ("Tamarind Paste Imli", 40, 200, "G", 5),
        ],
    },

    "Tea & Coffee": {
        "brands": [
            "Tapal", "Lipton", "Vital", "Supreme", "Tetley",
            "Nescafe", "Nestle", "Twinings", "Ahmad Tea", "Dilmah",
            "Davidoff", "Lavazza", "Maxwell House", "BRU", "Robert Timms",
        ],
        "items": [
            ("Black Tea Loose Leaf", 150, 600, "G", 7),
            ("Green Tea Bags", 80, 400, "PCS", 6),
            ("Tea Bags Regular", 80, 350, "PCS", 6),
            ("Earl Grey Tea Bags", 150, 500, "PCS", 5),
            ("Jasmine Green Tea", 100, 400, "PCS", 5),
            ("Chamomile Tea Bags", 120, 450, "PCS", 4),
            ("Instant Coffee Classic", 200, 700, "G", 6),
            ("Instant Coffee Gold", 300, 900, "G", 5),
            ("Instant Coffee 3in1", 80, 350, "PCS", 6),
            ("Ground Coffee", 250, 800, "G", 5),
            ("Coffee Beans Roasted", 400, 1200, "G", 4),
            ("White Coffee Mix", 100, 400, "PCS", 5),
            ("Kashmiri Chai Pink Tea", 100, 350, "G", 5),
            ("Doodh Patti Mix", 80, 300, "G", 5),
        ],
    },

    "Beverages & Drinks": {
        "brands": [
            "Coca-Cola", "Pepsi", "7Up", "Fanta", "Sprite",
            "Nestle", "Shezan", "Qarshi", "Tang", "Pakola",
            "Mountain Dew", "Mirinda", "Maza", "Tropicana", "Real",
        ],
        "items": [
            ("Cola Regular", 40, 200, "ML", 7),
            ("Cola Zero Sugar", 40, 200, "ML", 5),
            ("Lemon Lime Soda", 35, 190, "ML", 6),
            ("Orange Soda", 35, 190, "ML", 5),
            ("Sparkling Water", 30, 150, "ML", 5),
            ("Mineral Water Still", 15, 80, "ML", 7),
            ("Orange Juice Fresh", 40, 200, "ML", 6),
            ("Mango Juice Tetra", 35, 180, "ML", 6),
            ("Apple Juice Tetra", 45, 200, "ML", 6),
            ("Mixed Fruit Juice", 40, 190, "ML", 5),
            ("Guava Juice", 35, 170, "ML", 5),
            ("Pomegranate Juice", 50, 250, "ML", 4),
            ("Orange Drink Powder", 80, 380, "G", 6),
            ("Lemon Drink Powder", 70, 350, "G", 5),
            ("Energy Drink Can", 80, 280, "ML", 4),
            ("Rooh Afza Syrup", 80, 360, "ML", 5),
            ("Jam-e-Shirin Syrup", 80, 350, "ML", 5),
            ("Squash Lemon", 70, 300, "ML", 5),
            ("Iced Tea Lemon", 40, 160, "ML", 5),
            ("Coconut Water", 60, 200, "ML", 4),
            ("Lassi Traditional", 25, 80, "ML", 4),
        ],
    },

    "Snacks & Confectionery": {
        "brands": [
            "Lays", "Kurkure", "Doritos", "Cheetos", "Pringles",
            "Kolson", "Bisconni", "LU", "Peek Freans", "EBM",
            "Cadbury", "Nestle", "Mars", "Snickers", "Kit Kat",
        ],
        "items": [
            ("Potato Chips Salted", 20, 200, "G", 6),
            ("Potato Chips Masala", 20, 200, "G", 6),
            ("Potato Chips BBQ", 20, 200, "G", 5),
            ("Potato Chips Sour Cream", 20, 200, "G", 5),
            ("Tortilla Chips Nacho", 30, 250, "G", 5),
            ("Corn Puffs Cheese", 15, 150, "G", 5),
            ("Ring Chips", 15, 130, "G", 5),
            ("Namkeen Mix Nimko", 40, 200, "G", 6),
            ("Popcorn Butter", 25, 120, "G", 5),
            ("Pretzels Salted", 40, 200, "G", 4),
            ("Peanuts Salted Roasted", 30, 180, "G", 5),
            ("Cashew Nuts", 200, 700, "G", 5),
            ("Mixed Dry Fruits", 200, 800, "G", 5),
            ("Almonds", 250, 800, "G", 5),
            ("Biscuits Plain Cookies", 25, 130, "G", 6),
            ("Biscuits Chocolate Chip", 35, 170, "G", 6),
            ("Cream Biscuits Lemon", 30, 150, "G", 5),
            ("Cream Biscuits Chocolate", 35, 160, "G", 5),
            ("Wafer Chocolate", 20, 100, "G", 5),
            ("Wafer Vanilla", 20, 100, "G", 4),
            ("Cake Rusk", 60, 280, "G", 5),
            ("Chocolate Bar Dairy Milk", 40, 250, "G", 6),
            ("Chocolate Bar Dark", 60, 300, "G", 5),
            ("Toffees Assorted Pack", 50, 250, "G", 5),
            ("Gummy Bears", 40, 200, "G", 4),
            ("Bubble Gum", 10, 50, "PCS", 4),
        ],
    },

    "Noodles & Pasta": {
        "brands": [
            "Knorr", "Maggi", "Indomie", "Kolson", "Bake Parlor",
            "Barilla", "Del Monte", "National", "Shan", "Sabroso",
            "Wai Wai", "Samyang", "Cup Noodles", "Sunbulah", "Koka",
        ],
        "items": [
            ("Instant Noodles Chicken", 15, 80, "G", 6),
            ("Instant Noodles Masala", 15, 80, "G", 6),
            ("Instant Noodles Shrimp", 15, 80, "G", 5),
            ("Cup Noodles Chicken", 40, 100, "G", 4),
            ("Spaghetti Pasta", 30, 150, "G", 6),
            ("Penne Pasta", 30, 150, "G", 6),
            ("Macaroni Pasta", 25, 140, "G", 6),
            ("Fusilli Pasta", 30, 150, "G", 5),
            ("Lasagna Sheets", 80, 300, "G", 4),
            ("Egg Noodles", 30, 120, "G", 5),
            ("Rice Noodles", 30, 120, "G", 4),
            ("Pasta Sauce Marinara", 80, 300, "G", 5),
            ("Pasta Sauce Tomato Basil", 80, 300, "G", 5),
            ("Noodle Seasoning", 10, 40, "G", 5),
        ],
    },

    "Canned & Preserved Food": {
        "brands": [
            "Del Monte", "Mitchells", "National", "Frutella", "Shezan",
            "California Garden", "Al Alali", "Heinz", "Happy Home", "Chef's Pride",
            "Shangrila", "Freshly", "American Garden", "Libby's", "Golden Circle",
        ],
        "items": [
            ("Baked Beans", 60, 250, "G", 6),
            ("Chickpeas Canned", 50, 200, "G", 6),
            ("Tomato Paste", 30, 150, "G", 6),
            ("Tomatoes Diced Canned", 40, 180, "G", 5),
            ("Tuna Chunks", 100, 400, "G", 5),
            ("Sardines Canned", 60, 250, "G", 5),
            ("Sweet Corn Canned", 60, 250, "G", 5),
            ("Green Peas Canned", 50, 200, "G", 5),
            ("Mixed Vegetables Canned", 60, 250, "G", 5),
            ("Mushrooms Canned", 80, 300, "G", 4),
            ("Fruit Cocktail Canned", 100, 350, "G", 5),
            ("Peaches Canned", 100, 350, "G", 4),
            ("Pineapple Slices Canned", 100, 350, "G", 4),
            ("Coconut Milk Canned", 80, 280, "ML", 5),
            ("Coconut Cream Canned", 90, 300, "ML", 4),
        ],
    },

    "Frozen Food": {
        "brands": [
            "K&Ns", "Sabroso", "Menu", "Sufi", "Dawn",
            "MonSalwa", "Knorr", "Al Shaheer", "Tasty Food", "Kolson",
            "PK Meat", "Sunbulah", "Farmland", "Super Crisp", "Godrej",
        ],
        "items": [
            ("Chicken Nuggets", 200, 700, "G", 6),
            ("Chicken Strips Spicy", 220, 720, "G", 5),
            ("Chicken Samosa", 180, 600, "G", 5),
            ("Chicken Spring Rolls", 180, 600, "G", 5),
            ("Chicken Seekh Kabab", 250, 850, "G", 5),
            ("Chapli Kabab Beef", 280, 900, "G", 5),
            ("Shami Kabab Ready", 180, 600, "G", 5),
            ("Kofta Meatballs", 200, 650, "G", 5),
            ("Beef Burger Patties", 200, 700, "G", 5),
            ("Chicken Burger Patties", 180, 650, "G", 5),
            ("Fish Fingers Crispy", 180, 600, "G", 5),
            ("Frozen Paratha Plain", 60, 280, "PCS", 5),
            ("Frozen Paratha Lachha", 80, 300, "PCS", 4),
            ("Frozen Pizza Base", 80, 250, "PCS", 4),
            ("French Fries Crinkle", 120, 450, "G", 6),
            ("French Fries Straight", 120, 450, "G", 5),
            ("Fries Wedges", 130, 470, "G", 4),
            ("Frozen Mixed Vegetables", 100, 380, "G", 5),
            ("Frozen Peas Green", 80, 300, "G", 5),
            ("Frozen Corn Kernels", 90, 320, "G", 4),
            ("Ice Cream Vanilla", 120, 500, "ML", 6),
            ("Ice Cream Chocolate", 130, 520, "ML", 6),
            ("Ice Cream Strawberry", 130, 520, "ML", 5),
            ("Ice Cream Mango", 130, 520, "ML", 5),
            ("Ice Cream Kulfi", 100, 400, "ML", 4),
        ],
    },

    "Personal Care": {
        "brands": [
            "Dove", "Lux", "Lifebuoy", "Safeguard", "Dettol",
            "Sunsilk", "Pantene", "Head & Shoulders", "Clear", "Garnier",
            "Nivea", "Vaseline", "Fair & Lovely", "Ponds", "L'Oreal",
        ],
        "items": [
            ("Shampoo Anti Dandruff", 100, 580, "ML", 7),
            ("Shampoo Smooth Silky", 100, 570, "ML", 7),
            ("Shampoo Volume", 100, 570, "ML", 6),
            ("Shampoo Color Protect", 120, 600, "ML", 5),
            ("Conditioner Hair", 120, 630, "ML", 6),
            ("Hair Serum", 150, 500, "ML", 4),
            ("Hair Oil Coconut Pure", 60, 370, "ML", 6),
            ("Hair Oil Almond", 80, 400, "ML", 5),
            ("Body Wash Moisturizing", 100, 540, "ML", 6),
            ("Body Wash Antibacterial", 100, 540, "ML", 5),
            ("Soap Bar Beauty Cream", 30, 150, "G", 6),
            ("Soap Bar Antibacterial", 30, 150, "G", 6),
            ("Soap Bar Herbal", 30, 150, "G", 5),
            ("Hand Wash Liquid", 60, 320, "ML", 6),
            ("Hand Sanitizer Gel", 60, 300, "ML", 5),
            ("Face Wash Purifying", 100, 450, "ML", 5),
            ("Face Wash Brightening", 110, 460, "ML", 5),
            ("Face Cream Moisturizer", 100, 500, "G", 5),
            ("Body Lotion Moisturizing", 100, 540, "ML", 6),
            ("Petroleum Jelly", 50, 280, "ML", 5),
            ("Lip Balm", 80, 200, "G", 3),
            ("Sunscreen SPF50", 200, 700, "ML", 4),
        ],
    },

    "Oral Care": {
        "brands": [
            "Colgate", "Sensodyne", "Pepsodent", "Close Up", "Oral-B",
            "Aquafresh", "Crest", "Dentonic", "Medicam", "English",
            "Shield", "Forhan's", "Dabur", "Miswak", "Pearl Drops",
        ],
        "items": [
            ("Toothpaste Whitening", 50, 280, "G", 6),
            ("Toothpaste Sensitive", 100, 450, "G", 6),
            ("Toothpaste Cavity Protection", 40, 260, "G", 6),
            ("Toothpaste Herbal", 50, 270, "G", 5),
            ("Toothpaste Kids", 60, 200, "G", 5),
            ("Mouthwash Fresh Mint", 100, 450, "ML", 5),
            ("Mouthwash Antiseptic", 120, 500, "ML", 5),
            ("Toothbrush Soft", 50, 200, "PCS", 4),
            ("Toothbrush Medium", 50, 200, "PCS", 4),
            ("Dental Floss", 100, 300, "PCS", 3),
        ],
    },

    "Deodorants & Fragrances": {
        "brands": [
            "Axe", "Rexona", "Old Spice", "Nivea", "Dove",
            "Brut", "Fogg", "Wild Stone", "Engage", "Layer'r",
            "Body Spray", "Bold", "Denver", "Park Avenue", "Set Wet",
        ],
        "items": [
            ("Body Spray Men Original", 100, 550, "ML", 5),
            ("Body Spray Women Floral", 100, 550, "ML", 5),
            ("Deodorant Roll On Men", 100, 400, "ML", 5),
            ("Deodorant Roll On Women", 100, 400, "ML", 5),
            ("Deodorant Stick Men", 150, 450, "G", 4),
            ("Antiperspirant Spray", 120, 500, "ML", 5),
            ("Perfume Men EDT", 500, 2000, "ML", 4),
            ("Perfume Women EDP", 600, 2500, "ML", 4),
            ("After Shave Lotion", 150, 450, "ML", 4),
            ("Shaving Cream", 80, 350, "G", 5),
            ("Shaving Gel", 100, 400, "ML", 4),
            ("Razor Disposable", 40, 200, "PCS", 5),
        ],
    },

    "Household & Cleaning": {
        "brands": [
            "Surf Excel", "Ariel", "Bonus", "Brite", "Express Power",
            "Harpic", "Dettol", "Mr Muscle", "Vim", "Domex",
            "Finis", "Max Clean", "Robin", "Comfort", "Downy",
        ],
        "items": [
            ("Washing Powder", 100, 700, "G", 7),
            ("Liquid Detergent Bottle", 100, 580, "ML", 6),
            ("Fabric Softener", 100, 450, "ML", 6),
            ("Stain Remover", 100, 350, "ML", 5),
            ("Bleach Liquid", 40, 200, "ML", 6),
            ("Dishwash Bar Lemon", 20, 100, "G", 6),
            ("Dishwash Liquid Lemon", 60, 370, "ML", 6),
            ("Floor Cleaner Floral", 50, 280, "ML", 6),
            ("Floor Cleaner Pine", 50, 280, "ML", 5),
            ("Toilet Cleaner Original", 40, 220, "ML", 6),
            ("Glass Cleaner Spray", 60, 280, "ML", 5),
            ("Kitchen Cleaner Degreaser", 60, 300, "ML", 5),
            ("Bathroom Cleaner", 50, 250, "ML", 5),
            ("Antiseptic Liquid", 80, 450, "ML", 5),
            ("Air Freshener Spray", 80, 380, "ML", 5),
            ("Air Freshener Gel", 60, 200, "G", 4),
            ("Insect Killer Spray", 150, 600, "ML", 5),
            ("Mosquito Repellent", 100, 400, "ML", 4),
            ("Moth Balls", 30, 100, "G", 4),
        ],
    },

    "Tissue & Paper Products": {
        "brands": [
            "Rose Petal", "Jac", "Fine", "Bounty", "Plenty",
            "Kleenex", "Scott", "Nicky", "Nice", "Selpak",
            "Super Soft", "Fluffy", "HomeLife", "Office Fresh", "SilkSoft",
        ],
        "items": [
            ("Tissue Box Facial", 30, 180, "PCS", 6),
            ("Tissue Roll Kitchen", 20, 80, "PCS", 6),
            ("Tissue Roll Toilet", 15, 60, "PCS", 6),
            ("Wet Wipes Fresh", 40, 200, "PCS", 5),
            ("Napkins Paper", 20, 100, "PCS", 5),
            ("Garbage Bags Black", 30, 150, "PCS", 5),
            ("Garbage Bags Large", 40, 180, "PCS", 5),
            ("Aluminum Foil Roll", 100, 400, "PCS", 4),
            ("Cling Film Wrap", 80, 300, "PCS", 4),
            ("Baking Paper", 80, 300, "PCS", 3),
            ("Ziplock Bags", 50, 200, "PCS", 5),
        ],
    },

    "Baby Care": {
        "brands": [
            "Pampers", "Huggies", "Molfix", "MamyPoko", "Canbebe",
            "Johnson", "Cerelac", "Nestle", "Aptamil", "SMA",
            "NAN", "Similac", "Abbott", "Himalaya Baby", "Pigeon",
        ],
        "items": [
            ("Baby Diapers Newborn", 300, 1000, "PCS", 6),
            ("Baby Diapers Small", 350, 1200, "PCS", 6),
            ("Baby Diapers Medium", 400, 1300, "PCS", 6),
            ("Baby Diapers Large", 450, 1400, "PCS", 6),
            ("Baby Diapers XL", 500, 1600, "PCS", 5),
            ("Baby Pants Medium", 450, 1400, "PCS", 5),
            ("Baby Pants Large", 500, 1500, "PCS", 5),
            ("Baby Wipes Sensitive", 60, 370, "PCS", 6),
            ("Baby Wipes Regular", 50, 280, "PCS", 5),
            ("Baby Shampoo No Tears", 100, 580, "ML", 6),
            ("Baby Lotion Gentle", 100, 500, "ML", 5),
            ("Baby Powder Soothing", 50, 370, "G", 5),
            ("Baby Oil Pure", 80, 440, "ML", 5),
            ("Baby Soap Mild", 30, 190, "G", 5),
            ("Baby Cereal Rice", 150, 680, "G", 5),
            ("Baby Cereal Wheat", 150, 680, "G", 5),
            ("Baby Formula Stage 1", 700, 2500, "G", 4),
            ("Baby Formula Stage 2", 750, 2600, "G", 4),
            ("Diaper Rash Cream", 100, 450, "G", 4),
            ("Baby Bottle Feeding", 200, 600, "PCS", 3),
            ("Baby Pacifier", 100, 400, "PCS", 2),
        ],
    },

    "Health & Wellness": {
        "brands": [
            "Panadol", "Disprin", "Brufen", "Centrum", "Ensure",
            "Calpol", "Tiger Balm", "Vicks", "Strepsils", "ENO",
            "Glucon-D", "Complan", "Horlicks", "Pediasure", "Revital",
        ],
        "items": [
            ("Multivitamin Tablets", 300, 1200, "PCS", 5),
            ("Vitamin C Tablets", 150, 600, "PCS", 5),
            ("Calcium Tablets", 200, 800, "PCS", 5),
            ("Iron Supplement", 150, 600, "PCS", 4),
            ("Omega 3 Fish Oil", 400, 1500, "PCS", 4),
            ("Protein Powder Vanilla", 1000, 4000, "G", 5),
            ("Glucose Powder Orange", 60, 250, "G", 5),
            ("ORS Sachets", 10, 50, "PCS", 5),
            ("Antiseptic Cream", 60, 250, "G", 5),
            ("Pain Relief Balm", 50, 200, "G", 4),
            ("Bandage Adhesive", 30, 120, "PCS", 4),
            ("Cotton Buds", 20, 80, "PCS", 5),
            ("Cotton Pads", 30, 120, "PCS", 4),
            ("Hand Gloves Disposable", 50, 200, "PCS", 5),
            ("Face Mask Disposable", 30, 150, "PCS", 5),
        ],
    },

    "Fresh Meat & Poultry": {
        "brands": [
            "Farm Fresh", "Meat One", "K&Ns", "Al Shaheer", "PK Meat",
            "Zenith", "Quality Meats", "Natural Farms", "Organic", "Premium",
            "Local Farm", "Country", "Highland", "Valley Fresh", "Green Pastures",
        ],
        "items": [
            ("Chicken Whole", 200, 600, "KG", 5),
            ("Chicken Breast Boneless", 350, 900, "KG", 5),
            ("Chicken Leg Quarter", 200, 550, "KG", 5),
            ("Chicken Wings", 180, 550, "KG", 5),
            ("Chicken Drumstick", 200, 600, "KG", 5),
            ("Chicken Mince", 280, 700, "KG", 5),
            ("Beef Mince", 400, 1200, "KG", 5),
            ("Beef Nihari Cut", 450, 1400, "KG", 5),
            ("Beef Steak Cut", 500, 1500, "KG", 4),
            ("Mutton Leg", 800, 2200, "KG", 4),
            ("Mutton Chops", 900, 2500, "KG", 4),
            ("Fish Fillet Boneless", 350, 1100, "KG", 4),
            ("Prawns Medium", 600, 1800, "KG", 4),
            ("Eggs Desi Organic", 250, 500, "PCS", 4),
        ],
    },

    "Fresh Fruits & Vegetables": {
        "brands": [
            "Local Farm", "Organic Farm", "Fresh Pick", "Green Fields", "Nature",
            "Premium Select", "Valley Fresh", "Sun Ripe", "Country", "Farm Direct",
            "Agri Fresh", "Pure", "Natural", "Garden", "Harvest",
        ],
        "items": [
            ("Tomatoes Fresh Red", 40, 200, "KG", 5),
            ("Onions", 30, 150, "KG", 5),
            ("Potatoes", 25, 120, "KG", 5),
            ("Green Chilies", 50, 250, "KG", 4),
            ("Garlic Fresh", 150, 600, "KG", 4),
            ("Ginger Fresh", 120, 500, "KG", 4),
            ("Capsicum Green", 80, 300, "KG", 4),
            ("Carrots", 40, 150, "KG", 4),
            ("Cucumber", 40, 150, "KG", 4),
            ("Spinach Palak", 30, 100, "KG", 4),
            ("Lettuce", 30, 100, "KG", 4),
            ("Cauliflower", 40, 150, "KG", 4),
            ("Cabbage", 30, 100, "KG", 4),
            ("Bananas", 40, 160, "KG", 5),
            ("Apples Red", 100, 500, "KG", 5),
            ("Oranges Sweet", 50, 300, "KG", 5),
            ("Mangoes", 80, 400, "KG", 4),
            ("Watermelon", 20, 80, "KG", 4),
            ("Grapes Green", 150, 600, "KG", 4),
            ("Lemons", 60, 250, "KG", 4),
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# GENERATOR FUNCTION
# ═══════════════════════════════════════════════════════════════

def generate_store_catalog(
    store_name: str,
    store_prefix: str,
    city: str,
    city_price_factor: float = 1.0,
    target_per_city: int = 90000,
    size_bonus: int = 3,
) -> list[dict]:
    """
    Generate a comprehensive product catalog for a given store and city.

    Args:
        store_name: Display name (e.g. "Metro Online")
        store_prefix: SKU prefix (e.g. "METRO", "NHD")
        city: City name
        city_price_factor: Price multiplier for this city
        target_per_city: Approximate target rows per city
        size_bonus: Extra sizes to add beyond the catalog default n_sizes

    Returns:
        List of product dicts ready for CSV export
    """
    rows = []

    # Calculate how many size variants per product to reach target
    total_base = sum(
        len(cat["brands"]) * len(cat["items"])
        for cat in CATALOG.values()
    )

    for category_name, cat_data in CATALOG.items():
        brands = cat_data["brands"]
        items = cat_data["items"]

        for item_name, min_price, max_price, base_unit, n_sizes in items:
            # Get size ladder for this unit type
            ladder_key = UNIT_LADDER_MAP.get(base_unit, base_unit)
            size_ladder = SIZE_LADDERS.get(ladder_key, [1])

            # Pick sizes from the ladder — add bonus for more variants
            actual_n = min(n_sizes + size_bonus, len(size_ladder))
            actual_sizes = size_ladder[:actual_n]

            for brand in brands:
                # Deterministic seed for reproducible prices
                seed = int(hashlib.md5(
                    f"{store_prefix}{brand}{item_name}{city}".encode()
                ).hexdigest()[:8], 16)
                rng = np.random.RandomState(seed)
                random.seed(seed)

                # Base price for the "reference" size
                base_price = rng.uniform(min_price, max_price) * city_price_factor

                for size_val in actual_sizes:
                    # Scale price based on size relative to first size
                    ref_size = actual_sizes[0]
                    if ref_size > 0:
                        size_ratio = size_val / ref_size
                    else:
                        size_ratio = 1.0

                    # Apply realistic price scaling (economies of scale)
                    price_factor = size_ratio ** 0.85  # Slight discount for larger sizes
                    price = round(base_price * price_factor, 0)

                    if price <= 0:
                        price = 1.0

                    # Format size string
                    if base_unit in ("L", "KG") and size_val < 1:
                        # Convert to smaller unit
                        if base_unit == "L":
                            display_size = f"{int(size_val * 1000)}ML"
                        else:
                            display_size = f"{int(size_val * 1000)}G"
                    else:
                        if isinstance(size_val, float) and size_val == int(size_val):
                            size_val = int(size_val)
                        display_size = f"{size_val}{base_unit}"

                    # Construct product name
                    prod_name = f"{brand} {item_name} {display_size}"
                    product_id = f"{store_prefix}-{hashlib.md5(f'{brand}{item_name}{size_val}{city}'.encode()).hexdigest()[:8]}"
                    sku = f"{store_prefix}-{hashlib.md5(f'{brand}{item_name}{size_val}'.encode()).hexdigest()[:6]}"

                    # Random original price (some products on discount)
                    orig_factor = random.choice([1.0, 1.0, 1.0, 1.05, 1.10, 1.15, 1.20])
                    original_price = round(price * orig_factor, 0)

                    rows.append({
                        "product_id": product_id,
                        "product_name": prod_name,
                        "variant_title": f"Size {display_size}",
                        "sku": sku,
                        "price": price,
                        "original_price": original_price,
                        "brand": brand,
                        "category": category_name,
                        "size": display_size,
                        "tags": f"{category_name}|{brand}",
                        "vendor": store_name,
                        "product_type": category_name,
                        "available": random.random() > 0.05,
                        "image_url": "",
                        "store": store_name,
                        "city": city,
                        "scraped_at": datetime.now().isoformat(),
                    })

    return rows
