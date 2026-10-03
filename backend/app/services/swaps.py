"""Healthy swap suggestions.

A curated table that maps common high-calorie / high-sodium choices to
healthier alternatives, with an estimated per-piece (or per-katori) kcal
saving. The frontend surfaces one suggestion at a time on the dashboard,
based on the user's most-recent meals.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Swap:
    from_food: str
    to_food: str
    saved_kcal: int
    reason: str
    icon: str = "🔄"
    # Aliases the detector should match against (lowercase, no punctuation).
    aliases: tuple[str, ...] = ()


CATALOG: list[Swap] = [
    Swap("Butter naan",        "Whole wheat roti",     160, "Less refined flour, less ghee.",            aliases=("naan", "butter naan", "garlic naan", "kulcha")),
    Swap("White rice",         "Brown rice",           60,  "More fiber, same comfort.",                  aliases=("steamed rice", "rice", "white rice", "basmati")),
    Swap("Bhature",            "Roti",                 220, "Skip the deep-frying.",                      aliases=("bhature", "bhatura", "puri", "poori")),
    Swap("Aloo paratha (ghee)","Methi thepla",         120, "Lower fat, more greens.",                    aliases=("aloo paratha", "stuffed paratha", "paratha")),
    Swap("Samosa",             "Dhokla",               180, "Steamed, not deep-fried.",                   aliases=("samosa", "kachori", "pakora", "vada")),
    Swap("Gulab jamun",        "Rasgulla",             140, "Soaked in syrup, not fried.",                aliases=("gulab jamun", "jalebi", "ladoo", "barfi", "halwa")),
    Swap("Mango lassi",        "Chaas (buttermilk)",   80,  "Cuts most of the sugar.",                    aliases=("mango lassi", "sweet lassi", "lassi")),
    Swap("Paneer butter masala","Palak paneer",        90,  "Less cream, more iron.",                     aliases=("paneer butter masala", "shahi paneer", "kadai paneer")),
    Swap("Butter chicken",     "Tandoori chicken",     180, "Grilled, not buttered.",                     aliases=("butter chicken", "murgh makhani")),
    Swap("Pav bhaji",          "Misal pav (light)",    120, "Sprouts add protein and fiber.",             aliases=("pav bhaji", "vada pav")),
    Swap("White bread",        "Multigrain bread",     30,  "More fiber per slice.",                      aliases=("white bread", "bread slice")),
    Swap("Filter coffee (sweet)","Filter coffee (no sugar)", 60, "Same kick, no spike.",                  aliases=("coffee", "filter coffee")),
    Swap("Chips / namkeen",    "Roasted chana",        110, "Roasted, not fried; more protein.",          aliases=("chips", "namkeen", "sev")),
]


def suggest_for_names(names: list[str]) -> Swap | None:
    if not names:
        return None
    haystack = " | ".join(n.lower() for n in names)
    for swap in CATALOG:
        if any(alias in haystack for alias in swap.aliases):
            return swap
    return None


def swap_dict(s: Swap) -> dict:
    return {
        "from_food": s.from_food,
        "to_food": s.to_food,
        "saved_kcal": s.saved_kcal,
        "reason": s.reason,
        "icon": s.icon,
    }
