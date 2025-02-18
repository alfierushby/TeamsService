From python:3.9.21-alpine3.21
WORKDIR /app
COPY  requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app
EXPOSE 8000
ENV TEAMS_WEBHOOK_URL=""
ENV P1_QUEUE_URL=""
ENV AWS_REGION=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]
