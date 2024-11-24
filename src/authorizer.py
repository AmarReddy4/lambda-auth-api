"""
Custom Lambda authorizer that validates JWT tokens from the Authorization header.
Returns an IAM policy document granting or denying access to the API.
"""

import os
import logging
from token_utils import decode_token

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda authorizer handler. Extracts the Bearer token from the
    Authorization header and validates it against the configured secret.
    """
    logger.info("Authorizer invoked")

    token = event.get("authorizationToken", "")
    method_arn = event.get("methodArn", "")

    if not token:
        logger.warning("No authorization token provided")
        raise Exception("Unauthorized")

    # Strip "Bearer " prefix if present
    if token.lower().startswith("bearer "):
        token = token[7:]

    try:
        payload = decode_token(token)
        principal_id = payload.get("sub", "unknown")
        logger.info("Token validated for principal: %s", principal_id)

        return generate_policy(principal_id, "Allow", method_arn, payload)

    except Exception as e:
        logger.error("Token validation failed: %s", str(e))
        raise Exception("Unauthorized")


def generate_policy(principal_id, effect, method_arn, context_data=None):
    """
    Generate an IAM policy document for API Gateway.
    Uses a wildcard resource to allow access to all methods/resources
    under the same API stage.
    """
    arn_parts = method_arn.split(":")
    region = arn_parts[3]
    account_id = arn_parts[4]
    api_gateway_arn = arn_parts[5].split("/")
    api_id = api_gateway_arn[0]
    stage = api_gateway_arn[1]

    resource_arn = (
        f"arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/*"
    )

    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource_arn,
                }
            ],
        },
    }

    if context_data:
        policy["context"] = {
            "sub": context_data.get("sub", ""),
            "email": context_data.get("email", ""),
            "role": context_data.get("role", "user"),
        }

    return policy
