from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class SeedBatch(models.Model):
    VARIETY_CHOICES = [
        ('russet', 'Russet Burbank'),
        ('red', 'Red Pontiac'),
        ('yukon', 'Yukon Gold'),
        ('fingerling', 'Fingerling'),
        ('sweet', 'Sweet Potato'),
    ]
    
    variety = models.CharField(max_length=100, choices=VARIETY_CHOICES)
    quantity_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    supplier = models.CharField(max_length=100)
    import_date = models.DateField()
    cost_per_kg = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-import_date']
        verbose_name_plural = "Seed Batches"

    def __str__(self):
        return f"{self.get_variety_display()} - {self.quantity_kg}kg ({self.import_date})"

    @property
    def total_cost(self):
        return self.quantity_kg * self.cost_per_kg

class PlantingRecord(models.Model):
    STATUS_CHOICES = [
        ('planted', 'Planted'),
        ('growing', 'Growing'),
        ('ready', 'Ready for Harvest'),
        ('harvested', 'Harvested'),
        ('failed', 'Failed'),
    ]
    
    field_name = models.CharField(max_length=100)
    seed_batch = models.ForeignKey(SeedBatch, on_delete=models.CASCADE)
    date_planted = models.DateField()
    expected_yield_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    actual_yield_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    harvest_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planted')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_planted']

    def __str__(self):
        return f"{self.field_name} - {self.seed_batch.variety} ({self.date_planted})"

    @property
    def yield_efficiency(self):
        if self.actual_yield_kg and self.expected_yield_kg:
            return (self.actual_yield_kg / self.expected_yield_kg) * 100
        return None

class Sale(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    date = models.DateField()
    variety = models.CharField(max_length=100)
    quantity_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    price_per_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    @property
    def total_price(self):
        return self.quantity_kg * self.price_per_kg

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            last_sale = Sale.objects.order_by('-id').first()
            if last_sale:
                last_num = int(last_sale.invoice_number.split('-')[-1]) if last_sale.invoice_number else 0
            else:
                last_num = 0
            self.invoice_number = f"INV-{last_num + 1:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale to {self.customer_name} - {self.invoice_number}"

class Inventory(models.Model):
    QUALITY_CHOICES = [
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('seconds', 'Seconds'),
    ]
    
    variety = models.CharField(max_length=100)
    quantity_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    quality_grade = models.CharField(max_length=20, choices=QUALITY_CHOICES, default='standard')
    storage_location = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['variety', 'expiry_date']
        verbose_name_plural = "Inventory Items"

    def __str__(self):
        return f"{self.variety} - {self.quantity_kg}kg ({self.get_quality_grade_display()})"

    @property
    def is_low_stock(self):
        return self.quantity_kg < 50  # Threshold for low stock warning

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('seeds', 'Seeds'),
        ('transport', 'Transportation'),
        ('labor', 'Labor'),
        ('equipment', 'Equipment'),
        ('maintenance', 'Maintenance'),
        ('utilities', 'Utilities'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]
    
    description = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    receipt_number = models.CharField(max_length=100, blank=True)
    supplier = models.CharField(max_length=100, blank=True)
    is_recurring = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_category_display()}: ${self.amount} ({self.date})"