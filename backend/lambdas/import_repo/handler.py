import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Lambda import_repo iniciada")
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Lambda import_repo pronta para implementação'})
    }
