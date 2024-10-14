from django.urls import path
from attendance import views

urlpatterns = [
    path('sessions/', views.session_list, name='session_list'),
    path('session/<int:session_id>/attendance/', views.take_attendance, name='take_attendance'),
]
