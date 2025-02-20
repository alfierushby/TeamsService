import os

import boto3
import pytest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from app import create_app
from moto import mock_aws

from containers import Container
from tests import test_routes

load_dotenv()

@pytest.fixture
def app():
    """Create and configure a new Flask app instance for testing
    :return: app created
    """
    with patch('pymsteams.connectorcard') as MockConnectorCard:
        with mock_aws():
            sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION"))

            #  Create mock queue
            queue = sqs.create_queue(QueueName="test")["QueueUrl"]

            # Override the send message to be true
            mock_instance = MockConnectorCard.return_value
            mock_instance.send.return_value = True  # Simulate a successful send

            # Set up container for testing
            container = Container()

            # Override SQS client with mock version
            container.sqs_client.override(sqs)

            # Override priority queues with test values
            container.priority_queue = queue

            container.wire(modules=[test_routes])

            app = create_app(container)

            yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app
    :param app: The flask app
    :return: The app with a test client created
    """
    return app.test_client()
