from datetime import date, timedelta

from apps.inventory.models import (
    Amenity,
    HousingUnit,
    HousingUnitAmenity,
    HousingUnitImage,
    UnitAvailabilityCalendar,
)


SEED_OWNER_ID = 1
SEED_TITLE_PREFIX = "UniNest"

AMENITY_NAMES = [
    "wifi",
    "laundry",
    "kitchen",
    "heating",
    "parking",
    "elevator",
    "study_lounge",
    "security",
    "solar_power",
    "water_tank",
]

UNITS = [
    {
        "slug": "NOUR",
        "title": "UniNest NOUR - Mazzeh",
        "description": "Bright studio near faculty shuttle routes with quiet evening hours.",
        "price": 365,
        "location": "Damascus - Mazzeh",
        "unit_type": "studio",
        "star_rating": 4.6,
        "worker_count": 2,
        "max_occupancy": 2,
        "current_occupancy": 1,
        "amenities": ["wifi", "laundry", "kitchen", "study_lounge"],
    },
    {
        "slug": "WARD",
        "title": "UniNest WARD - Malki",
        "description": "Premium 1BR with ergonomic study corner and building security.",
        "price": 470,
        "location": "Damascus - Malki",
        "unit_type": "1br",
        "star_rating": 4.8,
        "worker_count": 3,
        "max_occupancy": 3,
        "current_occupancy": 1,
        "amenities": ["wifi", "heating", "elevator", "security"],
    },
    {
        "slug": "RAWAN",
        "title": "UniNest RAWAN - Abu Rummaneh",
        "description": "Shared apartment focused on affordability and stable internet.",
        "price": 295,
        "location": "Damascus - Abu Rummaneh",
        "unit_type": "shared",
        "star_rating": 4.1,
        "worker_count": 2,
        "max_occupancy": 5,
        "current_occupancy": 3,
        "amenities": ["wifi", "laundry", "water_tank"],
    },
    {
        "slug": "SALAM",
        "title": "UniNest SALAM - Muhajreen",
        "description": "Calm 2BR for roommates with sunny living area and rooftop view.",
        "price": 510,
        "location": "Damascus - Muhajreen",
        "unit_type": "2br",
        "star_rating": 4.7,
        "worker_count": 4,
        "max_occupancy": 4,
        "current_occupancy": 2,
        "amenities": ["wifi", "kitchen", "parking", "elevator"],
    },
    {
        "slug": "BAYT",
        "title": "UniNest BAYT - Baramkeh",
        "description": "Budget shared unit near public transit and local markets.",
        "price": 255,
        "location": "Damascus - Baramkeh",
        "unit_type": "shared",
        "star_rating": 3.9,
        "worker_count": 1,
        "max_occupancy": 6,
        "current_occupancy": 4,
        "amenities": ["wifi", "heating", "water_tank"],
    },
    {
        "slug": "DIAR",
        "title": "UniNest DIAR - Ruken Al Din",
        "description": "Compact studio with modern furnishings and monthly deep cleaning.",
        "price": 330,
        "location": "Damascus - Ruken Al Din",
        "unit_type": "studio",
        "star_rating": 4.3,
        "worker_count": 2,
        "max_occupancy": 2,
        "current_occupancy": 0,
        "amenities": ["wifi", "laundry", "heating", "security"],
    },
    {
        "slug": "LINA",
        "title": "UniNest LINA - Qassa",
        "description": "Large 1BR with private balcony and hybrid study/work desk.",
        "price": 425,
        "location": "Damascus - Qassa",
        "unit_type": "1br",
        "star_rating": 4.5,
        "worker_count": 3,
        "max_occupancy": 3,
        "current_occupancy": 2,
        "amenities": ["wifi", "kitchen", "elevator", "solar_power"],
    },
    {
        "slug": "SIRAJ",
        "title": "UniNest SIRAJ - Kfarsouseh",
        "description": "Spacious 2BR suited for international students and long stays.",
        "price": 560,
        "location": "Damascus - Kfarsouseh",
        "unit_type": "2br",
        "star_rating": 4.9,
        "worker_count": 5,
        "max_occupancy": 5,
        "current_occupancy": 3,
        "amenities": ["wifi", "parking", "elevator", "security"],
    },
    {
        "slug": "RITAJ",
        "title": "UniNest RITAJ - Jafra",
        "description": "Value shared room with quick access to university buses.",
        "price": 240,
        "location": "Damascus - Jafra",
        "unit_type": "shared",
        "star_rating": 3.8,
        "worker_count": 1,
        "max_occupancy": 5,
        "current_occupancy": 5,
        "amenities": ["wifi", "laundry", "kitchen"],
    },
    {
        "slug": "QAMAR",
        "title": "UniNest QAMAR - City Center",
        "description": "High-end studio with elevator access and flexible contracts.",
        "price": 545,
        "location": "Damascus - City Center",
        "unit_type": "studio",
        "star_rating": 5.0,
        "worker_count": 4,
        "max_occupancy": 2,
        "current_occupancy": 1,
        "amenities": ["wifi", "kitchen", "elevator", "security"],
    },
    {
        "slug": "YARA",
        "title": "UniNest YARA - Abu Rummaneh",
        "description": "Balanced 1BR option with quiet neighbors and reliable utilities.",
        "price": 390,
        "location": "Damascus - Abu Rummaneh",
        "unit_type": "1br",
        "star_rating": 4.4,
        "worker_count": 2,
        "max_occupancy": 2,
        "current_occupancy": 0,
        "amenities": ["wifi", "heating", "water_tank", "study_lounge"],
    },
    {
        "slug": "AYA",
        "title": "UniNest AYA - Mazzeh",
        "description": "Modern shared suite with housekeeping support for busy students.",
        "price": 315,
        "location": "Damascus - Mazzeh",
        "unit_type": "shared",
        "star_rating": 4.2,
        "worker_count": 3,
        "max_occupancy": 4,
        "current_occupancy": 2,
        "amenities": ["wifi", "laundry", "study_lounge", "security"],
    },
]

