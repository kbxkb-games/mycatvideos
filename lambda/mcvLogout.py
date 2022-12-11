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
try:
    regexUserid = re.compile(r'^[A-Za-z0-9]{6,}$')
    regexPassword = re.compile(r'^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-\\(\\)]).{8,}$')
except re.error:
    logger.error("Invalid regex pattern")
else:
    logger.info("Regex compilers initialized!")

#=========================================================
#Function to validate request body
#Accepts string, NOT JSON Object
#Returns Tuple: Boolean (T/F), string message, Json object
#=========================================================
def validateJSON(requestBody):
    if requestBody is not None:
        requestJsonObject = None
        try:
            requestJsonObject = json.loads(requestBody)
        except ValueError as err:
            return False, "Request Body ({})is invalid JSON. Error: ".format(requestBody) + " ".join(str(err).split()), None
        else:
            if "userid" not in requestJsonObject:
                return False, "'userid' missing in Request Body", None
            if not re.fullmatch(regexUserid, requestJsonObject["userid"]):
                return False, "Value of 'userid' must be alphanumeric with minimum length 6, found {}".format(requestJsonObject["userid"]), None
            return True, "", requestJsonObject
    else:
        return False, "Request Body cannot be empty. It must be a JSON string specifying \"userid\" and \"password\"", None

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
    if "body" not in event:
        responseDictBarebones['statusCode'] = 400
        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
        responseDictBarebones['headers']['Content-Type'] = "application/json"
        responseDictBarebones['body'] = json.dumps('body is missing in event parameter')
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
    #HANDLE ANYTHING OTHER THAN POST
    #=========================================================
    if event['httpMethod'] != 'POST':
        responseDictBarebones['statusCode'] = 400
        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
        responseDictBarebones['headers']['Content-Type'] = "application/json"
        responseDictBarebones['body'] = json.dumps('Only POST method allowed for Logout')
        return responseDictBarebones
        
    #=========================================================
    #NOW WE HAVE ONLY POST LEFT
    #=========================================================
    else:
        isRequestBodyValid, errorMessage, requestJsonObject = validateJSON(event['body'])
        if not isRequestBodyValid:
            responseDictBarebones['statusCode'] = 400
            responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
            responseDictBarebones['headers']['Content-Type'] = "application/json"
            responseDictBarebones['body'] = json.dumps(errorMessage)
            return responseDictBarebones
        else:
            userid = requestJsonObject["userid"]

            #=========================================================
            #LOG USER OUT BY UPDATING DYNAMODB TABLE mycatvideos_users
            #=========================================================
            try:
                userRecord = dynamodb.Table('mycatvideos_users').get_item(
                    Key={
                        'userid': userid
                    }
                )
            except botocore.exceptions.ClientError as e:
                #=========================================================
                #USER DOES NOT EXIST - SEND CRYPTIC ERROR MESSAGE
                #=========================================================
                responseDictBarebones['statusCode'] = 401
                responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
                responseDictBarebones['headers']['Content-Type'] = "application/json"
                responseDictBarebones['body'] = json.dumps('Invalid Username or Password')
                return responseDictBarebones
            else:
                if 'Item' not in userRecord:
                    #=========================================================
                    #USER DOES NOT EXIST - SEND CRYPTIC ERROR MESSAGE
                    #=========================================================
                    responseDictBarebones['statusCode'] = 401
                    responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
                    responseDictBarebones['headers']['Content-Type'] = "application/json"
                    responseDictBarebones['body'] = json.dumps('Invalid Username or Password')
                    return responseDictBarebones
                if userRecord['Item']['loggedin'] == '0':
                    #=========================================================
                    #USER EXISTS BUT NOT LOGGED IN - NO OP, PRETEND LOG OUT OK
                    #=========================================================
                    responseBody = "Log Out Successful"
                    responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
                    responseDictBarebones['headers']['Content-Type'] = "application/json"
                    responseDictBarebones['body'] = json.dumps(responseBody)
                    return responseDictBarebones
                else:
                    #=========================================================
                    #LOG THEM OUT, UPDATE FLAG
                    #=========================================================
                    try:
                        dynamodb.Table('mycatvideos_users').update_item(
                            Key={
                                'userid': userid
                            },
                            UpdateExpression="set loggedin=:newLoggedIn",
                            ExpressionAttributeValues={
                                ':newLoggedIn': '0'
                            }
                        )
                    except botocore.exceptions.ClientError as e:
                        #=========================================================
                        #OOPS, SOMETHING WENT WRONG WHILE LOGGING IN, SEND 500
                        #=========================================================
                        errorMessage = "Log out failed. Details from DaynamoDB update failure: " + e.response['Error']['Message']
                        responseDictBarebones['statusCode'] = 500
                        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
                        responseDictBarebones['headers']['Content-Type'] = "application/json"
                        responseDictBarebones['body'] = json.dumps(errorMessage)
                        return responseDictBarebones
                    else:
                        #=========================================================
                        #LOG OUT SUCCESSFUL!
                        #=========================================================
                        responseBody = "Log Out Successful"
                        responseDictBarebones['headers']['Access-Control-Expose-Headers'] = "Content-Type"
                        responseDictBarebones['headers']['Content-Type'] = "application/json"
                        responseDictBarebones['body'] = json.dumps(responseBody)
                        return responseDictBarebones
