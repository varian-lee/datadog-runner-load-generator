FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY app.py .

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV DD_SERVICE=load-generator
ENV DD_ENV=demo  
ENV DD_VERSION=0.1.0
ENV DD_LOGS_INJECTION=true

# 기본 설정
ENV BASE_URL=http://frontend-svc
ENV INTERVAL_SECONDS=30

# 애플리케이션 실행
CMD ["python", "app.py"]
