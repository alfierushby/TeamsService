import json
import os
import threading
import logging

from dependency_injector.wiring import inject, Provide
from flask import Flask, jsonify
import boto3
import pymsteams
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics, Counter
from pydantic import BaseModel, Field

from containers import Container

stop_event = threading.Event()

load_dotenv()

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


def poll_sqs_teams_loop(container: Container):
    """
    Constantly checks SQS queue for messages and processes them to send to teams if possible
    """
    config = container.config
    while not stop_event.is_set():
        try:
            response = container.sqs_client().receive_message(
                QueueUrl=config.priority_queue(), WaitTimeSeconds=20)

            messages = response.get("Messages", [])

            if not messages:
                # Use logging instead!!
                print("No messages available")
                continue

            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = json.loads(message['Body'])

                handled_body = Request(**body).model_dump()

                print(f"Message Body: {body}")

                teams_message = pymsteams.connectorcard(config.teams_web_hook())
                teams_message.title(f"Priority {handled_body['priority']}: {handled_body['title']}")
                teams_message.text(handled_body['description'])
                teams_message.send()

                request_counter.labels(priority="High").inc()

                container.sqs_client().delete_message(QueueUrl=config.priority_queue(), ReceiptHandle=receipt_handle)

        except Exception as e:
            # Use logging instead!!
            print(f"Error, cannot poll: {e}")

def create_app(container: Container = None):
    app = Flask(__name__)

    # Initialize Prometheus Metrics once
    metrics = PrometheusMetrics(app)

    # Initialize DI container if not provided
    if container is None:
        container = Container()
        container.config.from_dict({
            "aws_region": os.getenv("AWS_REGION"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "priority_queue": os.getenv("P1_QUEUE_URL"),
            "teams_web_hook": os.getenv("TEAMS_WEBHOOK_URL")
        })

    sqs_thread = threading.Thread(target=poll_sqs_teams_loop,args=(container,), daemon=True)
    sqs_thread.start()

    @app.route('/health',methods=["GET"])
    def health_check():
        """ Checks health, endpoint """
        return jsonify({"status":"healthy"}),200

    return app

if __name__ == '__main__':
    create_app().run()