import json
import base64
import re
from .models import Message, User, Post, Comment, Friend
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

class HomeConsumer(WebsocketConsumer):
    print("initial")
    def connect(self):
        self.host = self.scope["url_route"]["kwargs"]["host"]
        
        self.room_group_name = self.host

        print("r:", self.room_group_name)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def groupSend(self, data):  
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, data
        )

        print("sended")

    def receive(self, text_data):
        print("Home Consumer")
    
        text_data_json = json.loads(text_data)

        print(text_data_json)

        click_type = text_data_json['click_type']
        host = text_data_json['host']

        print("type::::::::: ", click_type)

        if click_type == 'like':
            post_id = text_data_json['post_id']
            post = Post.objects.get(id=post_id)

            host = User.objects.get(username=host)

            post.likes.add(host)
            self.disconnect(0)

        elif click_type == "cancel_like":
            post_id = text_data_json['post_id']
            post = Post.objects.get(id=post_id)

            host = User.objects.get(username=host)

            post.likes.remove(host)
            self.disconnect(0)

        elif click_type == "comment_create":   
            host = text_data_json["host"]
            post_id = text_data_json['post_id']
            text = text_data_json["text"] 
            newcomment = Comment.objects.create(
                host = User.objects.get(username=host),
                text = text,
            )
            Post.objects.get(id=post_id).comments.add(newcomment)

        elif click_type == "load_comments":
            comments_load_count = text_data_json['comments_load_count']
            post_id = text_data_json['post_id']
            post = Post.objects.get(id=post_id)
            #comments = post.comments.all().order_by('-created')[:5]

            comments = post.comments.all()

            comments_list = []
            print("comments_load_count", comments_load_count)

            step = 5

            i = step * comments_load_count

            if i+step > comments.count():
                step = comments.count() - i
                self.groupSend({"type" : "load_end"})

            print("fist i: ", i)
            for i in range(i, i+step):
                print(i)
                comment_data = [1, 2, 3, 4]

                comment_data[0] = comments[i].text
                comment_data[1] = comments[i].host.username
                comment_data[2] = comments[i].host.profile.image.name
                comment_data[3] = comments[i].id
        
                comments_list.append(comment_data)

                i += 1

            print("Comments list: ", comments_list)
    
            data = {"type":"load_comments", "comments_list": comments_list}
            
            self.groupSend(data)

        elif click_type == "load_posts":
            posts = Post.objects.all().order_by('-created')[:5]

            posts_list = []

            for i in range(len(posts)):
                posts_data = [1,2,3,4]

    def load_comments(self, event):
        print("uspex")
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "comments_list" : event["comments_list"],
        }))

    def load_end(self, event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
        }))
    

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        
        self.room_group_name = "chat_%s" % self.room_name

        print("r:", self.room_group_name)

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

    def groupSend(self, data):
        self.room_group_name = "chat_%s" % self.room_name
                
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, data
        )

        print("channel layer: ", self.channel_layer)

    def currentGroupSend(self, data, sender):
        self.room_group_name = "chat_%s" % sender

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, data
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        print(text_data_json)
        
        message_type = text_data_json['type']

        message = text_data_json['message']
        id = text_data_json["id"]
        sender = text_data_json["sender"]
        receiver = text_data_json["receiver"]
        image_url = text_data_json["image_url"]
        place = text_data_json["place"]

        parent_message_id = text_data_json["parent_message_id"]

        send_data = {
            "type" : message_type,
            "id" : id, 
            "message" : message,
            "sender" : sender,
            "receiver" : receiver,
            "image_url" : image_url,
            "place" : place,
        }

        if message_type == 'chat_edit':
            m = Message.objects.get(id=id)
            m.text = message
            m.save()

            updated = m.updated.strftime('%H:%M')

            send_data["updated"] = updated

            self.groupSend(send_data)

            self.currentGroupSend(send_data, sender)

        elif message_type == 'chat_message':
            if image_url != None:
                time = text_data_json['time']
                match = re.match(r'data:image/(\w+);base64,(.+)', image_url)

                image_data = match.group(2)
                image_data_bytes = base64.b64decode(image_data)
                image_content_file = ContentFile(image_data_bytes, name=f"{time}.jpg")
            else: 
                image_content_file = None

            if parent_message_id != None: 
                parent_message_model = Message.objects.get(id = parent_message_id)
                parent_message_text = parent_message_model.text
                parent_message_image = None
                if parent_message_model.image != '': 
                    parent_message_image = parent_message_model.image.url
            else: 
                parent_message_model = None 
                parent_message_text = None
                parent_message_image = None

            print("sender", sender)

            new_message = Message.objects.create(
                text=message,
                sender=User.objects.get(username=sender),
                receiver=User.objects.get(username=receiver),
                image=image_content_file,
                parent_message=parent_message_model, 
            )

            created = new_message.created.strftime('%H:%M')

            send_data["created"] = created
            send_data["id"] = new_message.id
            send_data["parent_message_text"] = parent_message_text
            send_data["parent_message_image"] = parent_message_image

            self.groupSend(send_data)

            self.currentGroupSend(send_data, sender)

        elif message_type == 'chat_delete': 
            m = Message.objects.get(id=id)
            m.delete()

            self.currentGroupSend(send_data, receiver)
            self.groupSend(send_data)
        elif message_type == 'load_messages':
            loads_count = text_data_json['messages_load_count']

            sender_model = User.objects.get(username = sender)    
            receiver_model = User.objects.get(username = receiver)        

            messages = Message.objects.filter(receiver = receiver_model, sender = sender_model).select_related('receiver', 'sender')|Message.objects.filter(receiver=sender_model, sender=receiver_model).select_related('receiver', 'sender').order_by("created")

            count_to = loads_count*10
            count_from = count_to-10

            print("huiiiiiiiiiiiii", loads_count, count_to, count_from)

            messages_list = messages[count_from:count_to]

            for i in range(len(messages_list)):
                if messages_list[i].parent_message_id != None: 
                    parent_message_model = Message.objects.get(id = messages_list[i].parent_message_id)
                    parent_message_text = parent_message_model.text
                    parent_message_image = None
                    if parent_message_model.image != '': 
                        parent_message_image = parent_message_model.image.url
                else: 
                    parent_message_model = None 
                    parent_message_text = None
                    parent_message_image = None

                if messages_list[i].image != '':
                    image_url = messages_list[i].image.url
                else: 
                    image_url = None

                send_data["created"] = messages_list[i].created.strftime('%H:%M')
                send_data["id"] = messages_list[i].id
                send_data["parent_message_text"] = parent_message_text
                send_data["parent_message_image"] = parent_message_image
                send_data["place"] = "top_board"
                send_data["type"] = "chat_message"
                send_data["message"] = messages_list[i].text
                send_data["image_url"] = image_url
                send_data["sender"] = User.objects.get(id = messages_list[i].sender_id).username    
                send_data["receiver"] = User.objects.get(id = messages_list[i].receiver_id).username
                
                print('message_data', messages_list[i].image, messages_list[i].text, messages_list[0].created, messages_list[0].id)

                self.groupSend(send_data)
            

    def chat_delete(self,event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "id" : event["id"], 
            "sender" : event["sender"],
            "receiver" : event["receiver"],
        }))
    
    # Receive message from room group
    def chat_message(self, event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "message": event["message"], 
            "sender" : event["sender"], 
            "receiver" : event["receiver"], 
            "id" : event["id"], 
            "created" : event["created"], 
            "image_url" : event["image_url"],
            "parent_message_text" : event["parent_message_text"],
            "parent_message_image" : event["parent_message_image"]
        }))

    def chat_edit(self, event):
        self.send(text_data=json.dumps({
            "type" : event["type"],
            "message" : event["message"],
            "sender" : event["sender"],
            "receiver" : event["receiver"],
            "id" : event["id"],
        }))
