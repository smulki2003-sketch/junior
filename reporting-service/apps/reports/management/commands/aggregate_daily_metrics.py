from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from apps.reports.services import aggregate_daily_metrics


class Command(BaseCommand):
    help = "Collect and persist daily KPI snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, required=False, help="Snapshot date in YYYY-MM-DD format.")

    def handle(self, *args, **options):
        requested_date = options.get("date")
        snapshot_date: date | None = None
        if requested_date:
            snapshot_date = parse_date(requested_date)
            if snapshot_date is None:
                raise CommandError("Invalid --date format. Expected YYYY-MM-DD.")

        result = aggregate_daily_metrics(snapshot_date=snapshot_date)
        self.stdout.write(
            self.style.SUCCESS(
                f"Daily metrics aggregated for {result['kpi'].date.isoformat()} "
                f"(bookings={result['kpi'].total_bookings}, gross_volume={result['kpi'].gross_volume})"
            )
        )

