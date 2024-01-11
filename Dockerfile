FROM python:3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 프로젝트 파일 복사
COPY . .

# Django 애플리케이션 실행 명령
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
