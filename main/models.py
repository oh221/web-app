from django.db import models
from django.core.validators import RegexValidator

class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('wholesale', 'Wholesale Orders'),
        ('supply', 'Supply Partnership'),
        ('quality', 'Quality Concerns'),
        ('support', 'Customer Support'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True,
        help_text="Optional: Phone number with country code"
    )
    company = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, help_text="Internal notes for staff")

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.name} - {self.get_subject_display()}"

    @property
    def is_recent(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.sent_at >= timezone.now() - timedelta(days=7)

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    interests = models.JSONField(default=list, blank=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return f"{self.email} ({'Active' if self.is_active else 'Inactive'})"

class QuoteRequest(models.Model):
    VARIETY_CHOICES = [
        ('russet', 'Russet Burbank'),
        ('red', 'Red Pontiac'),
        ('yukon', 'Yukon Gold'),
        ('fingerling', 'Fingerling'),
        ('sweet', 'Sweet Potato'),
        ('mixed', 'Mixed Varieties')
    ]
    
    QUANTITY_CHOICES = [
        ('small', '1-50 kg'),
        ('medium', '51-500 kg'),
        ('large', '501-2000 kg'),
        ('bulk', '2000+ kg')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('quoted', 'Quote Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ]
    
    company_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    variety = models.CharField(max_length=20, choices=VARIETY_CHOICES)
    quantity_range = models.CharField(max_length=20, choices=QUANTITY_CHOICES)
    delivery_location = models.CharField(max_length=200)
    delivery_date = models.DateField()
    additional_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Quote Request from {self.company_name} - {self.get_variety_display()}"