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
        message = text_data_json["message"]
        sender = text_data_json["sender"]
        receiver = text_data_json["receiver"]

        self.room_group_name = "chat_%s" % sender

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat_message", "message": message, "sender" : sender, "receiver" : receiver}
        )

        self.room_group_name = "chat_%s" % self.room_name

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat_message", "message": message, "sender" : sender, "receiver" : receiver}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        sender = event["sender"]
        receiver = event["receiver"]

        print(message, sender, receiver)

        if message != ' ' and sender != receiver:
            Message.objects.create(
                text=message,
                sender=User.objects.get(username=sender),
                receiver=User.objects.get(username=receiver),
            )

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))