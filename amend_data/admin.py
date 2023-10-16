from django.contrib import admin
from .models import Image, QuestionForChatbot, AnswerForChatbot, Intent, FilesQuestion, FilesAnswer, Synonyms,ModelRasa
from .models import Out_of_scope
# Register your models here.

admin.site.register(Image)
admin.site.register(QuestionForChatbot)
admin.site.register(AnswerForChatbot)
admin.site.register(Intent)
admin.site.register(FilesQuestion)
admin.site.register(FilesAnswer)
admin.site.register(Synonyms)
admin.site.register(ModelRasa)
admin.site.register(Out_of_scope)

