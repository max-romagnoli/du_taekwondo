from django.urls import path
from attendance import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('sessions/', views.session_list, name='session_list'),
    path('session/<int:session_id>/attendance/', views.take_attendance, name='take_attendance'),
    path('reminders/', views.reminders, name='payment_reminders'),
    path('reminders/setup/<int:month_period_id>/', views.email_setup, name='email_setup'),
    path('reminders/preview/<int:month_period_id>/', views.email_preview, name='email_preview'),
    path('payment-entry/', views.month_list, name='payment_entry'),
    path('payment-entry/<int:month_period_id>/', views.member_payment_entry, name='member_payment_entry'),
]
