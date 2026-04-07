import json
from django.utils import timezone
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.models.chats import Chat, Message, ChatPresence


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"chat_{self.chat_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        is_member = await self.user_in_chat()
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.set_user_online()
        await self.mark_messages_delivered()
        await self.mark_messages_read()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_event",
                "user_id": self.user.id,
                "is_online": True,
                "last_seen": "",
            }
        )

    async def disconnect(self, close_code):
        await self.set_user_offline()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_event",
                "user_id": self.user.id,
                "is_online": False,
                "last_seen": timezone.now().strftime("%H:%M"),
            }
        )

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            message_text = data.get("message", "").strip()
            if not message_text:
                return

            message = await self.save_message(message_text)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": message.id,
                    "message": message.text,
                    "sender_id": message.sender_id,
                    "created_at": message.created_at.strftime("%H:%M"),
                    "status": "sent",
                }
            )

        elif action == "read_messages":
            updated_ids = await self.mark_messages_read()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "messages_read_event",
                    "message_ids": updated_ids,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message_id": event["message_id"],
            "message": event["message"],
            "sender_id": event["sender_id"],
            "created_at": event["created_at"],
            "status": event["status"],
        }))

    async def presence_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "presence",
            "user_id": event["user_id"],
            "is_online": event["is_online"],
            "last_seen": event["last_seen"],
        }))

    async def messages_read_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "messages_read",
            "message_ids": event["message_ids"],
        }))

    @database_sync_to_async
    def user_in_chat(self):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return self.user.id in [chat.buyer_id, chat.seller_id]
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text):
        chat = Chat.objects.get(id=self.chat_id)
        return Message.objects.create(
            chat=chat,
            sender=self.user,
            text=text
        )

    @database_sync_to_async
    def set_user_online(self):
        chat = Chat.objects.get(id=self.chat_id)
        ChatPresence.objects.update_or_create(
            chat=chat,
            user=self.user,
            defaults={
                "is_online": True,
                "last_seen": timezone.now()
            }
        )

    @database_sync_to_async
    def set_user_offline(self):
        chat = Chat.objects.get(id=self.chat_id)
        ChatPresence.objects.update_or_create(
            chat=chat,
            user=self.user,
            defaults={
                "is_online": False,
                "last_seen": timezone.now()
            }
        )

    @database_sync_to_async
    def mark_messages_delivered(self):
        chat = Chat.objects.get(id=self.chat_id)
        Message.objects.filter(
            chat=chat
        ).exclude(
            sender=self.user
        ).filter(
            delivered_at__isnull=True
        ).update(delivered_at=timezone.now())

    @database_sync_to_async
    def mark_messages_read(self):
        chat = Chat.objects.get(id=self.chat_id)
        qs = Message.objects.filter(
            chat=chat
        ).exclude(
            sender=self.user
        ).filter(
            read_at__isnull=True
        )

        ids = list(qs.values_list("id", flat=True))
        qs.update(read_at=timezone.now())
        return ids