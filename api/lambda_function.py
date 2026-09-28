import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('dduwash')

def lambda_handler(event, context):
    try:
        bay_ids = ['Washbay 1', 'Washbay 2', 'Washbay 3', 'Washbay 4', 'Washbay 5', 'Washbay 6']
        results = []

        for bay_id in bay_ids:
            response = table.query(
                KeyConditionExpression=Key('bay_id').eq(bay_id),
                ScanIndexForward=False,  # This makes it sort in descending order
                Limit=1  # We only want the most recent entry
            )
            if response['Items']:
                results.append(response['Items'][0])

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': 'https://www.dduwash.com',
                'Cache-Control': 'public, max-age=60',
                'Content-Type': 'application/json'
            },
            'body': results
        }
    except Exception as e:
        print(e) # Log error message for debugging
        return { # Return generic message to user
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': 'https://www.dduwash.com',
                'Content-Type': 'application/json'
            },
            'body': {
                'error': 'internal server error'
            }
        }
