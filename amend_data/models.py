from django.db import models

# Create your models here.

class Image(models.Model):
    intent_id = models.ForeignKey('Intent', on_delete=models.CASCADE)
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
    intent_name = models.CharField(max_length=1000,unique=True)
    intent_detail = models.CharField(max_length=1000, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'intents'

class FilesQuestion(models.Model):
    filesQuestion = models.FileField(upload_to='questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'FilesQuestion'
        
class FilesAnswer(models.Model):
    filesAnswer = models.FileField(upload_to='answers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'FilesAnswer'


class Synonyms(models.Model):
    synonym_primary = models.CharField(max_length=1000)
    synonym = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sysnonyms'
        
class Out_of_scope(models.Model):
    out_of_scope = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'out_of_scope'
        
class FileConvert(models.Model):
    file_convert = models.FileField(upload_to='file_convert')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'file_convert'
        
        
class ModelRasa(models.Model):
    model_name = models.CharField(max_length=1000)
    isActivate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'name_model_rasa'

class SortAnswer(models.Model):
    
    intent_id = models.ForeignKey('Intent', on_delete=models.CASCADE)
    type_answer = models.CharField(max_length=1000)
    id_answer = models.IntegerField()
    sort = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sort_answer'
        