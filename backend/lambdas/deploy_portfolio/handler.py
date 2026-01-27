import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Lambda deploy_portfolio iniciada")
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Lambda deploy_portfolio pronta para implementação'})
    }
