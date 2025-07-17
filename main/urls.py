from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # Main pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('products/', views.ProductsView.as_view(), name='products'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # AJAX endpoints
    path('api/quote-request/', views.QuoteRequestView.as_view(), name='quote_request'),
    path('api/newsletter-signup/', views.NewsletterSignupView.as_view(), name='newsletter_signup'),
]