"""
Protected CRUD endpoints for user profiles backed by DynamoDB.
All requests are authenticated via the custom Lambda authorizer.
"""

import os
import json
import uuid
import logging
import time
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("USERS_TABLE", "user-profiles"))


def handler(event, context):
    """Route requests to the appropriate CRUD handler based on HTTP method."""
    http_method = event.get("httpMethod", "")
    path = event.get("path", "")
    path_params = event.get("pathParameters") or {}

    logger.info("Received %s %s", http_method, path)

    try:
        if http_method == "GET" and "userId" in path_params:
            return get_user(path_params["userId"])
        elif http_method == "GET":
            return list_users()
        elif http_method == "POST":
            body = json.loads(event.get("body", "{}"))
            return create_user(body)
        elif http_method == "PUT" and "userId" in path_params:
            body = json.loads(event.get("body", "{}"))
            return update_user(path_params["userId"], body)
        elif http_method == "DELETE" and "userId" in path_params:
            return delete_user(path_params["userId"])
        else:
            return response(405, {"error": "Method not allowed"})

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON in request body"})
    except Exception as e:
        logger.error("Unhandled error: %s", str(e))
        return response(500, {"error": "Internal server error"})


def get_user(user_id):
    """Retrieve a single user profile by ID."""
    result = table.get_item(Key={"userId": user_id})
    item = result.get("Item")

    if not item:
        return response(404, {"error": "User not found"})

    return response(200, item)


def list_users():
    """List all user profiles. In production, add pagination."""
    result = table.scan(Limit=50)
    items = result.get("Items", [])

    return response(200, {
        "users": items,
        "count": len(items),
    })


def create_user(body):
    """Create a new user profile."""
    required_fields = ["email", "name"]
    for field in required_fields:
        if field not in body:
            return response(400, {"error": f"Missing required field: {field}"})

    user_id = str(uuid.uuid4())
    now = int(time.time())

    item = {
        "userId": user_id,
        "email": body["email"],
        "name": body["name"],
        "bio": body.get("bio", ""),
        "createdAt": now,
        "updatedAt": now,
    }

    table.put_item(Item=item)
    logger.info("Created user: %s", user_id)

    return response(201, item)


def update_user(user_id, body):
    """Update an existing user profile."""
    existing = table.get_item(Key={"userId": user_id})
    if "Item" not in existing:
        return response(404, {"error": "User not found"})

    allowed_fields = ["name", "email", "bio"]
    update_expr_parts = []
    expr_attr_names = {}
    expr_attr_values = {}

    for field in allowed_fields:
        if field in body:
            placeholder = f"#{field}"
            value_key = f":{field}"
            update_expr_parts.append(f"{placeholder} = {value_key}")
            expr_attr_names[placeholder] = field
            expr_attr_values[value_key] = body[field]

    if not update_expr_parts:
        return response(400, {"error": "No valid fields to update"})

    update_expr_parts.append("#updatedAt = :updatedAt")
    expr_attr_names["#updatedAt"] = "updatedAt"
    expr_attr_values[":updatedAt"] = int(time.time())

    result = table.update_item(
        Key={"userId": user_id},
        UpdateExpression="SET " + ", ".join(update_expr_parts),
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW",
    )

    logger.info("Updated user: %s", user_id)
    return response(200, result["Attributes"])


def delete_user(user_id):
    """Delete a user profile."""
    existing = table.get_item(Key={"userId": user_id})
    if "Item" not in existing:
        return response(404, {"error": "User not found"})

    table.delete_item(Key={"userId": user_id})
    logger.info("Deleted user: %s", user_id)

    return response(200, {"message": "User deleted", "userId": user_id})


def response(status_code, body):
    """Build a standard API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }
