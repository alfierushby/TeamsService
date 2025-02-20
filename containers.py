import os

import boto3
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """Dependency injection container for Flask"""

    config = providers.Configuration()

    # Singleton so that the application only has one sqs on runtime. Can be overridden for testing
    sqs_client = providers.Singleton(
        boto3.client,
        service_name="sqs",
        region_name=config.aws_region,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
    )

    # Queue URLs provider
    config.set('priority_queue',"Hi")
    config.set('teams_web_hook',os.getenv("TEAMS_WEBHOOK_URL","default.com"))
