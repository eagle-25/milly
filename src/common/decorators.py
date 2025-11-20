import json
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest


# JSON body 파싱 데코레이터, 반복 줄이기 위해 추가
def parse_json_form_body[T](func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def _wrapper(
        request: HttpRequest, *args: dict[Any, Any], **kwargs: dict[Any, Any]
    ) -> T:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            payload = {}
        return func(request, payload, *args, **kwargs)

    return _wrapper
