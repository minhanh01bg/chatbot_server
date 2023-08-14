from rest_framework import serializers
from .models import QuestionForChatbot, AnswerForChatbot, Intent, Image

class QuestionForChatbotSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionForChatbot
        fields = ('id', 'question', 'intent_id')
        

class AnswerForChatbotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerForChatbot
        fields = ('id', 'answer', 'intent_id')
        
class IntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intent
        fields = ('id', 'intent_name')
        
class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'Image')