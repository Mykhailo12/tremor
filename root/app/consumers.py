import json
import base64
import re
from .models import Message, User
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if text_data_json["edited_message"] != None and text_data_json["id"] != None:
            edited_message = text_data_json["edited_message"]
            id = text_data_json["id"]
            sender = text_data_json["sender"]
            receiver = text_data_json["receiver"]

            m = Message.objects.get(id=id)
            m.text = edited_message
            m.save()

            print(m.text, edited_message)

            self.room_group_name = "chat_%s" % self.room_name

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message", 
                    "edited_message" : edited_message,
                    "id" : id,
                    "message": None, 
                    "sender" : sender, 
                    "receiver" : receiver, 
                }
            )

            self.room_group_name = "chat_%s" % sender

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message", 
                    "edited_message" : edited_message,
                    "id" : id,
                    "message": None, 
                    "sender" : sender, 
                    "receiver" : receiver, 
                }
            )

        elif text_data_json["message"] != None:
            sender = text_data_json["sender"]
            receiver = text_data_json["receiver"] 
            message = text_data_json["message"] 

            print("от хуйня")
            
            if len(message) > 0:
                Message.objects.create(
                    text=message,
                    sender=User.objects.get(username=sender),
                    receiver=User.objects.get(username=receiver),
                    image=None,
                )

            message_model = Message.objects.all().order_by('-id')[0]

            if message_model.text == message:
                id = message_model.id

                self.room_group_name = "chat_%s" % sender

                created = Message.objects.get(id=id).created.strftime('%H:%M')

                print(created)

                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {
                        "type": "chat_message", 
                        "message": message, 
                        "sender" : sender, 
                        "receiver" : receiver, 
                        "created" : created,
                        "id" : id,
                        "edited_message" : None,
                        "deleted_message_id" : None,
                        "image_url" : None,
                    }
                )

                self.room_group_name = "chat_%s" % self.room_name

                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {
                        "type": "chat_message", 
                        "message": message, 
                        "sender" : sender, 
                        "receiver" : receiver, 
                        "created" : created,
                        "id" : id,
                        "edited_message" : None,
                        "deleted_message_id" : None,
                        "image_url" : None,
                    }
                )


        elif text_data_json["deleted_message_id"] != None:
            deleted_message_id = text_data_json["deleted_message_id"]
            sender = text_data_json["sender"]

            m = Message.objects.get(id=deleted_message_id)
            m.delete()

            self.room_group_name = "chat_%s" % sender

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message", 
                    "edited_message" : None,
                    "id" : None,
                    "message": None, 
                    "sender" : sender, 
                    "receiver" : None, 
                    "deleted_message_id" : deleted_message_id,
                    "image_url" : None,
                }
            )

        elif text_data_json["image_url"] != None:
            sender = text_data_json["sender"]
            receiver = text_data_json["receiver"]
            image_url = text_data_json["image_url"]
            message = text_data_json["message"]
            time = text_data_json["time"]

            match = re.match(r'data:image/(\w+);base64,(.+)', image_url)

            image_data = match.group(2)

            image_data_bytes = base64.b64decode(image_data)

            image_content_file = ContentFile(image_data_bytes, name=f"{time}.jpg")
            
            try:
                new_message = Message.objects.create(
                    text=None,
                    sender=User.objects.get(username=sender),
                    receiver=User.objects.get(username=receiver),
                    image=image_content_file
                )
                new_message.save()
                print("Message created successfully:")
            except ValidationError as e:
                print("Validation Error:", e)
            except Exception as e:
                print("Error:", e)

            filepath = f'uploads/{time}.jpg'

            created = Message.objects.get(image=filepath).created.strftime('%H:%M')

            self.room_group_name = "chat_%s" % sender

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message", 
                    "message": None, 
                    "sender" : sender, 
                    "receiver" : receiver, 
                    "image_url" : image_url,
                    "edited_message" : None,
                    "deleted_message_id" : None,
                    "time" : time,
                    "created" : created,
                }
            )

            self.room_group_name = "chat_%s" % self.room_name

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message", 
                    "message": message, 
                    "sender" : sender, 
                    "receiver" : receiver, 
                    "image_url" : image_url,
                    "edited_message" : None,
                    "deleted_message_id" : None,
                    "time" : time,
                    "created" : created,
                }
            )

    # Receive message from room group
    def chat_message(self, event):
        if event["message"] != None:
            message = event["message"]
            sender = event["sender"]
            receiver = event["receiver"]
            created = event["created"]
            id = event["id"]
            
            self.send(text_data=json.dumps({"message": message, "sender" : sender, "receiver" : receiver, "id" : id, "created" : created}))

        elif event["edited_message"] != None:
            edited_message = event["edited_message"]
            id = event["id"]
            sender = event["sender"]
            receiver = event["receiver"]

            print("message sended on consumers to html")

            self.send(text_data=json.dumps({"edited_message" : edited_message, "id" : id, "sender" : sender, "receiver" : receiver}))

        elif event["deleted_message_id"] != None:
            deleted_message_id = event["deleted_message_id"]
            sender = event["sender"]

            print('del_mes', deleted_message_id)

            self.send(text_data=json.dumps({"deleted_message_id" : deleted_message_id, "sender" : sender}))

        elif event["image_url"] != None:
            sender = event["sender"]
            receiver = event["receiver"]
            image_url = event["image_url"]
            time = event["time"]
            created = event["created"]

            print("Image sended")

            self.send(text_data=json.dumps({"image_url" : image_url, "sender" : sender, "receiver" : receiver, 'time':time, 'created':created}))