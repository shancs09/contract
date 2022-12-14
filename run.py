#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 14 Nov 2022
@author: shanmsel@in.ibm.com
"""
import json,os,re,time,requests,bios
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions, CategoriesOptions, ClassificationsOptions
from flask import Flask, flash, request, redirect, render_template,jsonify
import PyPDF2,pandas as pd
import ibm_db, ibm_db_dbi as dbi


#CloudDB Credentials
CloudDB_dsn = 'DATABASE={};HOSTNAME={};PORT={};PROTOCOL=TCPIP;UID={uid};PWD={pwd};SECURITY=SSL'.format(
        'bludb',
        'b1bc1829-6f45-4cd4-bef4-10cf081900bf.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud',
        32304,
        uid='jhw60694',
        pwd="""gBZNmyBUQa0JBDVH""")

#Read Configuration
# config_yml=bios.read("config.yaml")
config_yml=bios.read("config.yaml")

## WKS Model
##Setting up Natual Language Understanding Service Credentials
# wks_wnl_apikey="UTonY4-OEylJP3RX-1-S8JHLEcbaosD_BgFIsUvfMl73"
# wks_wnl_url="https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/20cf926f-94f8-4d03-a042-9aa3d84813cf"
#Setting Configuration
wks_wnl_apikey=config_yml['wksmodel']['wks_wnl_apikey']
wks_wnl_url=config_yml['wksmodel']['wks_wnl_url']
wks_model_id=config_yml['wksmodel']['wks_model_id']

wks_authenticator = IAMAuthenticator(wks_wnl_apikey)
nlu = NaturalLanguageUnderstandingV1(version='2022-04-07',authenticator=wks_authenticator)
nlu.set_service_url(wks_wnl_url)
# wks_model_id='cd4bf121-c870-47c8-bf7e-800732fd3586'

# # NOTE: you must manually set API_KEY below using information retrieved from your IBM Cloud account.
# # binclass_wml_API_KEY = "XEF0v4yg_Tj8qUFPagbZ6cqFuq5Mz_m8xU0q1Z5RU82m"
# # wml_endpoint='https://us-south.ml.cloud.ibm.com/ml/v4/deployments/7e086ed6-4cd8-43db-bd1b-6961f204e89b/predictions?version=2022-08-08'
# binclass_wml_API_KEY = config_yml['wmlmodel']['wml_api_key']
# wml_endpoint=config_yml['wmlmodel']['wml_url']

#Read Company Credit Data
credit_data=pd.read_csv('company_credit_data.csv')

##Flask App Configuration
app=Flask(__name__)
port = int( os.getenv( 'PORT', 8000 ) )

# @app.route('/fileupload', methods=['POST'])
# def upload_file():

#   if 'file' not in request.files:
#     resp = jsonify({'message' : 'No file part in the request'})
#     resp.status_code = 400
#     return resp 
  
#   file = request.files['file']
#   lines=str(file.read())
#   print(lines)
  
#   analysis_result = nlu.analyze(text=lines, features=Features(
#     entities=EntitiesOptions(model=wks_model_id)
#     )).get_result()
  
#   print(analysis_result)
#   wks_nl_result=analysis_result['entities']

#   final_data={}
#   for i in wks_nl_result:
#         print(i)
#         type=i['type']
#         value=i['text']    
#         value=value.replace("\\n", " ")
#         value=value.replace("\\r", " ")
#         value=value.replace("\r", " ")
#         value=value.replace("\\", " ")
#         value=value.replace("/", " ")
#         final_data[i['type']] = value

#   final_data = json.dumps(final_data)
#   print(final_data)
#   return final_data 


# @app.route('/objstorageurl', methods=['POST'])
# def objstorageurl():
  
#   args = request.args
#   fileurl = args.get('fileurl')
#   print(fileurl)
  
#   analysis_result = nlu.analyze(url=fileurl, features=Features(
#     entities=EntitiesOptions(model=wks_model_id)
#     )).get_result()
  
#   print(analysis_result)
#   wks_nl_result=analysis_result['entities']

#   final_data={}
#   for i in wks_nl_result:
#         print(i)
#         type=i['type']
#         value=i['text']    
#         value=value.replace("\\n", " ")
#         value=value.replace("\\r", " ")
#         value=value.replace("\r", " ")
#         value=value.replace("\\", " ")
#         value=value.replace("/", " ")
#         final_data[i['type']] = value

#   final_data = json.dumps(final_data)
#   print(final_data)
#   return final_data 


@app.route('/fileupload', methods=['POST'])
def fileupload():

  if 'file' not in request.files:
    resp = jsonify({'message' : 'No file part in the request'})
    resp.status_code = 400
    return resp 
  
  file = request.files['file']
  pdfReader=PyPDF2.PdfFileReader(file)
  numPages=pdfReader.numPages

  # print(pdfReader.numPages)
  fileobj=""
  for i in range(numPages):
    pageObj = pdfReader.getPage(i)
    # print(pageObj.extractText())
    fileobj+=str(pageObj.extractText())+"\n"
  print("*****FILELINE*****")
  # print(fileobj)
  analysis_result = nlu.analyze(text=fileobj, features=Features(
    entities=EntitiesOptions(model=wks_model_id)
    )).get_result()
  
  print(analysis_result)
  wks_nl_result=analysis_result['entities']

  final_data={}
  # final_data={"processData":{},"risk":{}}
  for i in wks_nl_result:
        print(i)
        type=i['type']
        value=i['text']  
        value=value.replace("\\n", "")  
        value=value.replace("\n", "")
        value=value.replace("\\r", "")
        value=value.replace("\r", " ")
        value=value.replace("\\", " ")
        # value=value.replace("/", " ")
        final_data[i['type']] = value

  # final_data = json.dumps(final_data)
  print(final_data)
  if 'compliance' not in final_data:
    final_data['compliance']='NotAvailable'

  company=final_data['thirdparty']

  # risk=credit_data['Risk'].loc[credit_data['Company'].str.contains(company,case=False,na=False)]
  # final_data['Risk']=risk.to_string(index=False)

  risk=credit_data.loc[credit_data['Company'].str.contains(company,case=False,na=False)]
  risk_js=risk.to_dict('records')[0]

  mod_final_data={}
  mod_final_data['processDO']=final_data
  mod_final_data['risk']=risk_js

  return jsonify(mod_final_data)


@app.route('/getevents', methods=['GET'])    
def getevents():
  #DBConnect
  CloudDB_connection = dbi.connect(CloudDB_dsn)
  query = 'SELECT * FROM "JHW60694"."CM_EVENT_CALENDER"'

  final_wd_df = pd.read_sql_query(query, con=CloudDB_connection)
  final_wd_df.rename(columns = {'EVENT_ID':'eventId','EVENT_NAME':'eventName','EVENT_SCOPE':'eventScope','CREATION_DATE':'creationDate','EFFECTIVE_DATE':'effectiveDate','CASE_ID':'caseId','TRANSACTION_DATE':'transactionDate'}, inplace = True)

  final_wd_df['creationDate'] = pd.to_datetime(final_wd_df['creationDate'], errors='coerce')
  final_wd_df['creationDate'] = final_wd_df['creationDate'].dt.strftime('%Y-%m-%d')

  final_wd_df['effectiveDate'] = pd.to_datetime(final_wd_df['effectiveDate'], errors='coerce')
  final_wd_df['effectiveDate'] = final_wd_df['effectiveDate'].dt.strftime('%Y-%m-%d')

  final_wd_df['transactionDate'] = pd.to_datetime(final_wd_df['transactionDate'], errors='coerce')
  final_wd_df['transactionDate'] = final_wd_df['transactionDate'].dt.strftime('%Y-%m-%d %X')
  
  final_data= final_wd_df.to_json(orient="records")
  final_data=json.loads(final_data)
  final_data= {"calendarEvents":final_data}
  # json.dumps(final_data)

  return jsonify(final_data)

@app.route('/insertevents', methods=['POST'])    
def insertevents():

  request_data = request.get_json()
  request_data= request_data['calendarEvents']
  final_wd_df=pd.DataFrame(request_data)
  
#   col_list=final_wd_df.columns.tolist()
#   col_list=[x.upper() for x in col_list]  
#   cols = ",".join([str(i) for i in col_list])
  final_wd_df.rename(columns = {'eventId':'EVENT_ID','eventName':'EVENT_NAME','eventScope':'EVENT_SCOPE','creationDate':'CREATION_DATE','effectiveDate':'EFFECTIVE_DATE','caseId':'CASE_ID'}, inplace = True)
  # col_list=final_wd_df.columns.tolist()
  # col_list=[x.upper() for x in col_list] 
  cols = ",".join([str(i) for i in final_wd_df.columns.tolist()])
  tuple_of_tuples = tuple([tuple(x) for x in final_wd_df.values])
  print(cols) 
  #DBConnect
  cloud_db_conn = ibm_db.connect(CloudDB_dsn,'','')
  sql="INSERT INTO JHW60694.CM_EVENT_CALENDER (" + cols + ") VALUES (?,?,?,?,?,?)"
  stmt=ibm_db.prepare(cloud_db_conn,sql)
  rows_inserted=ibm_db.execute_many(stmt,tuple_of_tuples)
  ibm_db.close(cloud_db_conn)
  response={}
  response['NoOfRowsAdded']=rows_inserted
  print(response)
  return json.dumps(response)
  

@app.route('/')
def home():
    return 'Welcome to Python Flask!'

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=9101,debug=False)

