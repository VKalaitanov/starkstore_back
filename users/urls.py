from django.urls import path
from . import views


urlpatterns = [
    path('activate/<uid>/<token>/', views.ActivateUser.as_view(), name='activation'),
    path('global-message/', views.GlobalMessageView.as_view(), name='global-message'),
    path('balance-history/', views.BalanceHistoryView.as_view(), name='balance-history'),
]
