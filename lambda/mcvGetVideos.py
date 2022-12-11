import os
import re
import json
import boto3
import logging
import botocore

#=========================================================
#GLOBAL VARS
#=========================================================
logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    #==============================================================
    #DEFINE BAREBONES RESPONSE, ONE SENT FOR PREFLIGHT OPTIONS
    #==============================================================
    #If you get preflight errros on browser, set the following
    #values explicitly on the CORS pane for the API Gateway:
    #Access-Control-Allow-Origin:http://localhost:8000 (not *)
    #Access-Control-Allow-Headers:Content-Type, x-api-key, x-api-id
    #Access-Control-Allow-Methods:POST, PUT, GET, OPTIONS
    #Access-Control-Expose-Headers:Content-Type
    #Access-Control-Max-Age:86400
    #This should address the issue, and once addressed, revert back
    #==============================================================
    responseDictBarebones = {
        'statusCode': 200,
        'headers': {
            #"Access-Control-Allow-Origin": "http://localhost:8000",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, PUT, GET, OPTIONS",
            "X-Requested-With": "*",
            "Access-Control-Allow-Headers": "Content-Type, x-api-key, x-api-id, Access-Control-Allow-Headers, Access-Control-Allow-Origin, Access-Control-Allow-Methods, X-Requested-With",
            "Access-Control-Max-Age": 86400
        }
    }
    
    #=========================================================
    #VERY BASIC CHECKS HERE...
    #=========================================================
    if "httpMethod" not in event or event['httpMethod'] is None:
        responseDictBarebones['statusCode'] = 400
        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
        responseDictBarebones['headers']['Content-Type'] = "application/json"
        responseDictBarebones['body'] = json.dumps('httpMethod is missing in event parameter')
        return responseDictBarebones
    if "queryStringParameters" not in event:
        responseDictBarebones['statusCode'] = 400
        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
        responseDictBarebones['headers']['Content-Type'] = "application/json"
        responseDictBarebones['body'] = json.dumps('queryStringParameters is missing in event parameter')
        return responseDictBarebones
    if "userid" not in event['queryStringParameters']:
        responseDictBarebones['statusCode'] = 400
        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
        responseDictBarebones['headers']['Content-Type'] = "application/json"
        responseDictBarebones['body'] = json.dumps('userid must be present as query string parameter')
        return responseDictBarebones
        
    #=========================================================
    #LOGGING
    #=========================================================
    logger.info("Request HTTP Method: " + event['httpMethod'])
    if event['body'] is not None:
        logger.info("Request Body: " + event['body'])
    
    #=========================================================
    #HANDLE OPTIONS
    #=========================================================
    if event['httpMethod'] == 'OPTIONS':
        return responseDictBarebones
        
    #=========================================================
    #HANDLE ANYTHING OTHER THAN GET
    #=========================================================
    if event['httpMethod'] != 'GET':
        responseDictBarebones['statusCode'] = 400
        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
        responseDictBarebones['headers']['Content-Type'] = "application/json"
        responseDictBarebones['body'] = json.dumps('Only GET method allowed for get videos API')
        return responseDictBarebones
        
    #=========================================================
    #NOW WE HAVE ONLY GET LEFT
    #=========================================================
    else:
        userid = event["queryStringParameters"]['userid']
        responseBody = json.dumps(
            [
                {
                    "name": "John Doe",
                    "number": "123456789",
                    "email": "john@does.com"
                },
                {
                    "name": "Alice X",
                    "number": "123456789",
                    "email": "alice@a.com"
                },
                {
                    "name": "Cinderella Y",
                    "number": "123456789",
                    "email": "cin@deralla.com"
                }
            ]
        )
        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
        responseDictBarebones['headers']['Content-Type'] = "application/json"
        responseDictBarebones['body'] = json.dumps(responseBody)
        return responseDictBarebones
