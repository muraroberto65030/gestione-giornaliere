from django.contrib import admin
from .models import CleaningMachine, Area, Street, WorkOrder, PassagePlan, CleaningOperationType, StreetCleaningOperation


@admin.register(CleaningMachine)
class CleaningMachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'created_at']
    list_filter = ['area']
    search_fields = ['name', 'area__name']


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['street', 'cleaning_machine', 'daily_passages', 'date', 'created_by']
    list_filter = ['cleaning_machine', 'date', 'created_by', 'street__area']
    search_fields = ['street__name', 'cleaning_machine__name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PassagePlan)
class PassagePlanAdmin(admin.ModelAdmin):
    list_display = ['cleaning_machine', 'day_of_month', 'month', 'year', 'required_passages']
    list_filter = ['cleaning_machine', 'month', 'year']
    search_fields = ['cleaning_machine__name']
    ordering = ['year', 'month', 'day_of_month']


@admin.register(CleaningOperationType)
class CleaningOperationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'frequency_per_week', 'description']
    search_fields = ['name']
    list_filter = ['frequency_per_week']


@admin.register(StreetCleaningOperation)
class StreetCleaningOperationAdmin(admin.ModelAdmin):
    list_display = ['street', 'operation_type', 'day_of_month', 'month', 'year']
    list_filter = ['operation_type', 'month', 'year', 'street__area']
    search_fields = ['street__name', 'operation_type__name']
    date_hierarchy = None
    ordering = ['year', 'month', 'day_of_month', 'street__name']
