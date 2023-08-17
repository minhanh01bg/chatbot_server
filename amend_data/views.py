from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from django.http import FileResponse
import numpy as np
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from .forms import ImageUploadForm, FilesQuestionUploadForm, FilesAnswerUploadForm
from .models import Image, QuestionForChatbot, AnswerForChatbot, Intent, FilesQuestion, FilesAnswer, Out_of_scope
from .serializers import ImageSerializer, QuestionForChatbotSerializer, AnswerForChatbotSerializer, IntentSerializer, FilesAnswerSerializer, FilesQuestionSerializer, OutOfScopeSerializer
from django.utils.encoding import smart_str

import pandas as pd
import numpy as np
import re
import string

ALLOW_FILE_TYPES_IMAGE = ['jpg', 'jpeg', 'png']
ALLOW_FILE_TYPES_QUESTION = ['csv']
ALLOW_FILE_TYPES_ANSWER = ['csv']

def remove_diacritics(input_str):
        # Các ký tự có dấu và ký tự không dấu tương ứng
        diacritics = "áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
        nondiacritics = "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"

        # Loại bỏ dấu bằng cách thay thế các ký tự có dấu bằng ký tự không dấu tương ứng
        return re.sub('[' + diacritics + ']', lambda x: nondiacritics[diacritics.index(x.group(0))], input_str)
