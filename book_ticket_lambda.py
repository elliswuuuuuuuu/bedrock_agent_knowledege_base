# -*- coding: utf-8 -*-

import json
import time
import os
import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF

s3 = boto3.client('s3')
bucket = os.environ.get('BUCKET_NAME')  #Name of bucket with data file and OpenAPI file
SENDER = os.environ.get('SENDER') 
product_name_map_file = 'product_code_name_map.txt' #Location of data file in S3

font_lib = "DejaVuSansCondensed.ttf"
local_product_name_map_file = '/tmp/product_code_name_map.txt' #Location of data file in S3
s3.download_file(bucket, product_name_map_file, local_product_name_map_file)
s3.download_file(bucket, font_lib, "/tmp/"+font_lib)


def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']

def get_named_property(event, name):
    return next(item for item in event['requestBody']['content']['application/json']['properties'] if item['name'] == name)['value']


def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', '/tmp/DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 14)
    # pdf.set_font("Arial", size=12)
    for key, value in data.items():
        print(key, value)
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=1, align="C")
    file_path = "/tmp/invoice.pdf"
    pdf.output(file_path)
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_path, bucket, file_path)
    return  file_path

user_info = {
            "id": "000001",
            "name": "Xiaoqun",
            "email": "test1@163.com",
            "drawer": "Xiaoqun",
            "reviewer": "Sam",
            "payee": "Lili",
            "phone": "0755-0000000",
            "address": "Qiantan, Shanghai",
            "card_name": "Amazon",
            "card_number": "00000000000000",
            "company_name": "Amazon",
            "tax_number": "440301999999980"
}

## 函数设置
functions_configs = {
    "get_product_code":
        {
            "product_name_map_file": local_product_name_map_file,
        }
}

product_name_map = {}
product_tax_map = {}
with open(functions_configs["get_product_code"]["product_name_map_file"],encoding="utf-8") as f:
    for line in f.readlines():
        line = line.strip()
        if line:
            code,name,tax = line.split("\t")
            product_name_map[code] = name
            product_tax_map[code] = min([float(tax_ins.strip('%')) / 100 for tax_ins in tax.split("、")])


