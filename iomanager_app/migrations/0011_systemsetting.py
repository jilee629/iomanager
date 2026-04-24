from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("iomanager_app", "0010_backfill_product_name_snapshot"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("greeting_message", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
