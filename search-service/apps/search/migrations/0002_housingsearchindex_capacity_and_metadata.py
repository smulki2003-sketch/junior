from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("search", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="housingsearchindex",
            name="current_occupancy",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="housingsearchindex",
            name="max_occupancy",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="housingsearchindex",
            name="star_rating",
            field=models.DecimalField(decimal_places=1, default=3.0, max_digits=2),
        ),
        migrations.AddField(
            model_name="housingsearchindex",
            name="worker_count",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