def send_eamil(recipient: str, s3_file_path: str):
    sender = SENDER
    RECIPIENT = recipient

    AWS_REGION = "us-east-1"
    SUBJECT = "Invoice Info"
    
    BODY_TEXT = "Hello,\r\nInvoice has been generated, please check out attachment."

    # Download the S3 file to a temporary location
    tmp_file_path = '/tmp/' + os.path.basename(s3_file_path)
    s3.download_file(bucket, s3_file_path, tmp_file_path)

    ATTACHMENT = tmp_file_path

    # The HTML body of the email.
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello!</h1>
    <p>Invoice has been generated, please check out attachment.</p>
    </body>
    </html>
    """

    CHARSET = "utf-8"
    client = boto3.client('ses',region_name=AWS_REGION)
    msg = MIMEMultipart('mixed')

    msg['Subject'] = SUBJECT 
    msg['From'] = sender 
    msg['To'] = RECIPIENT

    msg_body = MIMEMultipart('alternative')
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    att = MIMEApplication(open(ATTACHMENT, 'rb').read())

    att.add_header('Content-Disposition','attachment',filename=os.path.basename(ATTACHMENT))
    msg.attach(msg_body)
    msg.attach(att)
    try:
        response = client.send_raw_email(
            Source=sender,
            Destinations=[
                RECIPIENT
            ],
            RawMessage={
                'Data':msg.as_string(),
            },
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
        return {"errcode": e.response['Error']['Message']} 
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return {"errcode": "0000", "MessageId": response['MessageId']} 

flight1 = [
    {"airline_name": "SUPARNA AIRLINES", "flight_number": "Y87587", "craft_type_name": "Aircraft 738(M)", "departure_time": "07:15", "arrival_time": "09:35", "departure_airport": "Shenzhen Baoan", "arrival_airport": "Shanghai Hongqiao", "price": 500},
    {"airline_name": "CHINA EASTERN AIRLINES", "flight_number": "MU5332", "craft_type_name": "Aircraft 32L(M)", "departure_time": "07:30", "arrival_time": "09:40", "departure_airport": "Shenzhen Baoan", "arrival_airport": "Shanghai Hongqiao", "price": 600},
    {"airline_name": "CHINA SOUTHERN AIRLINES", "flight_number": "CZ3625", "craft_type_name": "Aircraft 321(M)", "departure_time": "07:35", "arrival_time": "09:50", "departure_airport": "Shenzhen Baoan", "arrival_airport": "Shanghai Hongqiao", "price": 700}
]

flight2 = [
    {"airline_name": "SUPARNA AIRLINES", "flight_number": "Y87587", "craft_type_name": "Aircraft 738(M)", "departure_time": "07:15", "arrival_time": "09:35", "departure_airport": "Shenzhen Baoan", "arrival_airport": "Shanghai Hongqiao", "price": 800},
    {"airline_name": "CHINA EASTERN AIRLINES", "flight_number": "MU5332", "craft_type_name": "Aircraft 32L(M)", "departure_time": "07:30", "arrival_time": "09:40", "departure_airport": "Shenzhen Baoan", "arrival_airport": "Shanghai Hongqiao", "price": 900},
    {"airline_name": "CHINA SOUTHERN AIRLINES", "flight_number": "CZ3625", "craft_type_name": "Aircraft 321(M)", "departure_time": "07:35", "arrival_time": "09:50", "departure_airport": "Shenzhen Baoan", "arrival_airport": "Shanghai Hongqiao", "price": 1000}
]

data_flights = {
    "2024-02-22": flight1,
    "2024-02-23": flight2
}

def bookTicket(event):
    function_name = "getFlightInformation"
    print(f"calling method: {function_name}")
    print(f"Event: \n {json.dumps(event)}")

    flight_number = get_named_parameter(event, 'flight_number')
    
    data = {
        "airline_name": "SUPARNA AIRLINES",
        "flight_number": "Y87587",
        "craft_type_name": "Aircraft 738(M)",
        "departure_time": "07:15",
        "arrival_time": "09:35",
        "departure_airport": "Shenzhen Baoan",
        "arrival_airport": "Shanghai Hongqiao",
        "price": 500
    }

    result = {
                "input_args": {
                    "flight_number": flight_number
                },
                "status": "success",
                "results": {
                    "text_info": data
                }
            }

    return result

def getFlightInformation(event):
    function_name = "getFlightInformation"
    print(f"calling method: {function_name}")
    print(f"Event: \n {json.dumps(event)}")

    departure_city = get_named_parameter(event, 'departure_city')
    arrival_city = get_named_parameter(event, 'arrival_city')
    departure_date = get_named_parameter(event, 'departure_date')
    
    data = flight1

    result = {
                "input_args": {
                    "departure_city": departure_city,
                    "arrival_city": arrival_city,
                    "departure_data": departure_date
                },
                "status": "success",
                "results": {
                    "text_info": data
                }
            }

    return result

def sendReservationEmail(event):
    #定义输出
    res = {}
    res["input_args"] = {}
    res["input_args"]["invoice_code"] = "abc"
    res["input_args"]["invoice_number"] = "efg"
    res["input_args"]["email_address"] = "abc@amazon.com"
    res["status"] = "success"
    res["results"] = "邮件发送成功"
    print(res)
    return res


def lambda_handler(event, context):

    result = ''
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']
    
    print ("lambda_handler == > api_path: ",api_path)
    
    if api_path == '/getFlightInformation':
        result = getFlightInformation(event)
    elif api_path == '/bookTicket':
        result = bookTicket(event)
    elif api_path == '/sendReservationEmail':
        result = sendReservationEmail(event) 
    else:
        response_code = 404
        result = f"Unrecognized api path: {action_group}::{api_path}"

    response_body = {
        'application/json': {
            'body': json.dumps(result)
        }
    }
    
    session_attributes = event['sessionAttributes']
    prompt_session_attributes = event['promptSessionAttributes']
    
    print ("Event:", event)
    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': event['apiPath'],
        # 'httpMethod': event['HTTPMETHOD'], 
        'httpMethod': event['httpMethod'], 
        'httpStatusCode': response_code,
        'responseBody': response_body,
        'sessionAttributes': session_attributes,
        'promptSessionAttributes': prompt_session_attributes
    }

    api_response = {'messageVersion': '1.0', 'response': action_response}
        
    return api_response