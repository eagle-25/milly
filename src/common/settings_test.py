from .settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    },
    "replica": {
        "ENGINE": "django.db.backends.sqlite3",
        "TEST": {
            "MIRROR": "default",
        },
    },
}

# 테스트 설정 파일이 로드되었음을 확인하는 변수
TEST_SETTINGS_LOADED = True
print("🧪 TEST SETTINGS LOADED: Using settings.test.py")
