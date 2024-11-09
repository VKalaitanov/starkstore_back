from django.urls import path
from . import views


urlpatterns = [
    path('activate/<uid>/<token>/', views.ActivateUser.as_view({'get': 'activation'}), name='activation')
]
