from __future__ import annotations


SYRIAN_GOVERNORATES = [
    "Damascus",
    "Rural Damascus",
    "Aleppo",
    "Homs",
    "Hama",
    "Latakia",
    "Tartus",
    "Idlib",
    "Daraa",
    "As-Suwayda",
    "Quneitra",
    "Deir ez-Zor",
    "Raqqa",
    "Al-Hasakah",
]

UNIVERSITY_TO_GOVERNORATE = {
    "Damascus University": "Damascus",
    "University of Aleppo": "Aleppo",
    "University of Tishreen": "Latakia",
    "Al-Baath University": "Homs",
    "University of Hama": "Hama",
    "University of Tartous": "Tartus",
    "University of Idlib": "Idlib",
    "University of Daraa": "Daraa",
    "University of Al-Furat": "Deir ez-Zor",
    "Al-Sham Private University": "Rural Damascus",
    "Arab International University": "Rural Damascus",
    "Syrian Private University": "Rural Damascus",
}

SYRIAN_UNIVERSITIES = sorted(UNIVERSITY_TO_GOVERNORATE.keys())


def governorate_for_university(university: str) -> str:
    return UNIVERSITY_TO_GOVERNORATE.get(str(university or "").strip(), "")
