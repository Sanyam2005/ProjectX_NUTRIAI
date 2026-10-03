"""Curated nutrition database for common Indian foods.

Values are approximate, per the indicated serving (per 100 g unless noted).
Numbers come from public sources (IFCT 2017, USDA, brand labels) rounded for
display. Replace this module with a real nutrition DB integration when
available — the lookup signature in `lookup()` is the only thing other code
depends on.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True, frozen=True)
class FoodNutrition:
    name: str
    aliases: tuple[str, ...]
    default_weight_g: float
    default_unit: str   # "g" | "piece" | "bowl" | "cup" | "katori" | "ml"
    # All macros per 100 g of edible portion.
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float


# Per-100g values for ~55 common Indian + global foods.
_FOODS: list[FoodNutrition] = [
    # --- Staples ---
    FoodNutrition("Steamed rice",       ("rice", "chawal", "basmati", "white rice"),       180, "g",      130, 2.7,  28,   0.3, 0.4, 0.1, 1),
    FoodNutrition("Brown rice",         ("brown rice",),                                   180, "g",      111, 2.6,  23,   0.9, 1.8, 0.4, 5),
    FoodNutrition("Jeera rice",         ("jeera rice", "cumin rice"),                      180, "g",      170, 3.0,  29,   4.5, 0.8, 0.2, 220),
    FoodNutrition("Roti",               ("roti", "phulka", "chapati"),                     40,  "piece",  297, 11.0, 56,   3.7, 11,  1.5, 5),
    FoodNutrition("Paratha (plain)",    ("paratha", "plain paratha"),                      80,  "piece",  330, 7.5,  43,   14,  4.5, 1.0, 240),
    FoodNutrition("Stuffed paratha",    ("aloo paratha", "stuffed paratha"),               120, "piece",  290, 6.5,  35,   13,  4.0, 1.5, 320),
    FoodNutrition("Naan",               ("naan",),                                         90,  "piece",  310, 9.0,  53,   6.5, 2.3, 3.0, 480),
    FoodNutrition("Idli",               ("idli",),                                         35,  "piece",  150, 4.0,  31,   0.7, 1.6, 0.3, 200),
    FoodNutrition("Dosa (plain)",       ("dosa", "plain dosa"),                            80,  "piece",  170, 4.0,  30,   3.7, 1.2, 0.3, 220),
    FoodNutrition("Masala dosa",        ("masala dosa",),                                  150, "piece",  210, 4.5,  33,   7.0, 2.0, 1.2, 360),
    FoodNutrition("Uttapam",            ("uttapam",),                                      120, "piece",  175, 4.0,  28,   5.0, 1.8, 1.0, 280),
    FoodNutrition("Poha",               ("poha", "pohe"),                                  180, "bowl",   180, 3.5,  35,   3.0, 1.4, 1.2, 320),
    FoodNutrition("Upma",               ("upma",),                                         180, "bowl",   190, 4.5,  32,   5.0, 1.8, 1.0, 360),
    FoodNutrition("Khichdi",            ("khichdi", "moong khichdi"),                      200, "bowl",   140, 6.0,  22,   3.0, 2.2, 0.6, 280),
    FoodNutrition("Pulao",              ("pulao", "veg pulao"),                            200, "bowl",   180, 4.0,  31,   5.0, 1.4, 1.0, 340),
    FoodNutrition("Biryani (chicken)",  ("biryani", "chicken biryani"),                    250, "bowl",   240, 9.5,  28,   9.0, 1.6, 1.0, 480),
    FoodNutrition("Biryani (veg)",      ("veg biryani",),                                  250, "bowl",   200, 5.0,  30,   7.0, 1.8, 1.2, 420),

    # --- Dals & curries ---
    FoodNutrition("Dal tadka",          ("dal", "dal tadka", "yellow dal"),                150, "bowl",   116, 7.0,  17,   2.5, 5.0, 0.8, 280),
    FoodNutrition("Dal makhani",        ("dal makhani",),                                  150, "bowl",   175, 7.5,  17,   8.5, 6.0, 1.0, 380),
    FoodNutrition("Sambar",             ("sambar", "sambhar"),                             180, "bowl",   100, 5.0,  15,   2.5, 4.0, 1.5, 320),
    FoodNutrition("Rasam",              ("rasam",),                                        180, "bowl",   60,  2.5,  10,   1.5, 2.0, 1.0, 340),
    FoodNutrition("Rajma",              ("rajma", "kidney bean curry"),                    150, "bowl",   140, 8.0,  20,   2.5, 7.0, 1.5, 360),
    FoodNutrition("Chole",              ("chole", "chickpea curry", "chana masala"),       150, "bowl",   165, 8.5,  22,   4.5, 7.5, 2.0, 420),
    FoodNutrition("Paneer butter masala",("paneer", "paneer butter masala", "paneer masala"),120, "bowl", 270, 11.0, 8,    22,  1.5, 4.0, 460),
    FoodNutrition("Palak paneer",       ("palak paneer",),                                 150, "bowl",   180, 9.0,  7,    13,  3.0, 2.0, 380),
    FoodNutrition("Aloo gobi",          ("aloo gobi",),                                    150, "bowl",   95,  3.0,  13,   4.0, 3.5, 3.0, 320),
    FoodNutrition("Bhindi sabzi",       ("bhindi", "okra", "lady finger"),                 150, "bowl",   100, 2.5,  10,   6.0, 3.5, 1.5, 280),
    FoodNutrition("Mixed veg sabzi",    ("mixed veg", "sabzi", "subzi"),                   150, "bowl",   110, 3.0,  13,   5.5, 3.5, 3.0, 320),
    FoodNutrition("Baingan bharta",     ("baingan bharta", "brinjal"),                     150, "bowl",   105, 2.5,  10,   6.5, 3.5, 4.0, 320),
    FoodNutrition("Butter chicken",     ("butter chicken", "murgh makhani"),               180, "bowl",   240, 16.0, 7,    17,  1.0, 4.0, 520),
    FoodNutrition("Chicken curry",      ("chicken curry",),                                180, "bowl",   180, 18.0, 6,    9.5, 1.0, 3.0, 460),
    FoodNutrition("Fish curry",         ("fish curry",),                                   180, "bowl",   160, 18.0, 5,    8.0, 0.8, 2.5, 480),
    FoodNutrition("Egg curry",          ("egg curry",),                                    180, "bowl",   170, 12.0, 5,    11,  1.0, 2.0, 380),

    # --- Sides & accompaniments ---
    FoodNutrition("Curd",               ("curd", "dahi", "yogurt"),                        100, "bowl",   60,  3.5,  4.5,  3.3, 0,   4.5, 36),
    FoodNutrition("Raita",              ("raita", "cucumber raita"),                       100, "bowl",   70,  3.0,  5.5,  3.5, 0.5, 4.0, 220),
    FoodNutrition("Pickle (achaar)",    ("pickle", "achaar"),                              10,  "g",      180, 1.0,  10,   14,  2.0, 5.0, 1800),
    FoodNutrition("Papad",              ("papad", "papadum"),                              8,   "piece",  370, 23.0, 50,   2.0, 5.0, 1.5, 1800),
    FoodNutrition("Green chutney",      ("chutney", "green chutney", "mint chutney"),      15,  "g",      80,  2.5,  10,   2.5, 4.0, 3.0, 480),
    FoodNutrition("Coconut chutney",    ("coconut chutney",),                              30,  "g",      170, 2.5,  6,    15,  3.5, 3.0, 240),

    # --- Salads & veg ---
    FoodNutrition("Mixed salad",        ("salad", "mixed salad"),                          100, "bowl",   30,  1.5,  5,    0.3, 2.0, 2.5, 30),
    FoodNutrition("Kachumber salad",    ("kachumber",),                                    100, "bowl",   35,  1.5,  6,    0.3, 2.2, 3.0, 50),

    # --- Snacks ---
    FoodNutrition("Samosa",             ("samosa",),                                       60,  "piece",  300, 5.5,  32,   17,  2.5, 1.5, 420),
    FoodNutrition("Pakora",             ("pakora", "bhajiya"),                             50,  "g",      315, 7.0,  28,   19,  4.0, 1.5, 380),
    FoodNutrition("Vada",               ("vada", "medu vada"),                             40,  "piece",  300, 9.0,  30,   16,  4.0, 0.8, 360),
    FoodNutrition("Pav bhaji",          ("pav bhaji",),                                    250, "bowl",   170, 4.5,  20,   8.0, 4.0, 3.5, 460),
    FoodNutrition("Vada pav",           ("vada pav",),                                     130, "piece",  290, 7.0,  36,   13,  3.5, 3.0, 520),
    FoodNutrition("Dhokla",             ("dhokla",),                                       60,  "piece",  160, 6.0,  25,   3.5, 3.0, 2.5, 360),

    # --- Proteins (cooked) ---
    FoodNutrition("Boiled egg",         ("egg", "boiled egg"),                             50,  "piece",  155, 13.0, 1.1,  11,  0,   1.1, 124),
    FoodNutrition("Grilled chicken",    ("chicken", "grilled chicken", "tandoori chicken"),100, "g",      165, 31.0, 0,    3.6, 0,   0,   74),
    FoodNutrition("Paneer (raw)",       ("paneer cube", "raw paneer"),                     60,  "g",      265, 18.0, 1.2,  21,  0,   1.2, 22),
    FoodNutrition("Tofu",               ("tofu",),                                         80,  "g",      76,  8.0,  1.9,  4.8, 0.3, 0.7, 7),

    # --- Sweets & drinks ---
    FoodNutrition("Gulab jamun",        ("gulab jamun",),                                  40,  "piece",  340, 5.0,  52,   13,  0.5, 35,  120),
    FoodNutrition("Jalebi",             ("jalebi",),                                       30,  "piece",  370, 3.0,  68,   10,  0.5, 50,  60),
    FoodNutrition("Kheer",              ("kheer", "rice pudding"),                         150, "bowl",   140, 4.0,  22,   4.5, 0.5, 18,  60),
    FoodNutrition("Lassi (sweet)",      ("lassi",),                                        250, "ml",     90,  3.0,  13,   3.0, 0,   12,  60),
    FoodNutrition("Masala chai",        ("chai", "tea", "masala chai"),                    150, "ml",     50,  1.5,  6.5,  2.0, 0,   5.5, 20),
    FoodNutrition("Filter coffee",      ("coffee", "filter coffee"),                       150, "ml",     45,  1.2,  6.0,  1.8, 0,   5.0, 18),
    FoodNutrition("Water",              ("water",),                                        250, "ml",     0,   0,    0,    0,   0,   0,   2),

    # --- Western / generic ---
    FoodNutrition("Bread slice",        ("bread", "white bread"),                          30,  "piece",  265, 9.0,  49,   3.2, 2.7, 5.0, 491),
    FoodNutrition("Banana",             ("banana",),                                       120, "piece",  89,  1.1,  23,   0.3, 2.6, 12,  1),
    FoodNutrition("Apple",              ("apple",),                                        150, "piece",  52,  0.3,  14,   0.2, 2.4, 10,  1),
    FoodNutrition("Almonds",            ("almond", "almonds", "badam"),                    20,  "g",      579, 21.0, 22,   50,  12,  4.4, 1),

    # --- Additional staples & breads ---
    FoodNutrition("Bhakri",             ("bhakri", "jowar roti", "jowar bhakri"),          50,  "piece",  340, 10.0, 72,   1.7, 9.5, 1.0, 6),
    FoodNutrition("Missi roti",         ("missi roti",),                                   55,  "piece",  330, 13.0, 56,   5.5, 8.5, 1.6, 240),
    FoodNutrition("Makki roti",         ("makki roti", "makki di roti", "corn roti"),      55,  "piece",  365, 9.0,  74,   4.5, 7.5, 0.7, 35),
    FoodNutrition("Rumali roti",        ("rumali roti",),                                  40,  "piece",  290, 9.5,  55,   3.5, 2.0, 2.5, 380),
    FoodNutrition("Methi thepla",       ("thepla", "methi thepla"),                        50,  "piece",  315, 8.5,  46,   10,  4.0, 2.0, 280),
    FoodNutrition("Puri",               ("puri", "poori"),                                 25,  "piece",  370, 8.0,  44,   18,  2.0, 0.8, 220),
    FoodNutrition("Bhature",            ("bhature", "bhatura"),                            120, "piece",  330, 7.5,  44,   14,  2.0, 3.5, 280),
    FoodNutrition("Kulcha",             ("kulcha",),                                       90,  "piece",  295, 8.5,  50,   6.5, 2.0, 3.0, 420),
    FoodNutrition("Lemon rice",         ("lemon rice", "chitranna"),                       180, "bowl",   160, 3.0,  30,   3.5, 1.0, 0.8, 320),
    FoodNutrition("Tamarind rice",      ("tamarind rice", "pulihora", "puliyodarai"),      180, "bowl",   175, 3.5,  29,   5.0, 1.5, 1.5, 380),
    FoodNutrition("Curd rice",          ("curd rice", "thayir sadam"),                     180, "bowl",   115, 3.5,  19,   2.5, 0.8, 2.5, 220),
    FoodNutrition("Ghee rice",          ("ghee rice",),                                    180, "bowl",   195, 3.5,  29,   7.5, 0.8, 0.2, 240),
    FoodNutrition("Hyderabadi biryani", ("hyderabadi biryani",),                           250, "bowl",   250, 9.0,  29,   10,  1.6, 1.0, 500),
    FoodNutrition("Mutton biryani",     ("mutton biryani",),                               250, "bowl",   265, 10.0, 27,   13,  1.6, 1.0, 520),

    # --- Additional dals ---
    FoodNutrition("Toor dal",           ("toor dal", "arhar dal", "pigeon pea dal"),       150, "bowl",   115, 7.0,  17,   2.0, 5.0, 0.8, 300),
    FoodNutrition("Masoor dal",         ("masoor dal", "red lentil dal"),                  150, "bowl",   110, 7.5,  17,   1.5, 5.5, 0.8, 280),
    FoodNutrition("Moong dal",          ("moong dal", "yellow moong dal"),                 150, "bowl",   105, 7.0,  16,   1.2, 5.0, 0.8, 260),
    FoodNutrition("Urad dal",           ("urad dal", "black gram dal"),                    150, "bowl",   130, 8.5,  18,   2.5, 6.0, 0.6, 280),
    FoodNutrition("Chana dal",          ("chana dal", "split bengal gram"),                150, "bowl",   125, 7.5,  19,   2.2, 6.0, 0.8, 280),
    FoodNutrition("Kadhi",              ("kadhi", "kadi"),                                 180, "bowl",   95,  4.0,  10,   4.0, 0.5, 3.0, 320),
    FoodNutrition("Pindi chole",        ("pindi chole",),                                  150, "bowl",   175, 8.5,  22,   5.5, 7.5, 2.0, 460),

    # --- Sabzis / curries ---
    FoodNutrition("Aloo sabzi",         ("aloo sabzi", "aloo masala", "potato sabzi"),     150, "bowl",   110, 2.5,  16,   4.0, 2.2, 1.5, 320),
    FoodNutrition("Methi sabzi",        ("methi sabzi", "methi malai"),                    150, "bowl",   140, 4.0,  9,    10,  3.5, 2.0, 300),
    FoodNutrition("Lauki sabzi",        ("lauki sabzi", "doodhi", "bottle gourd"),         150, "bowl",   75,  2.0,  9,    3.5, 2.5, 3.0, 280),
    FoodNutrition("Karela sabzi",       ("karela", "bitter gourd"),                        150, "bowl",   95,  2.5,  10,   5.5, 4.0, 2.5, 260),
    FoodNutrition("Tinda sabzi",        ("tinda",),                                        150, "bowl",   85,  2.5,  9,    4.5, 2.8, 2.5, 260),
    FoodNutrition("Gobi sabzi",         ("gobi sabzi", "cauliflower sabzi"),               150, "bowl",   95,  3.0,  10,   5.0, 3.5, 3.0, 300),
    FoodNutrition("Mushroom curry",     ("mushroom curry", "kadai mushroom"),              150, "bowl",   145, 6.5,  10,   9.0, 2.5, 3.0, 380),
    FoodNutrition("Mutton curry",       ("mutton curry", "rogan josh"),                    180, "bowl",   240, 18.0, 5,    16,  0.8, 2.5, 480),
    FoodNutrition("Prawn curry",        ("prawn curry", "shrimp curry"),                   180, "bowl",   175, 17.0, 6,    9.0, 1.0, 2.5, 520),
    FoodNutrition("Egg bhurji",         ("egg bhurji", "anda bhurji"),                     120, "bowl",   195, 12.0, 4,    14,  0.8, 2.5, 360),
    FoodNutrition("Keema",              ("keema", "mutton keema"),                         150, "bowl",   220, 17.0, 5,    14,  0.8, 2.0, 460),

    # --- Sides ---
    FoodNutrition("Chaas (buttermilk)", ("chaas", "buttermilk"),                           250, "ml",     35,  1.8,  4,    1.0, 0,   3.5, 90),
    FoodNutrition("Tomato chutney",     ("tomato chutney",),                               30,  "g",      85,  2.0,  10,   3.5, 2.0, 4.0, 380),
    FoodNutrition("Peanut chutney",     ("peanut chutney",),                               30,  "g",      220, 7.0,  10,   17,  3.5, 2.0, 280),
    FoodNutrition("Onion raita",        ("onion raita",),                                  100, "bowl",   75,  3.0,  6,    4.0, 0.7, 4.5, 240),
    FoodNutrition("Boondi raita",       ("boondi raita",),                                 100, "bowl",   100, 3.5,  10,   5.0, 0.4, 3.5, 320),

    # --- Snacks & chaat ---
    FoodNutrition("Dhokla (khaman)",    ("khaman", "khaman dhokla"),                       60,  "piece",  155, 6.0,  24,   3.5, 2.8, 2.5, 380),
    FoodNutrition("Khandvi",            ("khandvi",),                                      50,  "g",      170, 5.5,  18,   8.0, 1.5, 1.5, 360),
    FoodNutrition("Sabudana khichdi",   ("sabudana khichdi", "sabudana"),                  180, "bowl",   215, 3.0,  38,   6.5, 1.5, 1.5, 260),
    FoodNutrition("Kachori",            ("kachori",),                                      50,  "piece",  340, 7.0,  36,   18,  3.5, 1.0, 380),
    FoodNutrition("Bhel puri",          ("bhel puri", "bhel"),                             120, "bowl",   295, 6.5,  44,   10,  4.5, 5.0, 580),
    FoodNutrition("Pani puri",          ("pani puri", "golgappa", "puchka"),               80,  "piece",  290, 6.0,  46,   9.0, 4.0, 4.0, 620),
    FoodNutrition("Aloo tikki",         ("aloo tikki",),                                   70,  "piece",  185, 3.5,  25,   8.0, 2.5, 1.5, 360),
    FoodNutrition("Chole tikki",        ("chole tikki", "ragda pattice"),                  220, "bowl",   240, 7.0,  32,   9.5, 6.0, 3.5, 520),
    FoodNutrition("Misal pav",          ("misal pav", "misal"),                            220, "bowl",   240, 9.0,  32,   8.5, 6.5, 3.0, 540),

    # --- Sweets ---
    FoodNutrition("Rasgulla",           ("rasgulla",),                                     50,  "piece",  205, 4.0,  46,   1.5, 0,   42,  35),
    FoodNutrition("Rasmalai",           ("rasmalai",),                                     60,  "piece",  225, 6.5,  32,   8.0, 0,   28,  45),
    FoodNutrition("Besan ladoo",        ("besan ladoo", "ladoo"),                          30,  "piece",  445, 8.0,  56,   20,  3.0, 38,  35),
    FoodNutrition("Motichoor ladoo",    ("motichoor ladoo",),                              30,  "piece",  430, 5.5,  62,   17,  1.5, 48,  35),
    FoodNutrition("Kaju barfi",         ("kaju katli", "kaju barfi"),                      20,  "piece",  475, 10.0, 48,   24,  1.5, 40,  18),
    FoodNutrition("Gajar halwa",        ("gajar halwa", "carrot halwa"),                   100, "bowl",   265, 5.0,  35,   12,  2.5, 30,  120),
    FoodNutrition("Sooji halwa",        ("sooji halwa", "rava halwa"),                     100, "bowl",   330, 4.0,  48,   14,  1.0, 32,  60),
    FoodNutrition("Kulfi",              ("kulfi",),                                        80,  "piece",  220, 5.5,  24,   12,  0.5, 22,  60),

    # --- Drinks ---
    FoodNutrition("Salted lassi",       ("salted lassi", "namkeen lassi"),                 250, "ml",     50,  2.5,  5,    2.0, 0,   4.5, 280),
    FoodNutrition("Mango lassi",        ("mango lassi",),                                  250, "ml",     115, 3.0,  21,   2.5, 0.5, 20,  60),
    FoodNutrition("Nimbu pani",         ("nimbu pani", "lemonade", "shikanji"),            250, "ml",     30,  0.1,  8,    0,   0.2, 7.5, 12),
    FoodNutrition("Filter coffee w/ milk",("south indian coffee",),                        150, "ml",     65,  2.0,  8,    2.5, 0,   7.0, 30),

    # --- Raw ingredients (commonly detected by VLMs) ---
    FoodNutrition("Boiled potato",      ("boiled potato", "aloo boiled", "potato"),        100, "g",      87,  1.9,  20,   0.1, 1.8, 0.9, 240),
    FoodNutrition("Tomato",             ("tomato",),                                       80,  "piece",  18,  0.9,  3.9,  0.2, 1.2, 2.6, 5),
    FoodNutrition("Onion",              ("onion",),                                        80,  "piece",  40,  1.1,  9.3,  0.1, 1.7, 4.2, 4),
    FoodNutrition("Cucumber",           ("cucumber",),                                     100, "g",      16,  0.7,  3.6,  0.1, 0.5, 1.7, 2),
    FoodNutrition("Carrot",             ("carrot",),                                       80,  "piece",  41,  0.9,  10,   0.2, 2.8, 4.7, 69),
    FoodNutrition("Spinach (cooked)",   ("palak", "spinach"),                              100, "g",      23,  2.9,  3.6,  0.4, 2.2, 0.4, 70),
    FoodNutrition("Cabbage",            ("cabbage",),                                      100, "g",      25,  1.3,  5.8,  0.1, 2.5, 3.2, 18),
    FoodNutrition("Green peas",         ("peas", "green peas", "matar"),                   100, "g",      84,  5.4,  16,   0.4, 5.5, 5.7, 5),
    FoodNutrition("Chicken breast",     ("chicken breast", "boiled chicken"),              100, "g",      165, 31.0, 0,    3.6, 0,   0,   74),
    FoodNutrition("Boiled rice (cooked)",("cooked rice",),                                 150, "bowl",   130, 2.7,  28,   0.3, 0.4, 0.1, 1),
    FoodNutrition("Ghee",               ("ghee", "clarified butter"),                      5,   "g",      898, 0.3,  0,    99,  0,   0,   2),
    FoodNutrition("Curd (low fat)",     ("low fat curd", "skim yogurt"),                   100, "bowl",   55,  4.0,  6,    1.5, 0,   6.0, 50),
    FoodNutrition("Honey",              ("honey", "shahad"),                               10,  "g",      304, 0.3,  82,   0,   0.2, 82,  4),
    FoodNutrition("Oats (cooked)",      ("oats", "cooked oats"),                           150, "bowl",   71,  2.5,  12,   1.5, 1.7, 0.3, 4),
]


def _scale(food: FoodNutrition, weight_g: float) -> dict[str, float]:
    factor = weight_g / 100.0
    return {
        "calories":  round(food.kcal      * factor, 1),
        "protein_g": round(food.protein_g * factor, 1),
        "carbs_g":   round(food.carbs_g   * factor, 1),
        "fat_g":     round(food.fat_g     * factor, 1),
        "fiber_g":   round(food.fiber_g   * factor, 1),
        "sugar_g":   round(food.sugar_g   * factor, 1),
        "sodium_mg": round(food.sodium_mg * factor, 1),
    }


def all_foods() -> Iterable[FoodNutrition]:
    return _FOODS


def lookup(name: str) -> FoodNutrition | None:
    needle = name.strip().lower()
    if not needle:
        return None
    for food in _FOODS:
        if food.name.lower() == needle or needle in food.aliases:
            return food
    # Loose contains-match as fallback so AI free-text labels still resolve.
    for food in _FOODS:
        haystack = (food.name.lower(), *food.aliases)
        if any(needle in h or h in needle for h in haystack):
            return food
    return None


def macros_for(name: str, weight_g: float | None = None) -> dict[str, float] | None:
    food = lookup(name)
    if food is None:
        return None
    w = weight_g if weight_g is not None else food.default_weight_g
    return _scale(food, w)


def default_serving(name: str) -> tuple[float, str] | None:
    food = lookup(name)
    if food is None:
        return None
    return food.default_weight_g, food.default_unit
