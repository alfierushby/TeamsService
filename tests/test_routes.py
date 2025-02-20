import json
import os

import boto3
from dependency_injector.wiring import Provide
from containers import Container


def test_empty_string_description_post(priority_queue: str = Provide[Container.priority_queue]):
    """Test a post with an empty string description
    :param client: The client to interact with the app
    """
    # Simulate form submission
    # Get the correct queue URL from Flask's test config

    # Ensure we use the same region as in mock_env
    sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION"))

    external_data = {
        "title": "Urgent Issue",
        "description": "Fix ASAP",
        "priority": "medium"
    }

    sqs.send_message(QueueUrl=priority_queue, MessageBody=json.dumps(external_data))



