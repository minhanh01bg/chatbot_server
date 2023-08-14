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
from .forms import ImageUploadForm
from .models import Image, QuestionForChatbot, AnswerForChatbot, Intent
from .serializers import ImageSerializer, QuestionForChatbotSerializer, AnswerForChatbotSerializer, IntentSerializer
ALLOW_FILE_TYPES = ['jpg', 'jpeg', 'png']

class Images(APIView):
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
                if file_type.lower() not in ALLOW_FILE_TYPES:
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
