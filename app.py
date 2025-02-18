import json
import os
import threading
import logging

from flask import Flask, jsonify
import boto3
import pymsteams
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics, Counter
from pydantic import BaseModel, Field

stop_event = threading.Event()

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
P1_QUEUE_URL = os.getenv('P1_QUEUE_URL')
TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL')
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
ACCESS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

gunicorn_logger = logging.getLogger("gunicorn.error")

# Want the minimum length to be at least 1, otherwise "" can be sent which breaks certain APIs.
class Request(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    priority: str = Field(..., min_length=1)

request_counter = Counter(
    "priority_requests_total",
    "Total priority requests processed",
    labelnames=["priority"]
)

def poll_sqs_teams_loop(sqs_client):
    """
    Constantly checks SQS queue for messages and processes them to send to teams if possible
    """
    while not stop_event.is_set():
        try:
            response = sqs_client.receive_message(
                QueueUrl=P1_QUEUE_URL, WaitTimeSeconds=2)

            messages = response.get("Messages", [])

            if not messages:
                # Use logging instead!!
                gunicorn_logger.info("No messages available")
                continue

            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = json.loads(message['Body'])

                handled_body = Request(**body).model_dump()

                gunicorn_logger.info(f"Message Body: {body}")

                teams_message = pymsteams.connectorcard(TEAMS_WEBHOOK_URL)
                teams_message.title(f"Priority {handled_body['priority']}: {handled_body['title']}")
                teams_message.text(handled_body['description'])
                teams_message.send()

                request_counter.labels(priority="High").inc()

                sqs_client.delete_message(QueueUrl=P1_QUEUE_URL, ReceiptHandle=receipt_handle)

        except Exception as e:
            # Use logging instead!!
            gunicorn_logger.info(f"Error, cannot poll: {e}")

def create_app():
    app = Flask(__name__)

    # Initialize Prometheus Metrics once
    metrics = PrometheusMetrics(app)

    sqs_client = boto3.client('sqs', region_name=AWS_REGION, aws_access_key_id=ACCESS_KEY,
                              aws_secret_access_key=ACCESS_SECRET)
    sqs_thread = threading.Thread(target=poll_sqs_teams_loop, args=(sqs_client,), daemon=True)
    sqs_thread.start()

    @app.route('/health',methods=["GET"])
    def health_check():
        """ Checks health, endpoint """
        return jsonify({"status":"healthy"}),200

    return app

if __name__ == '__main__':
    create_app().run()