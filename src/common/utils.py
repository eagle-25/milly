import secrets
import time
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from common.exceptions import ParameterRequired


def get_or_raise(
    payload: dict[str, Any],
    key: str = "",
    exception: type[Exception] = ParameterRequired,
) -> Any:
    if not (value := payload.get(key)):
        raise exception(key)
    return value


def new_id() -> str:
    """
    13자리 ms 타임스탬프 + 6자리 랜덤값 = 19자리 숫자 문자열
    시간순으로 정렬되기 때문에 B-Tree 인덱스에 유리함.
    """
    ts_ms = int(time.time() * 1000)  # epoch ms (13자리)
    rand = secrets.randbelow(10_000)  # 0 ~ 9999
    return f"{ts_ms:013d}-{rand:04d}"  # 총 18자리 숫자 문자열


def parse_datetime_with_default(
    datetime_str: str | None, 
) -> datetime:
    """
    datetime 문자열을 파싱하고 timezone aware로 변환
    
    Args:
        datetime_str: ISO 형식의 datetime 문자열 (옵션)
        default: 기본값 (None이면 현재 시간)
    
    Returns:
        timezone aware datetime 객체
    """
    parsed_dt = parse_datetime(datetime_str)
    if not parsed_dt:
        raise ValueError(f"Invalid datetime format: {datetime_str}")
    
    # timezone naive인 경우 aware로 변환
    if parsed_dt.tzinfo is None:
        parsed_dt = timezone.make_aware(parsed_dt)
    
    return parsed_dt