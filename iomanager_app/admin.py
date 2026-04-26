from django.contrib import admin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin

from .models import (
    Customer,
    CustomerPass,
    PassTransaction,
    VisitOrderItem,
    VisitSession,
    SystemSetting,
    PassTemplate,
    ProductTemplate,
)

class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer
        import_id_fields = ('phone_number',) 
        # fields = ('phone_number', 'visit_count', 'last_visit_at', 'created_at')
        fields = ('phone_number', 'visit_count', 'last_visit_at')

class CustomerPassResource(resources.ModelResource):
    customer = fields.Field(
        column_name='customer_phone_number',
        attribute='customer',
        widget=ForeignKeyWidget(Customer, 'phone_number')
    )
    template = fields.Field(
        column_name='template_name',
        attribute='template',
        widget=ForeignKeyWidget(PassTemplate, 'name')
    )
    class Meta:
        model = CustomerPass
        import_id_fields = ('id',) 
        fields = ('id', 'customer', 'template', 'remaining_count', 'expires_on')

@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    resource_class = CustomerResource
    list_display = ("phone_number", "visit_count", "last_visit_at", "created_at")
    search_fields = ("phone_number",)

@admin.register(CustomerPass)
class CustomerPassAdmin(ImportExportModelAdmin):
    resource_class = CustomerPassResource
    list_display = ("customer", "template", "remaining_count", "expires_on", "created_at")
    list_filter = ("template", "expires_on")
    search_fields = ("customer__phone_number", "template__name")

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
