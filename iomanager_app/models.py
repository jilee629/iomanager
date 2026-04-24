from django.db import models


class Customer(models.Model):
    phone_number = models.CharField(max_length=11, unique=True, db_index=True)
    last_visit_at = models.DateTimeField(null=True, blank=True)
    visit_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["last_visit_at", "id"], name="customer_last_visit_id_idx"),
        ]

    def __str__(self):
        return self.phone_number


class VisitSession(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "대기"
        ENTERED = "entered", "입장"
        EXITED = "exited", "퇴장"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="visits")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING, db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    entered_at = models.DateTimeField(null=True, blank=True)
    exited_at = models.DateTimeField(null=True, blank=True)
    re_wait_requested_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["requested_at", "id"], name="visit_requested_id_idx"),
        ]

    def __str__(self):
        return f"{self.customer.phone_number} ({self.get_status_display()})"


class ProductTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.price}원)"


class PassTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    issue_count = models.PositiveIntegerField(default=1)
    valid_days = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomerPass(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="passes")
    template = models.ForeignKey(PassTemplate, on_delete=models.CASCADE, related_name="customer_passes")
    remaining_count = models.PositiveIntegerField(default=0)
    expires_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expires_on", "id"]
        indexes = [
            models.Index(fields=["expires_on", "id"], name="customerpass_expires_id_idx"),
        ]

    def __str__(self):
        return f"{self.customer.phone_number} - {self.template.name} ({self.remaining_count})"


class PassTransaction(models.Model):
    class Status(models.TextChoices):
        ISSUED = "issued", "발행"
        USED = "used", "사용"
        EXPIRED = "expired", "만료"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="pass_transactions")
    template = models.ForeignKey(
        PassTemplate,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        blank=True,
    )
    template_name_snapshot = models.CharField(max_length=100, blank=True, default="")
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=Status.choices, db_index=True)
    happened_at = models.DateTimeField(auto_now_add=True, db_index=True)
    customer_pass = models.ForeignKey(
        CustomerPass,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        blank=True,
    )
    visit = models.ForeignKey(
        VisitSession,
        on_delete=models.SET_NULL,
        related_name="pass_transactions",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-happened_at"]
        indexes = [
            models.Index(fields=["happened_at", "id"], name="passtrx_happened_id_idx"),
        ]


class VisitOrderItem(models.Model):
    visit = models.ForeignKey(VisitSession, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(
        ProductTemplate,
        on_delete=models.SET_NULL,
        related_name="visit_items",
        null=True,
        blank=True,
    )
    product_name_snapshot = models.CharField(max_length=100, blank=True, default="")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        product_name = self.product.name if self.product else self.product_name_snapshot or "(삭제된 상품)"
        return f"{self.visit_id} - {product_name} x {self.quantity}"


class SystemSetting(models.Model):
    greeting_message = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "System Setting"
