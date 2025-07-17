from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import SeedBatch, PlantingRecord, Sale, Inventory, Expense

@admin.register(SeedBatch)
class SeedBatchAdmin(admin.ModelAdmin):
    list_display = ['variety', 'quantity_kg', 'supplier', 'import_date', 'cost_per_kg', 'total_cost_display']
    list_filter = ['variety', 'supplier', 'import_date']
    search_fields = ['variety', 'supplier']
    date_hierarchy = 'import_date'
    ordering = ['-import_date']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('variety', 'quantity_kg', 'supplier')
        }),
        ('Cost Details', {
            'fields': ('cost_per_kg', 'import_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_cost_display(self, obj):
        return f"${obj.total_cost:,.2f}"
    total_cost_display.short_description = 'Total Cost'
    total_cost_display.admin_order_field = 'cost_per_kg'

@admin.register(PlantingRecord)
class PlantingRecordAdmin(admin.ModelAdmin):
    list_display = ['field_name', 'seed_variety', 'date_planted', 'status', 'expected_yield_kg', 'actual_yield_kg', 'efficiency_display']
    list_filter = ['status', 'seed_batch__variety', 'date_planted']
    search_fields = ['field_name', 'seed_batch__variety']
    date_hierarchy = 'date_planted'
    ordering = ['-date_planted']
    readonly_fields = ['created_at', 'yield_efficiency']
    
    fieldsets = (
        ('Planting Information', {
            'fields': ('field_name', 'seed_batch', 'date_planted', 'status')
        }),
        ('Yield Information', {
            'fields': ('expected_yield_kg', 'actual_yield_kg', 'harvest_date', 'yield_efficiency')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def seed_variety(self, obj):
        return obj.seed_batch.get_variety_display()
    seed_variety.short_description = 'Variety'
    seed_variety.admin_order_field = 'seed_batch__variety'
    
    def efficiency_display(self, obj):
        efficiency = obj.yield_efficiency
        if efficiency is not None:
            color = 'green' if efficiency >= 100 else 'orange' if efficiency >= 80 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, efficiency
            )
        return '-'
    efficiency_display.short_description = 'Yield Efficiency'

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'date', 'variety', 'quantity_kg', 'price_per_kg', 'total_price_display', 'payment_status_display']
    list_filter = ['payment_status', 'variety', 'date']
    search_fields = ['customer_name', 'invoice_number', 'variety']
    date_hierarchy = 'date'
    ordering = ['-date']
    readonly_fields = ['invoice_number', 'total_price', 'created_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Sale Details', {
            'fields': ('date', 'variety', 'quantity_kg', 'price_per_kg', 'total_price')
        }),
        ('Payment & Invoice', {
            'fields': ('payment_status', 'invoice_number')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_price_display(self, obj):
        return f"${obj.total_price:,.2f}"
    total_price_display.short_description = 'Total'
    total_price_display.admin_order_field = 'price_per_kg'
    
    def payment_status_display(self, obj):
        colors = {
            'paid': 'green',
            'pending': 'orange',
            'overdue': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.payment_status, 'black'),
            obj.get_payment_status_display()
        )
    payment_status_display.short_description = 'Payment Status'
    payment_status_display.admin_order_field = 'payment_status'

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['variety', 'quantity_kg', 'quality_grade', 'storage_location', 'expiry_date', 'stock_status', 'updated_at']
    list_filter = ['quality_grade', 'variety', 'expiry_date']
    search_fields = ['variety', 'storage_location']
    ordering = ['variety', 'expiry_date']
    readonly_fields = ['updated_at', 'created_at']
    
    fieldsets = (
        ('Inventory Details', {
            'fields': ('variety', 'quantity_kg', 'quality_grade')
        }),
        ('Storage Information', {
            'fields': ('storage_location', 'expiry_date')
        }),
        ('Timestamps', {
            'fields': ('updated_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">Low Stock</span>'
            )
        return format_html(
            '<span style="color: green;">Good</span>'
        )
    stock_status.short_description = 'Stock Status'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'category', 'amount', 'date', 'supplier', 'receipt_number']
    list_filter = ['category', 'is_recurring', 'date']
    search_fields = ['description', 'supplier', 'receipt_number']
    date_hierarchy = 'date'
    ordering = ['-date']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Expense Details', {
            'fields': ('description', 'category', 'amount', 'date')
        }),
        ('Supplier Information', {
            'fields': ('supplier', 'receipt_number', 'is_recurring')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )

# Customize admin site
admin.site.site_header = "Potato Company Management"
admin.site.site_title = "Potato Company Admin"
admin.site.index_title = "Business Management Dashboard"