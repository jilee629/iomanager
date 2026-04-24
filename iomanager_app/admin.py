from django.contrib import admin

from .models import (
    Customer,
    CustomerPass,
    PassTemplate,
    PassTransaction,
    ProductTemplate,
    SystemSetting,
    VisitOrderItem,
    VisitSession,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "visit_count", "last_visit_at", "created_at")
    search_fields = ("phone_number",)


@admin.register(VisitSession)
class VisitSessionAdmin(admin.ModelAdmin):
    list_display = ("customer", "status", "requested_at", "entered_at", "exited_at")
    list_filter = ("status", "requested_at")
    search_fields = ("customer__phone_number",)


@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "created_at")
    search_fields = ("name",)


@admin.register(PassTemplate)
class PassTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "issue_count", "valid_days", "created_at")
    search_fields = ("name",)


@admin.register(CustomerPass)
class CustomerPassAdmin(admin.ModelAdmin):
    list_display = ("customer", "template", "remaining_count", "expires_on", "created_at")
    list_filter = ("template", "expires_on")
    search_fields = ("customer__phone_number", "template__name")


@admin.register(PassTransaction)
class PassTransactionAdmin(admin.ModelAdmin):
    list_display = ("customer", "template", "quantity", "status", "happened_at")
    list_filter = ("status", "happened_at", "template")
    search_fields = ("customer__phone_number", "template__name")


@admin.register(VisitOrderItem)
class VisitOrderItemAdmin(admin.ModelAdmin):
    list_display = ("visit", "product", "quantity")
    list_filter = ("product",)


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")
