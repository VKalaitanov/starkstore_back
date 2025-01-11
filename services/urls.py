from django.urls import path

from services.views import ServiceListView, ServiceCategoryListView, ServiceOptionListView, CalculateOrderPriceView

urlpatterns = [
    path('services/', ServiceListView.as_view(), name='service-list'),
    path('services/<int:service_id>/categories/', ServiceCategoryListView.as_view(), name='service-category-list'),
    path('services/<int:service_id>/categories/<str:category>/', ServiceOptionListView.as_view(),
         name='service-option-list'),
    path('popular-services/<int:popular_service_id>/', ServiceOptionListView.as_view(), name='popular-service-detail'),
    path('calculate-price/', CalculateOrderPriceView.as_view(), name='calculate-price'),
]
