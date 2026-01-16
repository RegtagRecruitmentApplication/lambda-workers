import json
import uuid

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.parser import event_parser, envelopes
from dto.PictureRequest import PictureRequest
from dto.PictureResponse import PictureResponse
from services.PictureGenerationService import generate_picture

logger = Logger()

@logger.inject_lambda_context(log_event=True)
@event_parser(model=PictureRequest, envelope=envelopes.ApiGatewayEnvelope)
def lambda_handler(model: PictureRequest, context: LambdaContext):
    setup_logger(context)

    try:
        logger.info(f"Started request: {context.aws_request_id}")

        s3_url = generate_picture(model, context.aws_request_id)

        response = PictureResponse(s3_url=s3_url, request_id=context.aws_request_id)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": response.model_dump_json()
        }
    except Exception as e:
        logger.exception(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"exception": str(e)})
        }
    
def setup_logger(context: LambdaContext):
    logger.set_correlation_id(context.aws_request_id)
    logger.append_keys(
        user_id="api_gateway",
        operation_id=f"osaka_worker-{str(uuid.uuid4())}"
    )
