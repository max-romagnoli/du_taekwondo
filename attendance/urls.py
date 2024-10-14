from django.urls import path
from attendance import views

urlpatterns = [
    path('session/<int:session_id>/attendance/', views.take_attendance, name='take_attendance'),
]
