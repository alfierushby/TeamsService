import os
import threading

from flask import Flask, jsonify
import boto3
import pymsteams
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
P1_QUEUE_URL = os.getenv('P1_QUEUE_URL')
TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL')
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
ACCESS_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')

app = Flask(__name__)


def poll_sqs_teams_loop():
    """
    Constantly checks SQS queue for messages and processes them to send to teams if possible
    """
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=P1_QUEUE_URL,MaxNumberOfMessages=1,WaitTimeSeconds=20)

            messages = response['Messages']
            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = message['Body']

                print(f"Message Body: {body}")


                teams_message = pymsteams.connectorcard(TEAMS_WEBHOOK_URL)
                teams_message.title(f"priority: {body[1]}: {body[3]}")
                teams_message.text("Test")
                teams_message.send()


        except Exception as e:
            print(f"Error, cannot poll: {e}")
        break



@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    sqs_client = boto3.client('sqs', region_name=AWS_REGION, aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=ACCESS_SECRET)
    print("test")
    sqs_thread = threading.Thread(target=poll_sqs_teams_loop,daemon=True)
    sqs_thread.start()
    app.run()
