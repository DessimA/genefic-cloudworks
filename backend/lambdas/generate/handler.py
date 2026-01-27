import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Lambda generate iniciada")
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Lambda generate pronta para implementação'})
    }
