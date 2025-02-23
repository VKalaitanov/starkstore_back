from django.urls import path
from . import views

urlpatterns = [
    path('activate/<uid>/<token>/', views.ActivateUser.as_view(), name='activation'),
    path('confirm-email-change/', views.ConfirmEmailChangeView.as_view(), name='confirm-email-change'),
    path('global-message/', views.GlobalMessageView.as_view(), name='global-message'),
    path('balance-history/', views.BalanceHistoryView.as_view(), name='balance-history'),
    path('info-message/', views.InfoMessageView.as_view(), name='info-message'),
    path('top-up/', views.CreateTopUpView.as_view(), name='top_up'),
    path('plisio-webhook/', views.PlisioWebhookView.as_view(), name='plisio_webhook'),
    path('request-password-reset/', views.RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('reset-password/<str:uid>/<str:token>/', views.ResetPasswordView.as_view(), name='reset-password'),
]
