import pytest
from django.contrib.auth.models import User
from django.db import transaction
from django.test import Client


@pytest.fixture
def api_client():
    """Django 테스트 클라이언트"""
    return Client()


@pytest.fixture
def test_user():
    """실제 테스트 사용자 생성"""
    with transaction.atomic():
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        yield user
        # 테스트 완료 후 정리
        user.delete()


@pytest.fixture
def authed_client(api_client, test_user):
    """인증된 클라이언트"""
    api_client.force_login(test_user)
    return api_client
