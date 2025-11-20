# Python 3.12 slim 이미지 사용
FROM python:3.12-slim

# 환경변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (PostgreSQL 클라이언트 등)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 전체 프로젝트 복사
COPY . /app/

# 의존성 설치 
RUN pip install -e .

# wait-for-it 스크립트에 실행 권한 부여
RUN chmod +x /app/scripts/wait-for-it.sh

# 포트 8000 노출
EXPOSE 8000

# Django 개발 서버 실행
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]