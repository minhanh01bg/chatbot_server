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
from .models import Image, QuestionForChatbot, AnswerForChatbot, Intent, FilesQuestion, FilesAnswer, Out_of_scope, FileConvert
from .models import ModelRasa
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from .serializers import ImageSerializer, QuestionForChatbotSerializer, AnswerForChatbotSerializer, IntentSerializer, FilesAnswerSerializer, FilesQuestionSerializer, OutOfScopeSerializer, FileConvertSerializer
from .serializers import UserSerializer, UserInfoSerializer
from .serializers import ModelRasaSerializer, GroupSerializer, PermissionSerializer
from django.contrib.auth.models import Permission, ContentType, Group, PermissionManager,GroupManager

from django.utils.encoding import smart_str
from django.contrib.auth import authenticate, login, logout

from django.middleware.csrf import get_token
from rest_framework.authtoken.models import Token
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import pandas as pd
import numpy as np
import re
import string
import subprocess
import shutil
import datetime
import os

from django.views.decorators.csrf import csrf_exempt

from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import permission_required

from .models import SortAnswer
from .serializers import SortAnswerSerializer

import socket
import time, datetime

ALLOW_FILE_TYPES_IMAGE = ['jpg', 'jpeg', 'png']
ALLOW_FILE_TYPES_QUESTION = ['csv','xlsx']
ALLOW_FILE_TYPES_ANSWER = ['csv','xlsx']

# def remove_diacritics(input_str):
#         # Các ký tự có dấu và ký tự không dấu tương ứng
#         diacritics = "áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ"
#         nondiacritics = "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd"

#         # Loại bỏ dấu bằng cách thay thế các ký tự có dấu bằng ký tự không dấu tương ứng
#         return re.sub('[' + diacritics + ']', lambda x: nondiacritics[diacritics.index(x.group(0))], input_str)
from unidecode import unidecode

def remove_diacritics(input_str):
    # Sử dụng unidecode để loại bỏ dấu và chuẩn hóa chuỗi
    return unidecode(input_str).replace(' ', '_')

from django.views import View

from django.conf import settings

