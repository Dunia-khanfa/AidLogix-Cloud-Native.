import os, json, boto3, time

SQS_URL = os.environ.get('QUEUE_URL')
DYNAMO_TABLE = os.environ.get('DYNAMODB_TABLE')
REGION = "eu-west-1"

sqs = boto3.client('sqs', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION).Table(DYNAMO_TABLE)

def process():
    print("Worker started. Monitoring SQS...")
    while True:
        response = sqs.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=10)
        if 'Messages' in response:
            for msg in response['Messages']:
                data = json.loads(msg['Body'])
                dynamodb.put_item(Item={
                    'uid': data['id'],
                    'username': data['user'],
                    'content': data['content'],
                    'type': data['type'],
                    'status': 'Pending'
                })
                sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=msg['ReceiptHandle'])
                print(f"Processed Request: {data['id']}")
        time.sleep(1)

if __name__ == "__main__":
    process()
