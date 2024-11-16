from django.urls import path

from .views import ServiceListView, ServiceCategoryListView, ServiceOptionListView

urlpatterns = [
    # path('all/', ServiceGetAllView.as_view())
    path('services/', ServiceListView.as_view(), name='service-list'),
    path('services/<int:service_id>/categories/', ServiceCategoryListView.as_view(), name='service-category-list'),
    path('services/<int:service_id>/categories/<str:category>/', ServiceOptionListView.as_view(),
         name='service-option-list'),
]
