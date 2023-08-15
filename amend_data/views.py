from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
import numpy as np
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from .forms import ImageUploadForm, FilesQuestionUploadForm, FilesAnswerUploadForm
from .models import Image, QuestionForChatbot, AnswerForChatbot, Intent, FilesQuestion, FilesAnswer
from .serializers import ImageSerializer, QuestionForChatbotSerializer, AnswerForChatbotSerializer, IntentSerializer
ALLOW_FILE_TYPES_IMAGE = ['jpg', 'jpeg', 'png']
ALLOW_FILE_TYPES_QUESTION = ['csv']
ALLOW_FILE_TYPES_ANSWER = ['csv']
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
            intent_name = request.POST.get('intent_name').strip().lower()
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


class Question(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Create new question...',
                         manual_parameters=[openapi.Parameter(
                             name="intent_name",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="intent name"
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

class Answer(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Create new answer...',
                         manual_parameters=[openapi.Parameter(
                             name="intent_name",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="intent name"
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
        
class FilesQuestionView(APIView):
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Upload attack file...',
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
                if file_type.lower() not in ALLOW_FILE_TYPES_QUESTION:
                    return Response({'error': 'File type not supported.'}, status=status.HTTP_400_BAD_REQUEST)
                filesQuestion = FilesQuestion(filesQuestion=file)
                filesQuestion.save()
                # 
                return Response({'success': 'File uploaded successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid form.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all files question...')
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            filesQuestion = FilesQuestion.objects.all()
            return Response(filesQuestion.data, status=status.HTTP_200_OK)
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
                # 
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
            return Response(filesAnswer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        