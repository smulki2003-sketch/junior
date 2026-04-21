from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="housingunit",
            name="current_occupancy",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="housingunit",
            name="max_occupancy",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="housingunit",
            name="star_rating",
            field=models.DecimalField(decimal_places=1, default=3.0, max_digits=2),
        ),
        migrations.AddField(
            model_name="housingunit",
            name="worker_count",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
