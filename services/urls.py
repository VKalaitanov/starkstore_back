from django.urls import path
from . import views

urlpatterns = [
    path('services/', views.ServiceListView.as_view(), name='service-list'),
    path('services/<int:service_id>/categories/', views.ServiceCategoryListView.as_view(), name='service-category-list'),
    path('services/<int:service_id>/categories/<str:category>/', views.ServiceOptionListView.as_view(),
         name='service-option-list'),
    path('popular-services/', views.PopularServiceOptionListView.as_view(), name='popular-service-detail'),
    path('calculate-price/', views.CalculateOrderPriceView.as_view(), name='calculate-price'),
]
