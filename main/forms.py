from django import forms
from django.core.validators import RegexValidator
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Full Name',
            'required': True
        }),
        help_text='Enter your first and last name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com',
            'required': True
        }),
        help_text='We\'ll never share your email with anyone else'
    )
    
    phone = forms.CharField(
        validators=[phone_regex],
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890'
        }),
        help_text='Optional: Include country code for international numbers'
    )
    
    company = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Company Name (Optional)'
        })
    )
    
    subject = forms.ChoiceField(
        choices=[
            ('', 'Select a Subject'),
            ('general', 'General Inquiry'),
            ('wholesale', 'Wholesale Orders'),
            ('supply', 'Supply Partnership'),
            ('quality', 'Quality Concerns'),
            ('support', 'Customer Support'),
            ('other', 'Other')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        help_text='Please select the most appropriate subject'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Please provide details about your inquiry...',
            'required': True
        }),
        help_text='Minimum 10 characters required',
        min_length=10
    )
    
    privacy_agreement = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I agree to the privacy policy and terms of service',
        help_text='Required: Please read and accept our privacy policy'
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'company', 'subject', 'message']

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message.split()) < 3:
            raise forms.ValidationError("Please provide a more detailed message (at least 3 words).")
        return message

    def clean_name(self):
        name = self.cleaned_data['name']
        if not any(char.isalpha() for char in name):
            raise forms.ValidationError("Name must contain at least one letter.")
        return name.title()  # Capitalize properly

class NewsletterForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'required': True
        }),
        help_text='Stay updated with our latest products and offers'
    )
    
    interests = forms.MultipleChoiceField(
        choices=[
            ('products', 'New Products'),
            ('prices', 'Price Updates'),
            ('seasonal', 'Seasonal Information'),
            ('recipes', 'Recipes & Tips'),
            ('wholesale', 'Wholesale Opportunities')
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text='Select your areas of interest (optional)'
    )

class QuoteRequestForm(forms.Form):
    POTATO_VARIETIES = [
        ('', 'Select Variety'),
        ('russet', 'Russet Burbank'),
        ('red', 'Red Pontiac'),
        ('yukon', 'Yukon Gold'),
        ('fingerling', 'Fingerling'),
        ('sweet', 'Sweet Potato'),
        ('mixed', 'Mixed Varieties')
    ]
    
    QUANTITY_RANGES = [
        ('', 'Select Quantity Range'),
        ('small', '1-50 kg'),
        ('medium', '51-500 kg'),
        ('large', '501-2000 kg'),
        ('bulk', '2000+ kg')
    ]
    
    company_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Company Name',
            'required': True
        })
    )
    
    contact_person = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Person Name',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'business@company.com',
            'required': True
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890',
            'required': True
        })
    )
    
    variety = forms.ChoiceField(
        choices=POTATO_VARIETIES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    quantity_range = forms.ChoiceField(
        choices=QUANTITY_RANGES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    delivery_location = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City, State/Country',
            'required': True
        })
    )
    
    delivery_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        }),
        help_text='Preferred delivery date'
    )
    
    additional_requirements = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Any specific requirements, packaging needs, or additional information...'
        }),
        required=False
    )