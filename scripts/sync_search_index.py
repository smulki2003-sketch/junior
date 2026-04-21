from django.utils import timezone

from apps.search.integrations import HousingServiceClient
from apps.search.models import HousingSearchIndex
from config.settings.base import HOUSING_SERVICE_BASE_URL


SEED_TITLE_PREFIX = "UniNest"

records = HousingServiceClient(HOUSING_SERVICE_BASE_URL).fetch_units_for_indexing()
if not records:
    print("SEARCH SYNCED upstream_records=0 inserted=0 updated=0 deleted=0")
    raise SystemExit(0)

inserted = 0
updated = 0
seeded_units = 0
synced_unit_ids = set()

for item in records:
    title = str(item.get("title", "")).strip()
    if not title.startswith(SEED_TITLE_PREFIX):
        continue

    seeded_units += 1
    unit_id = item["unit_id"]
    synced_unit_ids.add(unit_id)

    defaults = {
        "title": title,
        "description": str(item.get("description", "")).strip(),
        "price": item["price"],
        "location": str(item.get("location", "")).strip(),
        "unit_type": str(item.get("unit_type", "")).strip(),
        "star_rating": item.get("star_rating", 3.0),
        "worker_count": item.get("worker_count", 1),
        "max_occupancy": item.get("max_occupancy", 1),
        "current_occupancy": item.get("current_occupancy", 0),
        "amenities_json": item.get("amenities_json", []),
        "is_available": bool(item.get("is_available", True)),
        "source_updated_at": timezone.now(),
    }

    _, created = HousingSearchIndex.objects.update_or_create(
        unit_id=unit_id,
        defaults=defaults,
    )
    if created:
        inserted += 1
    else:
        updated += 1

deleted = 0
if synced_unit_ids:
    deleted, _ = HousingSearchIndex.objects.exclude(unit_id__in=synced_unit_ids).delete()

print(
    "SEARCH SYNCED",
    "upstream_records=", len(records),
    "seeded_units=", seeded_units,
    "inserted=", inserted,
    "updated=", updated,
    "deleted=", deleted,
)
