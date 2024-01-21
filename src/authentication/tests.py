import json
import unittest
from django.urls import reverse
from django.test import AsyncClient
from asgiref.sync import sync_to_async
from accounts.models import User


class AsyncRegisterView(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = AsyncClient()

    async def test_async_user_signup(self):
        url = reverse("register")
        data = {"intra_id": "testuser", "password": "testpassword123"}
        response = await self.client.post(
            url, json.dumps(data), content_type="application/json"
        )

        # 상태 코드 검증
        self.assertEqual(response.status_code, 201)
        await sync_to_async(User.objects.filter(intra_id="testuser").delete)()

    async def test_async_invalid_signup(self):
        url = reverse("register")
        data = {"intra_id": "", "password": "testpassword123"}
        response = await self.client.post(
            url, json.dumps(data), content_type="application/json"
        )

        # 잘못된 요청에 대한 상태 코드 검증
        self.assertEqual(response.status_code, 400)

    async def test_async_delete(self):
        # 먼저 사용자 등록
        register_url = reverse("register")
        register_data = {"intra_id": "testuser", "password": "testpassword123"}
        await self.client.post(
            register_url, json.dumps(register_data), content_type="application/json"
        )

        # 사용자 삭제
        unregister_url = reverse("register")
        unregister_data = {"intra_id": "testuser"}
        response = await self.client.delete(
            unregister_url, json.dumps(unregister_data), content_type="application/json"
        )

        # 상태 코드 검증
        self.assertEqual(response.status_code, 200)
