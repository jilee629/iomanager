from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from iomanager_app.models import CustomerPass, PassTransaction


class Command(BaseCommand):
    help = "Expires customer passes whose expiration date is today or earlier."

    def handle(self, *args, **options):
        today = timezone.localdate()
        expired_count = 0

        target_ids = list(
            CustomerPass.objects.filter(remaining_count__gt=0, expires_on__lte=today).values_list("id", flat=True)
        )

        for pass_id in target_ids:
            with transaction.atomic():
                customer_pass = (
                    CustomerPass.objects.select_for_update()
                    .select_related("customer", "template")
                    .filter(id=pass_id, remaining_count__gt=0, expires_on__lte=today)
                    .first()
                )
                if not customer_pass:
                    continue

                already_expired = PassTransaction.objects.filter(
                    customer_pass=customer_pass,
                    status=PassTransaction.Status.EXPIRED,
                ).exists()
                if already_expired:
                    continue

                remaining = customer_pass.remaining_count
                PassTransaction.objects.create(
                    customer=customer_pass.customer,
                    template=customer_pass.template,
                    template_name_snapshot=customer_pass.template.name,
                    quantity=remaining,
                    status=PassTransaction.Status.EXPIRED,
                    customer_pass=customer_pass,
                )
                customer_pass.remaining_count = 0
                customer_pass.save(update_fields=["remaining_count"])
                expired_count += 1

        self.stdout.write(self.style.SUCCESS(f"Expired passes processed: {expired_count}"))
