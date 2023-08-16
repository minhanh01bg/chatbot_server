from django.urls import path
from .views import (
    Images,
    Intents,                                                                                                                                                                                                            
    Question,
    Answer,
    FilesQuestionView,
    FilesAnswerView,
)

urlpatterns = [
    path('files/images',Images.as_view()),
    path('intents',Intents.as_view()),
    path('questions',Question.as_view()),
    path('answers',Answer.as_view()),
    path('files/question',FilesQuestionView.as_view()),
    path('files/answer',FilesAnswerView.as_view()),
]