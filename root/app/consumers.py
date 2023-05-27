import json
from .models import Message, User
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

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
            message = text_data_json["message"]
            sender = text_data_json["sender"]
            receiver = text_data_json["receiver"]
            
            if len(message) > 0:
                Message.objects.create(
                    text=message,
                    sender=User.objects.get(username=sender),
                    receiver=User.objects.get(username=receiver),
                )

            message_model = Message.objects.all().order_by('-id')[0]

            if message_model.text == message:
                id = message_model.id

            print('created message id: ', id)

            self.room_group_name = "chat_%s" % sender

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message", 
                    "message": message, 
                    "sender" : sender, 
                    "receiver" : receiver, 
                    "id" : id
                }
            )

            self.room_group_name = "chat_%s" % self.room_name

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message", 
                    "message": message, 
                    "sender" : sender, 
                    "receiver" : receiver, 
                    "id" : id
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
                    "deleted_message_id" : deleted_message_id
                }
            )

    # Receive message from room group
    def chat_message(self, event):
        print(event)
        if event["message"] != None:
            message = event["message"]
            sender = event["sender"]
            receiver = event["receiver"]
            id = event["id"]
            
            self.send(text_data=json.dumps({"message": message, "sender" : sender, "receiver" : receiver, "id" : id}))

        elif event["edited_message"] != None:
            edited_message = event["edited_message"]
            id = event["id"]
            sender = event["sender"]
            receiver = event["receiver"]

            self.send(text_data=json.dumps({"edited_message" : edited_message, "id" : id, "sender" : sender, "receiver" : receiver}))

        elif event["deleted_message_id"] != None:
            deleted_message_id = event["deleted_message_id"]
            sender = event["sender"]

            print('del_mes', deleted_message_id)

            self.send(text_data=json.dumps({"deleted_message_id" : deleted_message_id, "sender" : sender}))
