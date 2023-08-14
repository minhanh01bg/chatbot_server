from django.urls import path
from .views import (
    Images,
    Intents,                                                                                                                                                                                                            
    Question,
)

urlpatterns = [
    path('images',Images.as_view()),
    path('intents',Intents.as_view()),
    path('questions',Question.as_view()),
]