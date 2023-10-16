import json

from channels.generic.websocket import WebsocketConsumer
from channels.generic.http import AsyncHttpConsumer
from django.http import HttpResponse
from channels.consumer import SyncConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        print("connected")

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        print('-------------------')
        print(text_data)
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        if message == 'activated_rasa':
            self.send(text_data=json.dumps({"message": "model rasa activated"}))
        elif message=='training_rasa':
            self.send(text_data=json.dumps({"message": "rasa training"}))
            
    def chat_message(self, event):
        print("---------")
        self.send(text_data='Tác vụ đã hoàn thành.')

# from channels.generic.websocket import AsyncWebsocketConsumer

# class ChatConsumer(AsyncWebsocketConsumer):

#     async def connect(self):
#         await self.accept()

#     async def receive(self, text_data=None, bytes_data=None):
#         # await self.send(text_data="Hello world!")
#         text_data_json = json.loads(text_data)
#         print(text_data_json)
#         message = text_data_json["message"]
#         if message == 'activated_rasa':
#             self.send(text_data=json.dumps({"message": "model rasa activated", "status": "success",}))
#         elif message=='training_rasa':
#             self.send(text_data=json.dumps({"message": "rasa training", "status": "success",}))

#     async def disconnect(self, close_code):
#         pass
#     async def long_task(self, event):
#         print("---------")
#         await self.send(text_data='Tác vụ đã hoàn thành.')

# class GenerateConsumer(AsyncHttpConsumer):
#     async def handle(self, body):
#         print(body)
#         return HttpResponse("OK")
#     async def long_task(self, event):
#         print("---------")
#         await self.send(text_data='Tác vụ đã hoàn thành.')


class DeleteConsumer(AsyncHttpConsumer):
    async def handle(self, body):
        return HttpResponse("OK")