from django.urls import path
from monitoring import consumers

websocket_urlpatterns = [
    path('ws/posture/', consumers.PostureConsumer.as_asgi()),
]