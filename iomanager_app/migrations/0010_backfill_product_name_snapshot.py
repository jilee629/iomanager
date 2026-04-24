from django.db import migrations


def backfill_product_name_snapshot(apps, schema_editor):
    VisitOrderItem = apps.get_model("iomanager_app", "VisitOrderItem")
    rows = VisitOrderItem.objects.filter(product__isnull=False, product_name_snapshot="")
    for row in rows.select_related("product").iterator():
        row.product_name_snapshot = row.product.name
        row.save(update_fields=["product_name_snapshot"])


class Migration(migrations.Migration):
    dependencies = [
        ("iomanager_app", "0009_visitorderitem_product_name_snapshot_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_product_name_snapshot, migrations.RunPython.noop),
    ]