class Images(APIView):
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(operation_description='Upload images file...',
                         manual_parameters=[openapi.Parameter(
                             name="file",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_FILE,
                             required=True,
                             description="files"
                         )])
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'file' not in request.FILES:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            file = request.FILES['file']
            if file.size > 100000000:
                return Response(status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                file_type = file.name.split('.')[-1]
                if file_type.lower() not in ALLOW_FILE_TYPES_IMAGE:
                    return Response({'error': 'File type not supported.'}, status=status.HTTP_400_BAD_REQUEST)
                image = Image(Image=file)
                image.save()
                return Response({'success': 'File uploaded successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid form.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all images...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            images = ImageSerializer(Image.objects.all(), many=True)
            return Response(images.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    
class Intents(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all intents...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            intents = IntentSerializer(Intent.objects.all(), many=True)
            return Response(intents.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Create new intent...',
                         manual_parameters=[openapi.Parameter(
                             name="intent_name",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="intent name"
                         )])
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            intent_name = remove_diacritics(request.POST.get('intent_name').strip().lower()).replace(' ', '_')
            if intent_name is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            intent = Intent.objects.filter(intent_name=intent_name)
            if len(intent) > 0:
                return Response({'error': 'Intent already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                intent = Intent(intent_name=intent_name)
                intent.save()
                intent_serializer = IntentSerializer(intent)
                intent_serializer_json = intent_serializer.data
                return Response(intent_serializer_json, status=status.HTTP_200_OK)
                # return Response({'success': 'Intent created successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all intents...')
    def delete(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            intents = Intent.objects.all()
            intents.delete()
            return Response({'success': 'Delete all intents successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

class Question(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Create new question...',
                         manual_parameters=[openapi.Parameter(
                             name="intent_id",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="enter intent id"
                         ),openapi.Parameter(
                             name="question",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="question"
                         )])
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            question = request.POST.get('question')
            intent_id = request.POST.get('intent_id')
            if question is None or intent_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            intent = Intent.objects.filter(id=intent_id)
            if len(intent) == 0:
                return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                question_model = QuestionForChatbot(question=question, intent_id=intent_id)
                question_model.save()
                question_serializer = QuestionForChatbotSerializer(question_model)
                question_serializer_json = question_serializer.data
                return Response(question_serializer_json, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all questions...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            questions = QuestionForChatbotSerializer(QuestionForChatbot.objects.all(), many=True)
            return Response(questions.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all questions...')
    def delete(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            questions = QuestionForChatbot.objects.all()
            questions.delete()
            return Response({'success': 'Delete all questions successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class Answer(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Create new answer...',
                         manual_parameters=[openapi.Parameter(
                             name="intent_id",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="enter intent id"
                         ),openapi.Parameter(
                             name="answer",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="enter answer"
                         )])
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            answer = request.POST.get('answer')
            intent_id = request.POST.get('intent_id')
            if answer is None or intent_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            intent = Intent.objects.filter(id=intent_id)
            if len(intent) == 0:
                return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                answer_model = AnswerForChatbot(answer=answer, intent_id=intent_id)
                answer_model.save()
                answer_serializer = AnswerForChatbotSerializer(answer_model)
                answer_serializer_json = answer_serializer.data
                return Response(answer_serializer_json, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all answers...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            answers = AnswerForChatbotSerializer(AnswerForChatbot.objects.all(), many=True)
            return Response(answers.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all awswers...')
    def delete(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            answers = AnswerForChatbot.objects.all()
            answers.delete()
            return Response({'success': 'Delete all answers successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
       
class FilesQuestionView(APIView):
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Upload question file...',
                         manual_parameters=[openapi.Parameter(
                             name="file",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_FILE,
                             required=True,
                             description="files"
                         )])
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'file' not in request.FILES:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            file = request.FILES['file']
            if file.size > 10000000:
                return Response(status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                file_type = file.name.split('.')[-1]
                if file_type.lower() not in ALLOW_FILE_TYPES_QUESTION:
                    return Response({'error': 'File type not supported.'}, status=status.HTTP_400_BAD_REQUEST)
                filesQuestion = FilesQuestion(filesQuestion=file)
                filesQuestion.save()
                filesQuestionSerializer = FilesQuestionSerializer(filesQuestion)
                filesQuestionSerializerJson = filesQuestionSerializer.data
                print(filesQuestionSerializerJson)
                
                filename = filesQuestionSerializerJson['filesQuestion']
                print(filename)
                cnt = 0
                data_raw = pd.read_csv('.'+filename)
                for i in range(data_raw.shape[0]):
                    question = data_raw['question'][i]
                    intent_name = remove_diacritics(data_raw['topic'][i].lower().strip()).replace(' ', '_')
                    intent = Intent.objects.filter(intent_name=intent_name)
                    if len(intent) == 0:
                        
                        # check duplicated question
                        question_list = QuestionForChatbot.objects.filter(question=question)
                        if len(question_list) > 0:
                            cnt += 1
                            continue
                        intent = Intent(intent_name=intent_name)
                        intent.save()
                        intentSerializer = IntentSerializer(intent)
                        print('Intent id: ', intentSerializer.data['id'])
                        
                        question_model = QuestionForChatbot(question=question, intent_id=intent)
                        question_model.save()
                    else:
                        
                        # check duplicated question
                        question_list = QuestionForChatbot.objects.filter(question=question)
                        if len(question_list) > 0:
                            cnt += 1
                            continue
                        intent = intent[0]
                        intentSerializer = IntentSerializer(intent)
                        intentSerializer.data['id']
                        question_model = QuestionForChatbot(question=question, intent_id=intent)
                        question_model.save()
                
                questions_list = QuestionForChatbot.objects.all()
                questions_list_serializer = QuestionForChatbotSerializer(questions_list, many=True)
                
                intent_list = Intent.objects.all()
                intent_list_serializer = IntentSerializer(intent_list, many=True)
                #  convert to csv 
                df_intent = pd.DataFrame(intent_list_serializer.data)
                df_question = pd.DataFrame(questions_list_serializer.data)
                
                intent_id_to_name = dict(zip(df_intent['id'], df_intent['intent_name']))
                df_question['intent_id'] = df_question['intent_id'].map(intent_id_to_name)
                # print(df_question.head())
                df_question.rename(columns={'question': 'question','intent_id': 'topic'}, inplace=True)
                
                data_raw = df_question[['question', 'topic']]
                
                print('# Drop nan')
                print('  - Before: ',data_raw.shape)
                data_raw.dropna(inplace=True)
                data_raw.drop_duplicates(inplace=True)
                print('  - After: ',data_raw.shape)
                
                print('# Remove Number with regex')
                print('# Drop numbers in columns question of data_raw')
                data_raw['question'] = data_raw['question'].apply(lambda x:re.sub(r'\d+','',x))
                
                print('# Remove Punctuation')
                punctuation = string.punctuation
                data_raw['question'] = data_raw['question'].apply(lambda x: x.translate(str.maketrans('', '', punctuation)))
                
                print('# Remove whitespace')
                data_raw['question'] = data_raw['question'].apply(lambda x: re.sub(r'\s+', ' ', x, flags=re.I))
                
                print('# Remove emoji')
                emoj = re.compile("["
                        u"\U0001F600-\U0001F64F"  # emoticons
                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        u"\U00002500-\U00002BEF"  # chinese char
                        u"\U00002702-\U000027B0"
                        u"\U00002702-\U000027B0"
                        u"\U000024C2-\U0001F251"
                        u"\U0001f926-\U0001f937"
                        u"\U00010000-\U0010ffff"
                        u"\u2640-\u2642" 
                        u"\u2600-\u2B55"
                        u"\u200d"
                        u"\u23cf"
                        u"\u23e9"
                        u"\u231a"
                        u"\ufe0f"  # dingbats
                        u"\u3030"
                                    "]+", re.UNICODE)

                data_raw['question'] = data_raw['question'].apply(lambda x: re.sub(emoj, '', x))
                
                print('# Remove non ascii')
                print('# Remove character #x009f')
                data_raw['question'] = data_raw['question'].apply(lambda x: re.sub(r'[\x00-\x1F\x7F-\x9F]', '', x))
                
                list = data_raw['topic'].unique()
                with open('./media/nlu_data/nlu.yml', 'w') as f:
                    f.write('version: "3.1"\n\n')
                    f.write('nlu:\n')
                    for i in range(len(list)):
                        name_intent = remove_diacritics(list[i].lower()).replace(' ', '_')
                        f.write('- intent: ' + name_intent + '\n')
                        f.write('  examples: |\n')
                        for j in range(data_raw.shape[0]):
                            if data_raw['topic'][j] == list[i]:
                                f.write('    - ' + data_raw['question'][j] + '\n')
                                
                

                file_path = './media/nlu_data/nlu.yml'
                file_name = 'nlu.yml'

                response = FileResponse(open(file_path, 'rb'), content_type='application/force-download')
                response['Content-Disposition'] = f'attachment; filename={smart_str(file_name)}'

                return response
                # return Response({'success': 'File uploaded successfully.', 'duplicated':cnt}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid form.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all files question...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            filesQuestion = FilesQuestion.objects.all()
            filesQuestionSerializer = FilesQuestionSerializer(filesQuestion, many=True)
            return Response(filesQuestionSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all files question...')
    def delete(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            filesQuestion = FilesQuestion.objects.all()
            filesQuestion.delete()
            return Response({'success': 'Delete all files question successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
class FilesAnswerView(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Upload answer file...',
                         manual_parameters=[openapi.Parameter(
                             name="file",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_FILE,
                             required=True,
                             description="files"
                         )])
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'file' not in request.FILES:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            file = request.FILES['file']
            if file.size > 100000000:
                return Response(status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        
            form = FilesAnswerUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                file_type = file.name.split('.')[-1]
                if file_type.lower() not in ALLOW_FILE_TYPES_ANSWER:
                    return Response({'error': 'File type not supported.'}, status=status.HTTP_400_BAD_REQUEST)
                filesAnswer = FilesAnswer(filesAnswer=file)
                filesAnswer.save()
                filesAnswerSerializer = FilesAnswerSerializer(filesAnswer)
                filesAnswerSerializerJson = filesAnswerSerializer.data
                print(filesAnswerSerializerJson)
                filename = filesAnswerSerializerJson['filesAnswer']
                print(filename)
                
                data_raw = pd.read_csv('.'+filename)
                for i in range(data_raw.shape[0]):
                    answer = data_raw['answer'][i]
                    intent_name = remove_diacritics(data_raw['topic'][i].lower().strip()).replace(' ', '_')
                    intent = Intent.objects.filter(intent_name=intent_name)
                    if len(intent) == 0:
                        intent = Intent(intent_name=intent_name)
                        intent.save()
                        intentSerializer = IntentSerializer(intent)
                        print('Intent id: ', intentSerializer.data['id'])
                        answer_model = AnswerForChatbot(answer=answer, intent_id=intent)
                        answer_model.save()
                    else:
                        intent = intent[0]
                        intentSerializer = IntentSerializer(intent)
                        intentSerializer.data['id']
                        answer_model = AnswerForChatbot(answer=answer, intent_id=intent)
                        answer_model.save()
                
                return Response({'success': 'File uploaded successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid form.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all files answer...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            filesAnswer = FilesAnswer.objects.all()
            filesAnswerSerializer = FilesAnswerSerializer(filesAnswer, many=True)
            return Response(filesAnswerSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all files answer...')
    def delete(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            filesAnswer = FilesAnswer.objects.all()
            filesAnswer.delete()
            return Response({'success': 'Delete all files answer successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)


class OutOfScopeView(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all out of scope...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            outOfScope = Out_of_scope.objects.all()
            outOfScopeSerializer = OutOfScopeSerializer(outOfScope, many=True)
            return Response(outOfScopeSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Fill new outOfScope...',
                         manual_parameters=[openapi.Parameter(
                             name="outOfScope",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="outOfScope"
                         )])
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            outOfScope = request.POST.get('outOfScope')
            if outOfScope is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                out = Out_of_scope.objects.filter(out_of_scope=outOfScope)
                if len(out) > 0:
                    return Response({'error': 'Out of scope already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                # save
                new_outOfScope = Out_of_scope(out_of_scope=outOfScope)
                new_outOfScope.save()
                return Response({'success': 'Out of scope created successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all out of scope...')
    def delete(self, request, *args, **kwargs):
        if request.method == 'DELETE':
            Out_of_scope.objects.all().delete()
            return Response({'success': 'Delete all out of scope successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
class ExportAll(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Export all data...')
    def get(self, request, *agrs, **kwargs):
        questions_list = QuestionForChatbot.objects.all()
        questions_list_serializer = QuestionForChatbotSerializer(questions_list, many=True)
        
        intent_list = Intent.objects.all()
        intent_list_serializer = IntentSerializer(intent_list, many=True)

        #  convert to csv 
        df_intent = pd.DataFrame(intent_list_serializer.data)
        df_question = pd.DataFrame(questions_list_serializer.data)
        # map intent id
        intent_id_to_name = dict(zip(df_intent['id'], df_intent['intent_name']))
        print('------------------')
        print(intent_id_to_name)
        print('------------------')
        df_question['intent_id'] = df_question['intent_id'].map(intent_id_to_name)
        
        # print(df_question.head())
        df_question.rename(columns={'question': 'question','intent_id': 'topic'}, inplace=True)
        
        outOfScope = Out_of_scope.objects.all()
        outOfScopeSerializer = OutOfScopeSerializer(outOfScope, many=True)
        df_outOfScope = pd.DataFrame(outOfScopeSerializer.data)
        df_outOfScope.rename(columns={'out_of_scope': 'question'}, inplace=True)
        new_column = np.full(df_outOfScope.shape[0],'out_of_scope')
        df_outOfScope['topic'] = new_column
        
        df_outOfScope = df_outOfScope[['question', 'topic']]        
        print(df_outOfScope.head())
        data_raw = df_question[['question', 'topic']]
        data_raw = pd.concat([data_raw, df_outOfScope], ignore_index=True)
        print('# Drop nan')
        print('  - Before: ',data_raw.shape)
        data_raw.dropna(inplace=True)
        data_raw.drop_duplicates(inplace=True)
        print('  - After: ',data_raw.shape)
        
        print('# Remove Number with regex')
        print('# Drop numbers in columns question of data_raw')
        data_raw['question'] = data_raw['question'].apply(lambda x:re.sub(r'\d+','',x))
        
        print('# Remove Punctuation')
        punctuation = string.punctuation
        data_raw['question'] = data_raw['question'].apply(lambda x: x.translate(str.maketrans('', '', punctuation)))
        
        print('# Remove whitespace')
        data_raw['question'] = data_raw['question'].apply(lambda x: re.sub(r'\s+', ' ', x, flags=re.I))
        
        print('# Remove emoji')
        emoj = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                u"\U00002500-\U00002BEF"  # chinese char
                u"\U00002702-\U000027B0"
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                u"\U0001f926-\U0001f937"
                u"\U00010000-\U0010ffff"
                u"\u2640-\u2642" 
                u"\u2600-\u2B55"
                u"\u200d"
                u"\u23cf"
                u"\u23e9"
                u"\u231a"
                u"\ufe0f"  # dingbats
                u"\u3030"
                            "]+", re.UNICODE)

        data_raw['question'] = data_raw['question'].apply(lambda x: re.sub(emoj, '', x))
        
        print('# Remove non ascii')
        print('# Remove character #x009f')
        data_raw['question'] = data_raw['question'].apply(lambda x: re.sub(r'[\x00-\x1F\x7F-\x9F]', '', x))
        
        list = data_raw['topic'].unique()
        with open('./media/nlu_data/nlu.yml', 'w') as f:
            f.write('version: "3.1"\n\n')
            f.write('nlu:\n')
            for i in range(len(list)):
                name_intent = remove_diacritics(list[i].lower()).replace(' ', '_')
                f.write('- intent: ' + name_intent + '\n')
                f.write('  examples: |\n')
                for j in range(data_raw.shape[0]):
                    if data_raw['topic'][j] == list[i]:
                        f.write('    - ' + data_raw['question'][j] + '\n')
        
        

        file_path = './media/nlu_data/nlu.yml'
        file_name = 'nlu.yml'

        response = FileResponse(open(file_path, 'rb'), content_type='application/force-download')
        response['Content-Disposition'] = f'attachment; filename={smart_str(file_name)}'

        return response


