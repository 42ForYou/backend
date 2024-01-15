from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

from channels.db import database_sync_to_async


class IntraIDBackend(BaseBackend):
    @database_sync_to_async
    def authenticate(self, request, intra_id=None, password=None):
        return self.get_user(intra_id)

    @database_sync_to_async
    def get_user(self, intra_id):
        try:
            user = get_user_model().objects.get(intra_id=intra_id)
            return user
        except get_user_model().DoesNotExist:
            return None
