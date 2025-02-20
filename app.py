import json
import os
import threading
import logging

from flask import Flask, jsonify, g
import boto3
import pymsteams
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics, Counter
from pydantic import BaseModel, Field

from configdata import BaseConfig

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


def poll_sqs_teams_loop(sqs_client,config):
    """
    Constantly checks SQS queue for messages and processes them to send to teams if possible
    """
    while not stop_event.is_set():
        try:
            response = sqs_client.receive_message(
                QueueUrl=config.PRIORITY_QUEUE, WaitTimeSeconds=2)

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

                teams_message = pymsteams.connectorcard(config.TEAMS_WEBHOOK_URL)
                teams_message.title(f"Priority {handled_body['priority']}: {handled_body['title']}")
                teams_message.text(handled_body['description'])
                teams_message.send()

                request_counter.labels(priority="High").inc()

                sqs_client.delete_message(QueueUrl=config.PRIORITY_QUEUE, ReceiptHandle=receipt_handle)

        except Exception as e:
            # Use logging instead!!
            print(f"Error, cannot poll: {e}")


def create_app(sqs_client=None, config=None):
    app = Flask(__name__)

    # Initialize Prometheus Metrics once
    metrics = PrometheusMetrics(app)

    if config is None:
        config = BaseConfig()

    if sqs_client is None:
        sqs_client = boto3.client('sqs', region_name=config.AWS_REGION, aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)

    sqs_thread = threading.Thread(target=poll_sqs_teams_loop, args=(sqs_client,config), daemon=True)
    sqs_thread.start()

    # Store configuration in app config for other entities
    app.config.from_object(config)

    @app.route('/health', methods=["GET"])
    def health_check():
        """ Checks health, endpoint """
        return jsonify({"status": "healthy"}), 200

    return app


if __name__ == '__main__':
    create_app().run()
