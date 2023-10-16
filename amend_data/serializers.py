from rest_framework import serializers
from .models import QuestionForChatbot, AnswerForChatbot, Intent, Image,FilesAnswer, FilesQuestion, Out_of_scope, FileConvert
from django.contrib.auth.models import User
from .models import ModelRasa
from django.contrib.auth.models import Group
from .models import SortAnswer
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
        fields = ('id', 'intent_name','intent_detail', 'created_at', 'updated_at')
        
class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'Image','intent_id', 'created_at', 'updated_at')
        
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
        
class FileConvertSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FileConvert
        fields = ('id','file_convert','created_at','updated_at')
        
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id','username','password','email','first_name','last_name','is_staff','is_active','is_superuser','last_login','date_joined')
        
class ModelRasaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelRasa
        fields = ('id','model_name','isActivate','created_at','updated_at')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id','name')
        
from django.contrib.auth.models import Permission
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id','name','content_type_id','codename')
        
class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','email','first_name','last_name','is_staff','is_active','is_superuser','last_login','date_joined')
        
        
class SortAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SortAnswer
        fields = ('id','intent_id','type_answer','id_answer','sort','created_at','updated_at')