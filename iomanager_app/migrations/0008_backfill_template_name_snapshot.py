from django.db import migrations


def backfill_template_name_snapshot(apps, schema_editor):
    PassTransaction = apps.get_model("iomanager_app", "PassTransaction")
    rows = PassTransaction.objects.filter(template__isnull=False, template_name_snapshot="")
    for row in rows.select_related("template").iterator():
        row.template_name_snapshot = row.template.name
        row.save(update_fields=["template_name_snapshot"])


class Migration(migrations.Migration):
    dependencies = [
        ("iomanager_app", "0007_remove_passtemplate_is_active_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_template_name_snapshot, migrations.RunPython.noop),
    ]
