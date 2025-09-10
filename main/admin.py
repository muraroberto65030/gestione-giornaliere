from django.contrib import admin
from .models import CleaningMachine, Area, Street, WorkOrder, PassagePlan


@admin.register(CleaningMachine)
class CleaningMachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'created_at']
    list_filter = ['area']
    search_fields = ['name', 'area__name']


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['street', 'cleaning_machine', 'daily_passages', 'date', 'created_by']
    list_filter = ['cleaning_machine', 'date', 'created_by']
    search_fields = ['street__name', 'cleaning_machine__name']
    date_hierarchy = 'date'


@admin.register(PassagePlan)
class PassagePlanAdmin(admin.ModelAdmin):
    list_display = ['cleaning_machine', 'day_of_month', 'month', 'year', 'required_passages']
    list_filter = ['cleaning_machine', 'month', 'year']
    search_fields = ['cleaning_machine__name']