class Images(APIView):
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False

    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Upload images file...',
                         manual_parameters=[openapi.Parameter(
                             name="file",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_FILE,
                             required=True,
                             description="files"
                         ),
                         openapi.Parameter(
                                name="intent_id",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="intent id"
                            ),openapi.Parameter(
                                name="sort_answer",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="sort_answer"
                            )])
    def post(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",7) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
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
                intent_id = request.POST.get('intent_id')
                sort_answer = request.POST.get('sort_answer')
                if intent_id is None or sort_answer is None:
                    return Response({'error': 'Not value is required.'}, status=status.HTTP_400_BAD_REQUEST)
                intent = Intent.objects.filter(id=intent_id)
                if len(intent) == 0:
                    return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                
                intent = intent[0]
                image = Image(Image=file,intent_id=intent)
                sort_ = SortAnswer.objects.filter(intent_id=intent_id,sort=sort_answer)
                if len(sort_) > 0:
                    return Response({'error': 'Sort answer already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                image.save()
                sort_answer = SortAnswer(intent_id=intent,type_answer='image',id_answer=image.id,sort=sort_answer)
                sort_answer.save()
                imageSerializer = ImageSerializer(image)
                imageSerializerJson = imageSerializer.data
                return Response(imageSerializerJson, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid form.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all images...',
                         manual_parameters=[openapi.Parameter(
                             name="page",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_INTEGER,
                             required=True,
                             description="page"
                         ),
                         openapi.Parameter(
                                name="size",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="size"
                            )])
    def get(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",7) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if self.check_permissions_(request,'view_image'):
            page = request.GET.get('page')
            size = request.GET.get('size')
            # size = int(size)
            # page = int(page)

            images = Image.objects.all()
            paginator = Paginator(images, size)
            
            try:
                images_data = paginator.page(page)
            except PageNotAnInteger:
                return Response({'error': 'Page is not an integer.'}, status=status.HTTP_400_BAD_REQUEST)
            totalelement = paginator.count
            curentpage = page
            images = ImageSerializer(images_data, many=True)
            intent = IntentSerializer(Intent.objects.all(), many=True)
            intent_name = dict(zip([i['id'] for i in intent.data], [i['intent_name'] for i in intent.data]))
            for i in images.data:
                i['intent_name'] = intent_name[i['intent_id']]
            
            extra_data = {
                'total_element': totalelement,
                'curent_page': curentpage
            }
            response_data = {
                'results': images.data,
                **extra_data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete images...',
                            manual_parameters=[openapi.Parameter(
                                name="id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=False,
                                description="delete by id of image"
                            )])
    def delete(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",7) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'DELETE':
            id = request.GET.get('id')
            if id is not None:
                images = Image.objects.filter(id=id)
                
                if len(images) == 0:
                    return Response({'error': 'Image does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    images = images[0] 
                    print(images.Image.path)
                    try:
                        os.remove(images.Image.path)
                    except:
                        pass
                    sort_answer = SortAnswer.objects.filter(id_answer=id)
                    if len(sort_answer) > 0:
                        sort_answer = sort_answer[0]
                        sort_answer.delete()
                    images.delete()
                    return Response({'success': 'Delete image successfully.'}, status=status.HTTP_200_OK)
            else:
                images = Image.objects.all()
                sort_answer = SortAnswer.objects.filter(type_answer='image')
                if len(sort_answer) > 0:
                    sort_answer.delete()
                images.delete()
                return Response({'success': 'Delete all images successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)


class Intents(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get intents...',
                         manual_parameters=[openapi.Parameter(
                            name="page",
                            in_=openapi.IN_QUERY,
                            type=openapi.TYPE_STRING,
                            required=False,
                            description="page"
                        ),openapi.Parameter(
                            name="size",
                            in_=openapi.IN_QUERY,
                            type=openapi.TYPE_STRING,
                            required=False,
                            description="size"
                        ),openapi.Parameter(
                            name="intent_id",
                            in_=openapi.IN_QUERY,
                            type=openapi.TYPE_STRING,
                            required=False,
                            description="intent_id"
                        )])
    def get(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",8) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            # print(request.user.is_superuser)   
            page = request.GET.get('page')
            size = request.GET.get('size')
            intent_id = request.GET.get('intent_id')
            if intent_id is not None:
                intent = Intent.objects.filter(id=intent_id)
                if intent is None:
                    return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                if len(intent) == 0:
                    return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                intent = intent[0]
                intent_serializer = IntentSerializer(intent)
                intent_serializer_json = intent_serializer.data
                return Response(intent_serializer_json, status=status.HTTP_200_OK)
            if page is not None and size is not None:
            
                intents = Intent.objects.all()
                paginator = Paginator(intents, size)
                
                try:
                    intents_data = paginator.page(page)
                except PageNotAnInteger:
                    return Response({'error': 'Page is not an integer.'}, status=status.HTTP_400_BAD_REQUEST)
                totalelement = paginator.count
                curentpage = page
                intents = IntentSerializer(intents_data, many=True)
                
                extra_data = {
                    'total_element': totalelement,
                    'curent_page': curentpage
                }
                response_data = {
                    'results': intents.data,
                    **extra_data
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
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
                         ),openapi.Parameter(
                             name="intent_detail",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="intent detail"
                         )])
    def post(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",8) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'POST':
            intent_name = remove_diacritics(request.POST.get('intent_name').strip().lower())
            intent_detail = request.POST.get('intent_detail')
            if intent_name is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            intent = Intent.objects.filter(intent_name=intent_name,intent_detail = intent_detail)
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
    @swagger_auto_schema(operation_description='Update intent...', manual_parameters=[
        openapi.Parameter(
            name="intent_id",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            required=True,
            description="intent id"
        ),openapi.Parameter(
            name="intent_name",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            required=True,
            description="intent name"
        ),openapi.Parameter(
            name="intent_detail",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            required=True,
            description="intent detail"
        )])
    def put(self,request, *args, **kwargs):
        if self.check_permissions_(request,"",8) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'PUT':
            intent_id = request.POST.get('intent_id')
            intent_name = remove_diacritics(request.POST.get('intent_name').strip().lower())
            intent_detail = request.POST.get('intent_detail')
            if intent_id is None or intent_name is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            intent = Intent.objects.filter(id=intent_id)
            if len(intent) == 0:
                return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                intent = intent[0]
                intent.intent_name = intent_name
                intent.intent_detail = intent_detail
                intent.save()
                intent_serializer = IntentSerializer(intent)
                intent_serializer_json = intent_serializer.data
                return Response(intent_serializer_json, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all intents...',
                         manual_parameters=[openapi.Parameter(
                                name="id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_STRING,
                                required=False,
                                description="delete by id of intent"
                         ),openapi.Parameter(
                                name="intent_name",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_STRING,
                                required=False,
                                description="delete by intent_name"
                         )])
    def delete(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",8) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'DELETE':
            id = request.GET.get('id')
            intent_name = request.GET.get('intent_name')
            if id is not None:
                intent = Intent.objects.filter(id=id)
                if len(intent) == 0:
                    return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    intent.delete()
                    return Response({'success': 'Delete intent successfully.'}, status=status.HTTP_200_OK)
            elif intent_name is not None:
                intent = Intent.objects.filter(intent_name=intent_name)
                if len(intent) == 0:
                    return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    intent.delete()
                    return Response({'success': 'Delete intent successfully.'}, status=status.HTTP_200_OK)
            else:
                intents = Intent.objects.all()
                intents.delete()
                return Response({'success': 'Delete all intents successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

class Question(APIView):
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Create new question...',
                         manual_parameters=[openapi.Parameter(
                             name="intent_id",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_INTEGER,
                             required=True,
                             description="enter intent id"
                         ),openapi.Parameter(
                             name="question",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_INTEGER,
                             required=True,
                             description="question"
                         )])
    def post(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",9) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'POST':
            question = request.POST.get('question')
            intent_id = request.POST.get('intent_id')
            if question is None or intent_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            intent = Intent.objects.filter(id=intent_id)
            if len(intent) == 0:
                return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                intent = intent[0]
                question_model = QuestionForChatbot(question=question, intent_id=intent)
                question_model.save()
                question_serializer = QuestionForChatbotSerializer(question_model)
                question_serializer_json = question_serializer.data
                return Response(question_serializer_json, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all questions...',
                         manual_parameters=[openapi.Parameter(
                             name="id",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_INTEGER,
                             required=False,
                             description="question id"
                         ),openapi.Parameter(
                             name="intent_id",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_INTEGER,
                             required=False,
                             description="intent id"
                         ),openapi.Parameter(
                             name="page",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_INTEGER,
                             required=True,
                             description="page"
                         ),openapi.Parameter(
                             name="size",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_INTEGER,
                             required=True,
                             description="size"
                         ),openapi.Parameter(
                             name="question",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_STRING,
                             required=False,
                             description="question search"
                         )])
    def get(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",9) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            page = request.GET.get('page')
            size = request.GET.get('size')
            id = request.GET.get('id')
            intent_id = request.GET.get('intent_id')
            question = request.GET.get('question')
            
            questions = QuestionForChatbot.objects.all()
            
            if intent_id is not None and question is not None:
                questions = QuestionForChatbot.objects.filter(intent_id=intent_id, question__icontains=question)
            elif id is not None:
                questions = QuestionForChatbot.objects.filter(id=id)
            
            elif intent_id is not None:
                questions = QuestionForChatbot.objects.filter(intent_id=intent_id)
            
            elif question is not None:
                questions = QuestionForChatbot.objects.filter(question__icontains=question)
        
            paginator = Paginator(questions, size)
                
            try:
                questions_data = paginator.page(page)
            except PageNotAnInteger:
                return Response({'error': 'Page is not an integer.'}, status=status.HTTP_400_BAD_REQUEST)
            totalelement = paginator.count
            curentpage = page
            questionsSe = QuestionForChatbotSerializer(questions_data, many=True)
            extra_data = {
                'total_element': totalelement,
                'curent_page': curentpage
            }
            response_data = {
                'results': questionsSe.data,
                **extra_data
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Update question...', manual_parameters=[
        openapi.Parameter(
            name="question_id",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            required=True,
            description="question id"
        ),openapi.Parameter(
            name="question",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            required=True,
            description="question name"
        )])
    def put(self,request, *args, **kwargs):
        if self.check_permissions_(request,"",9) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'PUT':
            question_id = request.POST.get('question_id')
            question_name = request.POST.get('question')
            if question_id is None or question_name is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            question = QuestionForChatbot.objects.filter(id=question_id)
            if len(question) == 0:
                return Response({'error': 'Question does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                question = question[0]
                question.question = question_name
                print('question: ',question.question)
                question.save()
                question_serializer = QuestionForChatbotSerializer(question)
                question_serializer_json = question_serializer.data
                return Response(question_serializer_json, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete questions...',
                         manual_parameters=[openapi.Parameter(
                             name="id",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_STRING,
                             required=False,
                             description="delete by id of question"
                         ),openapi.Parameter(
                             name="intent_id",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_STRING,
                             required=False,
                             description="delete by intent_id"
                         ),openapi.Parameter(
                             name="question",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_STRING,
                             required=False,
                             description="delete by question"
                         )])
    def delete(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",9) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'DELETE':
            
            id = request.GET.get('id')
            intent_id = request.GET.get('intent_id')
            question = request.GET.get('question')
            questions = QuestionForChatbot.objects.all()
            if id is not None:
                questions = QuestionForChatbot.objects.filter(id=id)
            elif intent_id is not None:
                questions = QuestionForChatbot.objects.filter(intent_id=intent_id)
            elif question is not None:
                questions = QuestionForChatbot.objects.filter(question__icontains=question)

            questions.delete()
            return Response({'success': 'Delete all questions successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class Answer(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Create new answer...',
                         manual_parameters=[openapi.Parameter(
                             name="intent_id",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_INTEGER,
                             required=True,
                             description="enter intent id"
                         ),openapi.Parameter(
                             name="answer",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="enter answer"
                         ),openapi.Parameter(
                             name="sort",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="enter sort answer"
                         )
                         ])
    def post(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",10) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'POST':
            
            answer = request.POST.get('answer')
            intent_id = request.POST.get('intent_id')
            sort = request.POST.get('sort')
            if answer is None or intent_id is None or sort is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            intent = Intent.objects.filter(id=intent_id)
            if len(intent) == 0:
                return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                intent = intent[0]
                answer_model = AnswerForChatbot(answer=answer, intent_id=intent)
                sort_ = SortAnswer.objects.filter(intent_id=intent, sort=sort)
                if len(sort_) > 0:
                    return Response({'error': 'Sort answer already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                answer_model.save()
                sort_answer = SortAnswer(intent_id=intent,type_answer='text',id_answer=answer_model.id, sort=sort)
                sort_answer.save()
                answer_serializer = AnswerForChatbotSerializer(answer_model)
                answer_serializer_json = answer_serializer.data
                return Response(answer_serializer_json, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Update answer...', manual_parameters=[
        openapi.Parameter(
            name="answer_id",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_INTEGER,
            required=True,
            description="answer id"
        ),openapi.Parameter(
            name="answer",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_STRING,
            required=True,
            description="answer"
        )])
    def put(self,request, *args, **kwargs):
        if self.check_permissions_(request,"",10) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'PUT':
            answer_id = request.POST.get('answer_id')
            answer = request.POST.get('answer')
            if answer_id is None or answer is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            answer_model = AnswerForChatbot.objects.filter(id=answer_id)
            if len(answer_model) == 0:
                return Response({'error': 'Answer does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                answer_model = answer_model[0]
                answer_model.answer = answer
                answer_model.save()
                answer_serializer = AnswerForChatbotSerializer(answer_model)
                answer_serializer_json = answer_serializer.data
                return Response(answer_serializer_json, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all answers...',
                         manual_parameters=[openapi.Parameter(
                                name="id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=False,
                                description="answer id"
                            ),openapi.Parameter(
                                name="intent_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=False,
                                description="intent id"
                            )])
    def get(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",10) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            id = request.GET.get('id')
            intent_id = request.GET.get('intent_id')
            if id is not None and intent_id is not None:
                answers = AnswerForChatbot.objects.filter(id=id, intent_id=intent_id)
                if len(answers) == 0:
                    return Response({'error': 'Answer does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                answers = AnswerForChatbotSerializer(answers, many=True)
                return Response(answers.data, status=status.HTTP_200_OK)
            elif id is not None:
                answers = AnswerForChatbot.objects.filter(id=id)
                if len(answers) == 0:
                    return Response({'error': 'Answer does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                answers = AnswerForChatbotSerializer(answers, many=True)
                sort = SortAnswer.objects.filter(id_answer=id)
                sort = SortAnswerSerializer(sort, many=True)
                sort_data = sort.data
                # print(sort_data[0])
                sort_data[0]['answer'] = answers.data
                return Response(sort_data, status=status.HTTP_200_OK)
            elif intent_id is not None:
                answers = AnswerForChatbot.objects.filter(intent_id=intent_id)
                if len(answers) == 0:
                    return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                answers = AnswerForChatbotSerializer(answers, many=True)
                # sort = SortAnswer.objects.filter(intent_id=intent_id)
                # sort = SortAnswerSerializer(sort, many=True)
                # sort_data = sort.data
                # for i in range(len(sort_data)):
                #     answer = AnswerForChatbot.objects.filter(id=sort_data[i]['id_answer'])
                    
                #     sort_data[i]['answer'] = AnswerForChatbotSerializer(answer, many=True).data
                    
                return Response(answers.data, status=status.HTTP_200_OK)
            else:
                answers = AnswerForChatbotSerializer(AnswerForChatbot.objects.all(), many=True)
                return Response(answers.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete awswers...',
                         manual_parameters=[openapi.Parameter(
                             name="id",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_INTEGER,
                             required=False,
                             description="delete by id of awswer"
                         ),openapi.Parameter(
                             name="intent_id",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_INTEGER,
                             required=False,
                             description="delete by intent_id"
                         ),openapi.Parameter(
                             name="awswer",
                             in_=openapi.IN_QUERY,
                             type=openapi.TYPE_STRING,
                             required=False,
                             description="delete by awswer"
                         )])
    def delete(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",10) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'DELETE':
            id = request.GET.get('id')
            intent_id = request.GET.get('intent_id')
            answer = request.GET.get('answer')
            answers = AnswerForChatbot.objects.all()
            if id is not None:
                answers = AnswerForChatbot.objects.filter(id=id)
                if len(answers) == 0:
                    return Response({'error': 'Answer does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                sort_answer = SortAnswer.objects.filter(id_answer=id)
            elif intent_id is not None:
                answers = AnswerForChatbot.objects.filter(intent_id=intent_id)
                if len(answers) == 0:
                    return Response({'error': 'Intent does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                sort_answer = SortAnswer.objects.filter(intent_id=intent_id)
                
            elif answer is not None:
                answers = AnswerForChatbot.objects.filter(answer=answer)
                if len(answers) == 0:
                    return Response({'error': 'Answer does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                sort_answer = SortAnswer.objects.filter(id_answer=answers[0].id)
                
            answers.delete()
            sort_answer.delete()
            
            return Response({'success': 'Delete all answers successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

class FilesQuestionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
    
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
        if self.check_permissions_(request,"",12) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
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
                if file_type.lower() == 'xlsx':
                    data_raw = pd.read_excel('.'+filename)
                else:
                    data_raw = pd.read_csv('.'+filename)
                for i in range(data_raw.shape[0]):
                    question = data_raw['question'][i]
                    intent_name_raw = data_raw['topic'][i].lower().strip()
                    
                    intent_name = remove_diacritics(intent_name_raw)
                    
                    intent = Intent.objects.filter(intent_name=intent_name,intent_detail=intent_name_raw)
                    if len(intent) == 0:
                        # check duplicated question
                        question_list = QuestionForChatbot.objects.filter(question=question)
                        if len(question_list) > 0:
                            cnt += 1
                            continue
                        intent = Intent(intent_name=intent_name, intent_detail=intent_name_raw)
                        
                        intent.save()
                        intentSerializer = IntentSerializer(intent)
                        print(f'intent_name: {intent_name_raw}',end=" ")
                        print('intent id: ', intentSerializer.data['id'])
                        
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
                        name_intent = remove_diacritics(list[i].strip().lower())
                        f.write('- intent: ' + name_intent + '\n')
                        f.write('  examples: |\n')
                        for j in range(data_raw.shape[0]):
                            if data_raw['topic'][j] == list[i]:
                                f.write('    - ' + data_raw['question'][j] + '\n')

                file_path = './media/nlu_data/nlu.yml'
                file_name = 'nlu.yml'

                from django.http import HttpResponse, HttpResponseNotFound
                try:
                    with open(file_path, 'r') as f:
                        file_data = f.read()

                    # sending response 
                    response = HttpResponse(file_data, content_type='application/force-download')
                    response['Content-Disposition'] = 'attachment; filename="nlu.yml"'

                except IOError:
                    # handle file not exist case here
                    response = HttpResponseNotFound('<h1>File not exist</h1>')
                
                # return response
                return Response({'success': 'File uploaded successfully.', 'duplicated':cnt}, status=status.HTTP_200_OK)
                # return Response({'success': 'File uploaded successfully.', 'duplicated':cnt}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid form.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all files question...')
    def get(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",12) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            filesQuestion = FilesQuestion.objects.all()
            filesQuestionSerializer = FilesQuestionSerializer(filesQuestion, many=True)
            return Response(filesQuestionSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all files question...')
    def delete(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",12) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'DELETE':
            filesQuestion = FilesQuestion.objects.all()
            filesQuestion.delete()
            return Response({'success': 'Delete all files question successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

class FilesAnswerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
    
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
        if self.check_permissions_(request,"",11) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
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
                if file_type.lower() == 'xlsx':
                    data_raw = pd.read_excel('.'+filename)
                else:
                    data_raw = pd.read_csv('.'+filename)
                for i in range(data_raw.shape[0]):
                    answer = data_raw['answer'][i]
                    intent_name = remove_diacritics(data_raw['topic'][i].lower().strip())
                    intent = Intent.objects.filter(intent_name=intent_name)
                    
                    if len(intent) == 0:
                        intent = Intent(intent_name=intent_name,intent_detail=data_raw['topic'][i])
                        intent.save()
                        intentSerializer = IntentSerializer(intent)
                        sort = SortAnswer.objects.filter(intent_id=int(intentSerializer.data['id']), sort=int(data_raw['sort'][i]))
                        if len(sort) > 0:
                            intent.delete()
                            return Response({'error': f'Sort answer already exists.(line {i})'}, status=status.HTTP_400_BAD_REQUEST)
                        intentSerializer = IntentSerializer(intent)
                        print('Intent id: ', intentSerializer.data['id'])
                        answer_model = AnswerForChatbot(answer=answer, intent_id=intent)
                        answer_model.save()
                        sort = SortAnswer(intent_id=intent,type_answer='text',id_answer=answer_model.id, sort=data_raw['sort'][i])
                        sort.save()
                    else:
                        intent = intent[0]
                        intentSerializer = IntentSerializer(intent)
                        sort = SortAnswer.objects.filter(intent_id=int(intentSerializer.data['id']), sort=int(data_raw['sort'][i]))
                        if len(sort) > 0:
                            return Response({'error': f'Sort answer already exists.(line {i})'}, status=status.HTTP_400_BAD_REQUEST)
                        answer_model = AnswerForChatbot(answer=answer, intent_id=intent)
                        answer_model.save()
                        sort = SortAnswer(intent_id=intent,type_answer='text',id_answer=answer_model.id, sort=data_raw['sort'][i])
                        sort.save()
                
                return Response({'success': 'File uploaded successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid form.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get all files answer...')
    def get(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",11) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            filesAnswer = FilesAnswer.objects.all()
            filesAnswerSerializer = FilesAnswerSerializer(filesAnswer, many=True)
            return Response(filesAnswerSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all files answer...')
    def delete(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",11) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'DELETE':
            filesAnswer = FilesAnswer.objects.all()
            filesAnswer.delete()
            return Response({'success': 'Delete all files answer successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)

class OutOfScopeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Get out of scope...',
                         manual_parameters=[
                             openapi.Parameter(
                                    name="id",
                                    in_=openapi.IN_QUERY,
                                    type=openapi.TYPE_STRING,
                                    required=False,
                                    description="out of scope id"
                                ),openapi.Parameter(
                                    name="outOfScope",
                                    in_=openapi.IN_QUERY,
                                    type=openapi.TYPE_STRING,
                                    required=False,
                                    description="out of scope"
                                )])
    def get(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",13) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            id = request.GET.get('id')
            outOfScope = request.GET.get('outOfScope')
            if id is not None and outOfScope is not None:
                outOfScope_ = Out_of_scope.objects.filter(id=id, out_of_scope=outOfScope)
                outOfScopeSerializer = OutOfScopeSerializer(outOfScope_, many=True)
                return Response(outOfScopeSerializer.data, status=status.HTTP_200_OK)
            elif id is not None:
                outOfScope_ = Out_of_scope.objects.filter(id=id)
                outOfScopeSerializer = OutOfScopeSerializer(outOfScope_, many=True)
                return Response(outOfScopeSerializer.data, status=status.HTTP_200_OK)
            elif outOfScope is not None:
                outOfScope_ = Out_of_scope.objects.filter(out_of_scope=outOfScope)
                outOfScopeSerializer = OutOfScopeSerializer(outOfScope_, many=True)
                return Response(outOfScopeSerializer.data, status=status.HTTP_200_OK)
            else:
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
        if self.check_permissions_(request,"",13) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
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
    
    @swagger_auto_schema(operation_description='Get out of scope...',
                         manual_parameters=[
                             openapi.Parameter(
                                    name="id",
                                    in_=openapi.IN_FORM,
                                    type=openapi.TYPE_STRING,
                                    required=True,
                                    description="out of scope id"
                                ),openapi.Parameter(
                                    name="outOfScope",
                                    in_=openapi.IN_FORM,
                                    type=openapi.TYPE_STRING,
                                    required=True,
                                    description="out of scope"
                                )])
    def put(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",13) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'PUT':
            id = request.GET.get('id')
            outOfScope = request.GET.get('outOfScope')
            if id is None or outOfScope is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            outOfScope_ = Out_of_scope.objects.filter(id=id)
            if len(outOfScope_) == 0:
                return Response({'error': 'Out of scope does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                outOfScope_ = outOfScope_[0]
                outOfScope_.out_of_scope = outOfScope
                outOfScope_.save()
                outOfScopeSerializer = OutOfScopeSerializer(outOfScope_)
                outOfScopeSerializerJson = outOfScopeSerializer.data
                return Response(outOfScopeSerializerJson, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Delete all out of scope...',manual_parameters=[
                             openapi.Parameter(
                                    name="id",
                                    in_=openapi.IN_FORM,
                                    type=openapi.TYPE_STRING,
                                    required=True,
                                    description="out of scope id for delete"
                                ),openapi.Parameter(
                                    name="outOfScope",
                                    in_=openapi.IN_FORM,
                                    type=openapi.TYPE_STRING,
                                    required=True,
                                    description="out_of_scope for delete"
                                )])
    def delete(self, request, *args, **kwargs):
        if self.check_permissions_(request,"",13) == False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'DELETE':
            id = request.GET.get('id')
            outOfScope_ = request.GET.get('outOfScope')
            if id is not None:
                outOfScope = Out_of_scope.objects.filter(id=id)
                if len(outOfScope) == 0:
                    return Response({'error': 'Out of scope does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    outOfScope.delete()
                    return Response({'success': 'Delete out of scope successfully.'}, status=status.HTTP_200_OK)
            elif outOfScope_ is not None:
                outOfScope = Out_of_scope.objects.filter(out_of_scope=outOfScope_)
                if len(outOfScope) == 0:
                    return Response({'error': 'Out of scope does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    outOfScope.delete()
                    return Response({'success': 'Delete out of scope successfully.'}, status=status.HTTP_200_OK)
            else:
                Out_of_scope.objects.all().delete()
                return Response({'success': 'Delete all out of scope successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
class ExportAll(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Export all data...',
                         manual_parameters=[openapi.Parameter(
                                name="file",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_FILE,
                                required=True,
                                description="files"
                            )])
    def post(self, request, *agrs, **kwargs):
        
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
                fileConvert = FileConvert(file_convert=file)
                fileConvert.save()
                fileConvertSerializer = FileConvertSerializer(fileConvert)
                fileConvertSerializerJson = fileConvertSerializer.data
                print(fileConvertSerializerJson)

                filename = fileConvertSerializerJson['file_convert']
                print('path: ', filename)
                data_raw = pd.read_csv('.'+filename)
                # questions_list = QuestionForChatbot.objects.all()
                # questions_list_serializer = QuestionForChatbotSerializer(questions_list, many=True)
                
                # intent_list = Intent.objects.all()
                # intent_list_serializer = IntentSerializer(intent_list, many=True)

                # #  convert to csv 
                # df_intent = pd.DataFrame(intent_list_serializer.data)
                # df_question = pd.DataFrame(questions_list_serializer.data)
                # # map intent id
                # intent_id_to_name = dict(zip(df_intent['id'], df_intent['intent_name']))
                # print('------------------')
                # print(intent_id_to_name)
                # print('------------------')
                # df_question['intent_id'] = df_question['intent_id'].map(intent_id_to_name)
                
                # # print(df_question.head())
                # df_question.rename(columns={'question': 'question','intent_id': 'topic'}, inplace=True)
                
                # outOfScope = Out_of_scope.objects.all()
                # outOfScopeSerializer = OutOfScopeSerializer(outOfScope, many=True)
                # df_outOfScope = pd.DataFrame(outOfScopeSerializer.data)
                # df_outOfScope.rename(columns={'out_of_scope': 'question'}, inplace=True)
                # new_column = np.full(df_outOfScope.shape[0],'out_of_scope')
                # df_outOfScope['topic'] = new_column
                
                # df_outOfScope = df_outOfScope[['question', 'topic']]        
                # print(df_outOfScope.head())
                # data_raw = df_question[['question', 'topic']]
                # data_raw = pd.concat([data_raw, df_outOfScope], ignore_index=True)
                print('# Drop nan')
                print('  - Before: ',data_raw.shape)
                data_raw.dropna(inplace=True)
                # data_raw.drop_duplicates(inplace=True)
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
                
                list_ = data_raw['topic'].unique()
                # print(list_)
                with open('./media/nlu_data/nlu.yml', 'w') as f:
                    f.write('version: "3.1"\n\n')
                    f.write('nlu:\n')
                    for i in range(len(list_)):
                        name_intent = remove_diacritics(list_[i].lower())
                        f.write('- intent: ' + name_intent + '\n')
                        f.write('  examples: |\n')
                        for j in range(data_raw.shape[0]):
                            # print(data_raw['topic'][j])
                            # print(list_[i])
                            # print(j)
                            # print(data_raw['topic'][32])
                            if data_raw['topic'][j] == list_[i]:
                                f.write('    - ' + data_raw['question'][j] + '\n')

                file_path = './media/nlu_data/nlu.yml'
                file_name = 'nlu.yml'
                from django.http import HttpResponse, HttpResponseNotFound
                try:    
                    with open(file_path, 'r') as f:
                        file_data = f.read()

                    # sending response 
                    response = HttpResponse(file_data, content_type='application/force-download')
                    response['Content-Disposition'] = 'attachment; filename="nlu.yml"'

                except IOError:
                    # handle file not exist case here
                    response = HttpResponseNotFound('<h1>File not exist</h1>')

                return response
class AutoTrain(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    
    
    def post(self, request, *args, **kwargs):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'POST':
            # train model
            if settings.TRAINING_IN_PROGRESS == True:
                return Response({'error': 'Training in progress.'}, status=status.HTTP_400_BAD_REQUEST)
            
            settings.TRAINING_IN_PROGRESS = True
            
            time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            source_path =  './chatbot_bert/data/nlu.yml'
            destination_path = './chatbot_bert/data_old/' + time + '_nlu.yml'
            shutil.copyfile(source_path, destination_path)
            print('file_rename: ', destination_path)
            remove = subprocess.run(['rm','-r','./chatbot_bert/data/nlu.yml'], capture_output=True, text=True)
            print(remove.stdout)
            transfer = subprocess.run(['scp','-r','./media/nlu_data/nlu.yml','./chatbot_bert/data/'], capture_output=True, text=True)
            print(transfer.stdout)
            remove = subprocess.run(['rm','-r','./chatbot_bert/train_test_split/'], capture_output=True, text=True)
            print(remove.stdout)
            test = subprocess.run(['ls','-l'], capture_output=True, text=True)
            print(test.stdout)
            
            os.system('bash ./run_.sh')
            # print(train_nlu.stdout)
            
            settings.TRAINING_IN_PROGRESS = False
            return Response({'success': 'Train model successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class Login(APIView):
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='Login ...',
                         manual_parameters=[openapi.Parameter(
                             name="username",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="username"
                         ),openapi.Parameter(
                                name="password",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="password"
                            )
                         ]) 
    def post(self, request):
        if request.method =='POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                csrftoken = get_token(request)
                print("csrftoken: ",csrftoken)
                userSerializer = UserSerializer(user)
                userSerializerJson = userSerializer.data
                add_csrf = {'csrftoken': csrftoken}
                userSerializerJson.update(add_csrf)
                token = Token.objects.get(user=user)
                userSerializerJson['token'] = token.key
                return Response(userSerializerJson, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
class Logout(APIView):
    
    parser_classes = (MultiPartParser,)
    @swagger_auto_schema(operation_description='Logout ...')
    @csrf_exempt
    def post(self, request):
        if request.method =='POST':
            logout(request)
            return Response({'success': 'Logout successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
class Register(APIView):
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='Register ...',
                         manual_parameters=[openapi.Parameter(
                             name="username",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="username"
                         ),openapi.Parameter(
                                name="password",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="password"
                            ),openapi.Parameter(
                                name="email",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="email"
                            )])
    def post(self,request):
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            if username is None or password is None or email is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.filter(username=username)
            if len(user) > 0:
                return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.filter(email=email)
            if len(user) > 0:
                return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.create_user(username=username, password=password, email=email)
            user.save()
            token, created = Token.objects.get_or_create(user=user)
            data = {'token': token.key}
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class ChangePassword(APIView):
    parser_classes = (MultiPartParser,)
    
    @swagger_auto_schema(operation_description='Change password ...',
                         manual_parameters=[openapi.Parameter(
                             name="username",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="username"
                         ),openapi.Parameter(
                                name="password",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="password"
                            ),openapi.Parameter(
                                name="new_password",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="new_password"
                            )])
    @csrf_exempt
    def post(self,request):
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            new_password = request.POST.get('new_password')
            if username is None or password is None or new_password is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            user = authenticate(username=username, password=password)
            if user is None:
                return Response({'error': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            return Response({'success': 'Change password successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class ModelRasaView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    
    def put(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'PUT':
            print('------------------')
            print('Model Rasa')
            os.chdir('./chatbot_bert/models')
            file_list = os.listdir()
            
            for file_name in file_list:
                print(file_name)
                modelRasa = ModelRasa.objects.filter(model_name=file_name)
                if len(modelRasa) > 0:
                    modelRasa = modelRasa[0]
                    modelRasa.model_name = file_name
                    modelRasa.save()
                    continue
                modelRasa = ModelRasa(model_name=file_name, isActivate=False)
                modelRasa.save()
            os.chdir('../..')
            return Response({'success': 'Model Rasa updated.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    def get(self,request):
        if request.method == 'GET':
            # send message with websocket
            modelRasa = ModelRasa.objects.all()
            modelRasaSerializer = ModelRasaSerializer(modelRasa, many=True)
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(
                "response_person",  
                {
                    "type": "chat_message",
                },
            )
            return Response(modelRasaSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='Change password ...',
                         manual_parameters=[openapi.Parameter(
                             name="model_name",
                             in_=openapi.IN_FORM,
                             type=openapi.TYPE_STRING,
                             required=True,
                             description="model_name"
                         )])
    def post(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'POST':
            model_name = request.POST.get('model_name')
            modelRasa = ModelRasa.objects.filter(model_name=model_name)
            if len(modelRasa) > 0:
                _ = ModelRasa.objects.all()
                for model in _:
                    model.isActivate = False
                    model.save()
                modelRasa = modelRasa[0]
                modelRasa.isActivate = True
                modelRasa.save()
                
                # os.system('fuser -n tcp -k 6000')
                # os.chdir('./chatbot_bert/')
                # os.system("rasa run --enable-api -m ./models/"+model_name + " -p 6000")
                # os.chdir('../')
                subprocess.run(['fuser', '-n', 'tcp', '-k', '6000'])

                os.chdir('./chatbot_bert/')
                rasa_command = f"rasa run --enable-api -m ./models/{model_name} -p 6000"
                subprocess.Popen(rasa_command, shell=True)
                os.chdir('../')

                def is_port_open(host, port):
                    try:
                        # Tạo một kết nối socket đến host và port cụ thể
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(1)  # Đặt thời gian chờ cho kết nối (1 giây)

                            # Thử kết nối tới host và port
                            s.connect((host, port))
                        return True  # Kết nối thành công, cổng mở
                    except (socket.timeout, ConnectionRefusedError):
                        return False  # Kết nối thất bại, cổng đóng hoặc không thể kết nối

                # Thay thế host và port bằng giá trị thực tế bạn muốn kiểm tra
                host = 'localhost'
                port = 6000
                first_second = datetime.datetime.now()
                timeout_seconds = 60
                print("second start: ",first_second)
                while True:
                    time.sleep(10)
                    if is_port_open(host, port):
                        print(f"Cổng {port} trên {host} được mở.")
                        return Response({'success': 'Model Rasa activated.'}, status=status.HTTP_200_OK)                        
                        
                    second = datetime.datetime.now()
                    second_check = second - first_second

                    if second_check.total_seconds() > timeout_seconds:
                        print("second end: ",second)
                        print(f"Cổng {port} trên {host} đóng hoặc không thể kết nối.")
                        return Response({'error': 'Model Rasa not activated.'}, status=status.HTTP_400_BAD_REQUEST)
                    
            else:
                return Response({'error': 'Model does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response(modelRasaSerializerJson, status=status.HTTP_200_OK)
        
class ExportView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='Export data...',
                            manual_parameters=[openapi.Parameter(
                                name="check",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="nlu data or answer data"
                            )])
    def get(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            check = request.GET.get('check')
            # print(check)
            if check is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            if int(check) == 1:
                questions = QuestionForChatbot.objects.all()
                questionsSerializer = QuestionForChatbotSerializer(questions, many=True)
                answers = AnswerForChatbot.objects.all()
                answersSerializer = AnswerForChatbotSerializer(answers, many=True)
                
                outOfScope = Out_of_scope.objects.all()
                outOfScopeSerializer = OutOfScopeSerializer(outOfScope, many=True)
                intents = Intent.objects.all()
                intentsSerializer = IntentSerializer(intents, many=True)
                
                #  convert to csv
                df_question = pd.DataFrame(questionsSerializer.data)
                if (df_question.shape[0] == 0):
                    df_question = pd.DataFrame(columns=['id', 'question', 'intent_id'])
                # df_answer = pd.DataFrame(answersSerializer.data)
                df_outOfScope = pd.DataFrame(outOfScopeSerializer.data)
                if (df_outOfScope.shape[0] == 0):
                    df_outOfScope = pd.DataFrame(columns=['id', 'out_of_scope'])
                df_intent = pd.DataFrame(intentsSerializer.data)
                if (df_intent.shape[0] == 0):
                    df_intent = pd.DataFrame(columns=['id', 'intent_name'])
                # map intent id
                intent_id_to_name = dict(zip(df_intent['id'], df_intent['intent_name']))
                df_question['intent_id'] = df_question['intent_id'].map(intent_id_to_name)
                df_question.rename(columns={'question': 'question','intent_id': 'topic'}, inplace=True)
                # concat out of scope
                df_outOfScope.rename(columns={'out_of_scope': 'question'}, inplace=True)
                new_column = np.full(df_outOfScope.shape[0],'out_of_scope')
                df_outOfScope['topic'] = new_column
                df_outOfScope = df_outOfScope[['question', 'topic']]

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
                        name_intent = remove_diacritics(list[i].lower())
                        f.write('- intent: ' + name_intent + '\n')
                        f.write('  examples: |\n')
                        for j in range(data_raw.shape[0]):
                            if data_raw['topic'][j] == list[i]:
                                f.write('    - ' + data_raw['question'][j] + '\n')

                file_path = './media/nlu_data/nlu.yml'
                file_name = 'nlu.yml'

                from django.http import HttpResponse, HttpResponseNotFound
                try:
                    with open(file_path, 'r') as f:
                        file_data = f.read()

                    # sending response 
                    response = HttpResponse(file_data, content_type='application/force-download')
                    response['Content-Disposition'] = 'attachment; filename="nlu.yml"'

                except IOError:
                    # handle file not exist case here
                    response = HttpResponseNotFound('<h1>File not exist</h1>')
                
                return response
            
            elif int(check) == 0:
                questions = QuestionForChatbot.objects.all()
                questionsSerializer = QuestionForChatbotSerializer(questions, many=True)
                answers = AnswerForChatbot.objects.all()
                answersSerializer = AnswerForChatbotSerializer(answers, many=True)
                outOfScope = Out_of_scope.objects.all()
                outOfScopeSerializer = OutOfScopeSerializer(outOfScope, many=True)
                intents = Intent.objects.all()
                intentsSerializer = IntentSerializer(intents, many=True)
                
                images = Image.objects.all()
                imagesSerializer = ImageSerializer(images, many=True)
                
                #  convert to csv
                df_question = pd.DataFrame(questionsSerializer.data)
                if (df_question.shape[0] == 0):
                    df_question = pd.DataFrame(columns=['id', 'question', 'intent_id'])
                    
                df_answer = pd.DataFrame(answersSerializer.data)
                if(df_answer.shape[0] == 0):
                    df_answer = pd.DataFrame(columns=['id','answer','intent_id'])
                df_outOfScope = pd.DataFrame(outOfScopeSerializer.data)
                if (df_outOfScope.shape[0] == 0):
                    df_outOfScope = pd.DataFrame(columns=['id', 'out_of_scope'])
                df_intent = pd.DataFrame(intentsSerializer.data)
                if (df_intent.shape[0] == 0):
                    df_intent = pd.DataFrame(columns=['id', 'intent_name'])
                df_image = pd.DataFrame(imagesSerializer.data)
                
                if(df_image.shape[0] == 0):
                    df_image = pd.DataFrame(columns=['id','Image','intent_id'])
                
                # map intent id
                intent_id_to_name = dict(zip(df_intent['id'], df_intent['intent_name']))
                df_question['intent_id'] = df_question['intent_id'].map(intent_id_to_name)
                df_question.rename(columns={'question': 'question','intent_id': 'topic'}, inplace=True)
                df_answer['intent_id'] = df_answer['intent_id'].map(intent_id_to_name)
                df_answer.rename(columns={'answer': 'answer','intent_id': 'topic'}, inplace=True)
                df_answer.sort_values(by=['id'], inplace=True)
                
                df_image['intent_id'] = df_image['intent_id'].map(intent_id_to_name)
                df_image.rename(columns={'Image': 'Image','intent_id': 'topic'}, inplace=True)
                df_image.sort_values(by=['id'], inplace=True)
                # concat out of scope
                df_outOfScope.rename(columns={'out_of_scope': 'question'}, inplace=True)
                new_column = np.full(df_outOfScope.shape[0],'out_of_scope')
                df_outOfScope['topic'] = new_column
                df_outOfScope = df_outOfScope[['question', 'topic']]

                data_raw = df_question[['question', 'topic']]
            
                data_raw = pd.concat([data_raw, df_outOfScope], ignore_index=True)
                # print(df_image)
                datajson = {
                    
                }
                for it in df_intent['intent_name']:
                    datajson[it] = {}
                    
                    datanew_question = []
                    for i in range(df_question.shape[0]):
                        if df_question['topic'][i] == it:
                            datanew_question.append(df_question['question'][i])
                    datanew_answer = []
                    for i in range(df_answer.shape[0]):
                        if df_answer['topic'][i] == it:
                            datanew_answer.append({'type':'text','content':df_answer['answer'][i]})
                    for i in range(df_image.shape[0]):
                        if df_image['topic'][i] == it:
                            datanew_answer.append({'type':'image','content':df_image['Image'][i]})
                    
                    datajson[it].update({'questions': datanew_question, 'answers': datanew_answer})
                # print(datajson)
                import json
                # save file 
                file_path = './media/json/export_data.json'
                with open(file_path, 'w') as f:
                    json.dump(datajson, f, indent=4, ensure_ascii=False)
                
                from django.http import HttpResponse, HttpResponseNotFound
                try:
                    with open(file_path, 'r') as f:
                        file_data = f.read()

                    # sending response 
                    response = HttpResponse(file_data, content_type='application/force-download')
                    response['Content-Disposition'] = 'attachment; filename="export_data.json"'

                except IOError:
                    # handle file not exist case here
                    response = HttpResponseNotFound('<h1>File not exist</h1>')
                
                return response
            return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class AddUserGroupView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='get user in groups ...',
                            manual_parameters=[openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id")
                            ])
    def get(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            group_id = request.GET.get('group_id')
            users = User.objects.filter(groups__id=group_id)
            usersSerializer = UserInfoSerializer(users, many=True)
            return Response(usersSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='add user for groups ...',
                            manual_parameters=[openapi.Parameter(
                                name="user_id",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="user_id"
                            ),openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id")
                            ])
    def post(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'POST':
            group_id = request.POST.get('group_id')
            user_id = request.POST.get('user_id')
            user = User.objects.filter(id=user_id)
            if len(user) == 0:
                return Response({'error': 'User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            user = user[0]
            group = Group.objects.filter(id=group_id)
            if len(group) == 0:
                return Response({'error': 'Group does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            group = group[0]
            user.groups.add(group)
            user.save()
            return Response({'success': 'Add user to group successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='delete user in groups ...',
                            manual_parameters=[openapi.Parameter(
                                name="user_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="user_id"
                            ),openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id")
                            ])
    def delete(self, request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'DELETE':
            user_id  = request.GET.get('user_id')
            group_id = request.GET.get('group_id')
            user = User.objects.filter(id=user_id)
            
            if len(user) == 0:
                return Response({'error': 'User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            user = user[0]
            group = Group.objects.filter(id=group_id)
            if len(group) == 0:
                return Response({'error': 'Group does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            group = group[0]
            user.groups.remove(group)
            user.save()
            return Response({'success': 'Remove user from group successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
class GroupView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            groups = Group.objects.all()
            groupsSerializer = GroupSerializer(groups, many=True)
            return Response(groupsSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='create group ...',
                            manual_parameters=[openapi.Parameter(
                                name="name",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="name"
                            )])
    def post(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'POST':
            name_group = request.POST.get('name')
            if name_group is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            group = Group.objects.filter(name=name_group)
            if len(group) > 0:
                return Response({'error': 'Group already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            group = Group(name=name_group)
            group.save()
            return Response({'success': 'Create group successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='Change password ...',
                            manual_parameters=[openapi.Parameter(
                                name="name",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="name",
                            ),openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id"
                            )])
    def put(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'PUT':
            group_id = request.POST.get('group_id')
            name_group = request.POST.get('name')
            if group_id is None or name_group is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            group = Group.objects.filter(id=group_id)
            if len(group) == 0:
                return Response({'error': 'Group does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            _ = group[0]
            _.name = name_group
            _.save()
            groupSerializer = GroupSerializer(_)
            datajson = {
                'group': groupSerializer.data,
                'success': 'Update group successfully.'
            }
            return Response(datajson, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
            
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='Change password ...',
                            manual_parameters=[openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id"
                            )])
    def delete(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'DELETE':
            group_id = request.GET.get('group_id')
            if group_id is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            group = Group.objects.filter(id=group_id)
            if len(group) == 0:
                return Response({'error': 'Group does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            groupSerializer = GroupSerializer(group[0])
            group.delete()
            datajson = {
                'group': groupSerializer.data,
                'success': 'Delete group successfully.'
            }
            return Response(datajson, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class AuthPermissionGroupView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='get permission in groups ...',
                            manual_parameters=[openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id"
                            )])
    def get(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            group_id = request.GET.get('group_id')
            permission = Permission.objects.filter(group__id=group_id)
            permissionSerializer = PermissionSerializer(permission, many=True)
            return Response(permissionSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='add permission for groups...',
                            manual_parameters=[
                            openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id"
                            ),openapi.Parameter(
                                name="permission_id",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=False,
                                description="permission_id"
                            ),openapi.Parameter(
                                name="content_type_id",
                                in_=openapi.IN_FORM,
                                type=openapi.TYPE_INTEGER,
                                required=False,
                                description="content_type_id")])
    def post(self, request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method=='POST':
            group_id = request.POST.get('group_id')
            permission_id = request.POST.get('permission_id')
            content_type_id = request.POST.get('content_type_id')
            if group_id is None and permission_id is None and content_type_id is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            if group_id is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            group = Group.objects.filter(id=group_id)
            if len(group) == 0:
                return Response({'error': 'Group does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            if permission_id is not None:
                permission = Permission.objects.filter(id=permission_id)
                if len(permission) == 0:
                    return Response({'error': 'Permission does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                group[0].permissions.add(permission[0])
                groupSerializer = GroupSerializer(group[0])
                datajson = {
                    'group': groupSerializer.data,
                    'success': 'Add permission successfully.',
                    'permission': permission[0].name
                }
                return Response(datajson, status=status.HTTP_200_OK)
            if content_type_id is not None:
                content_type = ContentType.objects.filter(id=content_type_id)
                if len(content_type) == 0:
                    return Response({'error': 'Content type does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                permissions = Permission.objects.filter(content_type=content_type[0])
                for permission in permissions:
                    group[0].permissions.add(permission)
                groupSerializer = GroupSerializer(group[0])
                datajson = {
                    'group': groupSerializer.data,
                    'success': 'Add permission successfully.',
                    'permission': content_type[0].model
                }
                return Response(datajson, status=status.HTTP_200_OK)
        
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
    
    parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='delete permission in groups ...',
                            manual_parameters=[openapi.Parameter(
                                name="group_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="group_id"
                            ),openapi.Parameter(
                                name="permission_id",
                                in_=openapi.IN_QUERY,
                                type=openapi.TYPE_INTEGER,
                                required=True,
                                description="permission_id"
                            )])
    def delete(self, request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method=='DELETE':
            group_id = request.GET.get('group_id')
            permission_id = request.GET.get('permission_id')
            if group_id is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            if permission_id is None:
                group = Group.objects.filter(id=group_id)
                if len(group) == 0:
                    return Response({'error': 'Group does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                groupSerializer = GroupSerializer(group[0])
                group[0].permissions.clear()
                datajson = {
                    'group': groupSerializer.data,
                    'success': 'Delete permission successfully.'
                }
                return Response(datajson, status=status.HTTP_200_OK)
            else:
                group = Group.objects.filter(id=group_id)
                if len(group) == 0:
                    return Response({'error': 'Group does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                permission = Permission.objects.filter(id=permission_id)
                if len(permission) == 0:
                    return Response({'error': 'Permission does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                group[0].permissions.remove(permission[0])
                groupSerializer = GroupSerializer(group[0])
                datajson = {
                    'group': groupSerializer.data,
                    'success': 'Delete permission successfully.',
                    'permission': permission[0].name
                }
                return Response(datajson, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class PermissionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            permissions = Permission.objects.all()
            permissionsSerializer = PermissionSerializer(permissions, many=True)
            return Response(permissionsSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
class UserView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    
    def get(self,request):
        if request.user.is_superuser is False:
            return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            users = User.objects.all()
            userInfoSerializer = UserInfoSerializer(users, many=True)
            
            return Response(userInfoSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        

class UserViewInfo(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
        
    
    # @csrf_exempt
    # @swagger_auto_schema(operation_description='Change password ...',
    #                         manual_parameters=[openapi.Parameter(
    #                             name="username",
    #                             in_=openapi.IN_QUERY ,
    #                             type=openapi.TYPE_STRING,
    #                             required=True,
    #                             description="username"
    #                         )])
    def get(self,request):
        # if self.check_permissions_(request,"",4):
        request_user =request.user
        username = request_user.username
        if username is None:
            return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(username=username)
        if len(user) == 0:
            return Response({'error': 'User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        user = user[0]
        token = Token.objects.filter(user=user)
        if len(token) == 0:
            return Response({'error': 'Token does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        token = token[0]
        token = Token.objects.get(user=user)
        userInfoSerializer = UserInfoSerializer(user)
        userInfoSerializerJson = userInfoSerializer.data
        userInfoSerializerJson['token'] = token.key
        return Response(userInfoSerializerJson, status=status.HTTP_200_OK)


from .models import SortAnswer
from .serializers import SortAnswerSerializer
class SortAnswerView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    def check_permissions_(self, request,_codename='view_image',content_type_id=1):
        if request.user.is_superuser:
            return True        
        
        if request.user.groups is not None:
            for g in request.user.groups.all():
                name = g.name
                group = Group.objects.filter(name=name)
                if len(group) > 0:
                    group = group[0]
                    group_permission = group.permissions.all()
                    if len(group_permission) > 0:
                        for p in group_permission:
                            print(p.codename)
                            print(p.content_type_id)
                            if p.codename == _codename or p.content_type_id == content_type_id:
                                return True
                        return False
            return False
        else:
            return False
        
    
    @csrf_exempt
    @swagger_auto_schema(operation_description='Change password ...',
                            manual_parameters=[openapi.Parameter(
                                name="intent_id",
                                in_=openapi.IN_QUERY ,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="intent_id"
                            )])
    def get(self, request):
        # if check_permissions_(request,"",19) is False:
        #     return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        intent_id = request.GET.get('intent_id')
        
        if intent_id is None:
            return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
        
        sort_answer = SortAnswer.objects.filter(intent_id=intent_id)
        if sort_answer is None:
            return Response({'error':'intent_id not value'}, status=status.HTTP_400_BAD_REQUEST)
        
        if sort_answer.count() == 0:
            return Response({'error': 'table sort_answer not value'}, status=status.HTTP_400_BAD_REQUEST)
        
        sort_answerSerializer = SortAnswerSerializer(sort_answer, many=True)
        sort_answerSerializerJson = sort_answerSerializer.data
        # print(sort_answerSerializerJson)
        for i in range(len(sort_answerSerializerJson)):
            print(sort_answerSerializerJson[i])
            print(sort_answerSerializerJson[i]['id_answer'])
            if sort_answerSerializerJson[i]['type_answer'] == 'text':
                answer = AnswerForChatbot.objects.get(id=sort_answerSerializerJson[i]['id_answer'])
            
                if answer is not None:
                    sort_answerSerializerJson[i]['answer'] = AnswerForChatbotSerializer(answer).data
            
            else:
                image = Image.objects.get(id=sort_answerSerializerJson[i]['id_answer'])
                if image is not None:
                    sort_answerSerializerJson[i]['answer'] = ImageSerializer(image).data
                    
        return Response(sort_answerSerializerJson, status=status.HTTP_200_OK)
    
    # parser_classes = (MultiPartParser,)
    @csrf_exempt
    @swagger_auto_schema(operation_description='Change password ...',
                            manual_parameters=[openapi.Parameter(
                                name="intent_id",
                                in_=openapi.IN_QUERY ,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="intent_id"
                            ),openapi.Parameter(
                                name="id_answer",
                                in_=openapi.IN_QUERY ,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="id_answer"
                            ),openapi.Parameter(
                                name="sort",
                                in_=openapi.IN_QUERY ,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="sort"
                            ), openapi.Parameter(
                                name="type_answer",
                                in_=openapi.IN_QUERY ,
                                type=openapi.TYPE_STRING,
                                required=True,
                                description="type_answer"
                            )])
    def put(self, request):
        # if check_permissions_(request,"",19) is False:
        #     return Response({'error': 'You do not have permission to access.'}, status=status.HTTP_401_UNAUTHORIZED)
        if request.method == 'PUT':
            intent_id = request.GET.get('intent_id')
            id_answer = request.GET.get('id_answer')
            sort = request.GET.get('sort')
            type_answer = request.GET.get('type_answer')
            print(intent_id)
            sort_answer = SortAnswer.objects.filter(intent_id=intent_id, id_answer=id_answer)
            
            if sort_answer is None:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)
            if sort_answer.count() == 0:
                return Response({'error': 'Not sort answer'}, status=status.HTTP_400_BAD_REQUEST)
            sort_check = SortAnswer.object.filter(intent_id=int(intent_id),sort=int(sort))
            if len(sort_check) > 0:
                return Response({'error': 'Sort already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            sort_answer = sort_answer[0]
            sort_answer.sort = sort
            sort_answer.type_answer = type_answer
            sort_answer.save()
            
            sort_answerSerializer = SortAnswerSerializer(sort_answer)
            return Response(sort_answerSerializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid request method.'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        