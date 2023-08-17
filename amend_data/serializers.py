from rest_framework import serializers
from .models import QuestionForChatbot, AnswerForChatbot, Intent, Image,FilesAnswer, FilesQuestion, Out_of_scope

class QuestionForChatbotSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionForChatbot
        fields = ('id', 'question', 'intent_id', 'created_at', 'updated_at')
        

class AnswerForChatbotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerForChatbot
        fields = ('id', 'answer', 'intent_id', 'created_at', 'updated_at')
        
class IntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intent
        fields = ('id', 'intent_name', 'created_at', 'updated_at')
        
class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'Image', 'created_at', 'updated_at')
        
class FilesAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilesAnswer
        fields = ('id','filesAnswer','created_at','updated_at')

class FilesQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilesQuestion
        fields = ('id','filesQuestion','created_at','updated_at')
        
        
class OutOfScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Out_of_scope
        fields = ('id','out_of_scope','created_at','updated_at')