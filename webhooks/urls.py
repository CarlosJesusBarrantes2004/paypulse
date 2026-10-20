from django.urls import path
from webhooks.views import ReceiverWebhookView

urlpatterns = [
    path("pasarela/", ReceiverWebhookView.as_view(), name="webhook_receiver")
]
