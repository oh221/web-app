from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging

from .forms import ContactForm, NewsletterForm, QuoteRequestForm
from .models import ContactMessage, Newsletter, QuoteRequest

logger = logging.getLogger(__name__)

class HomeView(TemplateView):
    template_name = 'main/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['newsletter_form'] = NewsletterForm()
        # Add any featured products or recent news here
        return context

class AboutView(TemplateView):
    template_name = 'main/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add company statistics, team info, etc.
        context['company_stats'] = {
            'years_experience': 15,
            'satisfied_customers': 500,
            'varieties_available': 5,
            'countries_served': 10
        }
        return context

class ProductsView(TemplateView):
    template_name = 'main/products.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quote_form'] = QuoteRequestForm()
        context['products'] = [
            {
                'name': 'Russet Burbank',
                'description': 'Perfect for french fries and baking',
                'image': 'images/russet.jpg',
                'features': ['High starch content', 'Excellent for processing', 'Long storage life']
            },
            {
                'name': 'Red Pontiac',
                'description': 'Ideal for boiling and salads',
                'image': 'images/red.jpg',
                'features': ['Thin red skin', 'Waxy texture', 'Great for roasting']
            },
            {
                'name': 'Yukon Gold',
                'description': 'Versatile all-purpose potato',
                'image': 'images/yukon.jpg',
                'features': ['Buttery flavor', 'Medium starch', 'Perfect for mashing']
            },
            {
                'name': 'Fingerling',
                'description': 'Gourmet variety with unique shape',
                'image': 'images/fingerling.jpg',
                'features': ['Premium quality', 'Multiple colors', 'Restaurant favorite']
            },
            {
                'name': 'Sweet Potato',
                'description': 'Nutritious and delicious',
                'image': 'images/sweet.jpg',
                'features': ['High in vitamins', 'Natural sweetness', 'Versatile cooking']
            }
        ]
        return context

class ContactView(View):
    template_name = 'main/contact.html'
    
    def get(self, request):
        form = ContactForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                # Save the contact message
                contact_message = form.save()
                
                # Send notification email to admin (optional)
                try:
                    send_mail(
                        subject=f'New Contact Form Submission: {contact_message.get_subject_display()}',
                        message=f'''
                        New contact form submission received:
                        
                        Name: {contact_message.name}
                        Email: {contact_message.email}
                        Company: {contact_message.company or 'Not provided'}
                        Subject: {contact_message.get_subject_display()}
                        
                        Message:
                        {contact_message.message}
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else ['admin@potatocompany.com'],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification email: {e}")
                
                messages.success(
                    request, 
                    'Thank you for your message! We\'ll get back to you within 24 hours.'
                )
                return redirect('contact')
                
            except Exception as e:
                logger.error(f"Error saving contact form: {e}")
                messages.error(
                    request, 
                    'Sorry, there was an error processing your message. Please try again.'
                )
        else:
            messages.error(
                request, 
                'Please correct the errors below and try again.'
            )
        
        return render(request, self.template_name, {'form': form})

class QuoteRequestView(View):
    def post(self, request):
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            try:
                quote_request = QuoteRequest.objects.create(**form.cleaned_data)
                
                # Send confirmation email to customer
                try:
                    send_mail(
                        subject='Quote Request Received - Potato Company',
                        message=f'''
                        Dear {quote_request.contact_person},
                        
                        Thank you for your quote request. We have received your inquiry for {quote_request.get_variety_display()} potatoes.
                        
                        Request Details:
                        - Company: {quote_request.company_name}
                        - Variety: {quote_request.get_variety_display()}
                        - Quantity: {quote_request.get_quantity_range_display()}
                        - Delivery Location: {quote_request.delivery_location}
                        - Preferred Delivery Date: {quote_request.delivery_date}
                        
                        Our sales team will review your request and provide a detailed quote within 2 business days.
                        
                        Best regards,
                        Potato Company Sales Team
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[quote_request.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send quote confirmation email: {e}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Quote request submitted successfully! We\'ll send you a detailed quote within 2 business days.'
                })
                
            except Exception as e:
                logger.error(f"Error saving quote request: {e}")
                return JsonResponse({
                    'success': False,
                    'message': 'Sorry, there was an error processing your request. Please try again.'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please correct the form errors and try again.',
                'errors': form.errors
            })

@method_decorator(csrf_exempt, name='dispatch')
class NewsletterSignupView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            form = NewsletterForm(data)
            
            if form.is_valid():
                email = form.cleaned_data['email']
                interests = form.cleaned_data['interests']
                
                newsletter, created = Newsletter.objects.get_or_create(
                    email=email,
                    defaults={'interests': interests, 'is_active': True}
                )
                
                if not created:
                    # Update existing subscription
                    newsletter.interests = interests
                    newsletter.is_active = True
                    newsletter.save()
                    message = 'Your newsletter preferences have been updated!'
                else:
                    message = 'Thank you for subscribing to our newsletter!'
                
                # Send welcome email
                try:
                    send_mail(
                        subject='Welcome to Potato Company Newsletter',
                        message=f'''
                        Welcome to the Potato Company newsletter!
                        
                        Thank you for subscribing. You'll receive updates about:
                        {', '.join(interests) if interests else 'All our latest news and products'}
                        
                        You can unsubscribe at any time by clicking the link in our emails.
                        
                        Best regards,
                        Potato Company Team
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {e}")
                
                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter a valid email address.',
                    'errors': form.errors
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format.'
            })
        except Exception as e:
            logger.error(f"Newsletter signup error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Sorry, there was an error processing your subscription.'
            })

class ServicesView(TemplateView):
    template_name = 'main/services.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = [
            {
                'title': 'Wholesale Distribution',
                'description': 'Large volume orders for restaurants, grocery chains, and food processors',
                'icon': 'truck',
                'features': ['Bulk pricing', 'Reliable delivery', 'Quality assurance']
            },
            {
                'title': 'Custom Packaging',
                'description': 'Tailored packaging solutions for your brand requirements',
                'icon': 'package',
                'features': ['Private labeling', 'Various sizes', 'Sustainable options']
            },
            {
                'title': 'Quality Control',
                'description': 'Rigorous testing and grading to ensure premium quality',
                'icon': 'shield-check',
                'features': ['Grade A certification', 'Regular inspections', 'Traceability']
            },
            {
                'title': 'Logistics Support',
                'description': 'End-to-end supply chain management and delivery',
                'icon': 'globe',
                'features': ['Cold storage', 'Freight coordination', 'International shipping']
            }
        ]
        return context

# Function-based views for backwards compatibility
def home(request):
    return HomeView.as_view()(request)

def about(request):
    return AboutView.as_view()(request)

def products(request):
    return ProductsView.as_view()(request)

def services(request):
    return ServicesView.as_view()(request)