IMAGE_POOL = [
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1493666438817-866a91353ca9?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1484154218962-a197022b5858?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1505691938895-1758d7feb511?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop",
]

existing_seed_units = HousingUnit.objects.filter(title__startswith=SEED_TITLE_PREFIX)
deleted_seed_units = existing_seed_units.count()
if deleted_seed_units:
    existing_seed_units.delete()

amenity_map = {name: Amenity.objects.get_or_create(name=name)[0] for name in AMENITY_NAMES}

start = date.today() + timedelta(days=1)
mid = start + timedelta(days=120)
end = start + timedelta(days=240)

created = 0
updated = 0

for idx, row in enumerate(UNITS):
    unit, was_created = HousingUnit.objects.update_or_create(
        title=row["title"],
        defaults={
            "owner_user_id": SEED_OWNER_ID,
            "description": row["description"],
            "price": row["price"],
            "location": row["location"],
            "unit_type": row["unit_type"],
            "star_rating": row["star_rating"],
            "worker_count": row["worker_count"],
            "max_occupancy": row["max_occupancy"],
            "current_occupancy": row["current_occupancy"],
            "moderation_status": HousingUnit.STATUS_APPROVED,
        },
    )
    if was_created:
        created += 1
    else:
        updated += 1

    HousingUnitAmenity.objects.filter(unit=unit).delete()
    for amenity_name in row["amenities"]:
        HousingUnitAmenity.objects.get_or_create(unit=unit, amenity=amenity_map[amenity_name])

    HousingUnitImage.objects.filter(unit=unit).delete()
    for order in range(3):
        image_idx = (idx + order) % len(IMAGE_POOL)
        HousingUnitImage.objects.create(
            unit=unit,
            image_url=IMAGE_POOL[image_idx],
            sort_order=order + 1,
        )

    UnitAvailabilityCalendar.objects.filter(unit=unit).delete()
    UnitAvailabilityCalendar.objects.create(
        unit=unit,
        start_date=start,
        end_date=mid,
        status=UnitAvailabilityCalendar.STATUS_AVAILABLE,
    )
    UnitAvailabilityCalendar.objects.create(
        unit=unit,
        start_date=mid + timedelta(days=1),
        end_date=end,
        status=(
            UnitAvailabilityCalendar.STATUS_RESERVED
            if idx % 4 == 0
            else UnitAvailabilityCalendar.STATUS_AVAILABLE
        ),
    )

available_now = sum(1 for row in UNITS if row["current_occupancy"] < row["max_occupancy"])
print(
    "HOUSING SEEDED",
    "deleted_old=", deleted_seed_units,
    "created=", created,
    "updated=", updated,
    "total=", len(UNITS),
    "available_now=", available_now,
)
