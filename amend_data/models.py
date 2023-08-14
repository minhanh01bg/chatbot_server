from django.db import models

# Create your models here.

class Image(models.Model):
    Image = models.FileField(upload_to='images')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'images'

class QuestionForChatbot(models.Model):
    question = models.CharField(max_length=1000)
    intent_id = models.ForeignKey('Intent', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'questions_for_chatbot'

class AnswerForChatbot(models.Model):
    answer = models.CharField(max_length=1000)
    # intent_id foreign key
    intent_id = models.ForeignKey('Intent', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'answers_for_chatbot'

class Intent(models.Model):
    intent_name = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'intents'
        