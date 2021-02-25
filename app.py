import requests
from flask import Flask, render_template, url_for, request, redirect, jsonify, json, session, flash
from flask_login import LoginManager
from itsdangerous import URLSafeTimedSerializer
from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from time import strftime
import random
import string
import bson
import smtplib
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import datetime
import base64
import pymongo
import razorpay
from flask_cors import CORS
# from datetime import datetime
from flask_mail import Mail, Message
from pymongo import MongoClient
from collections import Counter
from functools import reduce
from dateutil.parser import parse
from datetime import timedelta, date
from collections import defaultdict
import datetime
from pythonappkit import Checksum
from pyfcm import FCMNotification
import calendar
import time
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required)

app = Flask(__name__)
CORS(app)
mail = Mail(app)


app = Flask(__name__)
app.config["MONGO_DBNAME"] = "OWO"
# app.config["MONGO_URI"] = "mongodb://owoadmin:sukeshfug@35.154.239.192:6909/OWO"
app.config["MONGO_URI"] = "mongodb://owoadmin:sukeshfug@13.235.150.131:6909/OWO"
mongo = PyMongo(app)
cors = CORS(app, resources={r"/owo/*": {"origins": "*"}})
# client = MongoClient('3.6.120.54:6909')
razorpay_client = razorpay.Client(auth=("rzp_test_Xoazv44T6Ic6L6", "ke8ZCOnw0pYuaupLIX3NJoIF"))
push_service = FCMNotification(api_key="AAAArm2Z6mY:APA91bFiXWw7bQPYms4vR3OV5LvRaWgawo2pX3JjGEwdcvbZK3KmTlbD-UaS_i-KoAyFFy26iGQwUvaQNGn9kaOxnI5oJgec600yuOCxKQsViehocsALw3jBKIhPKGwuy1otKtUpwntI")


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ramadevig@fugenx.com'
app.config['MAIL_PASSWORD'] = 'fugenx@23145'
app.config['MAIL_DEFAULT_SENDER'] = 'default_sender_email'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['DEBUG'] = True
app.secret_key = 'my secret key'
app.config['MAIL_ASCII_ATTACHMENTS'] = True
app.config['SESSION_USE_SIGNER'] = True

s = URLSafeTimedSerializer('12345')
login_manager = LoginManager()
login_manager.init_app(app)
mail = Mail(app)
jwt = JWTManager(app)

def getSubscriptionProductByDate(subscription_id,products,buy_plan,start_day):
    data = mongo.db.OWO
    db1 = data.products
    output1 = []
    product_count = int()
    for price in products:
        p_id = price['product_id']
        set_quantity = price['set_quantity']
        t_q = calculateProductQuant(buy_plan, start_day, set_quantity)
        p_price = price['purchase_price']
        product_price = t_q * p_price
        for k in db1.find():
            if str(p_id) == str(k['product_id']):
                product_name = k['product_name']
                try:
                   product_image = k['product_image']
                except KeyError or ValueError:
                    product_image = []
        output1.append({'subscription_id': subscription_id,
                        'product_id':p_id,'purchase_price':p_price,'package_type':price['package_type'],'product_image':product_image,'product_name':product_name,'product_quantity':t_q,'product_price':product_price})
    return(output1)


def randomStringDigits(stringLength=4):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def calculatePrice(set_quantity, purchase_price, buy_plan, start_day):
    ind = reduce(lambda x, y: tuple(x.values()) + tuple(y.values()), set_quantity)
    print(ind)
    k = ind.items()
    print(k)
    DayList = list(zip(*k))
    DailyQuant = list(DayList[1])
    total_quantity = 0
    for i in range(0, 7):
        total_quantity += int(DailyQuant[i])
    print(total_quantity)
    weeklyPrice = total_quantity * purchase_price
    print(weeklyPrice)
    DayValue = {
        "Mon": 1,
        "Tue": 2,
        "Wed": 3,
        "Thu": 4,
        "Fri": 5,
        "Sat": 6,
        "Sun": 7
    }
    startDay_code = DayValue.get(start_day)
    numberOfWeeks = int((buy_plan) / 7)
    if (buy_plan) % 7 == 0:
        total_price = numberOfWeeks *(weeklyPrice)
    else:
        remainingDays = int((buy_plan) % 7)
        s = int(startDay_code)
        l = int(startDay_code) + remainingDays
        QuantForRemainingDays = 0
        for i in range(s, l):
            if i > 7:
                j = int(i % 7)
            else:
                j = i
            QuantForRemainingDays += int(DailyQuant[j - 1])
        print(QuantForRemainingDays)
        PriceOfRemainingBottles = QuantForRemainingDays * purchase_price
        print(PriceOfRemainingBottles)
        total_price = (numberOfWeeks * (weeklyPrice)) + PriceOfRemainingBottles
    return (total_price)


def calculateProductQuant(buy_plan, start_day, set_quantity):
    ind = reduce(lambda x, y: tuple(x.values()) + tuple(y.values()), set_quantity)
    print(ind)
    k = ind.items()
    DayList = list(zip(*k))
    DailyQuant = list(DayList[1])
    weekly_quantity = 0
    for i in range(0, 7):
        weekly_quantity += int(DailyQuant[i])
    DayValue = {
        "Mon": 1,
        "Tue": 2,
        "Wed": 3,
        "Thu": 4,
        "Fri": 5,
        "Sat": 6,
        "Sun": 7
    }
    startDay_code = DayValue.get(start_day)
    numberOfWeeks = int((buy_plan) / 7)
    if (buy_plan) % 7 == 0:
        total_quantity = numberOfWeeks * weekly_quantity
    else:
        remainingDays = int((buy_plan) % 7)
        s = int(startDay_code)
        l = int(startDay_code) + remainingDays
        QuantForRemainingDays = 0
        for i in range(s, l):
            if i > 7:
                j = int(i % 7)
            else:
                j = i
            QuantForRemainingDays += int(DailyQuant[j - 1])
        total_quantity = ((numberOfWeeks * weekly_quantity) + QuantForRemainingDays)
    return (total_quantity)


def SubscriptionDelivery_charges(signin_type, amount):
    data = mongo.db.OWO
    db = data.delivery_charge_management
    delivery_charges = int(0)
    if signin_type == "individual":
        for i in db.find({'$and': [{'delivery_type': "subscription-individual"}, {'upper_range': {'$gte': amount}},
                                   {'lower_range': {'$lte': amount}}]}):
            delivery_charges = i['delivery_charge']
            print(delivery_charges)
            return (delivery_charges)
        else:
            delivery_charges = "0"
            return (delivery_charges)
    elif signin_type == "corporate":
        for j in db.find({'$and': [{'delivery_type': "subscription-corporate"}, {'upper_range':{'$gte': amount}},
                                   {'lower_range':{'$lte': amount}}]}):
            delivery_charges = j['delivery_charge']
            print(delivery_charges)
            return (delivery_charges)
    else:
        delivery_charges = "0"
    return (delivery_charges)


def push_notification(firebase_id, message_body, message_title):

    result = push_service.notify_single_device(registration_id=firebase_id, message_title=message_title,
                                               message_body=message_body)
    print(result)


def PaymentSuccess(wallet_id, amount):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.app_notifications
    n_list = data.app_notification_text
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "Payment Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{amount}}"), str(amount))
    firebase_id = str()
    fb_id = []
    fb_ids = []
    user_id = int()
    signin_type = str()
    for f_id in db_c.find({'wallet_id': wallet_id}):
        try:
            firebase_id = f_id['firebase_id']
        except KeyError or ValueError:
            firebase_id = ""
        fb_id.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
    for f_ids in db_i.find({'wallet_id': wallet_id}):
        try:
            firebase_id = f_ids['firebase_id']
        except KeyError or ValueError:
            firebase_id = ""
        fb_ids.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
    result = {x['wallet_id']: x for x in fb_id + fb_ids}.values()
    push_notification(firebase_id, message_title, message_body)
    try:
        for k in db_i.find():
            if int(wallet_id) == int(k['wallet_id']):
                user_id = k['user_id']
                signin_type = k['signin_type']
    except KeyError or ValueError:
        pass
    for j in db_c.find():
        if int(wallet_id) == int(j['wallet_id']):
            user_id = j['user_id']
            signin_type = j['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"

def PaymentFailure(wallet_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.app_notifications
    n_list = data.app_notification_text
    user_id = int()
    signin_type = str()
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "Payment Failure", 'status': True}):
        message_title = i['notification_title']
        message_body = i['notification_text_description']
    firebase_id = str()
    fb_id = []
    fb_ids = []
    for f_id in db_c.find({'wallet_id': wallet_id}):
        try:
            firebase_id = f_id['firebase_id']
        except KeyError or ValueError:
            firebase_id = ""
        fb_id.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
    for f_ids in db_i.find({'wallet_id': wallet_id}):
        try:
            firebase_id = f_ids['firebase_id']
        except KeyError or ValueError:
            firebase_id = ""
        fb_ids.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
    result = {x['wallet_id']: x for x in fb_id + fb_ids}.values()
    push_notification(firebase_id, message_title, message_body)
    try:
        for k in db_i.find():
            if int(wallet_id) == int(k['wallet_id']):
                user_id = k['user_id']
                signin_type = k['signin_type']
    except KeyError or ValueError:
        pass
    for j in db_c.find():
        if int(wallet_id) == int(j['wallet_id']):
            user_id = j['user_id']
            signin_type = j['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


############################################################################################################
# def SubscriptionSuccess(wallet_id, order_id):
#     data = mongo.db.OWO
#     db_c = data.corporate_users
#     db_i = data.individual_users
#     notifications = data.app_notifications
#     n_list = data.app_notification_text
#     message_title = str()
#     message_body = str()
#     user_id = int()
#     subscription_id = str()
#     for i in n_list.find({'notification_type': "Subscription Successfull", 'status': True}):
#         message_title = i['notification_title']
#         m_body = i['notification_text_description']
#         message_body = m_body.replace("{{order_id}}", order_id)
#     firebase_id = str()
#     fb_id = []
#     fb_ids = []
#     for f_id in db_c.find({'wallet_id': wallet_id}):
#         try:
#             firebase_id = f_id['firebase_id']
#         except KeyError or ValueError:
#             firebase_id = ""
#         fb_id.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
#     for f_ids in db_i.find({'wallet_id': wallet_id}):
#         try:
#             firebase_id = f_ids['firebase_id']
#         except KeyError or ValueError:
#             firebase_id = ""
#         fb_ids.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
#     result = {x['wallet_id']: x for x in fb_id + fb_ids}.values()
#     push_notification(firebase_id, message_title, message_body)
#     try:
#         for k in db_i.find():
#             if int(wallet_id) == int(k['wallet_id']):
#                 user_id = k['user_id']
#                 signin_type = k['signin_type']
#     except KeyError or ValueError:
#         pass
#     for j in db_c.find():
#         if int(wallet_id) == int(j['wallet_id']):
#             user_id = j['user_id']
#             signin_type = j['signin_type']
#     notifications.insert_one(
#         {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
#          'date_time': datetime.datetime.now()})
#     return "ok"


def UserSignupSucessfull(user_id, signin_type, first_name, firebase_id):
    data = mongo.db.OWO
    notifications = data.app_notifications
    n_list = data.app_notification_text
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "User Sign Up Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{first_name}}", first_name)
        print(message_body)
    push_notification(firebase_id, message_title, message_body)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return ("ok")


def UserSignupFailed(user_id, signin_type, first_name, firebase_id):
    data = mongo.db.OWO
    notifications = data.app_notifications
    n_list = data.app_notification_text
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "User Sign Up Failure", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{first_name}}", first_name)
        print(message_body)
    push_notification(firebase_id, message_title, message_body)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return ("ok")


def AddingMoneyToWallet(wallet_id, amount):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.app_notifications
    n_list = data.app_notification_text
    s_c = data.owo_users_wallet
    message_title = str()
    message_body = str()
    user_id = int()
    signin_type = str()
    firebase_id = str()
    for i in n_list.find({'notification_type': "Adding Money to Wallet", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{amount}}"), str(amount))
        print(message_body)
        for s in s_c.find({'wallet_id': wallet_id}):
            user_id = s['user_id']
            print(user_id)
            signin_type = s['signin_type']
            print(signin_type)
            for j in db_c.find():
                for k in db_i.find():
                    for l in j, k:
                        if str(signin_type) == str(l['signin_type']) and int(user_id) == int(l['user_id']):
                            print(l['wallet_id'])
                            firebase_id = l['firebase_id']
    push_notification(firebase_id, message_title, message_body)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return ("ok")


#------------------------------------------------ Email Notification Methods--------------------------------------------
def UserSignupSuccessfulEmailCorporate(user_id, signin_type, first_name, official_email_id):
    data = mongo.db.OWO
    notifications = data.email_notifications
    n_list = data.email_notification_text
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "User Sign Up Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{first_name}}", first_name)
        msg = Message(message_title, sender="ramadevig@fugenx.com", recipients=[official_email_id])
        msg.body = message_body
        mail.send(msg)
    notifications.insert_one({'user_id': user_id, 'signin_type': signin_type, 'title': message_title,
                              'notifications': message_body,
                              'date_time': datetime.datetime.now()})


def UserSignupSuccessfulEmailIndividual(user_id, signin_type, first_name, email_id):
    data = mongo.db.OWO
    notifications = data.email_notifications
    n_list = data.email_notification_text
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "User Sign Up Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{first_name}}", first_name)
        msg = Message(message_title, sender="ramadevig@fugenx.com", recipients=[email_id])
        msg.body = message_body
        mail.send(msg)
    notifications.insert_one({'user_id': user_id, 'signin_type': signin_type, 'title': message_title,
                              'notifications': message_body,
                              'date_time': datetime.datetime.now()})


def PaymentSuccessEmail(wallet_id, amount):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.email_notifications
    n_list = data.email_notification_text
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "Payment Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{amount}}"), str(amount))
    email_id = str()
    e_id = []
    official_e_id = []
    user_id = int()
    signin_type = str()
    for i in db_c.find({'wallet_id': wallet_id}):
        try:
            email_id = i['email_id']
        except KeyError or ValueError:
            email_id = ""
        e_id.append({'wallet_id': wallet_id, 'email_id': email_id})
    for m in db_i.find({'wallet_id': wallet_id}):
        try:
            email_id = m['email_id']
        except KeyError or ValueError:
            email_id = ""
        official_e_id.append({'wallet_id': wallet_id, 'email_id': email_id})
    result = {x['wallet_id']: x for x in e_id + official_e_id}.values()
    msg = Message(message_title, sender="ramadevig@fugenx.com", recipients=[email_id])
    msg.body = message_body
    mail.send(msg)
    try:
        for k in db_i.find():
            if int(wallet_id) == int(k['wallet_id']):
                user_id = k['user_id']
                signin_type = k['signin_type']
    except KeyError or ValueError:
        pass
    for j in db_c.find():
        if int(wallet_id) == int(j['wallet_id']):
            user_id = j['user_id']
            signin_type = j['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def PaymentFailureEmail(wallet_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.email_notifications
    n_list = data.email_notification_text
    user_id = int()
    signin_type = str()
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "Payment Failure", 'status': True}):
        message_title = i['notification_title']
        message_body = i['notification_text_description']
    email_id = str()
    e_id = []
    official_e_id = []
    for i in db_c.find({'wallet_id': wallet_id}):
        try:
            email_id = i['email_id']
        except KeyError or ValueError:
            email_id = ""
        e_id.append({'wallet_id': wallet_id, 'email_id': email_id})
    for m in db_i.find({'wallet_id': wallet_id}):
        try:
            email_id = m['email_id']
        except KeyError or ValueError:
            email_id = ""
        official_e_id.append({'wallet_id': wallet_id, 'email_id': email_id})
    result = {x['wallet_id']: x for x in e_id + official_e_id}.values()
    msg = Message(message_title, sender="ramadevig@fugenx.com", recipients=[email_id])
    msg.body = message_body
    mail.send(msg)
    try:
        for k in db_i.find():
            if int(wallet_id) == int(k['wallet_id']):
                user_id = k['user_id']
                signin_type = k['signin_type']
    except KeyError or ValueError:
        pass
    for j in db_c.find():
        if int(wallet_id) == int(j['wallet_id']):
            user_id = j['user_id']
            signin_type = j['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def SubscriptionSuccess(wallet_id, order_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.app_notifications
    n_list = data.app_notification_text
    message_title = str()
    message_body = str()
    user_id = int()
    subscription_id = str()
    for i in n_list.find({'notification_type': "Subscription Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{order_id}}", order_id)
    firebase_id = str()
    fb_id = []
    fb_ids = []
    for f_id in db_c.find({'wallet_id': wallet_id}):
        try:
            firebase_id = f_id['firebase_id']
        except KeyError or ValueError:
            firebase_id = ""
        fb_id.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
    for f_ids in db_i.find({'wallet_id': wallet_id}):
        try:
            firebase_id = f_ids['firebase_id']
        except KeyError or ValueError:
            firebase_id = ""
        fb_ids.append({'wallet_id': wallet_id, 'firebase_id': firebase_id})
    result = {x['wallet_id']: x for x in fb_id + fb_ids}.values()
    push_notification(firebase_id, message_title, message_body)
    try:
        for k in db_i.find():
            if int(wallet_id) == int(k['wallet_id']):
                user_id = k['user_id']
                signin_type = k['signin_type']
    except KeyError or ValueError:
        pass
    for j in db_c.find():
        if int(wallet_id) == int(j['wallet_id']):
            user_id = j['user_id']
            signin_type = j['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def SubscriptionSuccessEmail(wallet_id, order_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.email_notifications
    n_list = data.email_notification_text
    message_title = str()
    message_body = str()
    user_id = int()
    subscription_id = str()
    for i in n_list.find({'notification_type': "Subscription Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{order_id}}", order_id)
    email_id = str()
    e_id = []
    official_e_id = []
    for i in db_c.find({'wallet_id': wallet_id}):
        try:
            email_id = i['email_id']
        except KeyError or ValueError:
            email_id = ""
        e_id.append({'wallet_id': wallet_id, 'email_id': email_id})
    for m in db_i.find({'wallet_id': wallet_id}):
        try:
            email_id = m['email_id']
        except KeyError or ValueError:
            email_id = ""
        official_e_id.append({'wallet_id': wallet_id, 'email_id': email_id})
    result = {x['wallet_id']: x for x in e_id + official_e_id}.values()
    msg = Message(message_title, sender="ramadevig@fugenx.com", recipients=[email_id])
    msg.body = message_body
    mail.send(msg)
    try:
        for j in db_c.find():
            if int(wallet_id) == int(j['wallet_id']):
                user_id = j['user_id']
                signin_type = j['signin_type']
    except KeyError or ValueError:
        pass
    for k in db_i.find():
        if int(wallet_id) == int(k['wallet_id']):
            user_id = k['user_id']
            signin_type = k['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"

def OrderConfirmation(cart_id, order_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.app_notifications
    n_list = data.app_notification_text
    s_c = data.shoppingcart
    message_title = str()
    message_body = str()
    user_id = int()
    signin_type = str()
    firebase_id = str()
    for i in n_list.find({'notification_type': "Booking Order Confirmation", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{order_id}}"), str(order_id))
        for s in s_c.find({'cart_id': cart_id}):
            user_id = s['customer_id']
            signin_type = s['customer_type']
            if signin_type == "individual":
                for k in db_i.find():
                    if str(signin_type) == str("individual") and int(user_id) == int(k['user_id']):
                        firebase_id = k['firebase_id']
            elif signin_type == "corporate":
                for j in db_c.find():
                    if str(signin_type) == str("corporate") and int(user_id) == int(j['user_id']):
                        firebase_id = j['firebase_id']
    push_notification(firebase_id, message_title, message_body)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


# ---------------------------------------------------------------------------------------------------------------------
def OrderConfirmationEmail(cart_id, order_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.email_notifications
    n_list = data.email_notification_text
    s_c = data.shoppingcart
    message_title = str()
    message_body = str()
    user_id = int()
    signin_type = str()
    email_id = str()
    for i in n_list.find({'notification_type': "Booking Order Confirmation", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{order_id}}"), str(order_id))
        for s in s_c.find({'cart_id': cart_id}):
            user_id = s['customer_id']
            print(user_id)
            signin_type = s['customer_type']
            print(signin_type)
            if signin_type == "individual":
                print("ok")
                for k in db_i.find():
                    if str(signin_type) == str("individual") and int(user_id) == int(k['user_id']):
                        email_id = k['email_id']
            elif signin_type == "corporate":
                for j in db_c.find():
                    if str(signin_type) == str("corporate") and int(user_id) == int(j['user_id']):
                        email_id = j['email_id']
            else:
                return jsonify({'status': 'success', 'message': 'invalid signin_type'})
    msg = Message(message_title, sender="ramadevig@fugenx.com", recipients=[email_id])
    msg.body = message_body
    mail.send(msg)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def AddingMoneyToWalletEmail(wallet_id, amount):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.email_notifications
    n_list = data.email_notification_text
    s_c = data.owo_users_wallet
    message_title = str()
    message_body = str()
    user_id = int()
    signin_type = str()
    email_id = str()
    for i in n_list.find({'notification_type': "Adding Money to Wallet", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{amount}}"), str(amount))
        for s in s_c.find({'wallet_id': int(wallet_id)}):
            user_id = s['user_id']
            signin_type = s['signin_type']
            if signin_type == "individual":
                for k in db_i.find():
                        if int(wallet_id) == int(k['wallet_id']) and int(user_id) == int(k['user_id']):
                            email_id = k['email_id']
            elif signin_type == "corporate":
                for j in db_c.find():
                        if str(signin_type) == str(j['signin_type']) and int(user_id) == int(j['user_id']):
                            email_id = j['email_id']
            else:
                return jsonify({'status':'success', 'message':'invalid signin_type'})
    msg = Message(message_title, sender="ramadevig@fugenx.com", recipients=[email_id])
    msg.body = message_body
    mail.send(msg)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


#------------------------------------------------- SMS Notification Methods --------------------------------------------
def UserSignupSuccessfullySMSIndividual(user_id, signin_type, first_name, mobile_number):
    data = mongo.db.OWO
    notifications = data.SMS_notification_text
    n_list = data.sms_notification
    message_body = str()
    for i in notifications.find({'notification_type': "User Sign Up Successfull", 'status':True}):
        message_title = i['notification_title']
        print(message_title)
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{first_name}}", first_name)
        print(message_body)
        url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
               "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message= " \
                + str(message_body)
        f = requests.get(url)
        print(f)
        n_list.insert_one({'user_id': user_id, 'signin_type': signin_type, 'title': message_title,
                            'notifications': message_body,'date_time': datetime.datetime.now()})


def UserSignupSuccessfullySMSCorporate(user_id, signin_type, first_name, contact_number):
    data = mongo.db.OWO
    notifications = data.SMS_notification_text
    n_list = data.sms_notification
    for i in notifications.find({'notification_type': "User Sign Up Successfull", 'status':True}):
        message_title = i['notification_title']
        print(message_title)
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{first_name}}", first_name)
        url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(contact_number) + \
               "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message= " \
                + str(m_body)
        f = requests.get(url)
        print(f)
        n_list.insert_one({'user_id': user_id, 'signin_type': signin_type, 'title': message_title,
                            'notifications': message_body,'date_time': datetime.datetime.now()})


def OrderConfirmationSMS(cart_id, order_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.sms_notification
    n_list = data.SMS_notification_text
    s_c = data.shoppingcart
    message_title = str()
    message_body = str()
    user_id = int()
    signin_type = str()
    mobile_number = str()
    for i in n_list.find({'notification_type': "Booking Order Confirmation", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{order_id}}", order_id)
        for s in s_c.find({'cart_id': cart_id}):
            user_id = s['customer_id']
            signin_type = s['customer_type']
            if signin_type == "individual":
                for k in db_i.find():
                    if str(signin_type) == str("individual") and int(user_id) == int(k['user_id']):
                        mobile_number = k['mobile_number']
            elif signin_type == "corporate":
                for j in db_c.find():
                    if str(signin_type) == str("corporate") and int(user_id) == int(j['user_id']):
                        mobile_number = j['mobile_number']
            else:
                return jsonify({'status': 'success', 'message': 'invalid signin_type'})

    url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
        "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message= " \
        + str(message_body)
    f = requests.get(url)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def PaymentSuccessSMS(wallet_id,amount):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.sms_notification
    n_list = data.SMS_notification_text
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "Payment Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{amount}}"), str(amount))
    mobile_number = int()
    m_number = []
    contact_number = []
    user_id = int()
    signin_type = str()
    for i in db_c.find({'wallet_id': wallet_id}):
        try:
            mobile_number = i['mobile_number']
        except KeyError or ValueError:
            mobile_number = ""
        m_number.append({'wallet_id': wallet_id, 'mobile_number': mobile_number})
    for m in db_i.find({'wallet_id': wallet_id}):
        try:
            mobile_number = m['mobile_number']
        except KeyError or ValueError:
            mobile_number = ""
        contact_number.append({'wallet_id': wallet_id, 'mobile_number': mobile_number})
    result = {x['wallet_id']: x for x in m_number + contact_number}.values()
    url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
          "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message= " \
          + str(message_body)
    f = requests.get(url)
    try:
        for k in db_i.find():
            if int(wallet_id) == int(k['wallet_id']):
                user_id = k['user_id']
                signin_type = k['signin_type']
    except KeyError or ValueError:
        pass
    for j in db_c.find():
        if int(wallet_id) == int(j['wallet_id']):
            user_id = j['user_id']
            signin_type = j['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def PaymentFailureSMS(wallet_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.sms_notification
    n_list = data.SMS_notification_text
    user_id = int()
    signin_type = str()
    message_title = str()
    message_body = str()
    for i in n_list.find({'notification_type': "Payment Failure", 'status': True}):
        message_title = i['notification_title']
        message_body = i['notification_text_description']
    mobile_number = int()
    m_number = []
    contact_number = []
    for i in db_c.find({'wallet_id': wallet_id}):
        try:
            mobile_number = i['mobile_number']
        except KeyError or ValueError:
            mobile_number = ""
        m_number.append({'wallet_id': wallet_id, 'mobile_number': mobile_number})
    for m in db_i.find({'wallet_id': wallet_id}):
        try:
            mobile_number = m['mobile_number']
        except KeyError or ValueError:
            mobile_number = ""
        contact_number.append({'wallet_id': wallet_id, 'mobile_number': mobile_number})
    result = {x['wallet_id']: x for x in m_number + contact_number}.values()
    url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
          "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message= " \
          + str(message_body)
    f = requests.get(url)
    try:
        for k in db_i.find():
            if int(wallet_id) == int(k['wallet_id']):
                user_id = k['user_id']
                signin_type = k['signin_type']
    except KeyError or ValueError:
        pass
    for j in db_c.find():
        if int(wallet_id) == int(j['wallet_id']):
            user_id = j['user_id']
            signin_type = j['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def SubscriptionSuccessSMS(wallet_id, order_id):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.sms_notification
    n_list = data.SMS_notification_text
    message_title = str()
    message_body = str()
    user_id = int()
    subscription_id = str()
    for i in n_list.find({'notification_type': "Subscription Successfull", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace("{{order_id}}", order_id)
    mobile_number = str()
    m_number = []
    contact_number = []
    for i in db_c.find({'wallet_id': wallet_id}):
        try:
            mobile_number = i['mobile_number']
        except KeyError or ValueError:
            mobile_number = ""
        m_number.append({'wallet_id': wallet_id, 'mobile_number': mobile_number})
    for m in db_i.find({'wallet_id': wallet_id}):
        try:
            mobile_number = m['mobile_number']
        except KeyError or ValueError:
            mobile_number = ""
        contact_number.append({'wallet_id': wallet_id, 'mobile_number': mobile_number})
    result = {x['wallet_id']: x for x in m_number + contact_number}.values()
    url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
          "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message= " \
          + str(message_body)
    f = requests.get(url)
    try:
        for j in db_c.find():
            if int(wallet_id) == int(j['wallet_id']):
                user_id = j['user_id']
                signin_type = j['signin_type']
    except KeyError or ValueError:
        pass
    for k in db_i.find():
        if int(wallet_id) == int(k['wallet_id']):
            user_id = k['user_id']
            signin_type = k['signin_type']
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def AddingMoneyToWalletSMS(wallet_id, amount):
    data = mongo.db.OWO
    db_c = data.corporate_users
    db_i = data.individual_users
    notifications = data.sms_notification
    n_list = data.SMS_notification_text
    s_c = data.owo_users_wallet
    message_title = str()
    message_body = str()
    user_id = int()
    signin_type = str()
    mobile_number = str()
    for i in n_list.find({'notification_type': "Adding Money to Wallet", 'status': True}):
        message_title = i['notification_title']
        m_body = i['notification_text_description']
        message_body = m_body.replace(str("{{amount}}"), str(amount))
        for s in s_c.find({'wallet_id': int(wallet_id)}):
            user_id = s['user_id']
            signin_type = s['signin_type']
            if signin_type == "individual":
                for k in db_i.find():
                    if int(wallet_id) == int(k['wallet_id']) and int(user_id) == int(k['user_id']):
                        mobile_number = k['mobile_number']
            elif signin_type == "corporate":
                for j in db_c.find():
                    if str(signin_type) == str(j['signin_type']) and int(user_id) == int(j['user_id']):
                        mobile_number = j['mobile_number']
            else:
                return jsonify({'status': 'success', 'message': 'invalid signin_type'})
    url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
        "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message= " \
        + str(message_body)
    f = requests.get(url)
    notifications.insert_one(
        {'user_id': user_id, 'signin_type': signin_type, 'title': message_title, 'notifications': message_body,
         'date_time': datetime.datetime.now()})
    return "ok"


def findDay(date):
    day, month, year = (int(i) for i in date.split('-'))
    dayNumber = calendar.weekday(day, month, year)
    days = ["Mon", "Tue", "Wed", "Thu",
            "Fri", "Sat", "Sun"]
    return (days[dayNumber])


# ----------------------------------------- Customer Management -------------------------------------------------------
# ----------------------------------------- Corporate user registration -----------------------------------------------
@app.route('/owo/user_corporate_registration', methods=["POST"])
def corporateUserRegistration():
    data = mongo.db.OWO
    db = data.corporate_users
    db_c = data.config_loyalty
    db_l = data.loyalty
    db1 = data.individual_users
    user_wallet = data.owo_users_wallet
    output = []
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    session_id = request.json['session_id']
    password = request.json['password']
    confirm_password = request.json['confirm_password']
    signin_type = request.json['signin_type']
    date_of_join = request.json['date_of_join']
    company_name = request.json['company_name']
    gst_number = request.json['gst_number']
    official_email_id = request.json['official_email_id']
    contact_number = request.json['contact_number']
    legal_name_of_business = request.json['legal_name_of_business']
    pan_number = request.json['pan_number']
    state = request.json['state']
    firebase_id = request.json['firebase_id']
    device_token = request.json['device_token']
    referral_code = request.json['referral_code']
    email_result = db.find({'email_id': official_email_id})
    mobile_result = db.find({'mobile_number': contact_number})
    name = str(first_name) + str(last_name)
    if str(password) == str(confirm_password):

# ------------------------------------- Generating invite code --------------------------------------------------------
        invite_code = name[:2].upper() + str(random.randint(10, 99)) + name[2:4].upper() + str(random.randint(10, 99))
        print(invite_code)

# ---------------------------------- User system Id generate ----------------------------------------------------------
        try:
            user_id_list = [i['user_id'] for i in db.find()]
            if len(user_id_list) is 0:
                user_id = 1
            else:
                user_id = int(user_id_list[-1]) + 1
        except KeyError or ValueError:
            user_id = int(1)

# ----------------------------------- Wallet system Id generate -------------------------------------------------------
        try:
            wallet_id_list = [i['wallet_id'] for i in user_wallet.find()]
            if len(wallet_id_list) is 0:
                wallet_id = 1
            else:
                wallet_id = int(wallet_id_list[-1]) + 1
        except KeyError or ValueError:
            wallet_id = int(1)

# ------------------------------------ Checks the user is registered --------------------------------------------------

        if email_result.count() != 0 or mobile_result.count() != 0:
            return jsonify({'status': False, 'message': 'user already existed'})
        else:
            try:
                try:
                    for k in db.find():
                        code = k['invite_code']
                        print(code)
                        if str(code) == str(referral_code):
                            u_id = k['user_id']
                            m_number = k['mobile_number']
                            e_id = k['email_id']
                            s_type = k['signin_type']
                            for m in db_c.find():
                                print("ok")
                                r_type = m['loyalty_type']
                                if str(r_type) == 'Referral Points':
                                    points = m['loyalty_points']
                                    print(points)
                                    db.insert_one({'first_name': first_name, 'last_name': last_name, 'mobile_number': int(contact_number),
                                                   'email_id': str(official_email_id),  'active_user': True,
                                                   'password': password, 'confirm_password': confirm_password,
                                                   'company_name': company_name, 'gst_number': str(gst_number), 'session_id': session_id,
                                                   'user_id': int(user_id), 'legal_name_of_business': legal_name_of_business,
                                                   'pan_number': str(pan_number), 'date_of_join': date_of_join, 'state': state,
                                                   'signin_type': signin_type, 'email_verified': 0, 'mobile_verified': 0,
                                                   'wallet_id': wallet_id, 'invite_code': invite_code, 'referral_code': referral_code})
                                    user_wallet.insert_one({'wallet_id': wallet_id, 'signin_type': signin_type, 'user_id': user_id,
                                                            'current_balance': 0})
                                    for n in db_l.find():
                                        id = n['user_id']
                                        stype = n['signin_type']
                                        if int(id) == int(u_id) and str(stype) == str(s_type):
                                            t_earned = n['loyalty_balance']
                                            t_earned1 = t_earned + points
                                            db_l.find_one_and_update({'user_id': int(u_id), 'signin_type': str(s_type)},
                                                                     {'$set': {'loyalty_balance': int(t_earned1)},
                                                                      '$push': {'recent_earnings':
                                                                                    {'earn_points': int(points),
                                                                                     'loyalty_type': 'earned',
                                                                                     'referred_user_id': int(user_id),
                                                                                     'signin_type': str(signin_type),
                                                                                     'referral_code': referral_code,
                                                                                     'earn_date': datetime.datetime.now(),
                                                                                     'earn_type': "referral_code",
                                                                                     'current_balance': int(t_earned),
                                                                                     'closing_balance': int(t_earned1)
                                                                                     }}})
                                            output.append({'first_name': first_name, 'last_name': last_name, 'contact_number': int(contact_number),
                                                           'official_email_id': official_email_id, 'company_name': company_name,
                                                           'gst_number': str(gst_number), 'session_id': session_id,
                                                           'user_id': user_id,
                                                           'legal_name_of_business': legal_name_of_business, 'pan_number': pan_number,
                                                           'date_of_join': date_of_join, 'state': state, 'signin_type': signin_type,
                                                           'wallet_id': wallet_id, 'invite_code': invite_code})
                                            UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                            UserSignupSuccessfulEmailCorporate(user_id, signin_type, first_name, official_email_id)
                                            UserSignupSuccessfullySMSCorporate(user_id, signin_type, first_name, contact_number)
                                            return jsonify({'status': True, 'message': 'user register successfully', 'result': output})
                                    db_l.insert({'user_id': u_id, 'signin_type': s_type,
                                                 'mobile_number': m_number, 'email_id': e_id,
                                                 'loyalty_balance': int(points),
                                                 'recent_earnings': [{'earn_points': int(points),
                                                                      'loyalty_type': 'earned',
                                                                      'referred_user_id': int(user_id),
                                                                      'signin_type': str(signin_type),
                                                                      'referral_code': referral_code,
                                                                      'earn_date': datetime.datetime.now(),
                                                                      'earn_type': "referral_code",
                                                                      'current_balance': 0,
                                                                      'closing_balance': int(points)}]})

                                    output.append({'first_name': first_name, 'last_name': last_name,
                                                   'contact_number': int(contact_number),
                                                   'official_email_id': official_email_id, 'company_name': company_name,
                                                   'gst_number': str(gst_number), 'session_id': session_id,
                                                   'user_id': user_id,
                                                   'legal_name_of_business': legal_name_of_business,
                                                   'pan_number': pan_number,
                                                   'date_of_join': date_of_join, 'state': state,
                                                   'signin_type': signin_type,
                                                   'wallet_id': wallet_id, 'invite_code': invite_code})
                                    UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                    UserSignupSuccessfulEmailCorporate(user_id, signin_type, first_name, official_email_id)
                                    UserSignupSuccessfullySMSCorporate(user_id, signin_type, first_name,contact_number)
                                    return jsonify(
                                        {'status': True, 'message': 'user register successfully', 'result': output})
                except KeyError or ValueError:
                    pass
                for a in db1.find():
                    code = a['invite_code']
                    print(code)
                    if str(code) == str(referral_code):
                        u_id = a['user_id']
                        m_number = a['mobile_number']
                        e_id = a['email_id']
                        s_type = a['signin_type']
                        for m in db_c.find():
                            r_type = m['loyalty_type']
                            if str(r_type) == 'Referral Points':
                                points = m['loyalty_points']
                                db.insert_one({'first_name': first_name, 'last_name': last_name,
                                               'mobile_number': int(contact_number),
                                               'email_id': str(official_email_id),
                                               'password': password, 'confirm_password': confirm_password,
                                               'company_name': company_name, 'gst_number': str(gst_number),
                                               'session_id': session_id, 'active_user': True,
                                               'user_id': int(user_id),
                                               'legal_name_of_business': legal_name_of_business,
                                               'pan_number': str(pan_number), 'date_of_join': date_of_join,
                                               'state': state,
                                               'signin_type': signin_type, 'email_verified': 0, 'mobile_verified': 0,
                                               'wallet_id': wallet_id, 'invite_code': invite_code,
                                               'referral_code': referral_code})
                                user_wallet.insert_one(
                                    {'wallet_id': wallet_id, 'signin_type': signin_type, 'user_id': user_id,
                                     'current_balance': 0})
                                for n in db_l.find():
                                    id = n['user_id']
                                    stype = n['signin_type']
                                    if int(id) == int(u_id) and str(stype) == str(s_type):
                                        t_earned=n['loyalty_balance']
                                        t_earned1=t_earned + points
                                        db_l.find_one_and_update({'user_id': int(u_id), 'signin_type': str(s_type)},
                                                                 {'$set': {'loyalty_balance': int(t_earned1)},
                                                                  '$push': {'recent_earnings':
                                                                                {'earn_points': int(points),
                                                                                 'loyalty_type': 'earned',
                                                                                 'referred_user_id': int(user_id),
                                                                                 'signin_type': str(signin_type),
                                                                                 'referral_code': referral_code,
                                                                                 'earn_date': datetime.datetime.now(),
                                                                                 'earn_type': "referral_code",
                                                                                 'current_balance': int(t_earned),
                                                                                 'closing_balance': int(t_earned1)
                                                                                 }}})
                                        output.append({'first_name': first_name, 'last_name': last_name,
                                                       'contact_number': int(contact_number),
                                                       'official_email_id': official_email_id,
                                                       'company_name': company_name,
                                                       'gst_number': str(gst_number), 'session_id': session_id,
                                                       'user_id': user_id,
                                                       'legal_name_of_business': legal_name_of_business,
                                                       'pan_number': pan_number,
                                                       'date_of_join': date_of_join, 'state': state,
                                                       'signin_type': signin_type,
                                                       'wallet_id': wallet_id, 'invite_code': invite_code})
                                        UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                        UserSignupSuccessfulEmailCorporate(user_id, signin_type, first_name, official_email_id)
                                        UserSignupSuccessfullySMSCorporate(user_id, signin_type, first_name,contact_number)
                                        return jsonify(
                                            {'status': True, 'message': 'user register successfully', 'result': output})
                                db_l.insert({'user_id': u_id, 'signin_type': s_type,
                                             'mobile_number': m_number, 'email_id': e_id,
                                             'loyalty_balance': int(points),
                                             'recent_earnings': [{'earn_points': int(points),
                                                                  'loyalty_type': 'earned',
                                                                  'referred_user_id': int(user_id),
                                                                  'signin_type': str(signin_type),
                                                                  'referral_code': referral_code,
                                                                  'earn_date': datetime.datetime.now(),
                                                                  'earn_type': "referral_code",
                                                                  'current_balance': 0,
                                                                  'closing_balance': int(points)}]})

                                output.append({'first_name': first_name, 'last_name': last_name,
                                               'contact_number': int(contact_number),
                                               'official_email_id': official_email_id, 'company_name': company_name,
                                               'gst_number': str(gst_number), 'session_id': session_id,
                                               'user_id': user_id,
                                               'legal_name_of_business': legal_name_of_business,
                                               'pan_number': pan_number,
                                               'date_of_join': date_of_join, 'state': state,
                                               'signin_type': signin_type,
                                               'wallet_id': wallet_id, 'invite_code': invite_code})
                                UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                UserSignupSuccessfulEmailCorporate(user_id, signin_type, first_name, official_email_id)
                                UserSignupSuccessfullySMSCorporate(user_id, signin_type,first_name, contact_number)
                                return jsonify(
                                    {'status': True, 'message': 'user register successfully', 'result': output})
            except KeyError or ValueError:
                pass
            db.insert_one({'first_name': first_name, 'last_name': last_name, 'mobile_number': int(contact_number),
                           'email_id': str(official_email_id), 'active_user': True,
                           'password': password, 'confirm_password': confirm_password,
                           'company_name': company_name, 'gst_number': str(gst_number), 'session_id': session_id,
                           'user_id': int(user_id), 'legal_name_of_business': legal_name_of_business,
                           'pan_number': str(pan_number), 'date_of_join': date_of_join, 'state': state,
                           'signin_type': signin_type, 'email_verified': 0, 'mobile_verified': 0,
                           'wallet_id': wallet_id, 'invite_code': invite_code, 'referral_code': referral_code})
            user_wallet.insert_one({'wallet_id': wallet_id, 'signin_type': signin_type, 'user_id': user_id,
                                    'current_balance': 0})
            output.append({'first_name': first_name, 'last_name': last_name, 'contact_number': int(contact_number),
                           'official_email_id': official_email_id, 'company_name': company_name,
                           'gst_number': str(gst_number), 'session_id': session_id,
                           'user_id': user_id,
                           'legal_name_of_business': legal_name_of_business, 'pan_number': pan_number,
                           'date_of_join': date_of_join, 'state': state, 'signin_type': signin_type,
                           'wallet_id': wallet_id, 'invite_code': invite_code})
            UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
            UserSignupSuccessfulEmailCorporate(user_id, signin_type, first_name, official_email_id)
            UserSignupSuccessfullySMSCorporate(user_id, signin_type, first_name, contact_number)
            return jsonify({'status': True, 'message': 'user register successfully', 'result': output})
    return jsonify({'status': False, 'message': 'confirm password does not match', 'result': output})


# -------------------------------------- send email OTP corporate users -----------------------------------------------
@app.route('/owo/send_email_otp_corporate', methods=['POST'])
def sendEmailOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    output = []
    try:
        user_id = request.json['user_id']
        official_email_id = request.json['official_email_id']
        details = coll.find()
        for i in details:
            id = i['user_id']
            print(id)
            if str(user_id) == str(id):
                email_otp = random.randint(1000, 9999)
                msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com",
                              recipients=[official_email_id])
                print(i['email_id'])
                msg.body = 'Welcome to OWO \n\n Your mail verification OTP' + str(email_otp)
                mail.send(msg)
                coll.update_one({'user_id': user_id}, {'$set': {'email_otp': str(email_otp)}})
                output.append({'official_email_id': official_email_id, 'email_otp': str(email_otp), 'user_id': user_id})
                return jsonify({'status': True, 'message': 'otp send successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid user id'})

    except Exception as e:
        return jsonify(status=False, message=str(e))


# -------------------------------------- Verify email OTP corporate user ----------------------------------------------
@app.route('/owo/verify_email_otp_corporate', methods=['POST'])
def verifyEmailOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    email_otp_entered = request.json['email_otp_entered']
    official_email_id = request.json['official_email_id']
    output = []
    dflt_address = []
    details = coll.find()
    print("ok")
    for j in details:
        if str(official_email_id) == str(j['email_id']) and str(email_otp_entered) == str(j['email_otp']):
            try:
                u_add = j['user_address']
            except KeyError or ValueError:
                u_add = []
            try:
                for b in u_add:
                    d_address = b['default_address']
                    if d_address == True:
                        dflt_address.append(b)
            except KeyError or ValueError:
                pass
            print("otp")
            coll.update_many({'email_id': official_email_id}, {'$set': {'email_verified': 1}})
            output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'], 'first_name': j['first_name'],
                           'last_name': j['last_name'], 'company_name': j['company_name'], 'gst_number': j['gst_number'],
                           'session_id': j['session_id'], 'pan_number': j['pan_number'],
                           'date_of_join': j['date_of_join'], 'state': j['state'], 'signin_type': j['signin_type'],
                           'wallet_id': j['wallet_id'], 'contact_number': j['mobile_number'],
                           'default_address': dflt_address,
                           'otp_entered': j['email_otp'], 'email_verified': 1, 'mobile_verified': j['mobile_verified']})
            return jsonify({'status': True, 'message': 'email otp verified successfully', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid Credentials. Please check and try again', 'result': output})


# --------------------------------------------- send mobile OTP corporate user ----------------------------------------
@app.route('/owo/send_mobile_otp_corporate', methods=['POST'])
def sendMobileOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    output = []
    try:
        user_id = request.json['user_id']
        mobile = request.json['mobile']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            u_id = i['user_id']
            if str(u_id) == str(user_id):
                otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                      str(otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'user_id': int(u_id)}, {'$set': {'otp': str(otp)}})
                output.append({'mobile_number': m_number, 'otp': str(otp), 'user_id': u_id})
                return jsonify({'status': True, 'message': 'otp resend successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'individual mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------------------ Verify mobile OTP corporate user -----------------------------------------
@app.route('/owo/verify_mobile_otp_corporate', methods=['POST'])
def verifyMobileOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    otp_entered = request.json['otp_entered']
    mobile_number = request.json['mobile_number']
    output = []
    dflt_address = []
    details = coll.find()
    print("ok")
    for j in details:
        print('oki')
        if str(mobile_number) == str(j['mobile_number']) and str(otp_entered) == str(j['otp']):
            try:
                u_add = j['user_address']
            except KeyError or ValueError:
                u_add = []
            try:
                for b in u_add:
                    d_address = b['default_address']
                    if d_address == True:
                        dflt_address.append(b)
            except KeyError or ValueError:
                pass
            coll.update_many({'mobile_number': int(mobile_number)}, {'$set': {'mobile_verified': 1}})
            output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'], 'first_name': j['first_name'],
                           'last_name': j['last_name'], 'company_name': j['company_name'], 'gst_number': j['gst_number'],
                           'session_id': j['session_id'], 'pan_number': j['pan_number'],
                           'date_of_join': j['date_of_join'], 'state': j['state'], 'signin_type': j['signin_type'],
                           'wallet_id': j['wallet_id'], 'contact_number': j['mobile_number'], 'otp_entered': j['otp'],
                           'mobile_verified': 1, 'email_verified': j['email_verified'],
                           'default_address': dflt_address})
            return jsonify({'status': True, 'message': 'user mobile otp verified successfully', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid Credentials. Please check and try again',
                        'result': output})


# ------------------------------------------ Login Corporate User -----------------------------------------------------
@app.route("/owo/corporate_login", methods=["POST"])
def corporate_login():
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    dflt_address = []
    user_name = request.json['user_name']
    password = request.json['password']
    session_id = request.json['session_id']
    signin_type = request.json['signin_type']
    firebase_id = request.json['firebase_id']
    device_token = request.json['device_token']
    for j in db.find():
        name = j['email_id']
        m_number = j['mobile_number']
        pwd = j['password']
        u_id = j['user_id']
        try:
            invite_code = j['invite_code']
            profile_pic = j['profile_pic']
        except KeyError or ValueError:
            invite_code = ''
            profile_pic = ''
        try:
            u_add = j['user_address']
        except KeyError or ValueError:
            u_add = []
            print("Ok")
        if str(user_name) == str(name) or user_name == str(m_number):
            if str(pwd) == str(password):
                if str(signin_type) == "corporate":
                    try:
                        for b in u_add:
                            d_address = b['default_address']
                            if d_address == True:
                                dflt_address.append(b)
                    except KeyError or ValueError:
                        pass
                    if j['email_verified'] == 0 and j['mobile_verified'] == 0:
                        output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'],
                                       'first_name': j['first_name'], 'last_name': j['last_name'],
                                       'company_name': j['company_name'], 'gst_number': j['gst_number'],
                                       'session_id': j['session_id'], 'pan_number': j['pan_number'],
                                       'date_of_join': j['date_of_join'], 'state': j['state'],
                                       'signin_type': j['signin_type'], 'wallet_id': j['wallet_id'],
                                       'contact_number': j['mobile_number'], 'mobile_verified': j['mobile_verified'],
                                       'email_verified': j['email_verified'],'active_user': j['active_user'],
                                       'default_address': dflt_address,'invite_code':j['invite_code']})
                        return jsonify({'status': True, 'message': "OTP not verified", 'result': output})
                    else:
                        if j['email_verified'] == 1:
                            if j['mobile_verified'] == 1:
                                access_token = create_access_token(identity=user_name,
                                                                   expires_delta=datetime.timedelta(days=2))
                                db.update_many({'user_id': int(u_id)},
                                               {'$set': {'firebase_id': firebase_id, 'device_token': device_token,
                                                         'session_id': session_id, 'access_token': access_token,
                                                         'profile_pic': profile_pic}})
                                output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'],
                                               'first_name': j['first_name'], 'last_name': j['last_name'],
                                               'company_name': j['company_name'], 'gst_number': j['gst_number'],
                                               'session_id': j['session_id'], 'pan_number': j['pan_number'],
                                               'date_of_join': j['date_of_join'], 'state': j['state'],
                                               'signin_type': j['signin_type'], 'wallet_id': j['wallet_id'],
                                               'contact_number': j['mobile_number'], 'active_user': j['active_user'],
                                               'mobile_verified': j['mobile_verified'],
                                               'email_verified': j['email_verified'], 'access_token': access_token,
                                               'profile_pic': profile_pic, 'default_address': dflt_address
                                               ,'invite_code':j['invite_code']})
                                return jsonify({'status': True, 'message': 'customer login success', 'result': output})
                            else:
                                output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'],
                                               'first_name': j['first_name'], 'last_name': j['last_name'],
                                               'company_name': j['company_name'], 'gst_number': j['gst_number'],
                                               'session_id': j['session_id'], 'pan_number': j['pan_number'],
                                               'date_of_join': j['date_of_join'], 'state': j['state'],
                                               'signin_type': j['signin_type'], 'wallet_id': j['wallet_id'],
                                               'contact_number': j['mobile_number'], 'active_user': j['active_user'],
                                               'mobile_verified': j['mobile_verified'],
                                               'email_verified': j['email_verified'],
                                               'default_address': dflt_address,'invite_code':j['invite_code']})
                                return jsonify({'status': True, 'message': 'mobile OTP not verified',
                                                'result': output})
                        else:
                            output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'],
                                           'first_name': j['first_name'], 'last_name': j['last_name'],
                                           'company_name': j['company_name'], 'gst_number': j['gst_number'],
                                           'session_id': j['session_id'], 'pan_number': j['pan_number'],
                                           'date_of_join': j['date_of_join'], 'state': j['state'],
                                           'signin_type': j['signin_type'], 'wallet_id': j['wallet_id'],
                                           'contact_number': j['mobile_number'], 'mobile_verified': j['mobile_verified'],
                                           'email_verified': j['email_verified'], 'active_user': j['active_user'],
                                           'default_address': dflt_address,'invite_code':j['invite_code']})
                            return jsonify({'status': True, "message": 'email OTP not verified', 'result': output})
                else:
                    return jsonify({'status': False, 'message': 'sign-in type is invalid', 'result': output})
            else:
                return jsonify({'status': False, 'message': 'customer password is invalid', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid credentials', 'result': output})


# ------------------------------------------ Resend Email OTP for corporate user --------------------------------------
@app.route('/owo/resend_email_otp_corporate', methods=['POST'])
def resendEmailOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    output = []
    try:
        official_email_id = request.json['official_email_id']
        details = coll.find()
        for i in details:
            id = i['email_id']
            print(id)
            if str(id) == str(official_email_id):
                email_otp = random.randint(1000, 9999)
                msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com",
                              recipients=[official_email_id])
                msg.body = 'Welcome to OWO.\n\n This is email verification process from OWO \n\n Please enter the OTP: %s \n\n Thank You' % str(
                    email_otp)
                mail.send(msg)
                coll.update_one({'email_id': official_email_id}, {'$set': {'email_otp': str(email_otp)}})
                output.append({'official_email_id': official_email_id, 'email_otp': str(email_otp)})
                return jsonify({'status': True, 'message': 'otp send successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'email not registered'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------- Resend Mobile OTP for corporate user --------------------------------------------
@app.route('/owo/resend_mobile_otp_corporate', methods=['POST'])
def resendMobileOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    output = []
    try:
        mobile = request.json['mobile']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            u_id = i['user_id']
            if str(mobile) == str(m_number):
                otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                      str(otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'user_id': int(u_id)}, {'$set': {'otp': str(otp)}})
                output.append({'mobile_number': m_number, 'otp': str(otp), 'user_id': u_id})
                return jsonify({'status': True, 'message': 'otp resend successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------- Corporate user forgot password  -------------------------------------------------
@app.route('/owo/forgot_password_corporate', methods=['POST'])
def forgotPassword_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    output = []
    try:
        official_email_id = request.json['official_email_id']

        details = coll.find()
        for i in details:
            e_id = i['email_id']
            print(e_id)
            if str(e_id) == str(official_email_id):
                email_otp = random.randint(1000, 9999)
                msg = Message('Forgot password', sender="ramadevig@fugenx.com", recipients=[official_email_id])
                print(i['email_id'])
                msg.body = 'Welcome to OWO \n\n Please verify OTP to change password' + str(email_otp)
                mail.send(msg)
                coll.update_one({'email_id': official_email_id}, {'$set': {'email_otp': str(email_otp)}})
                output.append({'email_id': official_email_id, 'email_otp': str(email_otp)})
                return jsonify({'status': True, 'message': 'otp updated successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'not able find corporate user'})

    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------------------ Change Password Corporate users ------------------------------------------
@app.route('/owo/change_password_corporate', methods=['POST'])
def changePassword_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    output = []
    try:
        new_password = str(request.json['new_password'])
        confirm_password = str(request.json['confirm_password'])
        official_email_id = str(request.json['official_email_id'])
        if new_password != confirm_password:
            return "Please enter the same passwords."
        details = coll.find()
        for i in details:
            e_id = i['email_id']
            if e_id == official_email_id:
                coll.update({'email_id': official_email_id}, {'$set': {'password': new_password,
                                                                       'confirm_password': confirm_password}})
                output.append({'email_id': official_email_id, 'password': new_password,
                               'confirm_password': confirm_password})
                return jsonify({'status': True, 'message': 'password updated successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid email id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------------------------- Get Invite Code Corporate Users -----------------------------------
@app.route('/owo/get_invite_code_cp/<user_id>', methods=['GET'])
def getInviteCodeCP(user_id):
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    for i in db.find():
        u_id = i['user_id']
        if str(u_id) == str(user_id):
            temp = {}
            temp['user_id'] = i['user_id']
            if 'invite_code' not in i.keys():
                temp['invite_code'] = ''
            else:
                temp['invite_code'] = i['invite_code']
            output.append(temp)
            return jsonify({'status': True, 'message': 'get invite code', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})


# ------------------------------------------- Individual User Management ----------------------------------------------
# -------------------------------------------------- Individual Users Registration ------------------------------------
@app.route('/owo/individual_user_registration', methods=["POST"])
def user_individual_registration():
    data = mongo.db.OWO
    db = data.individual_users
    db1 = data.corporate_users
    user_wallet = data.owo_users_wallet
    db_c = data.config_loyalty
    db_l = data.loyalty
    output = []
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    session_id = request.json['session_id']
    password = request.json['password']
    confirm_password = request.json['confirm_password']
    signin_type = request.json['signin_type']
    date_of_join = request.json['date_of_join']
    mobile_number = request.json['mobile_number']
    referral_code = request.json['referral_code']
    firebase_id = request.json['firebase_id']
    device_token = request.json['device_token']
    email_id = request.json['email_id']
    email_result = db.find({'email_id': email_id})
    mobile_result = db.find({'mobile_number': mobile_number})
    name = str(first_name) + str(last_name)
    if str(password) == str(confirm_password):

# -------------------------------- Generating invite code  ------------------------------------------------------------

        invite_code = name[:2].upper() + str(random.randint(10, 99)) + name[2:4].upper() + str(random.randint(10, 99))

# --------------------------------------- System generate user id ----------------------------------------------------
        try:
            user_id_list = [i['user_id'] for i in db.find()]
            if len(user_id_list) is 0:
                user_id = 1
            else:
                user_id = int(user_id_list[-1]) + 1
        except KeyError or ValueError:
            user_id = int(1)

# ---------------------------------- System generate Wallet id --------------------------------------------------------
        try:
            wallet_id_list = [i['wallet_id'] for i in user_wallet.find()]
            if len(wallet_id_list) is 0:
                wallet_id = 1
            else:
                wallet_id = int(wallet_id_list[-1]) + 1
        except KeyError or ValueError:
            wallet_id = int(1)

# ---------------------------------- Checks the user is registered ----------------------------------------------------
        if email_result.count() != 0 or mobile_result.count() != 0:
            return jsonify({'status': False, 'message': 'user already existed'})
        else:
            try:
                try:
                    for k in db.find():
                        code = k['invite_code']
                        print(code)
                        if str(code) == str(referral_code):
                            u_id = k['user_id']
                            m_number = k['mobile_number']
                            e_id = k['email_id']
                            s_type = k['signin_type']
                            for m in db_c.find():
                                print("ok")
                                r_type = m['loyalty_type']
                                if str(r_type) == 'Referral Points':
                                    points = m['loyalty_points']
                                    print(points)
                                    db.insert_one({'first_name': first_name, 'last_name': last_name,
                                                   'mobile_number': int(mobile_number),
                                                   'email_id': str(email_id), 'user_id': user_id,
                                                   'session_id': session_id,  'active_user': True,
                                                   'password': str(password), 'confirm_password': confirm_password,
                                                   'date_of_join': date_of_join,
                                                   'signin_type': signin_type, 'email_verified': 0,
                                                   'mobile_verified': 0,
                                                   'wallet_id': wallet_id, 'invite_code': invite_code,
                                                   'referral_code': referral_code})
                                    user_wallet.insert_one({'wallet_id': wallet_id, 'signin_type': signin_type,
                                                            'user_id': user_id, 'current_balance': 0})
                                    for n in db_l.find():
                                        id = n['user_id']
                                        stype = n['signin_type']
                                        print(stype)
                                        if int(id) == int(u_id) and str(stype) == str(s_type):
                                            t_earned = n['loyalty_balance']
                                            print(t_earned)
                                            t_earned1 = t_earned + points
                                            db_l.find_one_and_update({'user_id': int(u_id), 'signin_type': str(s_type)},
                                                                     {'$set': {'loyalty_balance': int(t_earned1)},
                                                                      '$push': {'recent_earnings':
                                                                                    {'earn_points': int(points),
                                                                                     'loyalty_type': 'earned',
                                                                                     'referral_code': referral_code,
                                                                                     'earn_date': datetime.datetime.now(),
                                                                                     'earn_type': "referral_code",
                                                                                     'referred_user_id': int(user_id),
                                                                                     'signin_type':signin_type,
                                                                                     'current_balance': int(t_earned),
                                                                                     'closing_balance': int(t_earned1)
                                                                                     }}})
                                            output.append({'first_name': first_name, 'last_name': last_name,
                                                           'mobile_number': int(mobile_number),
                                                           'email_id': str(email_id), 'user_id': user_id,
                                                           'session_id': session_id,
                                                           'password': password, 'confirm_password': confirm_password,
                                                           'date_of_join': date_of_join, 'signin_type': signin_type,
                                                           'email_verified': 0, 'mobile_verified': 0,
                                                           'wallet_id': wallet_id,
                                                           'invite_code': invite_code})
                                            UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                            UserSignupSuccessfulEmailIndividual(user_id, signin_type, first_name, email_id)
                                            UserSignupSuccessfullySMSIndividual(user_id, signin_type, first_name, mobile_number)
                                            return jsonify({"status": True, "message": "registered successfully",
                                                            'result': output})

                                    db_l.insert({'user_id': u_id, 'signin_type': s_type,
                                                 'mobile_number': m_number, 'email_id': e_id,
                                                 'loyalty_balance': int(points),
                                                 'recent_earnings': [{'earn_points': int(points),
                                                                      'loyalty_type': 'earned',
                                                                      'referral_code': referral_code,
                                                                      'referred_user_id': int(user_id),
                                                                      'signin_type': signin_type,
                                                                      'earn_date': datetime.datetime.now(),
                                                                      'earn_type': "referral_code",
                                                                      'current_balance': 0,
                                                                      'closing_balance': int(points)}]})

                                    output.append({'first_name': first_name, 'last_name': last_name,
                                                   'mobile_number': int(mobile_number),
                                                   'email_id': str(email_id), 'user_id': user_id,
                                                   'session_id': session_id,
                                                   'password': password, 'confirm_password': confirm_password,
                                                   'date_of_join': date_of_join, 'signin_type': signin_type,
                                                   'email_verified': 0, 'mobile_verified': 0, 'wallet_id': wallet_id,
                                                   'invite_code': invite_code})
                                    UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                    UserSignupSuccessfulEmailIndividual(user_id, signin_type, first_name, email_id)
                                    UserSignupSuccessfullySMSIndividual(user_id, signin_type, first_name, mobile_number)
                                    return jsonify(
                                        {"status": True, "message": "registered successfully", 'result': output})

                except KeyError or ValueError:
                    pass
                for k in db1.find():
                    code = k['invite_code']
                    print(code)
                    if str(code) == str(referral_code):
                        u_id = k['user_id']
                        m_number = k['mobile_number']
                        e_id = k['email_id']
                        s_type = k['signin_type']
                        for m in db_c.find():
                            print("ok")
                            r_type = m['loyalty_type']
                            if str(r_type) == 'Referral Points':
                                points = m['loyalty_points']
                                print(points)
                                db.insert_one({'first_name': first_name, 'last_name': last_name,
                                               'mobile_number': int(mobile_number),
                                               'email_id': str(email_id), 'user_id': user_id,
                                               'session_id': session_id,  'active_user': True,
                                               'password': str(password), 'confirm_password': confirm_password,
                                               'date_of_join': date_of_join,
                                               'signin_type': signin_type, 'email_verified': 0,
                                               'mobile_verified': 0,
                                               'wallet_id': wallet_id, 'invite_code': invite_code,
                                               'referral_code': referral_code})
                                user_wallet.insert_one({'wallet_id': wallet_id, 'signin_type': signin_type,
                                                        'user_id': user_id, 'current_balance': 0})
                                for n in db_l.find():
                                    id = n['user_id']
                                    stype = n['signin_type']
                                    print(stype)
                                    if int(id) == int(u_id) and str(stype) == str(s_type):
                                        t_earned = n['loyalty_balance']
                                        print(t_earned)
                                        t_earned1 = t_earned + points
                                        db_l.find_one_and_update({'user_id': int(u_id), 'signin_type': str(s_type)},
                                                                 {'$set': {'loyalty_balance': int(t_earned1)},
                                                                  '$push': {'recent_earnings':
                                                                                {'earn_points': int(points),
                                                                                 'loyalty_type': 'earned',
                                                                                 'referral_code': referral_code,
                                                                                 'earn_date': datetime.datetime.now(),
                                                                                 'earn_type': "referral_code",
                                                                                 'referred_user_id': int(user_id),
                                                                                 'signin_type': signin_type,
                                                                                 'current_balance': int(t_earned),
                                                                                 'closing_balance': int(t_earned1)
                                                                                 }}})
                                        output.append({'first_name': first_name, 'last_name': last_name,
                                                       'mobile_number': int(mobile_number),
                                                       'email_id': str(email_id), 'user_id': user_id,
                                                       'session_id': session_id,
                                                       'password': password, 'confirm_password': confirm_password,
                                                       'date_of_join': date_of_join, 'signin_type': signin_type,
                                                       'email_verified': 0, 'mobile_verified': 0,
                                                       'wallet_id': wallet_id,
                                                       'invite_code': invite_code})
                                        UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                        UserSignupSuccessfulEmailIndividual(user_id, signin_type, first_name, email_id)
                                        UserSignupSuccessfullySMSIndividual(user_id, signin_type, first_name, mobile_number)
                                        return jsonify(
                                            {"status": True, "message": "registered successfully", 'result': output})

                                db_l.insert({'user_id': u_id, 'signin_type': s_type,
                                             'mobile_number': m_number, 'email_id': e_id,
                                             'loyalty_balance': int(points),
                                             'recent_earnings': [{'earn_points': int(points),
                                                                  'loyalty_type': 'earned',
                                                                  'referral_code': referral_code,
                                                                  'referred_user_id': int(user_id),
                                                                  'signin_type': signin_type,
                                                                  'earn_date': datetime.datetime.now(),
                                                                  'earn_type': "referral_code",
                                                                  'current_balance': 0,
                                                                  'closing_balance': int(points)}]})

                                output.append({'first_name': first_name, 'last_name': last_name,
                                               'mobile_number': int(mobile_number),
                                               'email_id': str(email_id), 'user_id': user_id, 'session_id': session_id,
                                               'password': password, 'confirm_password': confirm_password,
                                               'date_of_join': date_of_join, 'signin_type': signin_type,
                                               'email_verified': 0, 'mobile_verified': 0, 'wallet_id': wallet_id,
                                               'invite_code': invite_code})
                                UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
                                UserSignupSuccessfulEmailIndividual(user_id, signin_type, first_name, email_id)
                                UserSignupSuccessfullySMSIndividual(user_id, signin_type, first_name, mobile_number)
                                return jsonify({"status": True, "message": "registered successfully", 'result': output})
            except KeyError or ValueError:
                pass
            db.insert_one({'first_name': first_name, 'last_name': last_name,
                           'mobile_number': int(mobile_number),
                           'email_id': str(email_id), 'user_id': user_id,
                           'session_id': session_id,  'active_user': True,
                           'password': str(password), 'confirm_password': confirm_password,
                           'date_of_join': date_of_join,
                           'signin_type': signin_type, 'email_verified': 0,
                           'mobile_verified': 0,
                           'wallet_id': wallet_id, 'invite_code': invite_code,
                           'referral_code': referral_code})
            user_wallet.insert_one({'wallet_id': wallet_id, 'signin_type': signin_type,
                                    'user_id': user_id, 'current_balance': 0})
            output.append({'first_name': first_name, 'last_name': last_name, 'mobile_number': int(mobile_number),
                           'email_id': str(email_id), 'user_id': user_id, 'session_id': session_id,
                           'password': password, 'confirm_password': confirm_password,
                           'date_of_join': date_of_join, 'signin_type': signin_type,
                           'email_verified': 0, 'mobile_verified': 0, 'wallet_id': wallet_id,
                           'invite_code': invite_code})
            UserSignupSucessfull(user_id, signin_type, first_name, firebase_id)
            UserSignupSuccessfulEmailIndividual(user_id, signin_type, first_name, email_id)
            UserSignupSuccessfullySMSIndividual(user_id, signin_type, first_name, mobile_number)
            return jsonify({"status": True, "message": "registered successfully", 'result': output})
    return jsonify({"status": False, "message": "confirm password does not match", 'result': output})


# -------------------------------------------- send Email OTP Individual user ----------------------------------------
@app.route('/owo/send_email_otp_individual_user', methods=['POST'])
def sendEmailOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        user_id = request.json['user_id']
        email_id = request.json['email_id']
        details = coll.find()
        for i in details:
            id = i['user_id']
            if str(id) == str(user_id):
                email_otp = random.randint(1000, 9999)
                msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com", recipients=[email_id])
                print(i['email_id'])
                msg.body = 'Welcome to OWO \n\n Your mail verification OTP' + str(email_otp)
                mail.send(msg)
                coll.update_one({'email_id': email_id}, {'$set': {'email_otp': str(email_otp)}})
                output.append({'email_id': email_id, 'email_otp': str(email_otp), 'user_id': user_id})
                return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid user id'})

    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------------- Verify Email OTP individual user  ---------------------------------------------
@app.route('/owo/verify_email_otp_individual', methods=['POST'])
def verifyEmailOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    email_otp_entered = request.json['email_otp_entered']
    email_id = request.json['email_id']
    output = []
    dflt_address = []
    details = coll.find()
    for j in details:
        try:
            u_add = j['user_address']
        except KeyError or ValueError:
            u_add = []
        if str(email_id) == str(j['email_id']) and str(email_otp_entered) == str(j['email_otp']):
            try:
                for b in u_add:
                    d_address = b['default_address']
                    if d_address == True:
                        dflt_address.append(b)
            except KeyError or ValueError:
                pass
            print("otp")
            coll.update_many({'email_id': email_id}, {'$set': {'email_verified': 1}})
            output.append({'user_id': j['user_id'], 'email_id': j['email_id'], 'first_name': j['first_name'], 'last_name':j['last_name'],
                           'mobile_number': j['mobile_number'], 'session_id': j['session_id'],
                           'default_address': dflt_address,
                           'wallet_id': j['wallet_id'], 'email_verified': 1,'mobile_verified': j['mobile_verified']})
            return jsonify({'status': True, 'message': 'email otp verified successfully', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid Credentials. Please check and try again', 'result': output})


# -------------------------------------------- send mobile OTP --------------------------------------------------------
@app.route('/owo/send_mobile_otp_individual', methods=['POST'])
def sendMobileOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        user_id = request.json['user_id']
        mobile_number = request.json['mobile_number']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            u_id = i['user_id']
            if str(u_id) == str(user_id):
                otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                      str(otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'user_id': int(u_id)}, {'$set': {'otp': str(otp)}})
                output.append({'mobile_number': m_number, 'otp': str(otp), 'user_id': u_id})
                return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'individual user id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# --------------------------- Verify mobile OTP individual user ------------------------------------------------------
@app.route('/owo/verify_mobile_otp_individual', methods=['POST'])
def verifyMobileOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    otp_entered = request.json['otp_entered']
    mobile_number = request.json['mobile_number']
    output = []
    dflt_address = []
    details = coll.find()
    print("ok")
    for k in details:
        if str(mobile_number) == str(k['mobile_number']) and str(otp_entered) == str(k['otp']):
            try:
                u_add = k['user_address']
            except KeyError or ValueError:
                u_add = []
            try:
                for a in u_add:
                    d_address = a['default_address']
                    if d_address == True:
                        dflt_address.append(a)
            except KeyError or ValueError:
                pass
            coll.update_many({'mobile_number': int(mobile_number)}, {'$set': {'mobile_verified': 1}})
            output.append({'user_id': k['user_id'], 'email_id': k['email_id'], 'first_name': k['first_name'],
                           'last_name':k['last_name'], 'mobile_number': k['mobile_number'], 'session_id':k['session_id'],
                           'mobile_verified': 1, 'email_verified': k['email_verified'],'wallet_id': k['wallet_id'],
                           'default_address': dflt_address})
            return jsonify({'status': True, 'message': 'mobile otp verified successfully', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid Credentials. Please check and try again', 'result': output})


# ----------------------------------------- Resend Email OTP Individual user -----------------------------------------
@app.route('/owo/resend_email_otp_individual_user', methods=['POST'])
def resendEmailOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        email_id = request.json['email_id']
        details = coll.find()
        for i in details:
            id = i['email_id']
            print(id)
            if str(id) == str(email_id):
                email_otp = random.randint(1000, 9999)
                msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com", recipients=[email_id])
                print(i['email_id'])
                msg.body = 'Welcome to OWO \n\n Your mail verification OTP' + str(email_otp)
                mail.send(msg)
                coll.update_one({'email_id': email_id}, {'$set': {'email_otp': str(email_otp)}})
                output.append({'email_id': email_id, 'email_otp': str(email_otp)})
                return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid user'})

    except Exception as e:
        return jsonify(status=False, message=str(e))


# ---------------------------------------------------- Resend mobile OTP individual users ----------------------------
@app.route('/owo/resend_mobile_otp_individual', methods=['POST'])
def resendMobileOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        mobile_number = request.json['mobile_number']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            u_id = i['user_id']
            if str(mobile_number) == str(m_number):
                otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                      str(otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'user_id': int(u_id)}, {'$set': {'otp': str(otp)}})
                output.append({'mobile_number': m_number, 'otp': str(otp), 'user_id': u_id})
                return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'individual mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ---------------------------------------- individual-login -----------------------------------------------------------
@app.route("/owo/individual_login", methods=["POST"])
def individual_login():
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    dflt_address = []
    user_name = request.json['user_name']
    password = request.json['password']
    session_id = request.json['session_id']
    signin_type = request.json['signin_type']
    firebase_id = request.json['firebase_id']
    device_token = request.json['device_token']
    for i in db.find():
        name = i['email_id']
        m_number = i['mobile_number']
        pwd = i['password']
        u_id = i['user_id']
        try:
            invite_code = i['invite_code']
            profile_pic = i['profile_pic']
        except KeyError or ValueError:
            invite_code = ''
            profile_pic = ''
        try:
            u_add = i['user_address']
        except KeyError or ValueError:
            u_add = []
            print("Ok")
        if str(user_name) == str(name) or str(user_name) == str(m_number):
            if str(pwd) == str(password):
                if str(signin_type) == "individual":
                    try:
                        for b in u_add:
                            d_address = b['default_address']
                            if d_address == True:
                                dflt_address.append(b)
                    except KeyError or ValueError:
                        pass
                    if i['email_verified'] == 0 and i['mobile_verified'] == 0:
                        output.append({'user_id': i['user_id'], 'first_name': i['first_name'], 'active_user': i['active_user'],
                                       'last_name': i['last_name'], 'signin_type': i['signin_type'],
                                       'session_id': i['session_id'], 'email_id': i['email_id'],
                                       'mobile_number': i['mobile_number'], 'mobile_verified': i['mobile_verified'],
                                       'email_verified': i['email_verified'], 'wallet_id': i['wallet_id'],
                                       'default_address': dflt_address, 'invite_code':i['invite_code']})
                        return jsonify({'status': True, 'message': 'OTP not verified', 'result': output})
                    else:
                        if i['email_verified'] == 1:
                            if i['mobile_verified'] == 1:
                                access_token = create_access_token(identity=user_name,
                                                                   expires_delta=datetime.timedelta(days=2))
                                try:
                                    default_address = i['default_address']
                                except KeyError or ValueError:
                                    pass
                                db.update_one({'user_id': int(u_id)},
                                              {'$set': {'session_id': session_id, 'firebase_id': firebase_id,
                                                        'device_token': device_token, 'access_token': access_token,
                                                        'profile_pic': profile_pic}})
                                output.append({'user_id': i['user_id'], 'first_name': i['first_name'],
                                               'last_name': i['last_name'], 'signin_type': signin_type,
                                               'session_id': session_id, 'email_id': name, 'mobile_number': m_number,
                                               'email_verified': i['email_verified'], 'active_user': i['active_user'],
                                               'mobile_verified': i['mobile_verified'], 'wallet_id': i['wallet_id'],
                                               'access_token': access_token, 'profile_pic': profile_pic,
                                               'default_address': dflt_address,'invite_code':i['invite_code']})
                                return jsonify({'status': True, 'message': 'user login successfully', 'result': output})
                            else:
                                output.append({'user_id': i['user_id'], 'first_name': i['first_name'],
                                               'last_name': i['last_name'], 'signin_type': i['signin_type'],
                                               'session_id': i['session_id'], 'email_id': i['email_id'],
                                               'mobile_number': i['mobile_number'], 'active_user': i['active_user'],
                                               'mobile_verified': i['mobile_verified'], 'email_verified': 1,
                                               'wallet_id': i['wallet_id'],
                                               'default_address': dflt_address,'invite_code':i['invite_code']})
                                return jsonify({'status': True, 'message': 'mobile OTP not verified', 'result': output})
                        else:
                            output.append({'user_id': i['user_id'], 'first_name': i['first_name'],
                                           'last_name': i['last_name'], 'signin_type': i['signin_type'],
                                           'session_id': i['session_id'], 'email_id': i['email_id'],
                                           'mobile_number': i['mobile_number'], 'email_verified': i['email_verified'],
                                           'mobile_verified': 1, 'wallet_id': i['wallet_id'], 'active_user': i['active_user'],
                                           'default_address': dflt_address,'invite_code':i['invite_code']})
                            return jsonify({'status': True, 'message': 'email OTP not verified', 'result': output})
                else:
                    return jsonify({"status": False, "message": "invalid sign in type", 'result': output})
            else:
                return jsonify({'status': False, 'message': 'invalid password', 'result': output})
    return jsonify({'status': False, 'message': 'customer credentials is wrong', 'result': output})


# ----------------------------------- individual user forgot password  ------------------------------------------------
@app.route('/owo/forgot_password_individual', methods=['POST'])
def forgotPassword_individual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        user_name = request.json['user_name']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            e_id = i['email_id']
            u_id = i['user_id']
            if str(user_name) == str(m_number):
                f_otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(user_name) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n Please verify OTP to change your password \n\n Please enter the OTP:" + \
                      str(f_otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'user_id': int(u_id)}, {'$set': {'f_otp': str(f_otp)}})
                output.append({'user_name': str(user_name), 'f_otp': str(f_otp), 'user_id': u_id})
                return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
            else:
                if str(user_name) == str(e_id):
                    f_otp = random.randint(1000, 9999)
                    msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com", recipients=[e_id])
                    print(i['email_id'])
                    msg.body = 'Welcome to OWO \n\n Please verify OTP to change your password' + str(f_otp)
                    mail.send(msg)
                    coll.update_one({'user_id': int(u_id)}, {'$set': {'f_otp': str(f_otp)}})
                    output.append({'user_id': int(u_id), 'f_otp': str(f_otp), 'user_name': str(user_name)})
                    return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid credentials'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# --------------------------------- individual user forgot password resend OTP ----------------------------------------
@app.route('/owo/forgot_resend_password_individual', methods=['POST'])
def forgotResendPassword_individual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        user_name = request.json['user_name']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            e_id = i['email_id']
            u_id = i['user_id']
            if str(user_name) == str(m_number):
                f_otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(user_name) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n Please verify OTP to change your password \n\n Please enter the OTP:" + \
                      str(f_otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'user_id': int(u_id)}, {'$set': {'f_otp': str(f_otp)}})
                output.append({'user_name': str(user_name), 'f_otp': str(f_otp), 'user_id': u_id})
                return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
            else:
                if str(user_name) == str(e_id):
                    f_otp = random.randint(1000, 9999)
                    msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com", recipients=[e_id])
                    print(i['email_id'])
                    msg.body = 'Welcome to OWO \n\n Please verify OTP to change your password' + str(f_otp)
                    mail.send(msg)
                    coll.update_one({'user_id': int(u_id)}, {'$set': {'f_otp': str(f_otp)}})
                    output.append({'user_id': int(u_id), 'f_otp': str(f_otp), 'user_name': str(user_name)})
                    return jsonify({'status': True, 'message': 'otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid credentials'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------------------- Change Password individual users -----------------------------------------
@app.route('/owo/change_password_individual', methods=['POST'])
def changePassword_individual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        new_password = request.json['new_password']
        confirm_password = request.json['confirm_password']
        user_id = request.json['user_id']
        print(user_id)
        if new_password != confirm_password:
            return "Please enter the same passwords."
        details = coll.find()
        for i in details:
            u_id = i['user_id']
            print(u_id)
            if str(u_id) == str(user_id):
                print("ok")
                coll.update_one({'user_id': int(user_id)}, {'$set': {'password': str(new_password), 'confirm_password': str(confirm_password)}})
                print("all ok")
                output.append({'user_id': user_id, 'password': new_password})
                return jsonify({'status': True, 'message': 'password updated successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid user id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# --------------------------------------- Get Invite Code Individual Users --------------------------------------------
@app.route('/owo/get_invite_code_in/<user_id>', methods=['GET'])
def getInviteCodeIN(user_id):
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    for i in db.find():
        u_id = i['user_id']
        if str(u_id) == str(user_id):
            temp={}
            temp['user_id'] = i['user_id']
            if 'invite_code' not in i.keys():
                temp['invite_code'] = ''
            else:
                temp['invite_code'] = i['invite_code']
            output.append(temp)
            return jsonify({'status': True, 'message': 'get invite code', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})


# ----------------------------------------------- verify_referral_code ------------------------------------------------
@app.route('/owo/verify_referral_code', methods=['POST'])
def verifyReferralCode():
    data = mongo.db.OWO
    db = data.individual_users
    db1 = data.corporate_users
    output = []
    referral_code = request.json['referral_code']
    try:
        for k in db.find():
            code = k['invite_code']
            print(code)
            if str(code) == str(referral_code):
                return jsonify({"status": True, "message": "verified referral code", 'result': output})

    except KeyError or ValueError:
        pass
    for a in db1.find():
        code = a['invite_code']
        print(code)
        if str(code) == str(referral_code):
            return jsonify({"status": True, "message": "verified referral code", 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid referral code', 'result': output})


# ------------------------------------------------- get products list -------------------------------------------------
@app.route('/owo/get_products_list', methods=['GET'])
def get_products_list():
    data = mongo.db.OWO
    db = data.products
    output = []
    for i in db.find({'active_status':True}):
        try:
            if 'product_image' not in i.keys():
                product_image = [""]
            else:
                product_image = i['product_image']
            for j in i['package_type']:
                output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
                               'product_image': product_image,
                               'brand_name': i['brand_name'], 'company_name': i['company_name'],
                               'package_type': i['package_type'], 'package_id': j['package_id'],
                               'package_type': j['package_type'], 'purchase_price': j['purchase_price'],
                               'unit_price': j['unit_price'],
                               'discount_in_percentage': j['discount_in_percentage'],
                               'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
        except KeyError or ValueError:
            product_image = [""]
    return jsonify({'status': True, 'message': ' product details', 'result': output})


# ----------------------------------------------- get all brands ------------------------------------------------------
@app.route('/owo/get_all_brand', methods=['GET'])
def get_all_brand():
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find():
        company = i['company_name']
        company_id = i['company_id']
        try:
            brand = i['brand']
            for j in brand:
                brand_id = j['brand_id']
                brand_name = j['brand_name']
                brand_description = j['brand_description']
                brand_photo = j['brand_photo']
                brand_description = j['brand_description']
                output.append({'brand_id': brand_id, 'brand_name': brand_name, 'brand_description': brand_description,
                               'brand_photo': brand_photo,
                               })
        except KeyError or ValueError:
            brand = " "
    return jsonify({"status": "success", 'message': 'get all brands success', 'result': output})


# -------------------------------------------------- get all banners --------------------------------------------------
@app.route('/owo/get_banner_management', methods=['GET'])
def get_banner_managemet():
    data = mongo.db.OWO
    db = data.banners
    output = []
    for q in db.find():
        output.append({'screen_name': q['screen_name'], 'screen_id': q['screen_id'], 'banner_image': q['banner_image'],
                       'type_of_banner': q['type_of_banner']})
    return jsonify({'status': 'success', 'message': 'Banner Management data get successfully', 'result': output})


# -------------------------------------------------- get all products and brands --------------------------------------
@app.route('/owo/get_products_all', methods=['GET'])
def get_products_all():
    data = mongo.db.OWO
    db = data.products
    db1 = data.companies
    output = {}
    output1 = []
    output2 = []
    for i in db.find():
        temp = {}
        temp['product_name'] = i['product_name']
        temp['product_id'] = i['product_id']
        temp['product_image'] = i['product_image']
        output1.append(temp)
    for j in db1.find():
        for k in j['brand']:
            temp1 = {}
            temp1['brand_name'] = k['brand_name']
            temp1['brand_photo'] = k['brand_photo']
            temp1['brand_id'] = k['brand_id']
            output2.append(temp1)
    # output = output1 +output2
    return jsonify(
        {"status": "success", 'message': 'get all products and brands success', 'result1': {"product": output1},
         'result2': {"brand": output2}})


#----------------------------------------------- Get productd by id ----------------------------------------------------
@app.route('/owo/get_products/<product_id>', methods=['GET'])
def getProductById(product_id):
    data = mongo.db.OWO
    db = data.products
    db_r = data.rating
    product_rating = 0
    product_no_of_rating = 0
    output = []
    for i in db.find({'product_id': product_id}):
        try:
            product_image = i['product_image']
        except KeyError or ValueError:
            product_image = []
        product_name = i['product_name']
        product_id = i['product_id']
        product_image = product_image
        description = i['description']
        specification = i['specification']
        technical = i['technical']
        available_quantity = i['product_quantity']
        p_type = i['package_type']
        for j in i['package_type']:
            package_type = j['package_type']
            package_id = j['package_id']
            purchase_price = j['purchase_price']
            unit_price = j['mrp']
            gst = j['gst']
            return_policy = j['return_policy']
            discount_in_percentage = j['discount_in_percentage']
            expiry_date = j['expiry_date']
            for k in db_r.find():
                p_id=k['product_id']
                r_history=k['rating_history']
                try:
                    if str(p_id) == str(i['product_id']):
                        user_count = len(r_history)
                        product_no_of_rating = user_count
                        product_rating = k['current_rating']
                except KeyError or ValueError:
                    pass
            output.append({'product_name': product_name, 'product_id': product_id, 'product_image': product_image,
                           'description': description, 'specification': specification, 'technical': technical,
                           'package_type': [{'package_type': package_type, 'package_id': package_id,
                                             'purchase_price': purchase_price, 'unit_price': unit_price, 'gst': gst,
                                             'return_policy': return_policy, 'expiry_date': expiry_date,
                                             'discount_in_percentage': discount_in_percentage,
                                             'product_rating': product_rating, 'available_quantity': available_quantity,
                                             'product_no_of_rating': product_no_of_rating}]})
            return jsonify({'status': True, 'message': "product get success", 'result': output})
    else:
        return jsonify({'status': False, 'message': "get product details fail"})


#------------------------------------------ Get Products by type -------------------------------------------------------
@app.route('/owo/get_products/<product_id>/<package_type>', methods=['GET'])
def getProductByIdType(product_id, package_type):
    data = mongo.db.OWO
    db = data.products
    output = []
    for i in db.find({'product_id': product_id, 'package_type': package_type}):
        temp = {}
        temp['product_name'] = i['product_name']
        temp['product_id'] = i['product_id']
        temp['product_image'] = i['product_image']
        temp['product_description'] = i['product_description']
        temp['package_type'] = i['package_type']
        output.append(temp)
        return jsonify({'status': "success", 'message': "product get success", 'result': output})
    else:
        return jsonify({'status': 'fail', 'message': "get product details fail"})


#------------------------------------------------ Multiple images ------------------------------------------------------
@app.route('/multiple_images', methods=['POST'])
def upload_images():
    data = mongo.db.OWO
    coll = data.corporate_banners
    banner_image = request.json['banner_image']
    output = []
    banner_image = str(banner_image).encode()
    banner_path = '/var/www/html/owo/images/banner_images/' + '.' + 'jpg'
    mongo_db_path = 'owo/images/banner_images' + '.' + 'jpg'
    with open(banner_path, "wb") as fh:
        f_n = fh.write(base64.decodebytes(banner_image))
        print(f_n)
        output.append({'banner_image': mongo_db_path})
        print(output)
    # coll.insert_many({'banner_image':mongo_db_path})
    return jsonify({'status': "success"})


#--------------------------------------------- Product subscription ----------------------------------------------------
@app.route('/owo/product_subscription', methods=['POST'])
@jwt_required
def product_subcription():
    data = mongo.db.OWO
    db = data.product_subscription
    db_users = data.individual_users
    db_p = data.products
    output = []
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    set_frequency = request.json['set_frequency']
    set_quantity = request.json['set_quantity']
    buy_plan = request.json['buy_plan']
    set_starting_date = request.json['set_starting_date']
    for i in db_users.find():
        u_id = i['user_id']
        if str(u_id) == str(user_id):
            for j in db_p.find():
                p_id = j['product_id']
                if str(p_id) == str(product_id):
                    db.update_One({'user_id': user_id}, {
                        '$set': {'product_id': product_id, 'set_frequency': set_frequency, 'set_quantity': set_quantity,
                                 'buy_plan': buy_plan, 'set_starting_date': set_starting_date}})
                    output.append({'user_id': user_id, 'product_id': product_id, 'set_frequency': set_frequency,
                                   'set_quantity': set_quantity,
                                   'buy_plan': buy_plan, 'set_starting_date': set_starting_date})
                    return jsonify({'status': 'success', 'message': 'success product subscription', 'result': output})
            return jsonify({'status': 'fail', 'message': 'fail product subscription', 'result': output})
    return jsonify({'status': 'fail', 'message': 'user not found', 'result': output})


#---------------------------------------------------- get slot ---------------------------------------------------------
@app.route('/owo/get_slot_management', methods=['GET'])
def get_slot():
    try:
        data = mongo.db.OWO
        db = data.slot
        output = []
        for q in db.find():
            output.append({'slot_id': q['slot_id'], 'slot_title': q['slot_title'], 'slot_timing': q['slot_timing']})
        return jsonify({'status': 'success', 'message': 'Slot Management data get successfully', 'result': output})
    except Exception as e:
        return jsonify({'status': 'Fail', 'message': str(e)})


#--------------------------------------------------------- Add Delivery Address ----------------------------------------
@app.route('/owo/add_delivery_address', methods=['POST', 'GET'])
def edit_address():
    try:
        data = mongo.db.OWO
        db = data.corporate_users
        db1 = data.individual_users
        output = []
        user_id = request.json['user_id']
        pincode = request.json['pincode']
        building_number = request.json['building_number']
        street_name = request.json['street_name']
        address = request.json['address']
        state = request.json['state']
        district = request.json['district']
        taluka = request.json['taluka']
        landmark = request.json['landmark']
        signin_type = request.json['signin_type']
        if str(signin_type) == "corporate":
            info = db.find()
            for i in info:
                id = i['user_id']
                if int(id) == int(user_id):
                    db.find_one_and_update({'user_id': user_id},
                                           {'$set': {'user_address': [{'pincode': pincode,
                                                                       'building_number': building_number,
                                                                       'street_name': street_name,
                                                                       'address': address, 'state': state,
                                                                       'district': district, 'taluka': taluka,
                                                                       'landmark': landmark}]}})
                    output.append({'user_id': user_id, 'pincode': pincode, 'building_number': building_number,
                                   'street_name': street_name,
                                   'address': address, 'state': state, 'district': district, 'taluka': taluka,
                                   'landmark': landmark, 'signin_type': 'corporate'})
                    return jsonify(
                        {'status': 'success', 'message': 'delivery address edited successfully', 'result': output})
        elif str(signin_type) == 'individual':
            info2 = db1.find()
            for j in info2:
                id = j['user_id']
                if int(id) == int(user_id):
                    db1.find_one_and_update({'user_id': user_id}, {
                        '$set': {'user_address': [{'pincode': pincode, 'building_number': building_number,
                                                   'street_name': street_name, 'address': address,
                                                   'state': state, 'district': district, 'taluka': taluka,
                                                   'landmark': landmark}]}})
                    output.append({'user_id': user_id, 'pincode': pincode, 'building_number': building_number,
                                   'street_name': street_name,
                                   'address': address, 'state': state, 'district': district, 'taluka': taluka,
                                   'landmark': landmark,
                                   'signin_type': 'individual'})
                    return jsonify(
                        {'status': 'success', 'message': 'delivary address added successfully', 'result': output})
        else:
            return jsonify({'status': 'fail', 'message': 'invalid signin type'})

    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)})


# --------------------------------------------------- get delivery address ---------------------------------------------
@app.route('/owo/get_delivery_address/<user_id>/<signin_type>', methods=['POST', 'GET'])
def get_delivery_address(user_id, signin_type):
    try:
        data = mongo.db.OWO
        db = data.corporate_users
        db1 = data.individual_users
        if str(signin_type) == "corporate":
            info = db.find()
            for i in info:
                id = i['user_id']
                if int(id) == int(user_id):
                    address = i['user_address']
                    # output.append(address)
                    return jsonify(
                        {'status': 'success', 'message': 'delivery address data get successfully', 'result': address})
        elif str(signin_type) == "individual":
            info2 = db1.find()
            for j in info2:
                id = j['user_id']
                if int(id) == int(user_id):
                    address = j['user_address']
                    return jsonify(
                        {'status': 'success', 'message': 'delivery address data get successfull', 'result': address})
        else:
            return jsonify({'status': 'fail'})
    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)})


#--------------------------------------------------------- Payment status-----------------------------------------------
@app.route('/owo/payment', methods=['POST'])
@jwt_required
def app_charge():
    data = mongo.db.OWO
    db = data.orders
    signin_type = request.json['signin_type']
    user_id = request.json['user_id']
    amount = request.json['amount']
    address = request.json['address']
    reciept = request.json['reciept']
    order_status = request.json['order_status']
    ordered_date_time = request.json['ordered_date_time']
    ord_id = request.json['ord_id']
    output = []
    data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': reciept,
        'payment_capture': 1
    }
    order = (razorpay_client.order.create(data))
    print(order)
    db.update_many({'ord_id': ord_id},{'$set':{'signin_type': signin_type, 'orders': order, 'order_status': order_status,'delivery_status':"un_delivered",'transaction_id':reciept,
                   'ordered_date_time': ordered_date_time, 'address': address}})
    output.append({'user_id': user_id, 'signin_type': signin_type, 'orders': order, 'order_status': order_status,
                   'address': address})
    return jsonify({'status': "success", 'result': output})


#------------------------------------------------- Buy product ---------------------------------------------------------
@app.route('/owo/buy_product', methods=['POST', 'GET'])
@jwt_required
def buynow_product():
    try:
        data = mongo.db.OWO
        db = data.products
        db1 = data.corporate_users
        db2 = data.individual_users
        db3 = data.orders
        output = []
        user_id = request.json['user_id']
        payment_type = request.json['payment_type']
        signin_type = request.json['signin_type']
        product_id = request.json['product_id']
        package_type = request.json['package_type']
        select_product_item_quantity = request.json['select_product_item_quantity']
        select_time_slot = request.json['select_time_slot']
        order_status = request.json['order_status']
        purchase_price = request.json['purchase_price']
        discount_in_percentage = request.json['discount_in_percentage']
        mobile_number = int()
        email_id = str()
        product = []
        try:
            ord_id_list = [i['ord_id'] for i in db3.find()]
            if len(ord_id_list) is 0:
                ord_id = 1
            else:
                ord_id = int(ord_id_list[-1]) + 1
        except KeyError or ValueError:
            ord_id = int(1)
        for j in db1.find():
            for k in db2.find():
                for l in j, k:
                    if str(signin_type) == str(l['signin_type']) and int(user_id) == int(l['user_id']):
                        print(user_id)
                        print(signin_type)
                        mobile_number = l['mobile_number']
                        signin_type = l['signin_type']
                        email_id = l['email_id']
        for i in db.find():
            p_id = i['product_id']
            print(p_id)
            print(product_id)
            if str(product_id) == str(p_id):
                print("ok")
                db.find_one_and_update({'product_id': str(product_id)}, {'$set': {'order_status': order_status}})
                total_price = purchase_price
                print(total_price)
                product.append({'product_id': product_id, 'package_type': package_type,
                                'select_product_item_quantity': select_product_item_quantity,
                                'select_time_slot': select_time_slot, 'total_price': total_price,
                                'purchase_price': purchase_price,
                                'discount_in_percentage': discount_in_percentage})
                db3.insert({'ord_id':ord_id,'user_id':user_id,'signin_type':signin_type,'mobile_number':mobile_number,'email_id':email_id,'product_id':product_id,'delivery_slot':select_time_slot,'total_price':total_price})
                output.append(
                    {'ord_id':ord_id,'user_id': user_id, 'payment_type': payment_type, 'order_status': order_status,
                     'product': product, 'signin_type': signin_type})
                return jsonify({'status': 'success', 'message': 'successfully purchased', 'result': output})
    except Exception as e:
        return jsonify(status="Fail", message=str(e))


#----------------------------------------------- get_products_by_product_type ---------------------------------------
# @app.route('/owo/get_products_by_product_type', methods=['POST'])
# @jwt_required
# def getProductsByProductType():
#     data = mongo.db.OWO
#     db = data.products
#     db_r = data.rating
#     output = []
#     city_name = request.json['city_name']
#     package_type = request.json['package_type']
#     for i in db.find({'active_status': True}):
#         c_name = i['city_name']
#         for j in i['package_type']:
#             p_type = j['package_type']
#             if str(package_type) == str(p_type) and str(c_name) == str(city_name):
#                 temp = {}
#                 temp['company_name'] = i['company_name']
#                 temp['brand_name'] = i['brand_name']
#                 temp['package_type'] = j['package_type']
#                 temp['package_id'] = j['package_id']
#                 temp['purchase_price'] = j['purchase_price']
#                 temp['unit_price'] = j['mrp']
#                 temp['discount_in_percentage'] = j['discount_in_percentage']
#                 temp['return_policy'] = j['return_policy']
#                 temp['expiry_date'] = j['expiry_date']
#                 temp['product_rating'] = 0
#                 temp['product_no_of_rating'] = 0
#                 if 'product_quantity' not in i.keys():
#                     temp['available_quantity'] = 0
#                 else:
#                     temp['available_quantity'] = i['product_quantity']
#                 if 'product_id' not in i.keys():
#                     temp['product_id'] = '',
#                 else:
#                     temp['product_id'] = i['product_id']
#                 if 'product_name' not in i.keys():
#                     temp['product_name'] = '',
#                 else:
#                     temp['product_name'] = i['product_name']
#                 if 'product_image' not in i.keys():
#                     temp['product_image'] = '',
#                 else:
#                     temp['product_image'] = i['product_image']
#                 if 'purchase_price' not in j.keys():
#                     temp['purchase_price'] = '',
#                 else:
#                     temp['purchase_price'] = j['purchase_price']
#                 for k in db_r.find():
#                     p_id = k['product_id']
#                     r_history = k['rating_history']
#                     try:
#                         if str(p_id) == str(temp['product_id']):
#                             user_count = len(r_history)
#                             temp['product_no_of_rating'] = user_count
#                             temp['product_rating'] = k['current_rating']
#                     except KeyError or ValueError:
#                         pass
#                 output.append(temp)
#     return jsonify({"status": True, 'message': "product details get by product_type success", 'result': output})

@app.route('/owo/get_products_by_product_type', methods=['POST'])
@jwt_required
def getProductsByProductType():
    data = mongo.db.OWO
    db = data.products
    db_r = data.rating
    output = []
    city_name = request.json['city_name']
    package_type = request.json['package_type']
    sorting_type = request.json['sorting_type']
    if sorting_type == "DESCENDING":
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                c_name = i['city_name']
                for j in i['package_type']:
                    p_type = j['package_type']
                    if str(package_type) == str(p_type) and str(c_name) == str(city_name):
                        temp = {}
                        temp['company_name'] = i['company_name']
                        temp['brand_name'] = i['brand_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=True, key=lambda e: int(e['purchase_price']))
        return jsonify({"status": True, 'message': "product details get by product_type success", 'result': output})
    elif sorting_type == 'ASCENDING':
        for i in db.find(sort=[('purchase_price', pymongo.DESCENDING)]):
            a_status = i['active_status']
            if a_status is True:
                c_name = i['city_name']
                for j in i['package_type']:
                    p_type = j['package_type']
                    if str(package_type) == str(p_type) and str(c_name) == str(city_name):
                        temp = {}
                        temp['company_name'] = i['company_name']
                        temp['brand_name'] = i['brand_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=False, key=lambda e: int(e['purchase_price']))
        return jsonify({"status": True, 'message': "product details get by product_type success", 'result': output})
    else:
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                c_name = i['city_name']
                for j in i['package_type']:
                    p_type = j['package_type']
                    if str(package_type) == str(p_type) and str(c_name) == str(city_name):
                        temp = {}
                        temp['company_name'] = i['company_name']
                        temp['brand_name'] = i['brand_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
        return jsonify({"status": True, 'message': "product details get by product_type success", 'result': output})


# ---------------------------------------------------------get brand by id ----------------------------------------------
# @app.route('/owo/get_products_by_brand_name', methods=['POST'])
# @jwt_required
# def getProductsByBrandName():
#     data = mongo.db.OWO
#     db = data.products
#     db_r = data.rating
#     output = []
#     brand_name = request.json['brand_name']
#     city_name = request.json['city_name']
#     for i in db.find({'city_name': city_name}):
#         try:
#             prd = i['package_type']
#             for j in prd:
#                 b_id = i['brand_name']
#                 brand_name = brand_name.lower()
#                 brands_name = b_id.lower()
#                 if str(brand_name) == str(brands_name):
#                     temp = {}
#                     temp['brand_name'] = i['brand_name']
#                     temp['company_name'] = i['company_name']
#                     temp['package_type'] = j['package_type']
#                     temp['package_id'] = j['package_id']
#                     temp['purchase_price'] = j['purchase_price']
#                     temp['unit_price'] = j['mrp']
#                     temp['discount_in_percentage'] = j['discount_in_percentage']
#                     temp['return_policy'] = j['return_policy']
#                     temp['expiry_date'] = j['expiry_date']
#                     temp['product_rating'] = 0
#                     temp['product_no_of_rating'] = 0
#                     if 'product_quantity' not in i.keys():
#                         temp['available_quantity'] = 0,
#                     else:
#                         temp['available_quantity'] = i['product_quantity']
#                     if 'product_id' not in i.keys():
#                         temp['product_id'] = '',
#                     else:
#                         temp['product_id'] = i['product_id']
#                         print(i['product_id'])
#                     if 'product_name' not in i.keys():
#                         temp['product_name'] = '',
#                     else:
#                         temp['product_name'] = i['product_name']
#                     if 'product_image' not in i.keys():
#                         temp['product_image'] = '',
#                     else:
#                         temp['product_image'] = i['product_image']
#                     if 'purchase_price' not in j.keys():
#                         temp['purchase_price'] = '',
#                     else:
#                         temp['purchase_price'] = j['purchase_price']
#                     for k in db_r.find():
#                         p_id = k['product_id']
#                         r_history = k['rating_history']
#                         try:
#                             if str(p_id) == str(temp['product_id']):
#                                 user_count = len(r_history)
#                                 temp['product_no_of_rating'] = user_count
#                                 temp['product_rating'] = k['current_rating']
#                         except KeyError or ValueError:
#                             pass
#                     output.append(temp)
#         except KeyError or ValueError:
#             pass
#     return jsonify({"status": True, "message": "get products by brand_name success", 'result': output})

@app.route('/owo/get_products_by_brand_name', methods=['POST'])
@jwt_required
def getProductsByBrandName():
    data = mongo.db.OWO
    db = data.products
    db_r = data.rating
    output = []
    brand_name = request.json['brand_name']
    city_name = request.json['city_name']
    sorting_type = request.json['sorting_type']
    if sorting_type == "DESCENDING":
        for i in db.find({'city_name': city_name, 'active_status': True}):
            try:
                prd = i['package_type']
                for j in prd:
                    b_id = i['brand_name']
                    brand_name = brand_name.lower()
                    brands_name = b_id.lower()
                    if str(brand_name) == str(brands_name):
                        temp = {}
                        temp['brand_name'] = i['brand_name']
                        temp['company_name'] = i['company_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0,
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                            print(i['product_id'])
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=True, key=lambda e: int(e['purchase_price']))
            except KeyError or ValueError:
                pass
        return jsonify({"status": True, "message": "get products by brand_name success", 'result': output})
    elif sorting_type == 'ASCENDING':
        for i in db.find({'city_name': city_name,  'active_status': True}):
            try:
                prd = i['package_type']
                for j in prd:
                    b_id = i['brand_name']
                    brand_name = brand_name.lower()
                    brands_name = b_id.lower()
                    if str(brand_name) == str(brands_name):
                        temp = {}
                        temp['brand_name'] = i['brand_name']
                        temp['company_name'] = i['company_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0,
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                            print(i['product_id'])
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=False, key=lambda e: int(e['purchase_price']))
            except KeyError or ValueError:
                pass
        return jsonify({"status": True, "message": "get products by brand_name success", 'result': output})
    else:
        for i in db.find({'city_name': city_name,  'active_status': True}):
            try:
                prd = i['package_type']
                for j in prd:
                    b_id = i['brand_name']
                    brand_name = brand_name.lower()
                    brands_name = b_id.lower()
                    if str(brand_name) == str(brands_name):
                        temp = {}
                        temp['brand_name'] = i['brand_name']
                        temp['company_name'] = i['company_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0,
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                            print(i['product_id'])
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
            except KeyError or ValueError:
                pass
        return jsonify({"status": True, "message": "get products by brand_name success", 'result': output})


#------------------------------------------------- Product subscription plan -------------------------------------------
@app.route('/owo/product_subscribe', methods=['POST', 'GET'])
@jwt_required
def productSubscribe():
    data = mongo.db.OWO
    db = data.product_subscription_test
    output = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    product_id = request.json['product_id']
    package_type = request.json['package_type']
    purchase_price = request.json['purchase_price']
    buy_plan = request.json['buy_plan']
    set_quantity = request.json['set_quantity']
    frequency = request.json['frequency']
    starting_date = request.json['starting_date']
    product_expiry_date = request.json['product_expiry_date']
    # subscription_id = randomStringDigits()
    start_day = request.json['start_day']
    s_date = datetime.strptime(starting_date, "%d/%m/%y")
    modified_date = s_date + timedelta(days=buy_plan)
    plan_expiry_date = datetime.strftime(modified_date, "%d/%m/%y")
    subscription_status = request.json['subscription_status']
    try:
        subscription_id_list = [i['subscription_id'] for i in db.find()]
        if len(subscription_id_list) is 0:
            subscription_id = 1
        else:
            subscription_id = int(subscription_id_list[-1]) + 1
    except KeyError or ValueError:
        subscription_id = int(1)
    discount_in_percentage = request.json['discount_in_percentage']
    total_price = calculatePrice(set_quantity, purchase_price, buy_plan, start_day)
    total_quantity = calculateProductQuant(buy_plan, start_day, set_quantity)
    print(total_quantity)
    print(total_price)
    for i in db.find():
        if str(signin_type) == str(i['signin_type']) and int(user_id) == int(i['user_id']):
            db.update_one({'signin_type': signin_type}, {
                '$set': {'subscription_id': subscription_id, 'signin_type': signin_type, 'products': [
                    {'set_quantity': set_quantity, 'buy_plan': buy_plan, 'frequency': frequency,
                     'product_id': product_id, 'discount_in_percentage': discount_in_percentage,
                     'package_type': package_type, 'purchase_price': purchase_price,
                     'product_expiry_date': product_expiry_date, 'starting_date': starting_date,
                     'plan_expiry_date': plan_expiry_date, 'total_quantity': total_quantity,
                     'total_price': total_price}], 'subscription_status': subscription_status,
                         'delivery_status': "pending", 'user_id': user_id, 'payment_status': "pending"}})
            output.append({'user_id': user_id, 'subscription_id': subscription_id, 'set_quantity': set_quantity,
                           'signin_type': signin_type, 'buy_plan': buy_plan, 'frequency': frequency,
                           'product_id': product_id, 'package_type': package_type,
                           'discount_in_percentage': discount_in_percentage, 'purchase_price': purchase_price,
                           'product_expiry_date': product_expiry_date, 'plan_start_date': starting_date,
                           'subscription_status': subscription_status, 'plan_expiry_date': plan_expiry_date,
                           'total_quantity': total_quantity, 'total_price': total_price})
            return jsonify({"status": True, 'message': "subscription updated successfully", 'result': output})
    db.insert_one({'user_id': user_id, 'subscription_id': subscription_id, 'products': [
        {'set_quantity': set_quantity, 'buy_plan': buy_plan, 'frequency': frequency, 'product_id': product_id,
         'package_type': package_type, 'total_quantity': total_quantity,
         'discount_in_percentage': discount_in_percentage, 'total_price': total_price, 'purchase_price': purchase_price,
         'product_expiry_date': product_expiry_date}], 'starting_date': starting_date,
                   'plan_expiry_date': plan_expiry_date, 'subscription_status': subscription_status,
                   'delivery_status': "pending", 'signin_type': signin_type, 'payment_status': "pending"})
    output.append(
        {'user_id': user_id, 'subscription_id': subscription_id, 'set_quantity': set_quantity, 'buy_plan': buy_plan,
         'signin_type': signin_type, 'frequency': frequency, 'product_id': product_id, 'package_type': package_type,
         'discount_in_percentage': discount_in_percentage, 'purchase_price': purchase_price,
         'product_expiry_date': product_expiry_date, 'plan_start_date': starting_date, 'total_quantity': total_quantity,
         'total_price': total_price, 'subscription_status': subscription_status, 'plan_expiry_date': plan_expiry_date})
    return jsonify({"status": True, 'message': "subscription added successfully", 'result': output})


#------------------------------------------------- Payment status ------------------------------------------------------
@app.route('/owo/payment_status', methods=['POST', 'GET'])
@jwt_required
def paymentStatus():
    data = mongo.db.OWO
    db = data.product_subscription_test
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    payment_status = request.json['payment_status']
    subscription_id = request.json['subscription_id']
    amount = request.json['amount']
    receipt = request.json['receipt']
    delivery_address = request.json['delivery_address']
    delivery_status = request.json['delivery_status']
    output = []
    data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': receipt,
        'payment_capture': 1
    }
    order = (razorpay_client.order.create(data))
    for i in db.find():
        if int(subscription_id) == int(i['subscription_id']):
            db.update_many({'subscription_id': subscription_id}, {
                '$set': {'user_id': user_id, 'signin_type': signin_type, 'payment_status': payment_status,
                         'orders': order, 'delivery_status': delivery_status, 'delivery_addres': delivery_address,
                         'transaction_id': receipt}})
            output.append({'user_id': user_id, 'payment_status': payment_status, 'signin_type': signin_type,
                           'subscription_id': subscription_id, 'orders': order})
            return jsonify({'status': True, 'message': 'success', 'result': output})
    else:
        return jsonify({'status': False, 'message': "user_id not found"})


#------------------------------------------- get product by date -----------------------------------------------------
# @app.route('/owo/get_list_bydate', methods=['POST'])
# @jwt_required
# def getSubscriptionProductsByDate():
#     data = mongo.db.OWO
#     db2 = data.subscription_history
#     db = data.product_subscription_test
#     db1 = data.products
#     output = []
#     res = []
#     delivery_status = str()
#     user_id = request.json['user_id']
#     signin_type = request.json['signin_type']
#     date = request.json['date']
#     check_date = parse(date)
#     day = request.json['day']
#     subscription_status = str()
#     subcription_id = int()
#     order_id = str()
#     for s_status in db.find({'user_id':user_id,'signin_type':signin_type,'subscription_status':"cancelled"}):
#         return jsonify({'status': False, 'message': 'your subscription orders got cancelled', 'result': [],'subscription_status':"cancelled",'order_id':""})
#
#     for sub_status in db.find({'user_id': user_id, 'signin_type': signin_type}):
#         is_sub = sub_status['is_subscribed']
#         if is_sub is False:
#             return jsonify({'status': False, 'message': "You dont have a subscription please select subscription",
#                             'result': output})
#     for s_id in db.find({'user_id':user_id,'signin_type':signin_type}):
#         subscription_id = s_id['subscription_id']
#         print(subscription_id)
#     for ds in db2.find({'date':date}):
#         if str(date) == str(ds['date']):
#             for ord in ds['order_history']:
#                 if int(subscription_id) == int(ord['subscription_id']):
#                       print("ok3")
#                       delivery_status = ord['delivery_status']
#                       order_id = ord['order_id']
#     for i in db.find():
#         u_id = i['user_id']
#         s_type = i['signin_type']
#         if int(user_id) == int(u_id) and str(signin_type) == str(s_type) and i['is_subscribed'] == True:
#             subscription_status = i['subscription_status']
#             try:
#                 for j in i['products']:
#                     print("status ok")
#                     if j['cart_status'] == "deactive":
#                         print("cartdeactive")
#                         set_quantity = j['set_quantity']
#                         plan_start_date = i['starting_date']
#                         plan_expiry_date = i['plan_expiry_date']
#                         plan_sd = parse(plan_start_date)
#                         plan_ed = parse(plan_expiry_date)
#                         if plan_sd <= check_date <= plan_ed:
#                             print("okdates")
#                             for qua in set_quantity:
#                                 mydict = qua
#                                 for key in mydict:
#                                     if key == day:
#                                         quantity = mydict[key]
#                                         print(quantity)
#                                         p_i = j['purchase_price']
#                                         total_price = p_i * quantity
#                                         for k in db1.find():
#                                             p_type = k['package_type']
#                                             if str(j['product_id']) == str(k['product_id']):
#                                                 print("product_found")
#                                                 if 'product_image' not in k.keys():
#                                                     product_image = '',
#                                                 else:
#                                                     product_image = k['product_image']
#                                                 for l in p_type:
#                                                     u_price = l['unit_price']
#                                                     if 'package_type' not in l.keys():
#                                                         package_type = '',
#                                                     else:
#                                                         package_type = l['package_type']
#                                                     s_id = i['subscription_id']
#                                                     output.append(
#                                                         {'product_id': j['product_id'], 'product_image': product_image,
#                                                          'user_id': u_id,
#                                                          'signin_type': signin_type, 'product_name': k['product_name'],
#                                                          'subscription_id': i['subscription_id'],
#                                                          'delivery_status':delivery_status,
#                                                          'subscription_plan': i['buy_plan'],
#                                                          'subscription_status': i['subscription_status'],
#                                                          'package_type': package_type, 'product_quantity': quantity,
#                                                          'product_total_price': total_price,
#                                                          'unit_price': u_price, 'purchase_price': j['purchase_price']})
#                                                     res = [i for i in output if not (i['product_quantity'] == 0)]
#             except KeyError or ValueError:
#                 pass
#     return jsonify({'status': True, 'message': 'get images by subscription product_', 'result': res,'subscription_status':subscription_status,'order_id':order_id})


# ------------------------------------------- Add multiple products to subscription-------------------------------------
# @app.route('/owo/add_multipleProducts', methods=['POST'])
# @jwt_required
# def addMultipleProductsSubcription():
#     data = mongo.db.OWO
#     db = data.product_subscription_test
#     db_cu = data.corporate_users
#     db_iu = data.individual_users
#     mobile_number = int()
#     email_id = str()
#     output = []
#     user_id = request.json['user_id']
#     products = request.json['products']
#     signin_type = request.json['signin_type']
#     try:
#         subscription_id_list = [i['subscription_id'] for i in db.find()]
#         if len(subscription_id_list) is 0:
#             subscription_id = 1
#         else:
#             subscription_id = int(subscription_id_list[-1]) + 1
#     except KeyError or ValueError:
#         subscription_id = int(1)
#     for j in db_cu.find():
#         for k in db_iu.find():
#             for l in j, k:
#                 if str(signin_type) == str(l['signin_type']) and int(user_id) == int(l['user_id']):
#                     print(user_id)
#                     print(signin_type)
#                     mobile_number = l['mobile_number']
#                     signin_type = l['signin_type']
#                     email_id = l['email_id']
#     for i in db.find():
#         if str(signin_type) == str(i['signin_type']) and int(user_id) == int(i['user_id']):
#             product = i['products']
#             result_id = [dict(item, **{'product_status': "enabled"}) for item in products]
#             prod = result_id
#             lookup = {x['product_id']: x for x in prod}
#             lookup.update({x['product_id']: x for x in product})
#             result1 = list(lookup.values())
#             print(result1)
#             db.update_many({'subscription_id': i['subscription_id']}, {'$set': {'products':result1, 'payment_status': "pending", 'signin_type': signin_type,'mobile_number': mobile_number, 'email_id': email_id,'subscription_status':"active"}})
#             output.append({'user_id': user_id, 'signin_type': signin_type,'products': products})
#             return jsonify({'status': 'success', 'message': 'subscription to user updated successfully found', 'result': output})
#     results_id = [dict(item, **{'product_status': "enabled"}) for item in products]
#     db.insert_one({'user_id': user_id, 'products': results_id, 'subscription_id': subscription_id, 'signin_type': signin_type,'payment_status': "pending", 'mobile_number': mobile_number, 'email_id': email_id,'subscription_status':"active",'is_subscribed':False})
#     output.append({'user_id': user_id,'signin_type': signin_type, 'products': products})
#     return jsonify({'status': 'success', 'message': 'subscription for user added success', 'result': output})


#----------------------------------------- get product images subscription ---------------------------------------------
# @app.route('/owo/get_product_images_subscription', methods=['POST'])
# @jwt_required
# def getSubscriptionProductsImages():
#     data = mongo.db.OWO
#     db = data.product_subscription_test
#     db1 = data.products
#     output = []
#     product_count = int()
#     user_id = request.json['user_id']
#     sub_id = int()
#     signin_type = request.json['signin_type']
#     for i in db.find():
#         u_id = i['user_id']
#         s_type = i['signin_type']
#         if int(user_id) == int(u_id) and str(signin_type) == str(s_type) and str(i['payment_status']) == "pending":
#             s_i = i['subscription_id']
#             sub_id = s_i
#             try:
#                 products = i['products']
#             except KeyError or ValueError:
#                 pass
#             for j in products:
#                 if j['product_status']=="enabled":
#                     if j['cart_status']=="active" or j['cart_status']=="deactive":
#                         p_id = j['product_id']
#                         for k in db1.find():
#                             p_type = k['package_type']
#                             if str(p_id) == str(k['product_id']):
#                                 product_count += 1
#                                 # print(p_id)
#                                 if 'product_image' not in k.keys():
#                                     product_image = '',
#                                 else:
#                                     product_image = k['product_image']
#                                 for l in p_type:
#                                     u_price = l['unit_price']
#                                     if 'package_type' not in l.keys():
#                                         package_type = '',
#                                     else:
#                                         package_type = l['package_type']
#                                     output.append({'product_id': p_id, 'product_images': product_image, 'user_id': u_id,
#                                                    'signin_type': signin_type, 'product_name': k['product_name'],
#                                                    'package_type': package_type,
#                                                    'unit_price': u_price, 'purchase_price': j['purchase_price'],
#                                                    'subscription_id': i['subscription_id']})
#     return jsonify(
#         {'status': True, 'message': 'get images by subscription product_', 'result': output, 'count': product_count,
#          'subscription_id': sub_id})


#--------------------------------------------------- Get cart total ----------------------------------------------------
# @app.route('/owo/get_carttotal', methods=['POST'])
# @jwt_required
# def cartTotal():
#     data = mongo.db.OWO
#     db = data.product_subscription_test
#     db_wallet = data.owo_users_wallet
#     output = []
#     output1 = []
#     gstprice = []
#     user_id = request.json['user_id']
#     signin_type = request.json['signin_type']
#     products = request.json['products']
#     signin_type = request.json['signin_type']
#     buy_plan = request.json['buy_plan']
#     starting_date = request.json['starting_date']
#     s_date = datetime.datetime.strptime(starting_date, "%Y-%m-%d")
#     modified_date = s_date + timedelta(days=buy_plan)
#     plan_expiry_date = datetime.datetime.strftime(modified_date, "%Y-%m-%d")
#     start_day = request.json['start_day']
#     subscription_id = request.json['subscription_id']
#     frequency = request.json['frequency']
#     product_count = []
#     wallet_id = request.json['wallet_id']
#     wallet_amount = int()
#     required_amount = int()
#     for wallet in db_wallet.find({'wallet_id':wallet_id}):
#         wallet_amount = wallet['current_balance']
#     for i in products:
#         set_quantity = i['set_quantity']
#         purchase_price = i['purchase_price']
#         total_price = calculatePrice(set_quantity, purchase_price, buy_plan, start_day)
#         total_quantity = calculateProductQuant(buy_plan, start_day, set_quantity)
#         print(total_quantity)
#         product_count.append({'total_quantity':total_quantity})
#         print(product_count)
#         result2 = defaultdict(int)
#         for elm in product_count:
#             for k, v in elm.items():
#                 result2[k] += v
#         print(result2)
#         productcount = [result2[val] for val in result2 if result2[val] > 1]
#         print(productcount)
#         str3 = int(''.join(str(i) for i in productcount))
#         print(str3)
#         for j in db.find():
#             if str(signin_type) == str(j['signin_type']) and int(user_id) == int(j['user_id']):
#                 id = j['subscription_id']
#                 print(subscription_id)
#                 result_id = [dict(item, **{'product_status': "enabled"}) for item in products]
#                 db.update_many({'subscription_id': int(subscription_id)}, {
#                     '$set': {'products': result_id, 'buy_plan': buy_plan, 'starting_date': starting_date,
#                              'start_day': start_day, 'plan_expiry_date': plan_expiry_date,
#                              'subscription_status': "active", 'payment_status': "pending",'frequency':frequency}})
#         output1.append({'total_price': round(total_price)})
#         result = defaultdict(int)
#         for elm in output1:
#             for k, v in elm.items():
#                 result[k] += v
#         print(result)
#         total_cart_value = [result[val] for val in result if result[val] > 1]
#         print(total_cart_value)
#         str1 = int(''.join(str(i) for i in total_cart_value))
#         print(str1)
#         amount = str1
#         delivery_charges = SubscriptionDelivery_charges(signin_type, amount)
#         total_value = str1 + int(delivery_charges)
#         print(total_value)
#         if wallet_amount < total_value:
#           required_amount = total_value - wallet_amount
#           print(required_amount)
#         total_cart_value = str1
#         sub_details = getSubscriptionProductByDate(subscription_id,products,buy_plan,start_day)
#         print(sub_details)
#     db.update_many({'subscription_id': subscription_id}, {'$set': {'total_price': str1,'product_count':str3,'is_subscribed':False,'delivery_charges':delivery_charges}})
#     output.append({'subscription_plan': buy_plan, 'delivery_charge':delivery_charges, 'total_cart_value':total_value,
#                    'subscription_id': subscription_id,'sub_total':str1})
#     return jsonify({'status': "success", 'message': "success", 'result': output,'required_balance':required_amount,'current_wallet_balance':wallet_amount,'product_details':sub_details})


#--------------------------------------- Delete subscription by product id ---------------------------------------------
# @app.route('/owo/delete_subscription_by_product_id', methods=['POST'])
# @jwt_required
# def deleteSubscriptionByProductId():
#     try:
#         data = mongo.db.OWO
#         db = data.product_subscription_test
#         db1 = data.products
#         output = []
#         user_id = request.json['user_id']
#         signin_type = request.json['signin_type']
#         product_id = request.json['product_id']
#         p_id = []
#         for i in db.find({'user_id':user_id,'signin_type':signin_type}):
#             for j in i['products']:
#                 if j['product_id'] == product_id and j['cart_status'] == "deactive":
#                     db.find_one_and_update({'user_id':user_id,'signin_type':signin_type,'products.product_id': str(product_id)},{'$set': {'products.$.product_status':"disabled"}})
#                     p_id.append(product_id)
#                     return jsonify({"status": True, 'message': "subscription for product_id deleted", 'result':p_id})
#         db.find_one_and_update({'user_id':user_id,'signin_type':signin_type,'products.product_id': str(product_id)},{'$pull': {"products": {'product_id': str(product_id)}}})
#         output.append(product_id)
#         return jsonify({"status": True, 'message': "subscription for product_id deleted", 'result': output})
#     except Exception as e:
#         return jsonify({'status':False, 'message': str(e),'result':[]})


#---------------------------------------------- filter -----------------------------------------------------------------
@app.route('/owo/filter', methods=['POST'])
@jwt_required
def filter():
    data = mongo.db.OWO
    db1 = data.products
    db2 = data.rating
    output = []
    brands = request.json['brands']
    min_price = request.json['min_price']
    max_price = request.json['max_price']
    package_type = request.json['package_type']
    city_name = request.json['city_name']
    rating = request.json['rating']
    all_brand = []
    all_package = []
    for i in db1.find({'city_name': str(city_name)}):
        brd = i['brand_name']
        if brd in brands:
            all_brand.append(brd)
    for i in db1.find({'city_name': str(city_name)}):
        pkg = i['package_type']
        for j in pkg:
            pkgtype = j['package_type']
            if pkgtype in package_type:
                all_package.append(pkgtype)
    all_brand = list(set(all_brand))
    all_package = list(set(all_package))
    package_type = len(package_type)
    brands = len(brands)
    for j in db1.find({'city_name': str(city_name)}):
        brd = j['brand_name']
        for l in j['package_type']:
            p_price = l['purchase_price']
            price = int(p_price)
            if brd in all_brand and (int(min_price) <= price <= int(max_price)) and (l['package_type'] in all_package):
                for i in db2.find({"product_id": j['product_id']}):
                    if i['product_id'] == j['product_id'] and rating <= i['current_rating']:
                        if 'current_rating' not in i.keys():
                            rating1 = 0,
                        else:
                            rating1 = i['current_rating']
                        if 'rating_history' not in i.keys():
                            no_of_ratings = 0,
                        else:
                            no_of_ratings = len(i['rating_history'])
                        if 'product_image' not in j.keys():
                            product_image = '',
                        else:
                            product_image = j['product_image']
                        if 'product_quantity' not in j.keys():
                            available_quantity = 0
                        else:
                            available_quantity = j['product_quantity']
                        output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
                                       'product_image': product_image, 'product_rating': rating1,
                                       'brand_name': j['brand_name'], 'company_name': j['company_name'],
                                       'package_id': l['package_id'], 'product_no_of_ratings': no_of_ratings,
                                       'package_type': l['package_type'], 'purchase_price': l['purchase_price'],
                                       'unit_price': l['unit_price'], 'available_quantity': available_quantity,
                                       'discount_in_percentage': l['discount_in_percentage'],
                                       'return_policy': l['return_policy'], 'expiry_date': l['expiry_date']})
            elif brd in all_brand and (int(min_price) <= price <= int(max_price)):
                for i in db2.find():
                    if str(i['product_id']) == str(j['product_id']) and rating <= i['current_rating']:
                        if 'current_rating' not in i.keys():
                            rating1 = 0,
                        else:
                            rating1 = i['current_rating']
                        if 'rating_history' not in i.keys():
                            no_of_ratings = 0,
                        else:
                            no_of_ratings = len(i['rating_history'])
                        if 'product_image' not in j.keys():
                            product_image = '',
                        else:
                            product_image = j['product_image']
                        if 'product_quantity' not in j.keys():
                            available_quantity = 0
                        else:
                            available_quantity = j['product_quantity']
                        output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
                                       'product_image': product_image, 'product_rating': rating1,
                                       'brand_name': j['brand_name'], 'company_name': j['company_name'],
                                       'package_id': l['package_id'], 'product_no_of_ratings': no_of_ratings,
                                       'package_type': l['package_type'], 'purchase_price': l['purchase_price'],
                                       'unit_price': l['unit_price'],'available_quantity': available_quantity,
                                       'discount_in_percentage': l['discount_in_percentage'],
                                       'return_policy': l['return_policy'], 'expiry_date': l['expiry_date']})

            elif brd in all_brand and (l['package_type'] in all_package):
                for i in db2.find({"product_id": j['product_id']}):
                    if str(i['product_id']) == str(j['product_id']) and rating <= i['current_rating']:
                        if 'current_rating' not in i.keys():
                            rating1 = 0,
                        else:
                            rating1 = i['current_rating']
                        if 'rating_history' not in i.keys():
                            no_of_ratings = 0,
                        else:
                            no_of_ratings = len(i['rating_history'])
                        if 'product_image' not in j.keys():
                            product_image = '',
                        else:
                            product_image = j['product_image']
                        if 'product_quantity' not in j.keys():
                            available_quantity = 0
                        else:
                            available_quantity = j['product_quantity']
                        output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
                                       'product_image': product_image, 'product_rating': rating1,
                                       'brand_name': j['brand_name'], 'company_name': j['company_name'],
                                       'package_id': l['package_id'], 'product_no_of_ratings': no_of_ratings,
                                       'package_type': l['package_type'], 'purchase_price': l['purchase_price'],
                                       'unit_price': l['unit_price'],'available_quantity': available_quantity,
                                       'discount_in_percentage': l['discount_in_percentage'],
                                       'return_policy': l['return_policy'], 'expiry_date': l['expiry_date']})

            elif int(min_price) <= price <= int(max_price) and (l['package_type'] in all_package):
                for i in db2.find({"product_id": j['product_id']}):
                    if str(i['product_id']) == str(j['product_id']) and rating <= i['current_rating']:
                        if 'current_rating' not in i.keys():
                            rating1 = 0,
                        else:
                            rating1 = i['current_rating']
                        if 'rating_history' not in i.keys():
                            no_of_ratings = 0,
                        else:
                            no_of_ratings = len(i['rating_history'])
                        if 'product_image' not in j.keys():
                            product_image = '',
                        else:
                            product_image = j['product_image']
                        if 'product_quantity' not in j.keys():
                            available_quantity = 0
                        else:
                            available_quantity = j['product_quantity']
                        output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
                                       'product_image': product_image, 'product_rating': rating1,
                                       'brand_name': j['brand_name'], 'company_name': j['company_name'],
                                       'package_id': l['package_id'], 'product_no_of_ratings': no_of_ratings,
                                       'package_type': l['package_type'], 'purchase_price': l['purchase_price'],
                                       'unit_price': l['unit_price'],'available_quantity': available_quantity,
                                       'discount_in_percentage': l['discount_in_percentage'],
                                       'return_policy': l['return_policy'], 'expiry_date': l['expiry_date']})

            elif int(min_price) <= price <= int(max_price):
                for i in db2.find():
                    if str(i['product_id']) == str(j['product_id']) and rating <= i['current_rating']:
                        if 'current_rating' not in i.keys():
                            rating1 = 0,
                        else:
                            rating1 = i['current_rating']
                        if 'product_image' not in j.keys():
                            product_image = '',
                        else:
                            product_image = j['product_image']
                        if 'product_quantity' not in j.keys():
                            available_quantity = 0
                        else:
                            available_quantity = j['product_quantity']
                        if 'rating_history' not in i.keys():
                            no_of_ratings = 0,
                        else:
                            no_of_ratings = len(i['rating_history'])
                        output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
                                       'product_image': product_image, 'product_rating': rating1,
                                       'brand_name': j['brand_name'], 'company_name': j['company_name'],
                                       'package_id': l['package_id'], 'product_no_of_ratings': no_of_ratings,
                                       'package_type': l['package_type'], 'purchase_price': l['purchase_price'],
                                       'unit_price': l['unit_price'],'available_quantity': available_quantity,
                                       'discount_in_percentage': l['discount_in_percentage'],
                                       'return_policy': l['return_policy'], 'expiry_date': l['expiry_date']})

    output_both_not_null = []
    for i in output:
        if brands != 0 and package_type != 0:
            brd = i['brand_name']
            pck_type = i['package_type']
            if brd in all_brand and pck_type in all_package:
                output_both_not_null.append(i)
    only_package = []
    for i in output:
        if brands == 0 and package_type != 0:
            pck_type = i['package_type']
            if pck_type in all_package:
                only_package.append(i)
    only_brands = []
    for i in output:
        if package_type == 0 and brands != 0:
            brd = i['brand_name']
            if brd in all_brand:
                only_brands.append(i)
    both = []
    for i in output:
        if package_type == 0 and brands == 0:
            both.append(i)
    return jsonify({'status': True, 'message': 'get details', 'result': both+output_both_not_null+only_brands+only_package})


#------------------------------------------------- Search ---------------------------------------------------------------
@app.route('/owo/search', methods=['POST'])
@jwt_required
def search():
    data = mongo.db.OWO
    db = data.products
    db_rating = data.rating
    output = []

    product_name = request.json['product_name']
    city_name = request.json['city_name']

    for i in db.find({'$or': [{'product_name': {'$regex': product_name}}, {'brand_name': {'$regex': product_name}},
                              {'package_type.package_type': {'$regex': product_name}}]}):
        if str(city_name) == str(i['city_name']):
            for j in i['package_type']:
                temp = {}

                if 'product_image' not in i.keys():
                    temp['product_image'] = []
                else:
                    temp['product_image'] = i['product_image']
                temp['product_id'] = i['product_id']
                temp['company_name'] = i['company_name']
                temp['brand_name'] = i['brand_name']
                temp['package_type'] = j['package_type']
                temp['purchase_price'] = j['purchase_price']
                temp['unit_price'] = j['mrp']
                temp['package_id'] = j['package_id']
                temp['discount_in_percentage'] = j['discount_in_percentage']
                temp['return_policy'] = j['return_policy']
                temp['package_type'] = j['package_type']
                temp['expiry_date'] = j['expiry_date']
                temp['product_name'] = i['product_name']
                temp['available_quantity'] = i['product_quantity']
                try:
                    for k in db_rating.find():
                        pro_id = k['product_id']
                        if pro_id == i['product_id']:
                            if 'current_rating' not in k.keys():
                                temp['product_rating'] = 0,
                            else:
                                temp['product_rating'] = k['current_rating']

                            if 'rating_history' not in k.keys():
                                temp['product_no_of_ratings'] = '',
                            else:
                                temp['product_no_of_ratings'] = len(k['rating_history'])

                except KeyError or ValueError:
                    pass
                output.append(temp)
    return jsonify({'status': True, 'message': 'list of product names', 'result': output})


#------------------------------------------------- resend_otp_in -------------------------------------------------------
@app.route('/owo/resend_otp_in', methods=['POST', 'GET'])
def resendOTP_in():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        user_name = request.json['user_name']
        details = coll.find()
        for i in details:
            print("ok")
            name = i['email_id']
            m_number = i['mobile_number']
            u_id = i['user_id']
            print(name)
            if str(user_name) == str(m_number) or str(user_name) == str(name):
                otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(
                    m_number) + "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=your otp:" + str(
                    otp)
                msg = Message('your OWO account password is', sender="ramadevig@fugenx.com", recipients=[name])
                msg.body = 'Welcome to OWO.\n\n\n. Your OWO account passwosg91.comrd is: %s \n\n\n Thank You\n' % otp
                mail.send(msg)
                f = requests.get(url)
                print(f)
                coll.update_one({'user_id': int(u_id)}, {'$set': {'otp': str(otp)}})
                output.append({'email_id': name, 'mobile_number': m_number, 'otp':str(otp),
                               'user_id': u_id})
                return jsonify({'status': 'success', 'message': 'otp resend successfully', 'result': output})
        else:
            return jsonify({'status': 'fail', 'message': 'individual user does not exist in the database'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


#------------------------------------------------------ product_check --------------------------------------------------
@app.route('/owo/product_check', methods=['POST'])
@jwt_required
def SubscriptionCheck():
    data = mongo.db.OWO
    db = data.product_subscription_test
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    for i in db.find():
        if int(user_id)==i['user_id'] and str(signin_type)==str(i['signin_type']):
            if i['payment_status']=="success":
               return jsonify({'status':"success",'message':"subscription_found"})
    else:
        return jsonify({'status':'fail','message':"subscrption not found for this user"})


#------------------------------------------------------ Paytm -----------------------------------------------------------
MERCHANT_KEY='zhmE5IUyEFdIZYA4'
MID = 'UGrJVb04155196904214'
CALLBACK_URL="https://securegw-stage.paytm.in/theia/paytmCallback?ORDER_ID="


#--------------------------------------------- Generate checksum hash --------------------------------------------------
@app.route('/owo/generate_checksumhash',methods=['POST'])
@jwt_required
def generate_checksumhash():
    try:
        user_id=request.json['user_id']
        amount=request.json['amount']
        order_id= request.json['order_id']

        user_dict={
            'MID':MID,
            'ORDER_ID':str(order_id),
            'TXN_AMOUNT':str(amount),
            'CUST_ID':str(user_id),
            'INDUSTRY_TYPE_ID':'Retail',
            'WEBSITE':'APPSTAGING',
            'CHANNEL_ID':'WAP',
            'CALLBACK_URL':CALLBACK_URL+order_id
        }
        print(user_dict)
        user_dict['CHECKSUMHASH']= Checksum.generate_checksum(user_dict,MERCHANT_KEY)
        print(user_dict['CHECKSUMHASH'])
        return jsonify({'status':"success",'result':user_dict})

    except Exception as e:
        return jsonify({'status':'fail','result':str(e)})


#---------------------------------------------- check transaction ------------------------------------------------------
@app.route('/owo/check_transaction', methods=['POST'])
@jwt_required
def check_transaction():
            MERCHANT_KEY = 'zhmE5IUyEFdIZYA4'
            MID = 'UGrJVb04155196904214'
            user_id = request.json['user_id']
            order_id = request.json['order_id']
            paytmparams = {}
            paytmparams['MID'] = MID
            paytmparams['ORDERID'] = order_id
            checksum = Checksum.generate_checksum(paytmparams, MERCHANT_KEY)
            paytmparams['CHECKSUMHASH'] = checksum
            postdata = json.dumps(paytmparams)
            url = "https://securegw-stage.paytm.in/merchant-status/getTxnStatus"
            response = requests.post(url, data=postdata, headers={"Content-type": "application/json"}).json()
            return response


#----------------------------------------------- Get category ----------------------------------------------------------
@app.route('/owo/get_category', methods = ['GET'])
def get_category_app():
    data = mongo.db.OWO
    db = data.category
    output = []
    for i in db.find({'active_category': True}):
        temp = {}
        temp['category_id'] = i['category_id']
        temp['category_image'] = i['category_image']
        temp['category_type'] = i['category_type']
        output.append(temp)
    return jsonify({'status': True, 'message': 'category data get successfully', 'result': output})


#------------------------------------------ edit_individual_users ------------------------------------------------------
@app.route('/owo/edit_individual_user', methods=['POST'])
@jwt_required
def editIndividualUser():
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    user_id = request.json['user_id']
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    contact_number = request.json['contact_number']
    email_address = request.json['email_address']
    ts = calendar.timegm(time.gmtime())
    b = str(user_id) + str(ts)
    profile_pic = request.json['profile_pic']
    profile_pic = profile_pic.encode()
    profile_pic_path = '/var/www/html/owo/images/profile_images/' + str(b) + '.' + 'jpg'
    mongo_db_path = '/owo/images/profile_images/' + str(b) + '.' + 'jpg'
    with open(profile_pic_path, "wb") as fh:
        fh.write(base64.decodebytes(profile_pic))
    info = db.find()
    for i in info:
        u_id = i['user_id']
        m_number = i['mobile_number']
        e_id = i['email_id']
        if str(u_id) == str(user_id):
            if str(m_number) == str(contact_number) and str(email_address) == str(e_id):
                db.find_one_and_update({'user_id': int(user_id)},
                                       {'$set': {'first_name': first_name,
                                                 'last_name': last_name,
                                                 'mobile_number': int(contact_number),
                                                 'email_id': email_address,
                                                 'profile_pic': mongo_db_path,
                                                 'mobile_verified': i['mobile_verified'],
                                                 'email_verified': i['email_verified']}})
                output.append({'user_id': int(user_id), 'first_name': first_name,
                               'last_name': last_name, 'mobile_number': int(contact_number), 'email_id': email_address,
                               'profile_pic': mongo_db_path, 'mobile_verified': i['mobile_verified'],
                               'email_verified': i['email_verified']})
                return jsonify({'status': True, 'message': 'profile updated', 'result': output})
            else:
                if str(m_number) != str(contact_number) and str(email_address) != str(e_id):
                    db.find_one_and_update({'user_id': int(user_id)},
                                           {'$set': {'first_name': first_name,
                                                     'last_name': last_name,
                                                     'mobile_number': int(contact_number),
                                                     'email_id': email_address,
                                                     'profile_pic': mongo_db_path,
                                                     'mobile_verified': 0,
                                                     'email_verified': 0}})
                    output.append({'user_id': int(user_id), 'first_name': first_name,
                                   'last_name': last_name, 'email_id': email_address,
                                   'mobile_number': int(contact_number), 'profile_pic': mongo_db_path,
                                   'mobile_verified': 0, 'email_verified': 0})
                    return jsonify({'status': True, 'message': 'profile updated please verify mobile_number and email_id',
                                    'result': output})

                elif str(m_number) != str(contact_number):
                    db.find_one_and_update({'user_id': int(user_id)},
                                           {'$set': {'first_name': first_name,
                                                     'last_name': last_name,
                                                     'mobile_number': int(contact_number),
                                                     'email_id': email_address,
                                                     'profile_pic': mongo_db_path,
                                                     'mobile_verified': 0}})
                    output.append({'user_id': int(user_id), 'first_name': first_name,
                                   'last_name': last_name, 'mobile_number': int(contact_number),
                                   'email_id': email_address, 'profile_pic': mongo_db_path,
                                   'mobile_verified': 0, 'email_verified': i['email_verified']})
                    return jsonify({'status': True, 'message': 'profile updated please verify mobile_number',
                                    'result': output})
                elif str(e_id) != str(email_address):
                    db.find_one_and_update({'user_id': int(user_id)},
                                           {'$set': {'first_name': first_name,
                                                     'last_name': last_name,
                                                     'mobile_number': int(contact_number),
                                                     'email_id': email_address,
                                                     'profile_pic': mongo_db_path,
                                                     'email_verified': 0}})
                    output.append({'user_id': int(user_id), 'first_name': first_name,
                                   'last_name': last_name, 'mobile_number': int(contact_number),
                                   'email_id': email_address, 'profile_pic': mongo_db_path,
                                   'email_verified': 0, 'mobile_verified': i['mobile_verified']})
                    return jsonify({'status': True, 'message': 'profile updated please verify email_id',
                                    'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid user_id', 'result': output})


#------------------------------------------------ Update Mobile Number in Individual Users ----------------------------
@app.route('/owo/update_mobile_number_in', methods= ['POST'])
@jwt_required
def update_mobile_in():
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    user_id = request.json['user_id']
    contact_number = request.json['contact_number']
    mobile_result = db.find({'mobile_number': int(contact_number)})

    for i in db.find():
        u_id = i['user_id']
        if mobile_result.count() != 0:
            return jsonify({'status': False, 'message': 'mobile number is already exist', 'result': output})
        if str(u_id) == str(user_id):
            otp = random.randint(1000, 9999)
            url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(contact_number) + \
                  "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                  str(otp)
            f = requests.get(url)
            db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'mobile_number': int(contact_number),
                                                                        'otp': str(otp),
                                                                        'mobile_verified': 0}})
            output.append({'user_id': int(user_id), 'mobile_number': contact_number, 'otp': str(otp),
                           'mobile_verified': 0})
            return jsonify({'status': True, 'message': 'mobile_number updated', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})


#--------------------------------------------------- Update Email Id in Individual Users -------------------------------
@app.route('/owo/update_email_id_in', methods= ['POST'])
@jwt_required
def update_email_in():
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    user_id = request.json['user_id']
    email_id = request.json['email_id']
    email_result = db.find({'email_id': str(email_id)})

    for i in db.find():
        u_id = i['user_id']
        if email_result.count() != 0:
            return jsonify({'status': False, 'message': 'email_id already exist', 'result': output})
        if str(u_id) == str(user_id):
            email_otp = random.randint(1000, 9999)
            msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com",
                          recipients=[email_id])
            print(i['email_id'])
            msg.body = 'Welcome to OWO \n\n Your mail verification OTP' + str(email_otp)
            mail.send(msg)
            db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'email_id': str(email_id),
                                                                        'email_otp': str(email_otp),
                                                                        'email_verified': 0}})
            output.append({'user_id': int(user_id), 'email_id': email_id, 'email_otp': str(email_otp),
                           'email_verified': 0})
            return jsonify({'status': True, 'message': 'email id is updated', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})


#------------------------------------------------- Edit_corporate_users ------------------------------------------------
@app.route('/owo/edit_corporate_user', methods=['POST'])
@jwt_required
def editCorporateUser():
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    user_id = request.json['user_id']
    company_name = request.json['company_name']
    official_email_id = request.json['official_email_id']
    contact_number = request.json['contact_number']
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    gst_number = request.json['gst_number']
    legal_name_of_business = request.json['legal_name_of_business']
    state = request.json['state']
    pan_number = request.json['pan_number']
    ts = calendar.timegm(time.gmtime())
    b = str(user_id) + str(ts)
    profile_pic = request.json['profile_pic']
    profile_pic = profile_pic.encode()
    profile_pic_path = '/var/www/html/owo/images/profile_images/' + str(b) + '.' + 'jpg'
    mongo_db_path = '/owo/images/profile_images/' + str(b) + '.' + 'jpg'
    with open(profile_pic_path, "wb") as fh:
        fh.write(base64.decodebytes(profile_pic))
    info = db.find()
    for i in info:
        u_id = i['user_id']
        m_number = i['mobile_number']
        e_id = i['email_id']
        if str(u_id) == str(user_id):
            if str(m_number) == str(contact_number) and str(official_email_id) == str(e_id):
                db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'company_name': company_name,
                                                                            'email_id': str(official_email_id),
                                                                            'mobile_number': int(contact_number),
                                                                            'first_name': first_name,
                                                                            'last_name': last_name,
                                                                            'gst_number': gst_number,
                                                                            'legal_name_of_business':
                                                                                legal_name_of_business,
                                                                            'state': state,
                                                                            'pan_number': pan_number,
                                                                            'profile_pic': mongo_db_path,
                                                                            'email_verified': i['email_verified'],
                                                                            'mobile_verified': i['mobile_verified']}})
                output.append({'user_id': int(user_id), 'company_name': company_name, 'email_id': official_email_id,
                               'mobile_number': int(contact_number), 'first_name': first_name, 'last_name': last_name,
                               'gst_number': gst_number, 'legal_name_of_business': legal_name_of_business,
                               'state': state, 'pan_number': pan_number, 'profile_pic': mongo_db_path,
                               'email_verified': i['email_verified'], 'mobile_verified': i['mobile_verified']})
                return jsonify({'status': True, 'message': 'profile updated', 'result': output})
            else:
                if str(m_number) != str(contact_number) and str(official_email_id) != str(e_id):
                    db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'company_name': company_name,
                                                                                'email_id': str(official_email_id),
                                                                                'mobile_number': int(contact_number),
                                                                                'first_name': first_name,
                                                                                'last_name': last_name,
                                                                                'gst_number': gst_number,
                                                                                'legal_name_of_business':
                                                                                    legal_name_of_business,
                                                                                'state': state,
                                                                                'pan_number': pan_number,
                                                                                'profile_pic': mongo_db_path,
                                                                                'email_verified': 0,
                                                                                'mobile_verified': 0}})
                    output.append({'user_id': int(user_id), 'company_name': company_name,
                                   'email_id': str(official_email_id), 'mobile_number': int(contact_number),
                                   'first_name': first_name, 'last_name': last_name, 'gst_number': gst_number,
                                   'legal_name_of_business': legal_name_of_business, 'state': state,
                                   'pan_number': pan_number, 'profile_pic': mongo_db_path,
                                   'email_verified': 0, 'mobile_verified': 0})
                    return jsonify({'status': True, 'message': 'profile updated please verify mobile_number and email_id',
                                    'result': output})
                elif str(m_number) != str(contact_number):
                    db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'company_name': company_name,
                                                                                'email_id': str(official_email_id),
                                                                                'mobile_number': int(contact_number),
                                                                                'first_name': first_name,
                                                                                'last_name': last_name,
                                                                                'gst_number': gst_number,
                                                                                'legal_name_of_business':
                                                                                    legal_name_of_business,
                                                                                'state': state,
                                                                                'pan_number': pan_number,
                                                                                'profile_pic': mongo_db_path,
                                                                                'mobile_verified': 0}})
                    output.append({'user_id': int(user_id), 'company_name': company_name,
                                   'email_id': str(official_email_id), 'mobile_number': int(contact_number),
                                   'first_name': first_name, 'last_name': last_name, 'gst_number': gst_number,
                                   'legal_name_of_business': legal_name_of_business, 'profile_pic': mongo_db_path,
                                   'state': state, 'pan_number': pan_number, 'mobile_verified': 0,
                                   'email_verified': i['email_verified']})
                    return jsonify({'status': True, 'message': 'profile updated please verify mobile_number',
                                    'result': output})

                elif str(e_id) != str(official_email_id):
                    db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'company_name': company_name,
                                                                                'email_id': official_email_id,
                                                                                'mobile_number': int(contact_number),
                                                                                'first_name': first_name,
                                                                                'last_name': last_name,
                                                                                'gst_number': gst_number,
                                                                                'legal_name_of_business':
                                                                                    legal_name_of_business,
                                                                                'state': state,
                                                                                'pan_number': pan_number,
                                                                                'profile_pic': mongo_db_path,
                                                                                'email_verified': 0}})
                    output.append({'user_id': int(user_id), 'company_name': company_name,
                                   'email_id': str(official_email_id), 'mobile_number': int(contact_number),
                                   'first_name': first_name, 'last_name': last_name, 'gst_number': gst_number,
                                   'legal_name_of_business': legal_name_of_business, 'state': state,
                                   'pan_number': pan_number, 'profile_pic': mongo_db_path,
                                   'mobile_verified': i['mobile_verified'], 'email_verified': 0})
                    return jsonify({'status': True, 'message': 'profile updated please verify email_id',
                                    'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid user id', 'result': output})


#--------------------------------------------- Update Mobile Number for Corporate User --------------------------------
@app.route('/owo/update_mobile_number_cp', methods= ['POST'])
@jwt_required
def update_mobile_cp():
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    user_id = request.json['user_id']
    mobile_number = request.json['mobile_number']
    mobile_result = db.find({'mobile_number': int(mobile_number)})
    for i in db.find():
        u_id = i['user_id']
        if mobile_result.count() != 0:
            return jsonify({'status': False, 'message': 'mobile_number is already registered', 'result': output})
        if str(u_id) == str(user_id):
            otp = random.randint(1000, 9999)
            url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
                  "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                  str(otp)
            f = requests.get(url)
            print(f)
            db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'mobile_number': int(mobile_number),
                                                                        'otp': str(otp),
                                                                        'mobile_verified': 0}})
            output.append({'user_id': int(user_id), 'mobile_number': mobile_number, 'otp': str(otp),
                           'mobile_verified': 0})
            return jsonify({'status': True, 'message': 'mobile_number updated', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})


#--------------------------------------------------- Update Email Id for Corporate User --------------------------------
@app.route('/owo/update_email_id_cp', methods=['POST'])
@jwt_required
def update_email_cp():
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    user_id = request.json['user_id']
    official_email_id = request.json['official_email_id']
    email_result = db.find({'email_id': official_email_id})

    for i in db.find():
        u_id = i['user_id']
        if email_result.count() != 0:
            return jsonify({'status': False, 'message': 'email_id already exist', 'result': output})
        if str(u_id) == str(user_id):
            email_otp = random.randint(1000, 9999)
            msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com",
                          recipients=[official_email_id])
            print(i['email_id'])
            msg.body = 'Welcome to OWO \n\n Your mail verification OTP' + str(email_otp)
            mail.send(msg)
            db.find_one_and_update({'user_id': int(user_id)}, {'$set': {'email_id': str(official_email_id),
                                                                        'email_otp': str(email_otp),
                                                                        'email_verified': 0}})
            output.append({'user_id': int(user_id), 'email_id': official_email_id, 'email_otp': str(email_otp),
                           'email_verified': 0})
            return jsonify({'status': True, 'message': 'email id updated', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})


#---------------------------- Change Password for Corporate users and Individual user ---------------------------------
@app.route('/owo/user_change_password', methods=['POST'])
@jwt_required
def userChangePassword():
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    output = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    current_password = request.json['current_password']
    new_password = request.json['new_password']
    confirm_password = request.json['confirm_password']
    if new_password != confirm_password:
        return "Please enter the same passwords."
    if str(signin_type) == 'corporate':
        details = db.find()
        for i in details:
            u_id = i['user_id']
            pwd = i['password']
            if str(u_id) == str(user_id):
                if str(pwd) == str(current_password):
                    db.find_one_and_update({'user_id': int(user_id)},
                                           {'$set': {'password': new_password, 'confirm_password': confirm_password}})
                    output.append({'user_id': user_id, 'signin_type': signin_type, 'password': new_password,
                                   'confirm_password': confirm_password})
                    return jsonify({'status': True, 'message': 'password changed', 'result': output})
                else:
                    return jsonify({'status': False, 'message': 'password is not matched', 'result': output})
    elif str(signin_type) == 'individual':
        info1 = db1.find()
        for i in info1:
            u_id = i['user_id']
            pwd = i['password']
            if str(u_id) == str(user_id):
                if str(current_password) == str(pwd):
                    db1.find_one_and_update({'user_id': int(user_id)}, {'$set': {'password': new_password,
                                                                                'confirm_password': confirm_password}})
                    output.append({'user_id': int(user_id), 'signin_type':signin_type, 'password': new_password,
                                   'confirm_password': confirm_password})
                    return jsonify({'status': True, 'message': 'password changed', 'result': output})
                else:
                    return jsonify({'status': False, 'message': 'password is not matched', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    else:
        return jsonify({'status': True, 'message': 'invalid signin_type', 'result': output})


#------------------------------------------------- Add address ---------------------------------------------------------
@app.route('/owo/add_address', methods=['POST', 'GET'])
def add_address():
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    output = []
    address_id = int(1)
    user_id = request.json['user_id']
    building_number = request.json['building_number']
    address = request.json['address']
    landmark = request.json['landmark']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    city_name = request.json['city_name']
    address_type = request.json['address_type']
    signin_type = request.json['signin_type']
    if str(signin_type) == "corporate":
        info = db.find()
        for i in info:
            u_id = i['user_id']
            try:
                u_address = i['user_address']
            except KeyError or ValueError:
                u_address = 0
            if str(u_id) == str(user_id):
                if u_address != 0:
                    address_id_list = [k['address_id'] for k in u_address]
                    if len(address_id_list) is 0:
                        address_id = 1
                    else:
                        address_id = int(address_id_list[-1]) + 1
                    for j in u_address:
                        try:
                            a_id = j['address_id']
                        except KeyError or ValueError:
                            a_id = 0
                        if a_id != 0:
                            db.find_one_and_update({'user_id': int(user_id)}, {
                                '$push': {'user_address': {'address_id': int(address_id),
                                                           'building_number': building_number,
                                                           'address': address,
                                                           'landmark': landmark,
                                                           'city_name': city_name,
                                                           'address_type': address_type, 'latitude': latitude,
                                                           'longitude': longitude, 'default_address': False}}})
                            output.append({'user_id': int(user_id), 'address_id': int(address_id),
                                           'building_number': building_number, 'address': address,
                                           'landmark': landmark, 'address_type': address_type, 'city_name': city_name,
                                           'signin_type': 'corporate', 'latitude': latitude, 'longitude': longitude,
                                           'default_address': False})
                            return jsonify({'status': True, 'message': 'address added successfully',
                                            'result': output})

                db.find_one_and_update({'user_id': int(user_id)}, {
                    '$push': {'user_address': {'address_id': int(address_id),
                                               'building_number': building_number,
                                               'address': address,
                                               'city_name': city_name,
                                               'landmark': landmark,
                                               'address_type': address_type, 'latitude': latitude,
                                               'longitude': longitude, 'default_address': True}}})
                output.append({'user_id': int(user_id), 'address_id': int(address_id),
                               'building_number': building_number,
                               'address': address, 'city_name': city_name,
                               'landmark': landmark,
                               'address_type': address_type, 'signin_type': 'corporate', 'latitude': latitude,
                               'longitude': longitude, 'default_address': True})
                return jsonify({'status': True, 'message': 'address added successfully',
                                'result': output})
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    elif str(signin_type) == 'individual':
        info2 = db1.find()
        for j in info2:
            id = j['user_id']
            try:
                u_address = j['user_address']
            except KeyError or ValueError:
                u_address = 0
            if str(id) == str(user_id):
                if u_address != 0:
                    address_id_list = [l['address_id'] for l in u_address]
                    if len(address_id_list) is 0:
                        address_id = 1
                    else:
                        address_id = int(address_id_list[-1]) + 1
                    for m in u_address:
                        try:
                            a_id = m['address_id']
                        except KeyError or ValueError:
                            a_id = 0
                        if a_id != 0:
                            db1.find_one_and_update({'user_id': int(user_id)}, {
                                '$push': {'user_address': {'address_id': int(address_id),
                                                           'building_number': building_number,
                                                           'address': address,
                                                           'city_name': city_name,
                                                           'landmark': landmark,
                                                           'address_type': address_type, 'latitude': latitude,
                                                           'longitude': longitude, 'default_address': False}}})
                            output.append(
                                {'user_id': int(user_id), 'building_number': building_number, 'address': address, 'city_name': city_name,
                                 'address_type': address_type, 'landmark': landmark, 'signin_type': 'individual',
                                 'address_id': int(address_id), 'latitude': latitude, 'longitude': longitude,
                                 'default_address': False})
                            return jsonify({'status': True, 'message': 'address added successfully',
                                            'result': output})

                db1.find_one_and_update({'user_id': int(user_id)}, {
                    '$push': {'user_address': {'address_id': int(address_id),
                                               'building_number': building_number,
                                               'address': address,
                                               'landmark': landmark,
                                               'city_name': city_name,
                                               'address_type': address_type, 'latitude': latitude,
                                               'longitude': longitude, 'default_address': True}}})
                output.append({'user_id': int(user_id), 'building_number': building_number,
                               'address': address, 'city_name': city_name,
                               'address_type': address_type,
                               'landmark': landmark, 'signin_type': 'individual', 'address_id': int(address_id),
                               'latitude': latitude, 'longitude': longitude, 'default_address': True})
                return jsonify({'status': True, 'message': 'address added successfully',
                                'result': output})
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid signin type', 'result': output})


#--------------------------------------------- Edit_address ------------------------------------------------------------
@app.route('/owo/edit_address', methods=['POST'])
def edit_address1():
    data = mongo.db.OWO
    db1 = data.corporate_users
    db2 = data.individual_users
    output = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    address_id = request.json['address_id']
    building_number = request.json['building_number']
    address = request.json['address']
    landmark = request.json['landmark']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    city_name = request.json['city_name']
    address_type = request.json['address_type']
    if str(signin_type) == 'corporate':
        info = db1.find()
        for i in info:
            u_id = i['user_id']
            try:
                u_address = i['user_address']
                for j in u_address:
                    a_id = j['address_id']
                    if str(u_id) == str(user_id):
                        if str(a_id) == str(address_id):
                            print("ok")
                            db1.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                                    {'$set':
                                                        {'user_address.$.building_number': building_number,
                                                         'user_address.$.address': address,
                                                         'user_address.$.city_name': city_name,
                                                         'user_address.$.landmark': landmark,
                                                         'user_address.$.latitude': latitude,
                                                         'user_address.$.longitude': longitude,
                                                         'user_address.$.address_type': address_type}})
                            output.append({'user_id': int(user_id), 'signin_type': signin_type,
                                           'address_id': int(address_id), 'building_number': building_number,
                                           'address': address, 'landmark': landmark, 'city_name': city_name,
                                           'latitude': latitude, 'longitude': longitude, 'address_type': address_type,
                                           'default_address': j['default_address']})
                            return jsonify({'status': True, 'message': 'address edited successfully',
                                            'result': output})
            except KeyError or ValueError:
                pass
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    elif str(signin_type) == 'individual':
        info1 = db2.find()
        for m in info1:
            u_id = m['user_id']
            try:
                u_address = m['user_address']
                for n in u_address:
                    a_id = n['address_id']
                    if str(u_id) == str(user_id):
                        if str(a_id) == str(address_id):
                            print("ok")
                            db2.find_one_and_update({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                                    {'$set':
                                                         {'user_address.$.building_number': building_number,
                                                          'user_address.$.address': address,
                                                          'user_address.$.landmark': landmark,
                                                          'user_address.$.city_name': city_name,
                                                          'user_address.$.latitude': latitude,
                                                          'user_address.$.longitude': longitude,
                                                          'user_address.$.address_type': address_type}})
                            output.append(
                                {'user_id': int(user_id), 'signin_type': signin_type, 'address_id': int(address_id),
                                 'building_number': building_number,
                                 'address': address, 'city_name': city_name,
                                 'landmark': landmark, 'address_type': address_type, 'latitude': latitude,
                                 'longitude': longitude, 'default_address': n['default_address']})
                            return jsonify({'status': True, 'message': 'address edited successfully',
                                            'result': output})
            except KeyError or ValueError:
                pass
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid signin_type', 'result': output})


# ------------------------------------------------------ delete address ----------------------------------------------
@app.route('/owo/delete_address', methods=['POST'])
def delete_address1():
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    output = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    address_id = request.json['address_id']
    if str(signin_type) == 'corporate':
        for i in db.find():
            u_id = i['user_id']
            try:
                u_address = i['user_address']
                for j in u_address:
                    a_id = j['address_id']
                    d_address = j['default_address']
                    if str(address_id) == str(j['address_id']) and str(u_id) == str(user_id):
                        print(a_id)
                        if d_address == True:
                            return jsonify({'status': False,
                                            'message': 'this is default address user is not able to delete this address',
                                            'result': output})
                        db.update_one({'user_id': int(user_id)},
                                      {'$pull': {'user_address': {'address_id': int(address_id)}}})
                        return jsonify({'status': True, 'message': 'deleted address success', 'result': output})
            except KeyError or ValueError:
                pass
        return jsonify({'status': False, 'message': 'invalid credential', 'result': output})
    elif str(signin_type) == 'individual':
        for k in db1.find():
            u_id = k['user_id']
            try:
                u_address = k['user_address']
                for l in u_address:
                    a_id = l['address_id']
                    d_address = l['default_address']
                    if str(a_id) == str(l['address_id']) and str(u_id) == str(user_id):
                        if d_address == False:
                            db1.update_one({'user_id': int(user_id)},
                                           {'$pull': {'user_address': {'address_id': int(address_id)}}})
                            return jsonify({'status': True, 'message': 'deleted address success', 'result': output})
            except KeyError or ValueError:
                pass
        return jsonify({'status': False, 'message': 'invalid credential', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid signin_type', 'result': output})


# -------------------------------------------- get address api --------------------------------------------------------
@app.route('/owo/get_address', methods=['POST'])
def get_address1():
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    output = []
    address_id = request.json['address_id']
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    city_name = request.json['city_name']
    if str(signin_type) == 'corporate':
        for i in db.find():
            u_id = i['user_id']
            try:
                u_address = i['user_address']
            except KeyError or ValueError:
                pass
            if str(u_id) == str(user_id):
                for j in u_address:
                    a_id = j['address_id']
                    c_name = j['city_name']
                    if str(a_id) == str(address_id):
                        output.append({'address_id': j['address_id'],
                                       'building_number': j['building_number'],
                                       'address': j['address'], 'city_name': city_name,
                                       'landmark': j['landmark'], 'address_type': j['address_type'],
                                       'latitude': j['latitude'], 'longitude': j['longitude']})
                        return jsonify({'status': True, 'message': 'address data get successfully',
                                        'result': output})
                    return jsonify({'status': False, 'message': 'user_address not exist', 'result': output})
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    elif str(signin_type) == 'individual':
        for k in db1.find():
            u_id = k['user_id']
            try:
                u_address = k['user_address']
            except KeyError or ValueError:
                pass
            if str(u_id) == str(user_id):
                for l in u_address:
                    a_id = l['address_id']
                    c_name = l['city_name']
                    if str(a_id) == str(address_id):
                        output.append({'address_id': l['address_id'], 'city_name': l['city_name'],
                                       'building_number': l['building_number'], 'address': l['address'],
                                       'landmark': l['landmark'], 'address_type': l['address_type'],
                                       'latitude': l['latitude'], 'longitude': l['longitude']})
                        return jsonify({'status': True, 'message': 'address data get successfully',
                                        'result': output})
                return jsonify({'status': False, 'message': 'user_address not exist', 'result': output})
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid signin_type', 'result': output})


#------------------------------------------- Get all address by user id & signin type ----------------------------------
@app.route('/owo/get_all_address/<user_id>/<signin_type>', methods=['GET'])
def get_all_address(user_id, signin_type):
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    output = []
    if str(signin_type) == "corporate":
        info = db.find()
        for i in info:
            id = i['user_id']
            if int(id) == int(user_id):
                try:
                    address = i['user_address']
                    return jsonify(
                        {'status': True, 'message': 'address data get successfully', 'result': address})
                except KeyError or ValueError:
                    address = []
                    return jsonify({'status':False, 'message': 'user_address not found', 'result': address})
        return jsonify({'status': False, 'message': ' invalid user_id'})
    elif str(signin_type) == "individual":
        info2 = db1.find()
        for j in info2:
            id = j['user_id']
            if int(id) == int(user_id):
                try:
                    address = j['user_address']
                    return jsonify(
                        {'status': True, 'message': 'address data get successfully', 'result': address})
                except KeyError or ValueError:
                    address = []
                    return jsonify({'status':False, 'message': 'user_address not found', 'result': address})
        return jsonify({'status': False, 'message': ' invalid user_id'})
    else:
        return jsonify({'status': False, 'message': 'invalid signin_type', 'result': output})


#--------------------------------------------------- set as default address -------------------------------------------
@app.route('/owo/set_as_default', methods=['POST'])
def setAsDefault():
    global c_name
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    output = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    address_id = request.json['address_id']
    if str(signin_type) == 'corporate':
        info = db.find()
        for i in info:
            u_id = i['user_id']
            if int(u_id) == int(user_id):
                try:
                    u_address = i['user_address']
                    for j in u_address:
                        d_address = j['default_address']
                        if d_address == True:
                            c_name = j['city_name']
                            for k in u_address:
                                a_id = k['address_id']
                                if int(a_id) == int(address_id):
                                    cname = k['city_name']
                                    if str(c_name) == str(cname):
                                        db.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                                       {'$set': {'user_address.$[].default_address': False}})
                                        db.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                                       {'$set': {'user_address.$.default_address': True}})
                                        output.append({'user_id': user_id, 'address_id': address_id, 'default_address': True})
                                        return jsonify({'status': True, 'message': 'address set as default', 'result': output})
                                    else:
                                        return jsonify({'status':False, 'message': 'default address city is different',
                                                        'result':output})
                except KeyError or ValueError:
                        u_address = ''
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    elif str(signin_type) == 'individual':
        info1 = db1.find()
        for i in info1:
            u_id = i['user_id']
            if int(u_id) == int(user_id):
                try:
                    u_address = i['user_address']
                    for l in u_address:
                        d_address = l['default_address']
                        if d_address == True:
                            c_name = l['city_name']
                            for m in u_address:
                                a_id = m['address_id']
                                if int(a_id) == int(address_id):
                                    cname =  m['city_name']
                                    if str(c_name) == str(cname):
                                        db1.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                                       {'$set': {'user_address.$[].default_address': False}})
                                        db1.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                                       {'$set': {'user_address.$.default_address': True}})
                                        output.append({'user_id': user_id, 'address_id': address_id, 'default_address': True})
                                        return jsonify({'status': True, 'message': 'address set as default', 'result': output})
                                    else:
                                        return jsonify({'status':False, 'message': 'default address city is different',
                                                        'result': output})
                except KeyError or ValueError:
                    u_address = ''
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid signin_type', 'result': output})


#------------------------------------------ Get Profile Corporate -----------------------------------------------------
@app.route('/owo/get_profile_corporate/<user_id>', methods=['GET'])
def get_profile_corporate(user_id):
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    for i in db.find():
        temp = {}
        u_id = i['user_id']
        if int(u_id) == int(user_id):
            signin_type = i['signin_type']
            first_name = i['first_name']
            last_name = i['last_name']
            mobile_number = i['mobile_number']
            email_id = i['email_id']
            password = i['password']
            company_name = i['company_name']
            gst_number = i['gst_number']
            user_id = i['user_id']
            legal_name_of_business = i['legal_name_of_business']
            pan_number = i['pan_number']
            date_of_join = i['date_of_join']
            state = i['state']
            if 'profile_pic' not in i.keys():
                profile_pic = ''
            else:
                profile_pic = i['profile_pic']
            if 'contact_person_name' not in i.keys():
                contact_person_name = ''
            else:
                contact_person_name = i['contact_person_name']
            try:
                u_address = i['user_address']
                for j in u_address:
                    d_address = j['default_address']
                    try:
                        if d_address == True:
                            address_id = j['address_id']
                            building_number = j['building_number']
                            address = j['address']
                            landmark = j['landmark']
                            latitude = j['latitude']
                            longitude = j['longitude']
                            output.append({'user_id':user_id, 'signin_type': signin_type, 'first_name':first_name,
                                           'last_name':last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                           'password': password, 'company_name': company_name, 'gst_number': gst_number,
                                           'legal_name_of_business': legal_name_of_business, 'pan_number':pan_number,
                                           'date_of_join':date_of_join, 'state': state,
                                           'profile_pic': profile_pic, 'contact_person_name': contact_person_name,
                                           'default_address': [{'building_number': building_number,
                                                                'address_id': address_id,
                                                                'address': address,
                                                                'landmark': landmark,
                                                                'latitude': latitude,
                                                                'longitude': longitude}]
                                           })
                            return jsonify(
                            {'status': True, 'message': 'corporate user data get successfully', 'result': output})
                    except KeyError or ValueError:
                        pass
                        output.append({'user_id':user_id, 'signin_type': signin_type, 'first_name':first_name,
                                           'last_name':last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                           'password': password, 'company_name': company_name, 'gst_number': gst_number,
                                           'legal_name_of_business': legal_name_of_business, 'pan_number':pan_number,
                                           'date_of_join':date_of_join, 'state': state,
                                           'profile_pic': profile_pic, 'contact_person_name': contact_person_name,
                                       'default_address': []})
                        return jsonify(
                            {'status': True, 'message': 'corporate user data get successfully', 'result': output})
            except KeyError or ValueError:
                pass
            output.append({'user_id':user_id, 'signin_type': signin_type, 'first_name':first_name,
                           'last_name':last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                           'password': password, 'company_name': company_name, 'gst_number': gst_number,
                           'legal_name_of_business': legal_name_of_business, 'pan_number':pan_number,
                           'date_of_join':date_of_join, 'state': state,
                           'profile_pic': profile_pic, 'contact_person_name': contact_person_name,
                           'default_address': []})
            return jsonify({'status': True, 'message': 'corporate user data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})


#----------------------------------------------- Get Profile Individual -----------------------------------------------
@app.route('/owo/get_profile_individual/<user_id>', methods=['GET'])
def get_individual_user_by_id(user_id):
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    for i in db.find():
        u_id = i['user_id']
        if int(u_id) == int(user_id):
            user_id = i['user_id']
            signin_type = i['signin_type']
            first_name = i['first_name']
            last_name = i['last_name']
            mobile_number = i['mobile_number']
            email_id = i['email_id']
            password = i['password']
            date_of_join = i['date_of_join']
            if 'profile_pic' not in i.keys():
                profile_pic = ''
            else:
                profile_pic = i['profile_pic']
            try:
                u_add = i['user_address']
                for j in u_add:
                    d_address = j['default_address']
                    try:
                        if d_address == True:
                            address_id = j['address_id']
                            building_number = j['building_number']
                            address = j['address']
                            landmark = j['landmark']
                            latitude = j['latitude']
                            longitude = j['longitude']
                            output.append({'user_id': user_id, 'signin_type': signin_type, 'first_name': first_name,
                                           'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                           'password': password, 'date_of_join': date_of_join,
                                           'profile_pic': profile_pic,
                                           'default_address': [{'building_number': building_number,
                                                                'address_id': address_id,
                                                                'address': address,
                                                                'landmark': landmark,
                                                                'latitude': latitude,
                                                                'longitude': longitude}]})
                            return jsonify({'status': True, 'message': 'individual user data get successfully',
                                            'result': output})

                    except KeyError or ValueError:
                        pass
                        output.append({'user_id': user_id, 'signin_type': signin_type, 'first_name': first_name,
                                       'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                       'password': password, 'date_of_join': date_of_join,
                                       'profile_pic': profile_pic, 'default_address': []})
                        return jsonify({'status': True, 'message': 'individual user data get successfully',
                                        'result': output})
            except KeyError or ValueError:
                pass
            output.append({'user_id': user_id, 'signin_type': signin_type, 'first_name': first_name,
                           'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                           'password': password, 'date_of_join': date_of_join,
                           'profile_pic': profile_pic, 'default_address': []})
            return jsonify({'status': True, 'message': 'individual user data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'user not found', 'result': output})


#-------------------------------------------- Add cash wallet ----------------------------------------------------------
@app.route('/owo/add_cash_wallet', methods=['POST'])
@jwt_required
def add_cash_wallet():
    try:
        data = mongo.db.OWO
        db = data.owo_users_wallet
        wallet_id = request.json['wallet_id']
        transaction_id = request.json['transaction_id']
        payment_type = request.json['payment_type']
        transaction_type = request.json['transaction_type']
        amount = request.json['amount']
        status = request.json['status']
        order_id = transaction_type[:5].upper() + str(random.randint(1000, 9999))
        transaction_time_stamp = datetime.datetime.now()
        recent_transactions = []
        output=[]
        for i in db.find():
            if int(wallet_id) == int(i['wallet_id']) and status == "success":
                current_balance = i['current_balance']
                current_balance += amount
                try:
                    sub_closing_amount = i['subscription_amount']
                except KeyError or ValueError:
                    sub_closing_amount = 0
                recent_transactions.append({'amount': amount, 'transaction_id': transaction_id,
                                            'payment_type': payment_type,
                                            'transaction_type': transaction_type,
                                            'transaction_date': transaction_time_stamp})
                output.append({'wallet_id': wallet_id, 'amount': amount,
                               'transaction_id': transaction_id,'payment_type': payment_type,
                               'transaction_type': transaction_type,
                               'transaction_date': transaction_time_stamp})
                db.update_many({'wallet_id': wallet_id},
                               {'$set': {'current_balance': current_balance},
                                '$push': {'recent_transactions':
                                              {'amount': amount,
                                               'payment_type':payment_type,
                                               'transaction_id':transaction_id,
                                               'transaction_type':transaction_type,
                                               'transaction_date': transaction_time_stamp,
                                               'order_id':order_id,
                                               'status':status,
                                               'current_balance': i['current_balance'] - int(sub_closing_amount),
                                               'closing_balance':current_balance - int(sub_closing_amount)}}})
                AddingMoneyToWalletSMS(wallet_id, amount)
                AddingMoneyToWalletEmail(wallet_id, amount)
                AddingMoneyToWallet(wallet_id, amount)
                return jsonify({'status': 'success', 'result': output, 'message': 'Amount updated successfully'})
    except Exception as e:
        return jsonify({'status':'fail','result':str(e)})


#------------------------------------------------ User_balance ---------------------------------------------------------
@app.route('/owo/show_user_balance', methods=['POST'])
def show_user_balance():
    db = mongo.db.OWO
    user_wallet = db.owo_users_wallet
    wallet_id = request.json['wallet_id']
    try:
        for u in user_wallet.find({'wallet_id':wallet_id}):
                current_balance = u['current_balance']
                try:
                   subscription_amount = u['subscription_amount']
                except KeyError or ValueError:
                    subscription_amount = 0
                usable_balance = current_balance - subscription_amount
                return jsonify({'status': 'success', 'result': current_balance, 'message': 'current balance displayed','usable_balance':usable_balance,'subscription_amount':subscription_amount})
    except Exception as e:
        return jsonify({'status': 'fail', 'result': [], 'message': str(e)})


#------------------------------------------------ Recent transactions --------------------------------------------------
@app.route('/owo/user_recent_transactions', methods=['POST'])
@jwt_required
def user_recent_transactions():
    db = mongo.db.OWO
    user_wallet = db.owo_users_wallet
    wallet_id = request.json['wallet_id']
    offset = request.json['offset']
    limit = 10

    try:
        user_data = user_wallet.find_one({'wallet_id': wallet_id})
        if user_data is not None:
            recent_transactions = user_data['recent_transactions']
            user_transactions = sorted(recent_transactions, key=lambda i: i['transaction_date'], reverse=True)
            next_offset = str(offset) + str(limit)
            total_rec = len(user_transactions)
            if total_rec < int(limit) or int(next_offset) >= total_rec:
                next_offset = -1
                end = total_rec
            else:
                next_offset = next_offset
                end = next_offset
            result_data = user_transactions[:int(limit)]
            return jsonify({"next_offset": next_offset, 'status': 'success', 'result': result_data,
                            'message': 'recent 10 transactions displayed successfully'})
        else:
            return jsonify({"next_offset": -1, 'status': 'success', 'result': [], 'message': 'there are no such recent transactions'})
    except KeyError or ValueError:
        recent_transactions = []
        return jsonify({'status':"success",'result':[],'message':"there are no recent transactions"})


#-------------------------------------------- Pay from wallet ----------------------------------------------------------
@app.route('/owo/pay_from_wallet',methods=['POST'])
@jwt_required
def pay_from_wallet():
    db = mongo.db.OWO
    user_wallet = db.owo_users_wallet
    wallet_id = request.json['wallet_id']
    amount = request.json['amount']
    transaction_id = request.json['transaction_id']
    transaction_type = request.json['transaction_type']
    status = request.json['status']
    payment_type = request.json['payment_type']
    ts = calendar.timegm(time.gmtime())
    order_id = transaction_type[:5].upper()+ str(ts)
    result=[]
    user_balance = int()
    try:
        if user_wallet.find({'wallet_id': wallet_id}) is not None:
            for u in user_wallet.find({'wallet_id':wallet_id}):
                total_amount = u['current_balance'] - u['subscription_amount']
                print(total_amount)
                r_balance = amount-total_amount
                print(r_balance)
                if total_amount > amount and u['current_balance']>amount:
                    try:
                        sub_closing_amount = u['subscription_amount']
                    except KeyError or ValueError:
                        sub_closing_amount = 0
                    user_balance = u['current_balance']
                    user_balance = user_balance-amount
                    closing_balance = user_balance
                    message='Rs. %d deducted from your account'%amount
                    user_wallet.update({'wallet_id': wallet_id},
                                       {'$set':{'current_balance': user_balance},
                                        '$push':{'recent_transactions':
                                                {'amount':amount,
                                                 'payment_type':payment_type,
                                                 'transaction_id':transaction_id,
                                                 'transaction_type':transaction_type,
                                                 'order_id':order_id,
                                                 'current_balance': u['current_balance'] - int(sub_closing_amount),
                                                 'closing_balance':closing_balance - int(sub_closing_amount),
                                                 'status':status,
                                                 'transaction_date':datetime.datetime.now()}}})
                    result= 'Remaining balance in your wallet is %d'%user_balance
                    PaymentSuccess(wallet_id, amount)
                    PaymentSuccessEmail(wallet_id, amount)
                    PaymentSuccessSMS(wallet_id, amount)
                    return jsonify({'status':'success','result':result,'message':message})
                if  u['current_balance'] == 0:
                    PaymentFailure(wallet_id)
                    PaymentFailureEmail(wallet_id)
                    PaymentFailureSMS(wallet_id)
                    return jsonify({'status': 'fail', 'result':" ", 'message': 'You wallet is empty. Please add cash to proceed'})
                if int(u['current_balance'])>int(0) and int(u['current_balance'])<amount and amount>u['subscription_amount']:
                        bal_to_add= amount-user_balance
                        print(bal_to_add)
                        message= 'Please add Rs. %d to continue the transaction'%r_balance
                        PaymentFailure(wallet_id)
                        PaymentFailureEmail(wallet_id)
                        PaymentFailureSMS(wallet_id)
                        return jsonify({'status':'fail','result':" ",'message':message})
            else:
                return jsonify({'status':'fail','result':" ",'message':"please add Rs. %d to continue the transaction as we cannot deduct the amount from the subscription_amount "%amount})
        else:
            return jsonify({'status':'fail','result':" ",'message':'Process failed. Please try again'})
    except Exception as e:
        return jsonify({'status':'fail','result':str(e),'message':'fail'})


#------------------------------------------------- App Get FAQ --------------------------------------------------------
@app.route('/owo/app_get_faq', methods=['GET'])
def appGetFAQ():
    data = mongo.db.OWO
    db = data.FAQ_management
    output = []
    try:
        question_category = request.json['question_category']
        for i in db.find():
            category = i['question_category']
            if str(question_category) == str(category):
                output.append({'question_title': i['question_title'], 'question_description': i['question_description']})
        return jsonify({'status': True, 'message': 'question data get successfully', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e), 'result': output})


 #----------------------------------------------- Get Page Contant By Page Title --------------------------------------
@app.route('/owo/get_page_contant/<page_title>', methods=['GET'])
def getPageContantById(page_title):
    data = mongo.db.OWO
    db = data.page_contant_management
    output = []
    for i in db.find():
        title = i['page_title']
        if str(title) == str(page_title):
            output.append({'id': i['id'], 'page_title': i['page_title'], 'file_path': i['file_path']})
            return jsonify({'status': True, 'message': 'file data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'invalid page title', 'result': output})


# ------------------------------------------ shoppingcart management test ----------------------------------------------
@app.route('/owo/checking_shopping_cart', methods=['POST'])
@jwt_required
def checkingshoppingcart():
    data = mongo.db.OWO
    db_sc = data.shoppingcart
    db_r = data.rating
    product_rating = 0
    product_no_of_ratings = 0
    output = []
    customer_id = request.json['customer_id']
    customer_type = request.json['customer_type']
    for i in db_sc.find():
        u_id = i['customer_id']
        u_type = i['customer_type']
        ord_type = i['order_type']
        product = i['products']
        if int(u_id) == int(customer_id) and str(customer_type) == str(u_type):
            for j in product:
                p_id = j['product_id']
                for k in db_r.find():
                    id = k['product_id']
                    r_history = k['rating_history']
                    if str(id) == str(p_id):
                        try:
                            user_count = len(r_history)
                            product_rating = k['current_rating']
                            product_no_of_ratings = user_count
                        except KeyError or ValueError:
                            product_rating = 0
                            product_no_of_ratings = 0
                output.append({'product_id': j['product_id'],
                               'product_quantity': j['product_quantity'], 'purchase_price': j['purchase_price'],
                               'unit_price': j['unit_price'], 'package_type': j['package_type'],
                               'product_name': j['product_name'],
                               'save_price': j['save_price'], 'product_image': j['product_image'],
                               'company_name': j['company_name'], 'gst': j['gst'],
                               'brand_name': j['brand_name'], 'product_rating': product_rating,
                               'product_no_of_ratings': product_no_of_ratings})
            return jsonify({'status': True, 'message': "user cart is already exist",
                            'customer_id': customer_id, 'customer_type': customer_type,
                            'order_type': i['order_type'], 'cart_id': i['cart_id'], 'result': output})
    return jsonify({'status': False, 'message': 'cart is empty', 'result': output})


#--------------------------------------------- Add shopping cart -------------------------------------------------------
# @app.route('/owo/add_shopping_cart', methods=['POST'])
# @jwt_required
# def addshoppingcart():
#     data = mongo.db.OWO
#     db_cp = data.corporate_users
#     db_in = data.individual_users
#     db_sc = data.shoppingcart
#     db_p = data.products
#     output = []
#     customer_id = request.json['customer_id']
#     customer_type = request.json['customer_type']
#     order_type = request.json['order_type']
#     product_id = request.json['product_id']
#     product_quantity = request.json['product_quantity']
#     cart_added_date = strftime("%d/%m/%Y %H:%M:%S")
#     cart_id_list = [i['cart_id'] for i in db_sc.find()]
#     if len(cart_id_list) is 0:
#         cart_id = 1
#     else:
#         cart_id = int(cart_id_list[-1]) + 1
#     if str(customer_type) == "corporate":
#         for c in db_cp.find():
#             mb_no = c['mobile_number']
#             email = c['email_id']
#             for i in db_sc.find():
#                 cust_id = i['customer_id']
#                 c_type = i['customer_type']
#                 crt_id = i['cart_id']
#                 ord_type = i['order_type']
#                 products = i['products']
#                 if int(cust_id) == int(customer_id) and str(c_type) == str(customer_type):
#                     if str(ord_type) == str(order_type):
#                         for j in products:
#                             try:
#                                 p_id = j['product_id']
#                                 plant_name = j['plant_name']
#                             except KeyError or ValueError:
#                                 p_id = ''
#                                 plant_name = ''
#                             if str(product_id) == str(p_id):
#                                 output.append({'customer_id': cust_id, 'cart_id': crt_id,
#                                                'customer_type': c_type, 'email_id': i['email_id'],
#                                                'mobile_number': i['mobile_number'],
#                                                'products': [
#                                                    {"product_id": product_id, 'product_name': j['product_name'], 'product_quantity': product_quantity,
#                                                     'purchase_price': j['purchase_price'], 'return_policy': j['return_policy'],
#                                                     'package_type': j['package_type'], 'save_price': j['save_price'], 'discount_in_percentage': j['discount_in_percentage'],
#                                                     'product_image': j['product_image'], 'company_name': j['company_name'], 'gst': j['gst'],
#                                                     'brand_name': j['brand_name'], 'plant_name': plant_name, 'plant_id': j['plant_id'],
#                                                     'company_id': j['company_id'],'brand_id': j['brand_id']}],
#                                                'order_type': order_type, 'cart_added_date': cart_added_date})
#                                 return jsonify({'status': False, 'message': "product is already added to user", 'result': output})
#                         for j in db_p.find():
#                             prd_id = j['product_id']
#                             p_type = j['package_type']
#                             cmp_name = j['company_name']
#                             brd_name = j['brand_name']
#                             try:
#                                 p_img = j['product_image']
#                             except KeyError or ValueError:
#                                 p_img = []
#                             for k in p_type:
#                                 purchase_price = k['purchase_price']
#                                 unit_price = k['mrp']
#                                 save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
#                                 if str(prd_id) == str(product_id):
#                                     pck_type = k['package_type']
#                                     img = j['product_image']
#                                     db_sc.update_many(
#                                         {'customer_id': int(cust_id), 'customer_type': str(c_type)},
#                                         {'$push':
#                                              {'products':
#                                                   {"product_id": product_id, 'product_quantity': product_quantity,
#                                                    'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                    'package_type': pck_type, 'save_price': save_price, 'plant_id': j['plant_id'], 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
#                                                    'product_image': img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
#                                                    'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'], 'gst': k['gst']
#                                                    }
#                                               }
#                                          }
#                                         )
#                                     output.append({'customer_id': cust_id, 'cart_id': crt_id,
#                                                    'customer_type': c_type, 'email_id': i['email_id'],
#                                                    'mobile_number': i['mobile_number'],
#                                                    'products': [
#                                                        {"product_id": product_id, 'product_quantity': product_quantity,
#                                                         'purchase_price': purchase_price, 'unit_price': unit_price, 'plant_id': j['plant_id'],
#                                                         'package_type': k['package_type'], 'product_name': j['product_name'], 'gst': k['gst'],
#                                                         'save_price': int(save_price), 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
#                                                         'product_image': p_img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
#                                                         'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'],}],
#                                                    'order_type': order_type, 'cart_added_date': cart_added_date})
#                                     return jsonify({'status': True, 'message': "updated cart success", 'result': output})
#                     elif str(ord_type) != str(order_type):
#                         for j in db_p.find():
#                             prd_id = j['product_id']
#                             p_type = j['package_type']
#                             cmp_name = j['company_name']
#                             brd_name = j['brand_name']
#                             try:
#                                 p_img = j['product_image']
#                             except KeyError or ValueError:
#                                 p_img = []
#                             for k in p_type:
#                                 purchase_price = k['purchase_price']
#                                 unit_price = k['mrp']
#                                 save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
#                                 if str(prd_id) == str(product_id):
#                                     db_sc.remove({'customer_id': int(cust_id), 'customer_type': str(c_type)})
#                                     db_sc.insert_one({'customer_id': cust_id, 'cart_id': cart_id,
#                                                       'customer_type': c_type, 'email_id': i['email_id'],
#                                                       'mobile_number': i['mobile_number'],
#                                                       'products':
#                                                           [{"product_id": product_id, 'product_quantity': product_quantity,
#                                                             'purchase_price': purchase_price, 'unit_price': unit_price, 'plant_id': j['plant_id'],
#                                                             'package_type': k['package_type'], 'product_name': j['product_name'], 'gst': k['gst'],
#                                                             'save_price': int(save_price), 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
#                                                             'product_image': p_img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
#                                                             'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id']
#                                                             }],
#                                                       'order_type': order_type, 'cart_added_date': cart_added_date
#                                                       })
#                                     output.append({'customer_id': cust_id, 'cart_id': cart_id,
#                                                    'customer_type': c_type, 'email_id': i['email_id'],
#                                                    'mobile_number': i['mobile_number'],
#                                                    'products': [{"product_id": product_id, 'product_quantity': product_quantity, 'return_policy': k['return_policy'],
#                                                                  'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                                  'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
#                                                                  'product_image': p_img, 'company_name': cmp_name, 'plant_name': j['plant_name'],
#                                                                  'plant_id': j['plant_id'], 'gst': k['gst'],
#                                                                  'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id']}],
#                                                    'order_type': order_type, 'cart_added_date': cart_added_date})
#                                     return jsonify({'status': True, 'message': "updated cart_type success", 'result': output})
#
#             if int(customer_id) == int(c['user_id']) and str(customer_type) == str(c['signin_type']):
#                 print(cart_id)
#                 for j in db_p.find():
#                     prd_id = j['product_id']
#                     p_type = j['package_type']
#                     cmp_name = j['company_name']
#                     brd_name = j['brand_name']
#                     try:
#                         p_img = j['product_image']
#                     except KeyError or ValueError:
#                         p_img = []
#                     for k in p_type:
#                         purchase_price = k['purchase_price']
#                         unit_price = k['mrp']
#                         save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
#                         if str(prd_id) == str(product_id):
#                             db_sc.insert_one({'customer_id': customer_id, 'cart_id': cart_id,
#                                               'customer_type': customer_type, 'email_id': email,
#                                               'mobile_number': mb_no,
#                                               'products':
#                                                   [{"product_id": product_id, 'product_quantity': product_quantity, 'return_policy': k['return_policy'],
#                                                     'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                     'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
#                                                     'product_image': p_img, 'company_name': cmp_name, 'plant_name': j['plant_name'],
#                                                     'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'],
#                                                     'plant_id': j['plant_id'], 'gst': k['gst']
#                                                     }],
#                                               'order_type': order_type, 'cart_added_date': cart_added_date
#                                               })
#                             output.append({'customer_id': customer_id, 'cart_id': cart_id,
#                                            'customer_type': customer_type, 'email_id': c['email_id'],
#                                            'mobile_number': c['mobile_number'],
#                                            'products': [{"product_id": product_id, 'product_quantity': product_quantity,
#                                                          'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                          'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
#                                                          'product_image': p_img, 'company_name': cmp_name, 'brand_name': brd_name, 'return_policy': k['return_policy'],
#                                                          'company_id': j['company_id'],'brand_id': j['brand_id'], 'plant_name': j['plant_name'],
#                                                          'plant_id': j['plant_id'], 'gst': k['gst']
#                                                          }],
#                                            'order_type': order_type, 'cart_added_date': cart_added_date})
#                             return jsonify({'status': True, 'message': "cart added to user", 'result': output})
#
#     if str(customer_type) == "individual":
#         for n in db_in.find():
#             mb_no = n['mobile_number']
#             email = n['email_id']
#             for i in db_sc.find():
#                 cust_id = i['customer_id']
#                 c_type = i['customer_type']
#                 crt_id = i['cart_id']
#                 ord_type = i['order_type']
#                 products = i['products']
#                 if int(cust_id) == int(customer_id) and str(c_type) == str(customer_type):
#                     if str(ord_type) == str(order_type):
#                         for j in products:
#                             try:
#                                 p_id = j['product_id']
#                                 plant_name = j['plant_name']
#                                 plant_id = j['plant_id']
#                                 # products = j['products']
#                             except KeyError or ValueError:
#                                 p_id = ''
#                                 plant_name = ''
#                             if str(product_id) == str(p_id):
#                                 output.append({'customer_id': cust_id, 'cart_id': crt_id,
#                                                'customer_type': c_type, 'email_id': i['email_id'],
#                                                'mobile_number': i['mobile_number'],
#                                                'products': [
#                                                    {"product_id": product_id, 'product_name': j['product_name'], 'product_quantity': product_quantity,
#                                                     'purchase_price': j['purchase_price'], 'return_policy': j['return_policy'],
#                                                     'package_type': j['package_type'], 'save_price': j['save_price'], 'discount_in_percentage': j['discount_in_percentage'],
#                                                     'product_image': j['product_image'], 'company_name': j['company_name'], 'gst': j['gst'],
#                                                     'brand_name': j['brand_name'], 'plant_name': plant_name, 'plant_id': j['plant_id'],
#                                                     'company_id': j['company_id'],'brand_id': j['brand_id']}],
#                                                'order_type': order_type, 'cart_added_date': cart_added_date})
#                                 return jsonify({'status': False, 'message': "product is already added to user", 'result': output})
#                         for j in db_p.find():
#                             prd_id = j['product_id']
#                             p_type = j['package_type']
#                             cmp_name = j['company_name']
#                             brd_name = j['brand_name']
#                             try:
#                                 p_img = j['product_image']
#                             except KeyError or ValueError:
#                                 p_img = []
#                             for k in p_type:
#                                 purchase_price = k['purchase_price']
#                                 unit_price = k['mrp']
#                                 save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
#                                 if str(prd_id) == str(product_id):
#                                     # p_price = j['purchase_price']
#                                     # u_price = j['unit_price']
#                                     pck_type = k['package_type']
#                                     # s_price = j['save_price']
#                                     img = j['product_image']
#                                     db_sc.update_many(
#                                         {'customer_id': int(cust_id), 'customer_type': str(c_type)},
#                                         {'$push':
#                                              {'products':
#                                                   {"product_id": product_id, 'product_quantity': product_quantity,
#                                                    'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                    'package_type': pck_type, 'save_price': save_price, 'plant_id': j['plant_id'], 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
#                                                    'product_image': img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
#                                                    'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'], 'gst': k['gst']
#                                                    }
#                                               }
#                                          }
#                                         )
#                                     output.append({'customer_id': cust_id, 'cart_id': crt_id,
#                                                    'customer_type': c_type, 'email_id': i['email_id'],
#                                                    'mobile_number': i['mobile_number'],
#                                                    'products': [
#                                                        {"product_id": product_id, 'product_quantity': product_quantity,
#                                                         'purchase_price': purchase_price, 'unit_price': unit_price, 'plant_id': j['plant_id'],
#                                                         'package_type': k['package_type'], 'product_name': j['product_name'], 'gst': k['gst'],
#                                                         'save_price': int(save_price), 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
#                                                         'product_image': p_img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
#                                                         'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'],}],
#                                                    'order_type': order_type, 'cart_added_date': cart_added_date})
#                                     return jsonify({'status': True, 'message': "updated cart success", 'result': output})
#                     elif str(ord_type) != str(order_type):
#                         for j in db_p.find():
#                             prd_id = j['product_id']
#                             p_type = j['package_type']
#                             cmp_name = j['company_name']
#                             brd_name = j['brand_name']
#                             try:
#                                 p_img = j['product_image']
#                             except KeyError or ValueError:
#                                 p_img = []
#                             for k in p_type:
#                                 purchase_price = k['purchase_price']
#                                 unit_price = k['mrp']
#                                 save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
#                                 if str(prd_id) == str(product_id):
#                                     db_sc.remove({'customer_id': int(cust_id), 'customer_type': str(c_type)})
#                                     db_sc.insert_one({'customer_id': cust_id, 'cart_id': cart_id,
#                                                       'customer_type': c_type, 'email_id': i['email_id'],
#                                                       'mobile_number': i['mobile_number'],
#                                                       'products':
#                                                           [{"product_id": product_id, 'product_quantity': product_quantity,
#                                                             'purchase_price': purchase_price, 'unit_price': unit_price, 'plant_id': j['plant_id'],
#                                                             'package_type': k['package_type'], 'product_name': j['product_name'], 'gst': k['gst'],
#                                                             'save_price': int(save_price), 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
#                                                             'product_image': p_img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
#                                                             'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id']
#                                                             }],
#                                                       'order_type': order_type, 'cart_added_date': cart_added_date
#                                                       })
#                                     output.append({'customer_id': cust_id, 'cart_id': cart_id,
#                                                    'customer_type': c_type, 'email_id': i['email_id'],
#                                                    'mobile_number': i['mobile_number'],
#                                                    'products': [{"product_id": product_id, 'product_quantity': product_quantity, 'return_policy': k['return_policy'],
#                                                                  'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                                  'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
#                                                                  'product_image': p_img, 'company_name': cmp_name, 'plant_name': j['plant_name'],
#                                                                  'plant_id': j['plant_id'], 'gst': k['gst'],
#                                                                  'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id']}],
#                                                    'order_type': order_type, 'cart_added_date': cart_added_date})
#                                     return jsonify({'status': True, 'message': "updated cart_type success", 'result': output})
#
#             if int(customer_id) == int(n['user_id']) and str(customer_type) == str(n['signin_type']):
#                 # print(n['user_id'])
#                 # print(n['signin_type'])
#                 for j in db_p.find():
#                     prd_id = j['product_id']
#                     p_type = j['package_type']
#                     cmp_name = j['company_name']
#                     brd_name = j['brand_name']
#                     try:
#                         p_img = j['product_image']
#                     except KeyError or ValueError:
#                         p_img = []
#                     for k in p_type:
#                         purchase_price = k['purchase_price']
#                         unit_price = k['mrp']
#                         save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
#                         if str(prd_id) == str(product_id):
#                             db_sc.insert_one({'customer_id': customer_id, 'cart_id': cart_id,
#                                               'customer_type': customer_type, 'email_id': email,
#                                               'mobile_number': mb_no,
#                                               'products':
#                                                   [{"product_id": product_id, 'product_quantity': product_quantity, 'return_policy': k['return_policy'],
#                                                     'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                     'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
#                                                     'product_image': p_img, 'company_name': cmp_name, 'plant_name': j['plant_name'],
#                                                     'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'],
#                                                     'plant_id': j['plant_id'], 'gst': k['gst']
#                                                     }],
#                                               'order_type': order_type, 'cart_added_date': cart_added_date
#                                               })
#                             output.append({'customer_id': customer_id, 'cart_id': cart_id,
#                                            'customer_type': customer_type, 'email_id': email,
#                                            'mobile_number': mb_no,
#                                            'products': [{"product_id": product_id, 'product_quantity': product_quantity,
#                                                          'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
#                                                          'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
#                                                          'product_image': p_img, 'company_name': cmp_name, 'brand_name': brd_name, 'return_policy': k['return_policy'],
#                                                          'company_id': j['company_id'],'brand_id': j['brand_id'], 'plant_name': j['plant_name'],
#                                                          'plant_id': j['plant_id'], 'gst': k['gst']
#                                                          }],
#                                            'order_type': order_type, 'cart_added_date': cart_added_date})
#                             return jsonify({'status': True, 'message': "cart added to user", 'result': output})
#     return jsonify({'status': False, 'message': 'please enter a valid credentials', 'result': output})


@app.route('/owo/add_shopping_cart', methods=['POST'])
@jwt_required
def addshoppingcart():
    data = mongo.db.OWO
    db_cp = data.corporate_users
    db_in = data.individual_users
    db_sc = data.shoppingcart
    db_p = data.products
    output = []
    customer_id = request.json['customer_id']
    customer_type = request.json['customer_type']
    order_type = request.json['order_type']
    product_id = request.json['product_id']
    product_quantity = request.json['product_quantity']
    cart_added_date = strftime("%d/%m/%Y %H:%M:%S")
    cart_id_list = [i['cart_id'] for i in db_sc.find()]
    if len(cart_id_list) is 0:
        cart_id = 1
    else:
        cart_id = int(cart_id_list[-1]) + 1
    if str(customer_type) == "corporate":
        for c in db_cp.find():
            mb_no = c['mobile_number']
            email = c['email_id']
            for i in db_sc.find():
                # print(customer_id)
                cust_id = i['customer_id']
                c_type = i['customer_type']
                crt_id = i['cart_id']
                ord_type = i['order_type']
                products = i['products']
                if int(cust_id) == int(customer_id) and str(c_type) == str(customer_type):
                    if str(ord_type) == str(order_type):
                        for j in products:
                            try:
                                p_id = j['product_id']
                                plant_name = j['plant_name']
                            except KeyError or ValueError:
                                p_id = ''
                                plant_name = ''
                            if str(product_id) == str(p_id):
                                output.append({'customer_id': cust_id, 'cart_id': crt_id,
                                               'customer_type': c_type, 'email_id': i['email_id'],
                                               'mobile_number': i['mobile_number'],
                                               'products': [
                                                   {"product_id": product_id, 'product_name': j['product_name'], 'product_quantity': product_quantity,
                                                    'purchase_price': j['purchase_price'], 'return_policy': j['return_policy'],
                                                    'package_type': j['package_type'], 'save_price': j['save_price'], 'discount_in_percentage': j['discount_in_percentage'],
                                                    'product_image': j['product_image'], 'company_name': j['company_name'], 'gst': j['gst'],
                                                    'brand_name': j['brand_name'], 'plant_name': plant_name, 'plant_id': j['plant_id'],
                                                    'company_id': j['company_id'], 'brand_id': j['brand_id']}],
                                               'order_type': order_type, 'cart_added_date': cart_added_date})
                                return jsonify({'status': False, 'message': "product is already added to user", 'result': output})
                        for l in db_p.find():
                            prd_id = l['product_id']
                            p_type = l['package_type']
                            cmp_name = l['company_name']
                            brd_name = l['brand_name']
                            try:
                                p_img = l['product_image']
                            except KeyError or ValueError:
                                p_img = []
                            for k in p_type:
                                purchase_price = k['purchase_price']
                                unit_price = k['mrp']
                                old_unit_price = k['unit_price']
                                save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
                                if str(prd_id) == str(product_id):
                                    pck_type = k['package_type']
                                    img = l['product_image']
                                    db_sc.update_many(
                                        {'customer_id': int(cust_id), 'customer_type': str(c_type)},
                                        {'$push':
                                             {'products':
                                                  {"product_id": product_id, 'product_quantity': product_quantity,
                                                   'purchase_price': purchase_price, 'unit_price': unit_price,
                                                   'product_name': l['product_name'], 'old_old_unit_price': old_unit_price,
                                                   'package_type': pck_type, 'save_price': save_price,
                                                   'plant_id': l['plant_id'], 'plant_name': l['plant_name'],
                                                   'return_policy': k['return_policy'],
                                                   'product_image': img, 'company_name': cmp_name,
                                                   'discount_in_percentage': k['discount_in_percentage'],
                                                   'brand_name': brd_name, 'company_id': l['company_id'],
                                                   'brand_id': l['brand_id'], 'gst': k['gst']
                                                   }
                                              }
                                         }
                                        )
                                    output.append({'customer_id': cust_id, 'cart_id': crt_id,
                                                   'customer_type': c_type, 'email_id': i['email_id'],
                                                   'mobile_number': i['mobile_number'],
                                                   'products': [
                                                       {"product_id": product_id, 'product_quantity': product_quantity,
                                                        'purchase_price': purchase_price, 'unit_price': unit_price, 'plant_id': j['plant_id'],
                                                        'package_type': k['package_type'], 'product_name': j['product_name'], 'gst': k['gst'],
                                                        'save_price': int(save_price), 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
                                                        'product_image': p_img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
                                                        'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'],}],
                                                   'order_type': order_type, 'cart_added_date': cart_added_date})
                                    return jsonify({'status': True, 'message': "updated cart success", 'result': output})
                    elif str(ord_type) != str(order_type):
                        for j in db_p.find():
                            prd_id = j['product_id']
                            p_type = j['package_type']
                            cmp_name = j['company_name']
                            brd_name = j['brand_name']
                            try:
                                p_img = j['product_image']
                            except KeyError or ValueError:
                                p_img = []
                            for k in p_type:
                                purchase_price = k['purchase_price']
                                unit_price = k['mrp']
                                old_unit_price = k['unit_price']
                                save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
                                if str(prd_id) == str(product_id):
                                    db_sc.remove({'customer_id': int(cust_id), 'customer_type': str(c_type)})
                                    db_sc.insert_one({'customer_id': cust_id, 'cart_id': cart_id,
                                                      'customer_type': c_type, 'email_id': i['email_id'],
                                                      'mobile_number': i['mobile_number'],
                                                      'products':
                                                          [{"product_id": product_id, 'product_quantity': product_quantity,
                                                            'purchase_price': purchase_price, 'unit_price': unit_price,
                                                            'plant_id': j['plant_id'], 'old_unit_price': old_unit_price,
                                                            'package_type': k['package_type'],
                                                            'product_name': j['product_name'], 'gst': k['gst'],
                                                            'save_price': int(save_price), 'plant_name': j['plant_name'],
                                                            'return_policy': k['return_policy'],
                                                            'product_image': p_img, 'company_name': cmp_name,
                                                            'discount_in_percentage': k['discount_in_percentage'],
                                                            'brand_name': brd_name, 'company_id': j['company_id'],
                                                            'brand_id': j['brand_id']
                                                            }],
                                                      'order_type': order_type, 'cart_added_date': cart_added_date
                                                      })
                                    output.append({'customer_id': cust_id, 'cart_id': cart_id,
                                                   'customer_type': c_type, 'email_id': i['email_id'],
                                                   'mobile_number': i['mobile_number'],
                                                   'products': [{"product_id": product_id, 'product_quantity': product_quantity, 'return_policy': k['return_policy'],
                                                                 'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
                                                                 'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
                                                                 'product_image': p_img, 'company_name': cmp_name, 'plant_name': j['plant_name'],
                                                                 'plant_id': j['plant_id'], 'gst': k['gst'],
                                                                 'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id']}],
                                                   'order_type': order_type, 'cart_added_date': cart_added_date})
                                    return jsonify({'status': True, 'message': "updated cart_type success", 'result': output})
            if int(customer_id) == int(c['user_id']) and str(customer_type) == str(c['signin_type']):
                print(cart_id)
                for j in db_p.find():
                    prd_id = j['product_id']
                    p_type = j['package_type']
                    cmp_name = j['company_name']
                    brd_name = j['brand_name']
                    try:
                        p_img = j['product_image']
                    except KeyError or ValueError:
                        p_img = []
                    for k in p_type:
                        purchase_price = k['purchase_price']
                        unit_price = k['mrp']
                        old_unit_price = k['unit_price']
                        save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
                        if str(prd_id) == str(product_id):
                            db_sc.insert_one({'customer_id': customer_id, 'cart_id': cart_id,
                                              'customer_type': customer_type, 'email_id': email,
                                              'mobile_number': mb_no,
                                              'products':
                                                  [{"product_id": product_id, 'product_quantity': product_quantity,
                                                    'return_policy': k['return_policy'],
                                                    'purchase_price': purchase_price, 'unit_price': unit_price,
                                                    'product_name': j['product_name'], 'old_unit_price': old_unit_price,
                                                    'package_type': k['package_type'], 'save_price': int(save_price),
                                                    'discount_in_percentage': k['discount_in_percentage'],
                                                    'product_image': p_img, 'company_name': cmp_name,
                                                    'plant_name': j['plant_name'],
                                                    'brand_name': brd_name, 'company_id': j['company_id'],
                                                    'brand_id': j['brand_id'],
                                                    'plant_id': j['plant_id'], 'gst': k['gst']
                                                    }],
                                              'order_type': order_type, 'cart_added_date': cart_added_date
                                              })
                            output.append({'customer_id': customer_id, 'cart_id': cart_id,
                                           'customer_type': customer_type, 'email_id': c['email_id'],
                                           'mobile_number': c['mobile_number'],
                                           'products': [{"product_id": product_id, 'product_quantity': product_quantity,
                                                         'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
                                                         'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
                                                         'product_image': p_img, 'company_name': cmp_name, 'brand_name': brd_name, 'return_policy': k['return_policy'],
                                                         'company_id': j['company_id'],'brand_id': j['brand_id'], 'plant_name': j['plant_name'],
                                                         'plant_id': j['plant_id'], 'gst': k['gst']
                                                         }],
                                           'order_type': order_type, 'cart_added_date': cart_added_date})
                            return jsonify({'status': True, 'message': "cart added to user", 'result': output})
    if str(customer_type) == "individual":
        for n in db_in.find():
            mb_no = n['mobile_number']
            email = n['email_id']
            for i in db_sc.find():
                cust_id = i['customer_id']
                c_type = i['customer_type']
                crt_id = i['cart_id']
                ord_type = i['order_type']
                products = i['products']
                if int(cust_id) == int(customer_id) and str(c_type) == str(customer_type):
                    if str(ord_type) == str(order_type):
                        for j in products:
                            try:
                                p_id = j['product_id']
                                plant_name = j['plant_name']
                                plant_id = j['plant_id']
                            except KeyError or ValueError:
                                p_id = ''
                                plant_name = ''
                            if str(product_id) == str(p_id):
                                output.append({'customer_id': cust_id, 'cart_id': crt_id,
                                               'customer_type': c_type, 'email_id': i['email_id'],
                                               'mobile_number': i['mobile_number'],
                                               'products': [
                                                   {"product_id": product_id, 'product_name': j['product_name'],
                                                    'product_quantity': product_quantity,
                                                    'purchase_price': j['purchase_price'],
                                                    'return_policy': j['return_policy'],
                                                    'package_type': j['package_type'], 'save_price': j['save_price'],
                                                    'discount_in_percentage': j['discount_in_percentage'],
                                                    'product_image': j['product_image'], 'company_name': j['company_name'],
                                                    'gst': j['gst'],
                                                    'brand_name': j['brand_name'], 'plant_name': plant_name,
                                                    'plant_id': j['plant_id'],
                                                    'company_id': j['company_id'],'brand_id': j['brand_id']}],
                                               'order_type': order_type, 'cart_added_date': cart_added_date})
                                return jsonify({'status': False, 'message': "product is already added to user", 'result': output})
                        for l in db_p.find():
                            prd_id = l['product_id']
                            p_type = l['package_type']
                            cmp_name = l['company_name']
                            brd_name = l['brand_name']
                            try:
                                p_img = l['product_image']
                            except KeyError or ValueError:
                                p_img = []
                            for k in p_type:
                                purchase_price = k['purchase_price']
                                unit_price = k['mrp']
                                old_unit_price = k['unit_price']
                                save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
                                if str(prd_id) == str(product_id):
                                    pck_type = k['package_type']
                                    img = l['product_image']
                                    db_sc.update_many(
                                        {'customer_id': int(cust_id), 'customer_type': str(c_type)},
                                        {'$push':
                                             {'products':
                                                  {"product_id": product_id, 'product_quantity': product_quantity,
                                                   'purchase_price': purchase_price, 'unit_price': unit_price,
                                                   'product_name': l['product_name'], 'old_unit_price': old_unit_price,
                                                   'package_type': pck_type, 'save_price': save_price,
                                                   'plant_id': l['plant_id'], 'plant_name': l['plant_name'], 'return_policy': k['return_policy'],
                                                   'product_image': img, 'company_name': cmp_name,
                                                   'discount_in_percentage': k['discount_in_percentage'],
                                                   'brand_name': brd_name, 'company_id': l['company_id'],
                                                   'brand_id': l['brand_id'], 'gst': k['gst']
                                                   }
                                              }
                                         }
                                        )
                                    output.append({'customer_id': cust_id, 'cart_id': crt_id,
                                                   'customer_type': c_type, 'email_id': i['email_id'],
                                                   'mobile_number': i['mobile_number'],
                                                   'products': [
                                                       {"product_id": product_id, 'product_quantity': product_quantity,
                                                        'purchase_price': purchase_price, 'unit_price': unit_price, 'plant_id': j['plant_id'],
                                                        'package_type': k['package_type'], 'product_name': j['product_name'], 'gst': k['gst'],
                                                        'save_price': int(save_price), 'plant_name': j['plant_name'], 'return_policy': k['return_policy'],
                                                        'product_image': p_img, 'company_name': cmp_name, 'discount_in_percentage': k['discount_in_percentage'],
                                                        'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id'],}],
                                                   'order_type': order_type, 'cart_added_date': cart_added_date})
                                    return jsonify({'status': True, 'message': "updated cart success", 'result': output})
                    elif str(ord_type) != str(order_type):
                        for j in db_p.find():
                            prd_id = j['product_id']
                            p_type = j['package_type']
                            cmp_name = j['company_name']
                            brd_name = j['brand_name']
                            try:
                                p_img = j['product_image']
                            except KeyError or ValueError:
                                p_img = []
                            for k in p_type:
                                purchase_price = k['purchase_price']
                                unit_price = k['mrp']
                                old_unit_price = k['unit_price']
                                save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
                                if str(prd_id) == str(product_id):
                                    db_sc.remove({'customer_id': int(cust_id), 'customer_type': str(c_type)})
                                    db_sc.insert_one({'customer_id': cust_id, 'cart_id': cart_id,
                                                      'customer_type': c_type, 'email_id': i['email_id'],
                                                      'mobile_number': i['mobile_number'],
                                                      'products':
                                                          [{"product_id": product_id, 'product_quantity': product_quantity,
                                                            'purchase_price': purchase_price, 'unit_price': unit_price,
                                                            'plant_id': j['plant_id'], 'old_unit_price': old_unit_price,
                                                            'package_type': k['package_type'],
                                                            'product_name': j['product_name'], 'gst': k['gst'],
                                                            'save_price': int(save_price), 'plant_name': j['plant_name'],
                                                            'return_policy': k['return_policy'],
                                                            'product_image': p_img, 'company_name': cmp_name,
                                                            'discount_in_percentage': k['discount_in_percentage'],
                                                            'brand_name': brd_name, 'company_id': j['company_id'],
                                                            'brand_id': j['brand_id']
                                                            }],
                                                      'order_type': order_type, 'cart_added_date': cart_added_date
                                                      })
                                    output.append({'customer_id': cust_id, 'cart_id': cart_id,
                                                   'customer_type': c_type, 'email_id': i['email_id'],
                                                   'mobile_number': i['mobile_number'],
                                                   'products': [{"product_id": product_id, 'product_quantity': product_quantity, 'return_policy': k['return_policy'],
                                                                 'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
                                                                 'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
                                                                 'product_image': p_img, 'company_name': cmp_name, 'plant_name': j['plant_name'],
                                                                 'plant_id': j['plant_id'], 'gst': k['gst'],
                                                                 'brand_name': brd_name, 'company_id': j['company_id'],'brand_id': j['brand_id']}],
                                                   'order_type': order_type, 'cart_added_date': cart_added_date})
                                    return jsonify({'status': True, 'message': "updated cart_type success", 'result': output})
            if int(customer_id) == int(n['user_id']) and str(customer_type) == str(n['signin_type']):
                for j in db_p.find():
                    prd_id = j['product_id']
                    p_type = j['package_type']
                    cmp_name = j['company_name']
                    brd_name = j['brand_name']
                    try:
                        p_img = j['product_image']
                    except KeyError or ValueError:
                        p_img = []
                    for k in p_type:
                        purchase_price = k['purchase_price']
                        unit_price = k['mrp']
                        old_unit_price = k['unit_price']
                        save_price = abs((int(unit_price) - int(purchase_price)) * int(product_quantity))
                        if str(prd_id) == str(product_id):
                            db_sc.insert_one({'customer_id': customer_id, 'cart_id': cart_id,
                                              'customer_type': customer_type, 'email_id': email,
                                              'mobile_number': mb_no,
                                              'products':
                                                  [{"product_id": product_id, 'product_quantity': product_quantity,
                                                    'return_policy': k['return_policy'], 'old_unit_price': old_unit_price,
                                                    'purchase_price': purchase_price, 'unit_price': unit_price,
                                                    'product_name': j['product_name'],
                                                    'package_type': k['package_type'], 'save_price': int(save_price),
                                                    'discount_in_percentage': k['discount_in_percentage'],
                                                    'product_image': p_img, 'company_name': cmp_name,
                                                    'plant_name': j['plant_name'],
                                                    'brand_name': brd_name, 'company_id': j['company_id'],
                                                    'brand_id': j['brand_id'],
                                                    'plant_id': j['plant_id'], 'gst': k['gst']
                                                    }],
                                              'order_type': order_type, 'cart_added_date': cart_added_date
                                              })
                            output.append({'customer_id': customer_id, 'cart_id': cart_id,
                                           'customer_type': customer_type, 'email_id': email,
                                           'mobile_number': mb_no,
                                           'products': [{"product_id": product_id, 'product_quantity': product_quantity,
                                                         'purchase_price': purchase_price, 'unit_price': unit_price, 'product_name': j['product_name'],
                                                         'package_type': k['package_type'], 'save_price': int(save_price), 'discount_in_percentage': k['discount_in_percentage'],
                                                         'product_image': p_img, 'company_name': cmp_name, 'brand_name': brd_name, 'return_policy': k['return_policy'],
                                                         'company_id': j['company_id'],'brand_id': j['brand_id'], 'plant_name': j['plant_name'],
                                                         'plant_id': j['plant_id'], 'gst': k['gst']
                                                         }],
                                           'order_type': order_type, 'cart_added_date': cart_added_date})
                            return jsonify({'status': True, 'message': "cart added to user", 'result': output})
    return jsonify({'status': False, 'message': 'please enter a valid credentials', 'result': output})


#-------------------------------------------- Get user shopping cart ---------------------------------------------------
@app.route('/owo/get_user_shopping_cart', methods=['POST'])
@jwt_required
def getbyidshopingcart():
    data = mongo.db.OWO
    db_sc = data.shoppingcart
    db_r = data.rating
    product_rating = 0
    product_no_of_ratings = 0
    output = []
    customer_id = request.json['customer_id']
    customer_type = request.json['customer_type']
    for i in db_sc.find():
        c_id = i['customer_id']
        c_type = i['customer_type']
        cart_id = i['cart_id']
        prd = i['products']
        if int(c_id) == int(customer_id) and str(customer_type) == str(c_type):
            for j in prd:
                p_id = j['product_id']
                for k in db_r.find():
                    id = k['product_id']
                    r_history = k['rating_history']
                    if str(id) == str(p_id):
                        try:
                            user_count = len(r_history)
                            product_rating = k['current_rating']
                            product_no_of_ratings = user_count
                        except KeyError or ValueError:
                            product_rating = 0
                            product_no_of_ratings = 0

                output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
                               'product_quantity': j['product_quantity'], 'purchase_price': j['purchase_price'],
                               'unit_price': j['mrp'], 'package_type': j['package_type'],
                               'save_price': j['save_price'], 'product_image': j['product_image'],
                               'company_name': j['company_name'], 'plant_id': j['plant_id'], 'plant_name': j['plant_name'],
                               'brand_name': j['brand_name'], 'gst': j['gst'],
                               'product_rating': product_rating,
                               'product_no_of_ratings': product_no_of_ratings})
            return jsonify({'status': True, 'message': "user cart details get success",
                            'customer_id': customer_id, 'customer_type': customer_type,
                            'order_type': i['order_type'], 'cart_id': i['cart_id'], 'result': output})
    return jsonify({'status': False, 'message': "cart is empty", 'result': output})


#-------------------------------------------------- Product quantity edit ----------------------------------------------
@app.route('/owo/product_quantity_edit', methods=['POST'])
@jwt_required
def editproductquantity():
    data = mongo.db.OWO
    db_sc = data.shoppingcart
    output = []
    customer_id = request.json['customer_id']
    customer_type = request.json['customer_type']
    product_id = request.json['product_id']
    product_quantity = request.json['product_quantity']
    for i in db_sc.find():
        c_id = i['customer_id']
        c_type = i['customer_type']
        cart_id = i['cart_id']
        prd = i['products']
        for j in prd:
            p_id = j['product_id']
            purchase_price = j['purchase_price']
            unit_price = j['unit_price']
            save_price = abs(int(unit_price) - int(purchase_price)) * int(product_quantity)
            if int(customer_id) == int(c_id) and str(customer_type) == str(c_type):
                if str(p_id) == str(product_id):
                    db_sc.update_many({'customer_id': int(customer_id), 'customer_type': str(customer_type),
                                       'products.product_id': str(product_id)},
                                      {'$set': {'products.$.product_quantity': product_quantity,
                                                'products.$.save_price': save_price
                                                }
                                       })
                    output.append({'customer_id': customer_id, 'cart_id': cart_id,
                                   'customer_type': customer_type, 'email_id': i['email_id'],
                                   'mobile_number': i['mobile_number'],
                                   'products': [{"product_id": product_id, 'product_quantity': product_quantity,
                                                 'purchase_price': purchase_price, 'unit_price': unit_price,
                                                 'package_type': j['package_type'], 'product_name': j['product_name'],
                                                 'save_price': int(save_price),
                                                 'product_image':j['product_image'],
                                                 'company_name': j['company_name'],
                                                 'brand_name': j['brand_name']}],
                                   'order_type': i['order_type'], 'cart_added_date': i['cart_added_date']})
                    return jsonify({'status': True, 'message': "cart product_quantity updated success", 'result': output})
    return jsonify({'status': False, 'message': "please enter a valid product_id", 'result': output})


#--------------------------------------------- delete product from cart -------------------------------------------------
@app.route('/owo/delete_product_from_cart', methods=['POST'])
@jwt_required
def deleteproductfromcart():
    data = mongo.db.OWO
    db_sc = data.shoppingcart
    output = []
    customer_id = request.json['customer_id']
    customer_type = request.json['customer_type']
    product_id = request.json['product_id']
    # product_quantity = request.json['product_quantity']
    for i in db_sc.find():
        c_id = i['customer_id']
        c_type = i['customer_type']
        cart_id = i['cart_id']
        prd = i['products']
        count = len(prd)
        for j in prd:
            p_id = j['product_id']
            if int(customer_id) == int(c_id) and str(customer_type) == str(c_type):
                if str(p_id) == str(product_id):
                    db_sc.update_many({'customer_id': int(customer_id), 'customer_type': str(customer_type),
                                       'products.product_id': str(product_id)},
                                      {'$pull': {"products":
                                                     {'product_id': str(product_id)
                                                      }
                                                 }
                                       })
                    output.append({'customer_id': customer_id, 'cart_id': cart_id,
                                   'customer_type': customer_type, 'email_id': i['email_id'],
                                   'mobile_number': i['mobile_number'],
                                   "product_id": product_id, 'product_name': j['product_name'],
                                   'order_type': i['order_type'], 'cart_added_date': i['cart_added_date']})
                    if count == 1:
                        db_sc.remove({'cart_id': cart_id})
                    return jsonify({'status': True, 'message': "cart product_delete success", 'result': output})
    return jsonify({'status': False, 'message': "please enter a valid product_id or product is not exist in user cart", 'result': output})


#--------------------------------------------------- user cart list ----------------------------------------------------
# @app.route('/owo/user_cart_list', methods=['POST'])
# @jwt_required
# def usercartlist():
#     data = mongo.db.OWO
#     db_sc = data.shoppingcart
#     db_dc = data.delivery_charge_management
#     db_r = data.rating
#     output = []
#     product_rating = 0
#     product_no_of_ratings = 0
#     sub_total = int()
#     delivery_charge = int()
#     total_save_price = int()
#     gst = int()
#     customer_id = request.json['customer_id']
#     customer_type = request.json['customer_type']
#     cart_id = int()
#     for i in db_sc.find():
#         cart_id = i['cart_id']
#         u_id = i['customer_id']
#         u_type = i['customer_type']
#         ord_type = i['order_type']
#         product = i['products']
#         if int(u_id) == int(customer_id) and str(customer_type) == str(u_type):
#             for j in product:
#                 p_id = j['product_id']
#                 for k in db_r.find():
#                     id = k['product_id']
#                     r_history = k['rating_history']
#                     if str(id) == str(p_id):
#                         try:
#                             user_count = len(r_history)
#                             product_rating = k['current_rating']
#                             product_no_of_ratings = user_count
#                         except KeyError or ValueError:
#                             product_rating = 0
#                             product_no_of_ratings = 0
#                 purchase_price = int(j['purchase_price'])
#                 product_quantity = int(j['product_quantity'])
#                 total_save_price += j['save_price']
#                 gst += int(j['gst'])
#                 output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
#                                'product_quantity': j['product_quantity'], 'purchase_price': j['purchase_price'],
#                                'unit_price': j['unit_price'], 'package_type': j['package_type'],
#                                'save_price': j['save_price'], 'product_image': j['product_image'],
#                                'company_name': j['company_name'], 'gst': j['gst'],
#                                'brand_name': j['brand_name'], 'product_rating': product_rating,
#                                'product_no_of_ratings': product_no_of_ratings})
#                 sub_total += (purchase_price * product_quantity)
#             total = int(sub_total)
#             total_save_price = total_save_price
#             count = int()
#             for s in db_dc.find():
#                 d_type = s['delivery_type']
#                 if d_type == 'event-instant' and count == 0:
#                     if s['lower_range'] <= int(total):
#                         if int(total) <= s['upper_range']:
#                             d_charge = s['delivery_charge']
#                             delivery_charge = d_charge
#                             count = count + 1
#             db_sc.update_many({'cart_id': cart_id}, {'$set': {'delivery_charges': delivery_charge, 'total_gst': gst}})
#             return jsonify({'status': True, 'message': "user cart list data get success",
#                             'customer_id': customer_id, 'customer_type': customer_type, 'total_gst': gst,
#                             'order_type': i['order_type'], 'cart_id': i['cart_id'], 'sub_total': sub_total,
#                             'delivery_charge': delivery_charge, 'total_save_price': total_save_price, 'result': output})
#     return jsonify({'status': False, 'message': 'please enter valid credentials', 'result': output})


@app.route('/owo/user_cart_list', methods=['POST'])
@jwt_required
def usercartlist():
    data = mongo.db.OWO
    db_sc = data.shoppingcart
    db_dc = data.delivery_charge_management
    db_r = data.rating
    output = []
    product_rating = 0
    product_no_of_ratings = 0
    sub_total = int()
    delivery_charge = int()
    total_save_price = int()
    customer_id = request.json['customer_id']
    customer_type = request.json['customer_type']
    gst_amount = 0
    for i in db_sc.find():
        cart_id = i['cart_id']
        u_id = i['customer_id']
        u_type = i['customer_type']
        ord_type = i['order_type']
        product = i['products']
        if int(u_id) == int(customer_id) and str(customer_type) == str(u_type):
            for j in product:
                p_id = j['product_id']
                for k in db_r.find():
                    id = k['product_id']
                    r_history = k['rating_history']
                    if str(id) == str(p_id):
                        try:
                            user_count = len(r_history)
                            product_rating = k['current_rating']
                            product_no_of_ratings = user_count
                        except KeyError or ValueError:
                            product_rating = 0
                            product_no_of_ratings = 0
                purchase_price = int(j['purchase_price'])
                product_quantity = int(j['product_quantity'])
                unit_price = int(j['old_unit_price'])
                gst = int(j['gst'])
                mrp = int(j['unit_price'])
                total_save_price += j['save_price']
                gst_calc = int(mrp) - int(unit_price)
                gst_amount += gst_calc * product_quantity
                output.append({'product_id': j['product_id'], 'product_name': j['product_name'],
                               'product_quantity': j['product_quantity'], 'purchase_price': j['purchase_price'],
                               'unit_price': j['unit_price'], 'package_type': j['package_type'],
                               'save_price': j['save_price'], 'product_image': j['product_image'],
                               'company_name': j['company_name'], 'gst': gst_calc,
                               'brand_name': j['brand_name'], 'product_rating': product_rating,
                               'product_no_of_ratings': product_no_of_ratings})
                sub_total += (purchase_price * product_quantity)
            total = int(sub_total)
            total_save_price = total_save_price
            count = int()
            for s in db_dc.find():
                d_type = s['delivery_type']
                if d_type == 'event-instant' and count == 0:
                    if s['lower_range'] <= int(total):
                        if int(total) <= s['upper_range']:
                            d_charge = s['delivery_charge']
                            delivery_charge = d_charge
                            count = count + 1
            db_sc.update_many({'cart_id': cart_id}, {'$set': {'delivery_charges': delivery_charge, 'total_gst': gst_amount}})
            return jsonify({'status': True, 'message': "user cart list data get success",
                            'customer_id': customer_id, 'customer_type': customer_type, 'total_gst': gst_amount,
                            'order_type': i['order_type'], 'cart_id': i['cart_id'], 'sub_total': sub_total,
                            'delivery_charge': delivery_charge, 'total_save_price': total_save_price, 'result': output})
    return jsonify({'status': False, 'message': 'please enter valid credentials', 'result': output})

#--------------------------------------------- Slot management ---------------------------------------------------------
@app.route('/owo/get_available_slots/<day>', methods=['GET'])
def AppgetAvailableSlots(day):
    try:
        data = mongo.db.OWO
        db = data.slot
        output = []
        current_time = datetime.datetime.now()
        now_30 = current_time + datetime.timedelta(minutes=30)
        a = current_time.strftime("%H:%M")
        b = now_30.strftime("%H:%M")
        print(a)
        print(b)
        for i in db.find(sort=[('available_slot', pymongo.ASCENDING)]):
            print(current_time)
            st = i['slot_start_time']
            print(st)
            if str(st) > str(b):
                if i['active_slot'] == True:
                    if (i[day] == True):
                        output.append({'slot_id': i['slot_id'], 'active_slot': i['active_slot'], 'available_slot': i['available_slot']})
        return jsonify({'status': True, 'message': 'list of slots', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


#------------------------------------------------ Add money to subscription --------------------------------------------
# @app.route('/owo/add_money_subscription', methods=['POST'])
# # @jwt_required
# def add_subscription_wallet():
#     try:
#         data = mongo.db.OWO
#         db = data.owo_users_wallet
#         db1 = data.product_subscription_test
#         wallet_id = request.json['wallet_id']
#         transaction_id = request.json['transaction_id']
#         subscription_id = request.json['subscription_id']
#         payment_type = request.json['payment_type']
#         transaction_type = request.json['transaction_type']
#         amount = request.json['amount']
#         status = request.json['status']
#         delivery_address = request.json['delivery_address']
#         transaction_time_stamp = datetime.datetime.now()
#         order_id = transaction_type[:5].upper() + str(random.randint(1000, 9999))
#         recent_transactions = []
#         output=[]
#         for j in db1.find({'subscription_id':subscription_id}):
#              if status == "success":
#                  for i in db.find({'wallet_id': wallet_id}):
#                      if status == "success":
#                          print(wallet_id)
#                          print(i['wallet_id'])
#                          try:
#                             subscription_amount = i['subscription_amount']
#                          except KeyError or ValueError:
#                              subscription_amount = int()
#                              c_b = i['current_balance']
#                              db1.update_many({'subscription_id': subscription_id},
#                                              {'$set': {'products.$[].cart_status': "deactive"}})
#                              db1.update_many({'subscription_id': subscription_id}, {
#                                  '$set': {'payment_status': status, 'is_subscribed': True, 'order_id': order_id,
#                                           'transaction_id': transaction_id, 'delivery_address': delivery_address,
#                                           'subscription_status': "active", 'transaction_date': transaction_time_stamp}})
#                              db.update_many({'wallet_id': wallet_id}, {
#                                  '$set': {'current_balance': c_b, 'subscription_id': subscription_id,
#                                           'subscription_amount': amount}, '$push': {
#                                      'recent_transactions': {'amount': amount, 'payment_type': payment_type,
#                                                              'transaction_id': transaction_id,
#                                                              'transaction_type': transaction_type,
#                                                              'transaction_date': transaction_time_stamp,
#                                                              'order_id': order_id, 'status': status,
#                                                              'current_balance': c_b,
#                                                              'closing_balance': c_b - amount}}})
#
#                              output.append({'wallet_id': wallet_id, 'status': status, 'amount': amount,
#                                             'transaction_id': transaction_id, 'payment_type': payment_type,
#                                             'transaction_type': transaction_type,
#                                             'transaction_date': transaction_time_stamp, 'order_id': order_id,
#                                             'closing_balance': c_b})
#                              SubscriptionSuccess(wallet_id, order_id)
#                              SubscriptionSuccessEmail(wallet_id,order_id)
#                              SubscriptionSuccessSMS(wallet_id, order_id)
#                              return jsonify(
#                                  {'status': 'success', 'result': output, 'message': 'subscription amount successfully'})
#                          current_balance = i['current_balance']
#                          if amount < subscription_amount:
#                              remaining_balance = subscription_amount - amount
#                              db1.update_many({'subscription_id': subscription_id},
#                                              {'$set': {'products.$[].cart_status': "deactive"}})
#                              db1.update_many({'subscription_id': subscription_id}, {
#                                  '$set': {'payment_status': status, 'is_subscribed': True, 'order_id': order_id,
#                                           'transaction_id': transaction_id, 'subscription_status':"active",'delivery_address': delivery_address,'transaction_date':transaction_time_stamp}})
#                              db.update_many({'wallet_id': wallet_id}, {
#                                  '$set': {'current_balance': current_balance, 'subscription_id': subscription_id,
#                                           'subscription_amount': amount}, '$push': {
#                                      'recent_transactions': {'amount': remaining_balance, 'payment_type': "refund",
#                                                              'transaction_id': transaction_id,
#                                                              'transaction_type': "subscription_refund",
#                                                              'transaction_date': transaction_time_stamp,
#                                                              'order_id': order_id, 'status': status,
#                                                              'current_balance': current_balance,
#                                                              'closing_balance': current_balance - amount}}})
#                              db.update_many({'wallet_id': wallet_id}, {'$push': {
#                                      'recent_transactions': {'amount': amount, 'payment_type': "subscription",
#                                                              'transaction_id': transaction_id,
#                                                              'transaction_type': "subscription_modify",
#                                                              'transaction_date': transaction_time_stamp,
#                                                              'order_id': order_id, 'status': status,
#                                                              'current_balance': current_balance,
#                                                              'closing_balance': current_balance - amount}}})
#                              for subs in db1.find({'subscription_id': subscription_id}):
#                                  # old_subscription_plan.append({'user_id':subs['user_id'],'signin_type':subs['signin_type'],'buy_plan':subs['buy_plan'],'starting_date':subs['starting_date'],'plan_expiry_date':subs['plan_expiry_date'],'total_amount':subs['total_price'],'product_count':subs['product_count']})
#                                  db1.update_many({'subscription_id': subscription_id}, {'$push': {
#                                      'old_subscription_plan': {'user_id': subs['user_id'],
#                                                                'signin_type': subs['signin_type'],
#                                                                'buy_plan': subs['buy_plan'],
#                                                                'starting_date': subs['starting_date'],
#                                                                'plan_expiry_date': subs['plan_expiry_date'],
#                                                                'total_amount': subs['total_price'],
#                                                                'product_count': subs['product_count'],
#                                                                'products': subs['products']}}})
#
#                              output.append({'wallet_id': wallet_id, 'status': status, 'amount': remaining_balance,
#                                             'transaction_id': transaction_id, 'payment_type': "refund",
#                                             'transaction_type': "subscription_refund",
#                                             'transaction_date': transaction_time_stamp, 'order_id': order_id,
#                                             'closing_balance': current_balance})
#                              SubscriptionSuccess(wallet_id, order_id)
#                              SubscriptionSuccessEmail(wallet_id,order_id)
#                              SubscriptionSuccessSMS(wallet_id, order_id)
#                              return jsonify(
#                                  {'status': 'success', 'result': output, 'message': 'Amount refunded successfully'})
#                          elif amount > current_balance:
#                              return jsonify(
#                                  {'status': 'failed', 'result':[], 'message': 'please refill your wallet to place order'})
#                          else:
#                              db1.update_many({'subscription_id': subscription_id},
#                                              {'$set': {'products.$[].cart_status': "deactive"}})
#                              db1.update_many({'subscription_id': subscription_id}, {
#                                  '$set': {'payment_status': status, 'is_subscribed': True, 'order_id': order_id,
#                                           'transaction_id': transaction_id, 'delivery_address': delivery_address,'subscription_status':"active",'transaction_date':transaction_time_stamp}})
#                              db.update_many({'wallet_id': wallet_id}, {
#                                  '$set': {'current_balance': current_balance, 'subscription_id': subscription_id,
#                                           'subscription_amount': amount}, '$push': {
#                                      'recent_transactions': {'amount': amount, 'payment_type': payment_type,
#                                                              'transaction_id': transaction_id,
#                                                              'transaction_type': transaction_type,
#                                                              'transaction_date': transaction_time_stamp,
#                                                              'order_id': order_id, 'status': status,
#                                                              'current_balance': current_balance,
#                                                              'closing_balance': current_balance- amount}}})
#                              for subs in db1.find({'subscription_id': subscription_id}):
#                                  db1.update_many({'subscription_id': subscription_id}, {'$push': {'old_subscription_plan': {'user_id': subs['user_id'],'signin_type': subs['signin_type'],'buy_plan': subs['buy_plan'],'starting_date': subs['starting_date'],'plan_expiry_date': subs['plan_expiry_date'], 'total_amount': subs['total_price'],'product_count': subs['product_count'], 'products': subs['products']}}})
#                              output.append({'wallet_id': wallet_id, 'status': status, 'amount': amount,
#                                             'transaction_id': transaction_id, 'payment_type': payment_type,
#                                             'transaction_type': transaction_type,
#                                             'transaction_date': transaction_time_stamp, 'order_id': order_id,
#                                             'closing_balance': current_balance})
#                              SubscriptionSuccess(wallet_id, order_id)
#                              SubscriptionSuccessEmail(wallet_id,order_id)
#                              SubscriptionSuccessSMS(wallet_id, order_id)
#                              return jsonify(
#                                  {'status': 'success', 'result': output, 'message': 'Amount updated successfully'})
#     except Exception as e:
#         return jsonify({'status':'fail','result':str(e)})


#----------------------------------------------------- Modify subscription ---------------------------------------------
@app.route('/owo/modify_subscription_cart', methods=['POST'])
def ModifyCartTotal():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    output = []
    output1 = []
    gstprice = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    products = request.json['products']
    signin_type = request.json['signin_type']
    buy_plan = request.json['buy_plan']
    starting_date = request.json['starting_date']
    s_date = datetime.datetime.strptime(starting_date, "%Y-%m-%d")
    modified_date = s_date + timedelta(days=buy_plan)
    plan_expiry_date = datetime.datetime.strftime(modified_date, "%Y-%m-%d")
    start_day = request.json['start_day']
    subscription_id = request.json['subscription_id']
    transaction_time_stamp = datetime.datetime.now()
    transaction_type = "SubscriptionModify"
    payment_type = "Subscriptionrefund"
    order_id = transaction_type[:8].upper() + str(random.randint(100000, 999999))
    transaction_id = order_id
    product_count = []
    old_subscription_plan = []
    wallet_amount = int()
    current_balance = int()
    for wallet in db_wallet.find({'subscription_id': subscription_id}):
        wallet_amount = wallet['subscription_amount']
    for i in products:
        set_quantity = i['set_quantity']
        purchase_price = i['purchase_price']
        total_price = calculatePrice(set_quantity, purchase_price, buy_plan, start_day)
        print(purchase_price)
        total_quantity = calculateProductQuant(buy_plan, start_day, set_quantity)
        print(total_quantity)
        product_count.append({'total_quantity': total_quantity})
        print(product_count)
        result2 = defaultdict(int)
        for elm in product_count:
            for k, v in elm.items():
                result2[k] += v
        print(result2)
        productcount = [result2[val] for val in result2 if result2[val] > 1]
        print(productcount)
        str3 = int(''.join(str(i) for i in productcount))
        print(str3)
        total_gst_price = total_quantity * round(purchase_price)
        gstprice.append({'gst': round(total_gst_price)})
        print(gstprice)
        result1 = defaultdict(int)
        for elm in gstprice:
            for k, v in elm.items():
                result1[k] += v
        print(result1)
        gst_price = [result1[val] for val in result1 if result1[val] > 1]
        print(gst_price)
        str2 = int(''.join(str(i) for i in gst_price))
        print(str2)
        for j in db.find():
            if str(signin_type) == str(j['signin_type']) and int(user_id) == int(j['user_id']):
                id = j['subscription_id']
                print(subscription_id)
                result_id = [dict(item, **{'product_status': "enabled"}) for item in products]
                db.update_many({'subscription_id': int(subscription_id)}, {
                    '$set': {'products': result_id, 'buy_plan': buy_plan, 'starting_date': starting_date,
                             'start_day': start_day, 'plan_expiry_date': plan_expiry_date,
                             'subscription_status':"active", 'payment_status': "pending"}})
        output1.append({'total_price': round(total_price)})
        result = defaultdict(int)
        for elm in output1:
            for k, v in elm.items():
                result[k] += v
        print(result)
        total_cart_value = [result[val] for val in result if result[val] > 1]
        print(total_cart_value)
        str1 = int(''.join(str(i) for i in total_cart_value))
        print(str1)
        amount = str1
        delivery_charges = SubscriptionDelivery_charges(signin_type, amount)
        sub_details = getSubscriptionProductByDate(subscription_id,products,buy_plan,start_day)
        print(sub_details)
    db.update_many({'subscription_id': subscription_id},
                   {'$set': {'total_price': str1, 'gst_price': str2, 'product_count': str3,'delivery_charges':int(delivery_charges)}})
    for subs in db.find({'subscription_id':subscription_id}):
        # old_subscription_plan.append({'user_id':subs['user_id'],'signin_type':subs['signin_type'],'buy_plan':subs['buy_plan'],'starting_date':subs['starting_date'],'plan_expiry_date':subs['plan_expiry_date'],'total_amount':subs['total_price'],'product_count':subs['product_count']})
        db.update_many({'subscription_id':subscription_id},{'$push':{'old_subscription_plan':{'user_id':subs['user_id'],'signin_type':subs['signin_type'],'buy_plan':subs['buy_plan'],'starting_date':subs['starting_date'],'plan_expiry_date':subs['plan_expiry_date'],'total_amount':subs['total_price'],'product_count':subs['product_count'],'products':subs['products']}}})
    for w_amount in db_wallet.find({'subscription_id':subscription_id}):
        wallet_amount = w_amount['subscription_amount']
        current_balance = w_amount['current_balance']
        if wallet_amount<str1:
            d = str1 - wallet_amount
            #db_wallet.update_many({'subscription_id':subscription_id},{'$set':{'subscription_amount':str1}})
            output.append({'subscription_plan': buy_plan, 'delivery_charge': delivery_charges, 'gst_value': str2, 'total_cart_value': str1,'subscription_id': subscription_id})
            return jsonify({'status':"success",'message':"please add remaining amount to wallet",'result':output,'required_amount':d,'product_details':sub_details})
    else:
            # remaining_amount = wallet_amount - str1
            # print(remaining_amount)
            # c_balance = current_balance + remaining_amount
            # print(c_balance)
            # db_wallet.update_many({'subscription_id': subscription_id}, {'$set': {'subscription_amount': str1,'current_balance':c_balance}, '$push': {
            #                                             'recent_transactions': {'amount': c_balance,
            #                                                                     'payment_type': payment_type,
            #                                                                     'transaction_id': transaction_id,
            #                                                                     'transaction_type': transaction_type,
            #                                                                     'transaction_date': transaction_time_stamp,
            #                                                                     'order_id': order_id,
            #                                                                     'status': "success",
            #                                                                     'closing_balance': c_balance}}})
            output.append(
                {'subscription_plan': buy_plan, 'delivery_charge': delivery_charges, 'gst_value': str2, 'total_cart_value': str1,
                 'subscription_id': subscription_id})
    return jsonify({'status': "success", 'message': "success", 'result': output,'product_details':sub_details})



#--------------------------------------------------- subscription modification list ------------------------------------
# @app.route('/owo/get_products_modify', methods=['POST'])
# # @jwt_required
# def getSubscriptionProductsModify():
#     data = mongo.db.OWO
#     db = data.product_subscription_test
#     db1 = data.products
#     output = []
#     product_count = int()
#     user_id = request.json['user_id']
#     sub_id = int()
#     signin_type = request.json['signin_type']
#     frequency =str()
#     buy_plan = int()
#     subscription_id = int()
#     for i in db.find({'user_id':user_id,'signin_type':signin_type}):
#         u_id = i['user_id']
#         s_type = i['signin_type']
#         subscription_id = i['subscription_id']
#         print(subscription_id)
#         try:
#            frequency = i['frequency']
#         except KeyError or ValueError:
#             frequency = ""
#         try:
#            buy_plan = i['buy_plan']
#         except KeyError or ValueError:
#             buy_plan = 0
#         if int(user_id) == int(u_id) and str(signin_type) == str(s_type) and i['subscription_status'] == "active":
#             try:
#                 products = i['products']
#             except KeyError or ValueError:
#                 pass
#             for j in products:
#                     p_id = j['product_id']
#                     if j['product_status'] == "enabled":
#                         try:
#                             set_quantity = j['set_quantity']
#                         except KeyError or ValueError:
#                             set_quantity = []
#                         for k in db1.find():
#                             p_type = k['package_type']
#                             if str(p_id) == str(k['product_id']):
#                                 product_count += 1
#                                 # print(p_id)
#                                 if 'product_image' not in k.keys():
#                                     product_image = '',
#                                 else:
#                                     product_image = k['product_image']
#                                 for l in p_type:
#                                     u_price = l['unit_price']
#                                     if 'package_type' not in l.keys():
#                                         package_type = '',
#                                     else:
#                                         package_type = l['package_type']
#                                     output.append({'product_id': p_id, 'product_images': product_image, 'user_id': u_id,
#                                                    'signin_type': signin_type, 'product_name': k['product_name'],
#                                                    'package_type': package_type,
#                                                    'starting_date': i['starting_date'],
#                                                    'plan_expiry_date': i['plan_expiry_date'], 'set_quantity': set_quantity,
#                                                    'unit_price': u_price, 'purchase_price': j['purchase_price'],
#                                                    'subscription_id': i['subscription_id']})
#     return jsonify({'status': True, 'message': 'get images by subscription product_', 'result': output,'frequency':frequency,'buy_plan':buy_plan,
#                     'count': product_count, 'subscription_id': subscription_id})


#---------------------------------------------- subscription pause and active ------------------------------------------
# @app.route('/owo/plan_pause_and_active', methods=['POST'])
# @jwt_required
# def SubscriptionPlanPause():
#     data = mongo.db.OWO
#     db = data.product_subscription_test
#     subscription_id = request.json['subscription_id']
#     subscription_status = request.json['subscription_status']
#     t_date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
#     output = []
#     for i in db.find({'subscription_id':subscription_id,"subscription_status":"active"}):
#         if subscription_status == 'pause':
#             if i['starting_date'] <= t_date < i['plan_expiry_date']:
#                 db.update_many({'subscription_id':subscription_id},{'$set':{'subscription_status':subscription_status,
#                                                                             'plan_pause_date':t_date}})
#                 output.append({'subscription_id':subscription_id,
#                                'subscription_status':subscription_status,
#                                'plan_start_date':i['starting_date'],
#                                'plan_expiry_date':i['plan_expiry_date'],
#                                'plan_pause_date':t_date})
#                 return jsonify({'status':True,'message':'you have successfully paused your subscription plan','result':output})
#         # elif subscription_status == 'expired' or subscription_status == 'cancelled':
#             else:
#                 return jsonify({'status': False,
#                             'message': 'sorry you cannot modify your subscription plan as your plan '
#                                        'has either not started or expired',
#                             'result': output})
#     else:
#         if subscription_status == 'active':
#             for j in db.find({'subscription_id': subscription_id, "subscription_status": "pause"}):
#                     plan_start_day = j['starting_date']
#                     plan_pause_day = j['plan_pause_date']
#                     plan_expiry_date = j['plan_expiry_date']
#                     print(plan_expiry_date)
#                     db.update_many({'subscription_id': subscription_id},
#                                    {'$set': {'subscription_status': subscription_status,
#                                              'plan_activation_date':t_date,
#                                              'plan_expiry_date':plan_expiry_date,
#                                              'buy_plan':j['buy_plan']}})
#                     output.append({'subscription_id': subscription_id,
#                                    'subscription_status': subscription_status,
#                                    'plan_start_date': starting_date,
#                                    'plan_expiry_date': plan_expiry_date,
#                                    'plan_pause_date': plan_pause_day})
#     return jsonify({'status': True, 'message': 'you have successfully activated your subscription plan',
#                                 'result': output})

@app.route('/owo/plan_pause_and_active', methods=['POST'])
@jwt_required
def SubscriptionPlanPause():
    data = mongo.db.OWO
    db = data.product_subscription_test
    subscription_id = request.json['subscription_id']
    subscription_status = request.json['subscription_status']
    t_date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
    output = []
    for i in db.find({'subscription_id':subscription_id,"subscription_status":"active"}):
        subsc_status = i['subscription_status']
        if subscription_status == 'pause':
            if i['starting_date'] <= t_date < i['plan_expiry_date']:
                db.update_many({'subscription_id':subscription_id},{'$set':{'subscription_status':subscription_status,
                                                                            'plan_pause_date':t_date}})
                output.append({'subscription_id':subscription_id,
                               'subscription_status':subscription_status,
                               'plan_start_date':i['starting_date'],
                               'plan_expiry_date':i['plan_expiry_date'],
                               'plan_pause_date':t_date})
                return jsonify({'status':True,'message':'you have successfully paused your subscription plan','result':output})
        elif subsc_status == 'expired' or subsc_status == 'cancelled':
            return jsonify({'status': False,
                        'message': "sorry your plan has been expired or cancelled",
                        'result': output})
        else:
            return jsonify({'status': False,
                        'message': 'sorry you cannot modify your subscription plan as your plan '
                                       'has either not started or expired',
                            'result': output})
    if subscription_status == 'active':
        for j in db.find({'subscription_id': subscription_id, "subscription_status": "pause"}):
            plan_start_day = j['starting_date']
            plan_pause_day = j['plan_pause_date']
            plan_expiry_date = j['plan_expiry_date']
            print(plan_expiry_date)
            db.update_many({'subscription_id': subscription_id},
                           {'$set': {'subscription_status': subscription_status,
                                     'plan_activation_date': t_date,
                                     'plan_expiry_date': plan_expiry_date,
                                     'buy_plan': j['buy_plan']}})
            output.append({'subscription_id': subscription_id,
                           'subscription_status': subscription_status,
                           'plan_start_date': plan_start_day,
                           'plan_expiry_date': plan_expiry_date,
                           'plan_pause_date': plan_pause_day})
            return jsonify({'status': True, 'message': 'you have successfully activated your subscription plan',
                            'result': output})
    return jsonify({'status': False,
                    'message': 'sorry you cannot modify your subscription plan as your plan '
                               'has either not started or expired',
                    'result': output})


#----------------------------------------------check user subscription -------------------------------------------------
@app.route('/owo/chech_user_subscription', methods=['POST'])
@jwt_required
def subscribed():
    data = mongo.db.OWO
    db = data.product_subscription_test
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    for i in db.find({'user_id':user_id,'signin_type':signin_type}):
        try:
            transaction_id = i['transaction_id']
        except KeyError or ValueError:
            transaction_id = ""
            return jsonify({'status': "false", 'is_subscribed': False})
        if  transaction_id is not None:
                return jsonify({'status':"success",'is_subscribed_user':True})
    else:
        return jsonify({'status': "false", 'is_subscribed': False})


#----------------------------------------cart checkout -------------------------------------------------------------
@app.route('/owo/paymentcart_checkout', methods=['POST'])
@jwt_required
def PaymentcartCheckout():
    data = mongo.db.OWO
    db = data.shoppingcart
    cart_id = request.json['cart_id']
    sub_total = request.json['sub_total']
    order_type = request.json['order_type']
    ts = calendar.timegm(time.gmtime())
    order_id = order_type[:5].upper() + str(ts)
    output = []
    for i in db.find({'cart_id':int(cart_id)}):
        if int(cart_id) == int(i['cart_id']):
            output.append({'order_id':order_id,'products':i['products'],'sub_total':sub_total,'order_type':order_type,'cart_id':cart_id,'delivery_charges':i['delivery_charges']})
            return jsonify({'status':"success",'message':"success",'result':output})
    else:
        return jsonify({'status':"fail",'message':"failed to search cart id",'result':[]})


# -------------------------------------------- Event order summary ------------------------------------------------------
@app.route('/owo/eventorder_summery', methods = ['POST'])
@jwt_required
def eventorderSummery():
    data = mongo.db.OWO
    db1 = data.individual_users
    db2 = data.corporate_users
    db3 = data.shoppingcart
    db = data.event_management
    output = []
    event_id_list = [i['event_id'] for i in db.find()]
    if len(event_id_list) is 0:
        event_id = 1
    else:
        event_id = int(event_id_list[-1]) + 1
    event_type = request.json['event_type']
    venue = request.json['venue']
    date = request.json['date']
    time = request.json['time']
    order_id = request.json['order_id']
    cart_id = request.json['cart_id']
    signin_type = request.json['signin_type']
    user_id = request.json['user_id']
    cart_products = []
    for m in db3.find({'cart_id':cart_id}):
        db.insert_one({'event_id': event_id, 'products':m['products'],'email_id':m['email_id'],'mobile_number':m['mobile_number'], 'user_id': user_id, 'signin_type': signin_type,
                    'order_id': order_id,'event_type':event_type,'payment_status':"pending",'delivery_charges':m['delivery_charges'],'order_type':m['order_type'],'total_gst':m['total_gst']})
    for i in db2.find():
        us_id = i['user_id']
        s_type = i['signin_type']
        if str(us_id) == str(user_id) and str(s_type) == str(signin_type):
            for k in i['user_address']:
                a_id = k['address_id']
                if str(a_id) == str(venue):
                    building_number = k['building_number']
                    address = k['address']
                    address_type = k['address_type']
                    landmark = k['landmark']
                    latitude = k['latitude']
                    longitude = k['longitude']
                    output.append({'venue':[{'building_number': building_number,
                                                                'address': address,
                                                                'landmark': landmark,
                                                                'latitude': latitude,
                                                                'address_type': address_type,
                                                                'longitude': longitude}],
                                   'date':date,'time':time, 'order_id': order_id,
                                   'signin_type': signin_type, 'user_id': user_id})
                    db.update_many({'event_id':event_id},{'$set':{'venue':[{'building_number': building_number,'address': address,'landmark': landmark,'latitude': latitude,'address_type': address_type,'longitude': longitude}],'date':date,'time':time}})
            return jsonify({'status': True, 'message': 'details', 'result': output,'event_id':event_id})
    for j in db1.find():
        us_id = j['user_id']
        s_type = j['signin_type']
        if str(us_id) == str(user_id) and str(s_type) == str(signin_type):
            for a in j['user_address']:
                a_id = a['address_id']
                if str(a_id) == str(venue):
                    building_number = a['building_number']
                    address = a['address']
                    address_type = a['address_type']
                    landmark = a['landmark']
                    latitude = a['latitude']
                    longitude = a['longitude']
                    output.append({'venue':[{'building_number': building_number,
                                                                'address': address,
                                                                'landmark': landmark,
                                                                'latitude': latitude,
                                                                'address_type': address_type,
                                                                'longitude': longitude}],
                                   'date':date,'time':time, 'order_id': order_id,
                                   'signin_type': signin_type, 'user_id': user_id})
                    db.update_many({'event_id': event_id}, {'$set': {'venue': [{'building_number': building_number, 'address': address, 'landmark': landmark,'latitude': latitude, 'address_type': address_type, 'longitude': longitude}],'date':date,'time':time}})
            return jsonify({'status': True, 'message': 'details', 'result': output,'event_id':event_id})
    return jsonify({'status': False, 'message': 'invalid details', 'result': output})


# -------------------------------------------------- Instant Order Summary --------------------------------------------
@app.route('/owo/instantorder_summary', methods=['POST'])
@jwt_required
def InstantOrderSummary():
    data = mongo.db.OWO
    db = data.instant_delivery_management
    db3 = data.shoppingcart
    db1 = data.corporate_users
    db2 = data.individual_users
    db_s = data.slot
    output = []
    instant_id_list = [i['instant_id'] for i in db.find()]
    if len(instant_id_list) is 0:
        instant_id = 1
    else:
        instant_id = int(instant_id_list[-1]) + 1
    user_id = request.json['user_id']
    address_id = request.json['address_id']
    signin_type = request.json['signin_type']
    order_id = request.json['order_id']
    slot_id = request.json['slot_id']
    cart_id = request.json['cart_id']
    for m in db3.find({'cart_id': int(cart_id)}):
        db.insert_one({'instant_id': instant_id, 'products': m['products'], 'user_id': user_id, 'email_id':m['email_id'],
                        'mobile_number': m['mobile_number'], 'signin_type': signin_type, 'order_id': order_id,
                       'payment_status': "pending", 'delivery_charges': m['delivery_charges'], 'order_type':m['order_type'],'total_gst':m['total_gst']
                       })
    for i in db1.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        if int(u_id) == int(user_id) and str(signin_type) == str(s_type):
            for addr in i['user_address']:
                if addr['address_id']== address_id:
                    delivery_address = addr['address']
                    print(delivery_address)
                    for j in db_s.find():
                        s_id = j['slot_id']
                        if str(s_id) == str(slot_id):
                            output.append({'user_id': user_id, 'signin_type': signin_type, 'order_id': order_id,
                                           'slot_id': slot_id, 'available_slot': j['available_slot'],
                                           'instant_id': instant_id})
                            db.update({'instant_id':instant_id},{'$set':{'slot_id':slot_id, 'available_slot': j['available_slot'],'delivery_address':delivery_address}})
                            return jsonify({'status': True, 'message': 'order summary', 'result': output})
    for k in db2.find():
        u_id = k['user_id']
        s_type = k['signin_type']
        if int(u_id) == int(user_id) and str(signin_type) == str(s_type):
            for addr in k['user_address']:
                if addr['address_id']== address_id:
                    delivery_address = addr['address']
                    print(delivery_address)
                    for l in db_s.find():
                        s_id = l['slot_id']
                        if str(s_id) == str(slot_id):
                            output.append({'user_id': user_id, 'signin_type': signin_type, 'order_id': order_id,
                                           'slot_id': slot_id, 'available_slot': l['available_slot'], 'cart_id': cart_id, 'instant_id': instant_id})
                            db.update({'instant_id': instant_id},
                                      {'$set': {'slot_id': slot_id, 'available_slot': l['available_slot'],'delivery_address':delivery_address}})
                    return jsonify({'status': True, 'message': 'order summary', 'result': output})
    return jsonify({'status': False, 'message': 'invalid user_id'})

#------------------------------------------------ Event payment status ------------------------------------------------
@app.route('/owo/eventpaymentstatus', methods=['POST'])
@jwt_required
def EventPaymentStatus():
    try:
        data = mongo.db.OWO
        db3 = data.shoppingcart
        db = data.event_management
        transaction_id = request.json['transaction_id']
        payment_type = request.json['payment_type']
        transaction_type = request.json['transaction_type']
        sub_total=request.json['sub_total']
        order_id = request.json['order_id']
        status = request.json['status']
        cart_id = request.json['cart_id']
        event_id = request.json['event_id']
        ordered_date = datetime.datetime.now()
        if status == "success":
            for i in db3.find({'cart_id': cart_id}):
                db.update_many({'event_id': event_id}, {'$set': {'transaction_id': transaction_id,
                                                                 'transaction_type': transaction_type,
                                                                 'sub_total': sub_total,
                                                                 'payment_type': payment_type,
                                                                 'payment_status': status,
                                                                 'order_id': order_id,
                                                                 'order_status': "confirmed",
                                                                 'delivery_status': "pending",
                                                                 'ordered_date': ordered_date}})

                OrderConfirmation(cart_id, order_id)
                OrderConfirmationEmail(cart_id, order_id)
                OrderConfirmationSMS(cart_id, order_id)
                db3.delete_one({'cart_id': cart_id})
                return jsonify({'status': "success", 'message': "order placed successfully", 'result': order_id})
            return jsonify({'status': False, 'message': 'invalid cart id', 'result':  order_id})
        else:
            return jsonify({'status': False, 'message': "order not placed", 'result': order_id})
    except Exception as e:
           return jsonify({'status': 'failed', 'result': str(e), 'message': 'fail'})

# @app.route('/owo/eventpaymentstatus', methods=['POST'])
# @jwt_required
# def EventPaymentStatus():
#     try:
#         data = mongo.db.OWO
#         db3 = data.shoppingcart
#         db = data.event_management
#         transaction_id = request.json['transaction_id']
#         payment_type = request.json['payment_type']
#         transaction_type = request.json['transaction_type']
#         sub_total=request.json['sub_total']
#         order_id = request.json['order_id']
#         status = request.json['status']
#         cart_id = request.json['cart_id']
#         event_id = request.json['event_id']
#         ordered_date = datetime.datetime.now()
#         if status == "success":
#             for i in db3.find({'cart_id': cart_id}):
#                 for e in db.find({'transaction_id': transaction_id}):
#                     db.update_many({'event_id': event_id}, {'$set': {'transaction_id': transaction_id,
#                                                                      'transaction_type': transaction_type,
#                                                                      'sub_total': sub_total,
#                                                                      'payment_type': payment_type,
#                                                                      'payment_status': status,
#                                                                      'order_id': e["order_id"],
#                                                                      'order_status': "confirmed",
#                                                                      'delivery_status': "pending",
#                                                                      'ordered_date': ordered_date}})
#
#                     OrderConfirmation(cart_id, order_id)
#                     OrderConfirmationEmail(cart_id, order_id)
#                     OrderConfirmationSMS(cart_id, order_id)
#                     db3.delete_one({'cart_id': cart_id})
#                     return jsonify({'status': "success", 'message': "order placed successfully", 'result': order_id})
#                 return jsonify({'status': False, 'message': 'transaction id not found', 'result': order_id})
#             return jsonify({'status': False, 'message': 'invalid cart id', 'result':  order_id})
#         else:
#             return jsonify({'status': False, 'message': "order not placed", 'result': order_id})
#     except Exception as e:
#            return jsonify({'status': 'failed', 'result': str(e), 'message': 'fail'})

# ---------------------------------------- instant payment status -----------------------------------------------------
@app.route('/owo/instantpaymentstatus', methods=['POST'])
@jwt_required
def InstantPaymentStatus():
    try:
        data = mongo.db.OWO
        db3 = data.shoppingcart
        db_p = data.products
        db = data.instant_delivery_management
        transaction_id = request.json['transaction_id']
        payment_type = request.json['payment_type']
        transaction_type = request.json['transaction_type']
        sub_total=request.json['sub_total']
        order_id = request.json['order_id']
        status = request.json['status']
        cart_id = request.json['cart_id']
        instant_id = request.json['instant_id']
        ordered_date = datetime.datetime.now()
        if status == "success":
            for i in db3.find({'cart_id': int(cart_id)}):
                products = i['products']
                for j in products:
                    p_qnt = j['product_quantity']
                    p_id = j['product_id']
                    for k in db_p.find({'product_id': str(p_id)}):
                        if int(p_qnt) > k['product_quantity']:
                            if k['active_status'] is False:
                                return jsonify({'status': False,
                                                'message': 'Sorry product is not available', 'result': order_id})
                            return jsonify({'status': False,
                                            'message':  str(k['product_name']) + ' available quantity is '
                                                       + str(k['product_quantity']), 'result': order_id})
            db.update_many({'instant_id': instant_id}, {'$set': {'transaction_id': transaction_id,
                                                                 'transaction_type': transaction_type,
                                                                 'sub_total': sub_total,
                                                                 'payment_type': payment_type,
                                                                 'payment_status': status,
                                                                 'order_id': order_id,
                                                                 'order_status': "confirmed",
                                                                 'delivery_status': "pending",
                                                                 'ordered_date': ordered_date}})
            OrderConfirmation(cart_id, order_id)
            OrderConfirmationEmail(cart_id, order_id)
            OrderConfirmationSMS(cart_id, order_id)
            db3.delete_one({'cart_id': cart_id})
            return jsonify({'status': True, 'message': "order placed successfully", 'result': order_id})
        return jsonify({'status': False, 'message': 'invalid cart id', 'result':  order_id})
    except Exception as e:
        return jsonify({'status': 'failed', 'result': str(e), 'message': 'fail'})


#----------------------------------------------- My Orders event and instant -------------------------------------------
@app.route('/owo/my_orders', methods =['POST'])
@jwt_required
def myOrders():
    data = mongo.db.OWO
    db = data.event_management
    db_instant = data.instant_delivery_management
    db_r = data.rating
    output = []
    output1 = []
    product_rating = 0
    final_output = []
    user_id = request.json['user_id']

    signin_type = request.json['signin_type']
    # temp = {}
    for i in db.find({'payment_status': 'success'}):
        u_id = i['user_id']
        s_type = i['signin_type']
        e_type = i['order_type']
        p_type = i['products']
        order_id = i['order_id']
        order_type = i['order_type']
        ordered_date = i['ordered_date']
        if 'sub_total' not in i.keys():
            sub_total = ''
        else:
            sub_total = i['sub_total']
        delivery_status = i['delivery_status']
        if str(delivery_status) == 'delivered' or str(delivery_status) == 'pending' or str(delivery_status) == 'cancelled':
            if e_type == 'event':
                if str(u_id) == str(user_id) and str(s_type) == str(signin_type):
                    for j in p_type:
                        product_name = j['product_name']
                        product_id = j['product_id']
                        p_q = j['product_quantity']
                        if 'product_image' not in j.keys():
                            product_image = [],
                        else:
                            product_image = j['product_image']
                        for k in db_r.find():
                            id = k['product_id']
                            r_history = k['rating_history']
                            if str(id) == str(product_id):
                                try:
                                    product_rating = k['current_rating']
                                except KeyError or ValueError:
                                    product_rating = 0
                        # products.append({'product_image': product_image, 'ratings':4,'product_name':product_name})
                    output.append({'order_type': order_type, 'product_quantity': p_q, 'order_id': order_id,
                                   'product_id': product_id, 'ordered_date': ordered_date,
                                   'product_image': product_image, 'ratings': product_rating, 'product_name': product_name,
                                   'delivery_status': delivery_status, 'sub_total': sub_total})
    for k in db_instant.find({'payment_status': 'success'}):
        u_id = k['user_id']
        s_type = k['signin_type']
        e_type = k['order_type']
        p_type = k['products']
        order_id = k['order_id']
        order_type = k['order_type']
        ordered_date = k['ordered_date']
        if 'sub_total' not in k.keys():
            sub_total = ''
        else:
            sub_total = k['sub_total']
        delivery_status = k['delivery_status']
        if str(delivery_status) == 'delivered' or str(delivery_status) == 'pending' or str(delivery_status) == 'cancelled':
            if e_type == 'instant':
                if str(u_id) == str(user_id) and str(s_type) == str(signin_type):
                    for l in p_type:
                        p_q = l['product_quantity']
                        product_id = l['product_id']
                        product_name = l['product_name']
                        if 'product_image' not in l.keys():
                            product_image = [],
                        else:
                            product_image = l['product_image']
                        for k in db_r.find():
                            id = k['product_id']
                            r_history = k['rating_history']
                            if str(id) == str(product_id):
                                try:
                                    product_rating = k['current_rating']
                                except KeyError or ValueError:
                                    product_rating = 0
                    output1.append({'order_type': order_type, 'product_quantity': p_q, 'order_id': order_id,
                                    'product_id': product_id, 'ordered_date': ordered_date, 'product_name': product_name,
                                    'product_image': product_image, 'ratings': product_rating,
                                    'delivery_status': delivery_status, 'sub_total': sub_total})
    final_output = output+output1
    final_output.sort(reverse=True, key=lambda e: e['ordered_date'])
    return jsonify({'status': True, 'message': 'List of orders', 'result': final_output})


#----------------------------------------------------- Subscription orders----------------------------------------------
@app.route("/owo/subscription_orders", methods=['POST'])
@jwt_required
def subscriptionOrderHistory():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db1 = data.subscription_history
    db_p = data.products
    date = request.json['date']
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    output = []
    order_status = str()
    products = []
    for i in db1.find({'date':date,'order_history.delivery_status':"Delivered"}):
        for j in i['order_history']:
            subscription_id = j['subscription_id']
            for s_id in db.find({'subscription_id':subscription_id,'user_id':user_id,'signin_type':signin_type}):
                for pro in s_id['products']:
                    if s_id['is_subscribed'] == True and pro['cart_status'] == "deactive":
                        p_id = pro['product_id']
                        for k in db_p.find():
                            if str(p_id) == str(k['product_id']):
                                if 'product_image' not in k.keys():
                                    product_image = '',
                                else:
                                    product_image = k['product_image']
                                products.append({'product_image':product_image,'product_id':k['product_id'],'product_name':k['product_name'],'ratings':3.5})
                                order_status = j['delivery_status'] + " " + date
                output.append({ 'amount_paid':j['total_price'],'order_id':j['order_id'],'delivered_date':date, 'delivery_status':j['delivery_status'],'products':products,'order_type':"subscription",'product_quantity':j['product_count'],'order_status':order_status,'paid_through':"wallet",'subscription_id':j['subscription_id']})
    return jsonify({'status': True, 'message': 'get subscription data success','return':output})


#--------------------------------------------- Order details -----------------------------------------------------------
@app.route('/owo/order_details', methods=['POST'])
@jwt_required
def OrderDetails():
    data = mongo.db.OWO
    db = data.event_management
    db1 = data.instant_delivery_management
    db_iu = data.individual_users
    db_cp = data.corporate_users
    db_s = data.product_subscription_test
    dbs_h = data.subscription_history
    db_p = data.products
    db_r = data.rating
    output = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    order_id = request.json['order_id']
    products = []
    product_rating = 0

    for i in db.find({'user_id':int(user_id),'signin_type':signin_type,'payment_status':'success'}):
        o_id = i['order_id']
        if str(order_id) == str(o_id):
            if 'ordered_date' not in i.keys():
                order_date = ''
            else:
                order_date = i['ordered_date']
            order_type = i['order_type']
            if 'order_status' not in i.keys():
                order_status = ''
            else:
                order_status = i['order_status']
            if 'sub_total' not in i.keys():
                sub_total = ''
            else:
                sub_total = i['sub_total']
            if 'payment_type' not in i.keys():
                paid_through = ''
            else:
                paid_through = i['payment_type']
            for address in i['venue']:
                shipping_address = address['address']
            try:
                p = i['products']
                for j in p:
                    product_name = j['product_name']
                    p_id = j['product_id']
                    if 'product_image' not in j.keys():
                        product_image = '',
                    else:
                        product_image = j['product_image']
                    for m in db_r.find():
                        id = m['product_id']
                        r_history = m['rating_history']
                        if str(id) == str(p_id):
                            try:
                                product_rating = m['current_rating']
                            except KeyError or ValueError:
                                product_rating = 0
                    products.append({'product_image': product_image, 'product_id': j['product_id'],
                                         'product_name': j['product_name'], 'ratings': product_rating})
                output.append({'order_date': order_date, 'order_type': order_type, 'total_amount_paid': sub_total,
                           'shipping_address': shipping_address,'order_status':order_status,'paid_through': paid_through, 'user_id': user_id,
                               'signin_type':signin_type,'order_id':order_id,'products':products})
            except KeyError or ValueError:
                p = []
    for k in db1.find({'user_id':user_id,'signin_type':signin_type,'payment_status':'success'}):
        o_id = k['order_id']
        if str(order_id) == str(o_id):
            try:
              order_date = k['ordered_date']
            except KeyError or ValueError:
              order_date = " "
            order_type = k['order_type']
            if 'order_status' not in k.keys():
                order_status = ''
            else:
                order_status = k['order_status']
            if 'sub_total' not in k.keys():
                sub_total = ''
            else:
                sub_total = k['sub_total']
            if 'payment_type' not in k.keys():
                paid_through = ''
            else:
                paid_through = k['payment_type']
            shipping_address = k['delivery_address']
            try:
                p = k['products']
                for l in p:
                    product_name = l['product_name']
                    p_id = l['product_id']
                    if 'product_image' not in l.keys():
                        product_image = '',
                    else:
                        product_image = l['product_image']
                    for n in db_r.find():
                        id = n['product_id']
                        r_history = n['rating_history']
                        if str(id) == str(p_id):
                            print("ok")
                            try:
                                product_rating = n['current_rating']
                            except KeyError or ValueError:
                                product_rating = 0
                    products.append({'product_image': product_image, 'product_id': l['product_id'],
                                     'product_name': l['product_name'], 'ratings': product_rating})
                output.append({'order_date': order_date, 'order_type': order_type, 'total_amount_paid': sub_total,
                           'shipping_address': shipping_address,'order_status':order_status,
                            'products': products,'paid_through': paid_through, 'user_id': user_id,
                               'signin_type':signin_type,'order_id':order_id})
            except KeyError or ValueError:
                p = []
    for s_id in db_s.find({'user_id': user_id, 'signin_type': signin_type}):
        subscription_id = s_id['subscription_id']
        print(subscription_id)
        for h in dbs_h.find({'order_history.subscription_id': subscription_id, 'order_history.order_id': order_id}):
            print("okids")
            for oh in h['order_history']:
                if oh['order_id'] == order_id:
                    print(oh['order_id'])
                    print(order_id)
                    for pro in s_id['products']:
                        if s_id['is_subscribed'] == True and pro['cart_status'] == "deactive":
                            p_id = pro['product_id']
                            for k in db_p.find():
                                if str(p_id) == str(k['product_id']):
                                    if 'product_image' not in k.keys():
                                        product_image = '',
                                    else:
                                        product_image = k['product_image']
                                    for o in db_r.find():
                                        id = o['product_id']
                                        r_history = o['rating_history']
                                        if str(id) == str(p_id):
                                            try:
                                                product_rating = o['current_rating']
                                            except KeyError or ValueError:
                                                product_rating = 0
                                    products.append({'product_image': product_image, 'product_id': k['product_id'],
                                                     'product_name': k['product_name'], 'ratings': product_rating})
                                    order_status = oh['delivery_status']
                                    total_price = oh['total_price']
            output.append({'order_date': h['date'], 'total_amount_paid': total_price, 'order_id': order_id,
                 'delivery_status': oh['delivery_status'],
                 'products': products, 'order_type': "subscription", 'order_status': "confirmed",
                 'paid_through': "wallet", 'user_id': s_id['user_id'], 'signin_type': s_id['signin_type'],
                 'shipping_address': s_id['delivery_address']})

    return jsonify({'status': True, 'message': 'product details', 'result': output})


#-------------------------------------------------- Download Invoice ---------------------------------------------------
@app.route('/owo/download_invoice/<user_id>/<signin_type>/<order_id>', methods=['GET'])
# @jwt_required
def DownloadInvoice(user_id, signin_type, order_id):
    data = mongo.db.OWO
    db = data.event_management
    db1 = data.instant_delivery_management
    db_iu = data.individual_users
    db_cp = data.corporate_users
    db_s = data.product_subscription_test
    dbs_h = data.subscription_history
    db_p = data.products
    db_r = data.rating
    output = []
    # user_id = request.json['user_id']
    # signin_type = request.json['signin_type']
    # order_id = request.json['order_id']
    products = []
    product_count = int()
    product_rating = 0
    for i in db.find({'payment_status':'success'}):
        o_id = i['order_id']
        if str(order_id) == str(o_id):
            order_date = i['date']
            order_type = i['order_type']
            if 'order_status' not in i.keys():
                order_status = ''
            else:
                order_status = i['order_status']
            if 'sub_total' not in i.keys():
                sub_total = ''
            else:
                sub_total = i['sub_total']
            if 'payment_type' not in i.keys():
                paid_through = ''
            else:
                paid_through = i['payment_type']
            for address in i['venue']:
                shipping_address = address['address']
            try:
                p = i['products']
                for j in p:
                    product_name = j['product_name']
                    pq = j['product_quantity']
                    p_id = j['product_id']
                    product_count += pq
                    for a in db_r.find():
                        id = a['product_id']
                        r_history = a['rating_history']
                        if str(id) == str(p_id):
                            try:
                                product_rating = a['current_rating']
                            except KeyError or ValueError:
                                product_rating = 0

                    products.append({'purchase_price': j['purchase_price'], 'gst': j['gst'], 'unit_price': j['unit_price'],
                                     'discount': j['discount_in_percentage'], 'product_id': j['product_id'],
                                     'product_name': j['product_name'], 'product_quantity': pq,
                                     'ratings': product_rating})
                output.append({'order_date': order_date, 'order_type': order_type, 'total_amount_paid': sub_total,
                               'total_gst': i['total_gst'], 'delivery_charges': i['delivery_charges'],
                               'shipping_address': shipping_address, 'order_status': order_status,
                               'paid_through': paid_through, 'user_id': user_id, 'signin_type': signin_type,
                               'order_id': order_id, 'products': products, 'total_quantity': product_count})
            except KeyError or ValueError:
                p = []

    for k in db1.find({'payment_status':'success'}):
        o_id = k['order_id']
        if str(order_id) == str(o_id):
            order_date = k['ordered_date']
            order_type = k['order_type']
            if 'order_status' not in k.keys():
                order_status = ''
            else:
                order_status = k['order_status']
            if 'sub_total' not in k.keys():
                sub_total = ''
            else:
                sub_total = k['sub_total']
            if 'payment_type' not in k.keys():
                paid_through = ''
            else:
                paid_through = k['payment_type']
            shipping_address = k['delivery_address']
            try:
                p = k['products']
                for l in p:
                    product_name = l['product_name']
                    pq = l['product_quantity']
                    p_id = l['product_id']
                    product_count += pq
                    for a in db_r.find():
                        id = a['product_id']
                        r_history = a['rating_history']
                        if str(id) == str(p_id):
                            try:
                                product_rating = a['current_rating']
                            except KeyError or ValueError:
                                product_rating = 0
                    products.append({'purchase_price': l['purchase_price'], 'gst': l['gst'],
                                     'unit_price': l['unit_price'], 'discount': l['discount_in_percentage'],
                                     'product_id': l['product_id'], 'product_name': l['product_name'],
                                     'product_quantity': pq, 'ratings': product_rating})

                output.append({'order_date': order_date, 'order_type': order_type, 'total_amount_paid': sub_total,
                               'total_gst': k['total_gst'], 'delivery_charges': k['delivery_charges'],
                               'shipping_address': shipping_address, 'order_status': order_status,
                               'products': products, 'paid_through': paid_through, 'user_id': user_id,
                               'signin_type': signin_type, 'order_id': order_id, 'total_quantity': product_count})
            except KeyError or ValueError:
                p = []

    # for s in db_s.find({'payment_status': 'success'}):
    #     subscription_id = s['subscription_id']
    #     for i in dbs_h.find({'order_history.order_id': order_id}):
    #         for j in i['order_history']:
    #             r_id = j['order_id']
    #             s_id = j['subscription_id']
    #             count = []
    #             if subscription_id == s_id and order_id == r_id and s['is_subscribed'] == True:
    #                 for p in s['products']:
    #                     p_id = p['product_id']
    #                     count.append(p_id)
    #                     if p['cart_status'] == "deactive":
    #                         for k in db_p.find({'product_id': p_id}):
    #                             product_count = 0
    #                             for p_t in k['package_type']:
    #                                 purchase_price = p_t['purchase_price']
    #                                 gst = p_t['gst']
    #                                 unit_price = p_t['unit_price']
    #                                 discount = p_t['discount_in_percentage']
    #                                 product_rating = 0
    #                                 for a in db_r.find({'product_id': p_id}):
    #                                     product_count = product_count + 1
    #                                     try:
    #                                         product_rating = a['current_rating']
    #                                     except KeyError or ValueError:
    #                                         product_rating = 0
    #                                 products.append({'purchase_price': str(purchase_price), 'gst': gst,
    #                                                  'unit_price': unit_price,
    #                                                  'discount': discount,
    #                                                  'product_id': k['product_id'],
    #                                                  'product_name': k['product_name'],
    #                                                  'product_quantity': product_count,
    #                                                  'ratings': product_rating
    #                                                  })
    #                 output.append(
    #                     {'order_date': i['date'], 'total_amount_paid': s['total_price'], 'order_id': order_id,
    #                      'delivery_status': j['delivery_status'], 'total_gst': j['gst'],
    #                      'delivery_charges': s['delivery_charges'], 'products': products,
    #                      'order_type': j['transaction_type'],
    #                      'order_status': i['order_status'], 'paid_through': j['payment_type'], 'user_id': s['user_id'],
    #                      'signin_type': s['signin_type'],
    #                      'shipping_address': s['delivery_address'],
    #                      'total_quantity': len(products)
    #                      })

    for s in db_s.find({'payment_status': 'success'}):
        subscription_id = s['subscription_id']
        for i in dbs_h.find({'order_history.order_id': order_id}):
            for j in i['order_history']:
                r_id = j['order_id']
                s_id = j['subscription_id']
                count = []
                total_gst = 0
                if subscription_id == s_id and order_id == r_id and s['is_subscribed'] == True:
                    for p in s['products']:
                        p_id = p['product_id']
                        count.append(p_id)
                        if p['cart_status'] == "deactive":
                            for k in db_p.find({'product_id': p_id}):
                                product_count = 0
                                for p_t in k['package_type']:
                                    purchase_price = p_t['purchase_price']
                                    gst = p_t['gst']
                                    unit_price = p_t['unit_price']
                                    discount = p_t['discount_in_percentage']
                                    try:
                                        mrp = p_t['mrp']
                                    except KeyError or ValueError:
                                        mrp = 0
                                    t_gst = int(mrp) - int(unit_price)
                                    total_gst += int(t_gst)
                                    product_rating = 0
                                    for a in db_r.find({'product_id': p_id}):
                                        product_count = product_count + 1
                                        try:
                                            product_rating = a['current_rating']
                                        except KeyError or ValueError:
                                            product_rating = 0
                                    products.append({'purchase_price': str(purchase_price), 'gst': t_gst,
                                                     'unit_price': unit_price,
                                                     'discount': discount,
                                                     'product_id': k['product_id'],
                                                     'product_name': k['product_name'],
                                                     'product_quantity': product_count,
                                                     'ratings': product_rating
                                                     })
                    output.append(
                        {'order_date': i['date'], 'total_amount_paid': j['total_price'], 'order_id': order_id,
                         'delivery_status': j['delivery_status'], 'total_gst': j['gst'],
                         'delivery_charges': 0, 'products': products,
                         'order_type': j['transaction_type'],
                         'order_status': i['order_status'], 'paid_through': j['payment_type'], 'user_id': s['user_id'],
                         'signin_type': s['signin_type'],
                         'shipping_address': s['delivery_address'],
                         'total_quantity': len(products)
                         })
    # return jsonify({'status': True, 'message': 'product details', 'result': output})
    return jsonify(output)


#------------------------------------------------------ App notifications ----------------------------------------------
@app.route('/owo/appNotifications', methods=['POST'])
@jwt_required
def appNotifications():
    data = mongo.db.OWO
    db = data.app_notifications
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    output = []
    for j in db.find({'user_id':user_id,'signin_type':signin_type}).sort('date_time', -1):
        output.append({'user_id':user_id,'signin_type':signin_type,'title':j['title'],'notifications':j['notifications'],'date_time':j['date_time']})
    return jsonify({'status':"success",'message':"get all notifications",'result':output})


# ------------------------------------------------ App Get question Category -----------------------------------------
@app.route('/owo/app_get_question_category', methods=['GET'])
def appGetFAQCategory123():
    data = mongo.db.OWO
    db = data.FAQ_management
    output = []
    output1 = []
    output2 = []
    output3 = []
    PaymentRelated = []
    RefundRelated = []
    ProfileRelated = []
    HelpAndSupport = []
    for i in db.find():
        category = i['category']
        question_category = i['question_category']
        try:
            if question_category == "Payment Related":
                for j in category:
                    question_status = j['question_status']
                    if question_status == True:
                        PaymentRelated.append({'admin_id': j['admin_id'], 'admin_userName': j['admin_userName'],
                                               'date_of_creation': j['date_of_creation'],
                                               'modified_on': j['modified_on'],
                                               'question_description': j['question_description'],
                                               'question_id': j['question_id'],
                                               'question_status': question_status,
                                               'question_title': j['question_title']})
        except KeyError or ValueError:
            pass
    output.append({'question_category': "Payment Related", 'category': PaymentRelated})
    for j in db.find():
        category = j['category']
        question_category = j['question_category']
        try:
            if question_category == "Refund Related":
                for k in category:
                    question_status = k['question_status']
                    if question_status == True:
                        RefundRelated.append({'admin_id': k['admin_id'], 'admin_userName': k['admin_userName'],
                                              'date_of_creation': k['date_of_creation'],
                                              'modified_on': k['modified_on'],
                                              'question_description': k['question_description'],
                                              'question_id': k['question_id'],
                                              'question_status': question_status,
                                              'question_title': k['question_title']})
        except KeyError or ValueError:
            pass
    output1.append({'question_category': "Refund Related", 'category': RefundRelated})
    for a in db.find():
        category = a['category']
        question_category = a['question_category']
        try:
            if question_category == "Profile Related":
                for b in category:
                    question_status = b['question_status']
                    if question_status == True:
                        ProfileRelated.append({'admin_id': b['admin_id'], 'admin_userName': b['admin_userName'],
                                               'date_of_creation': b['date_of_creation'],
                                               'modified_on': b['modified_on'],
                                               'question_description': b['question_description'],
                                               'question_id': b['question_id'],
                                               'question_status': question_status,
                                               'question_title': b['question_title']})
        except KeyError or ValueError:
            pass
    output2.append({'question_category': "Profile Related", 'category': ProfileRelated})
    for m in db.find():
        category = m['category']
        question_category = m['question_category']
        try:
            if question_category == "Help & Support":
                for n in category:
                    question_status = n['question_status']
                    if question_status == True:
                        HelpAndSupport.append({'admin_id': n['admin_id'], 'admin_userName': n['admin_userName'],
                                               'date_of_creation': n['date_of_creation'],
                                               'modified_on': n['modified_on'],
                                               'question_description': n['question_description'],
                                               'question_id': n['question_id'],
                                               'question_status': question_status,
                                               'question_title': n['question_title']})
        except KeyError or ValueError:
            pass
    output3.append({'question_category': "Help & Support", 'category': HelpAndSupport})
    return jsonify({'status': True, 'message': 'Get all questions successfully',
                    'result': output + output1 + output2 + output3})


#------------------------------------------------- Get app banner ------------------------------------------------------
@app.route("/owo/get_app_banner", methods= ['GET'])
def getappbanners():
    data = mongo.db.OWO
    db = data.banners
    output = []
    hstb = []
    hsbb = []
    hstc20 = []
    hstc10 = []
    tb = []
    hsumla = []
    for i in db.find():
        s_name = i['screen_name']
        if s_name == "Home_screen_top_banner":
            hstb.append(i['banner_image'])
        if s_name == "Home_screen_brand_banner":
            hsbb.append(i['banner_image'])
        if s_name == "Home_screen_top_categories_20_ltrs":
            hstc20.append(i['banner_image'])
        if s_name == "Home_screen_top_categories_10_ltrs":
            hstc10.append(i['banner_image'])
        if s_name == "Trending_brands":
            tb.append(i['banner_image'])
        if s_name == "Home_screen_you_may_also_like":
            hsumla.append(i['banner_image'])
    return jsonify({'status': True, 'message': 'get banners success',  'Home_screen_top_banner': hstb,
                    'Home_screen_brand_banner': hsbb, 'Home_screen_top_categories_20_ltrs': hstc20,
                    'Home_screen_top_categories_10_ltrs': hstc10, 'Trending_brands': tb, 'Home_screen_you_may_also_like': hsumla})


# ---------------------------------------------------- pay from loyalty balance ---------------------------------------
@app.route('/owo/pay_from_loyalty_points', methods=['POST'])
@jwt_required
def pay_from_loyalty_points():
    db = mongo.db.OWO
    db_loyalty = db.loyalty
    user_id = request.json['user_id']
    amount = request.json['amount']
    signin_type = request.json['signin_type']
    transaction_type = request.json['transaction_type']
    transaction_id=request.json['transaction_id']
    order_type = request.json['order_type']
    ts=calendar.timegm(time.gmtime())
    print(ts)
    order_id = order_type[:4].upper() +str(ts)
    print(order_id)
    try:
        for u in db_loyalty.find():
            print("ok")
            u_id = u['user_id']
            s_type = u['signin_type']
            if int(user_id) == int(u_id) and str(signin_type) == str(s_type):
                if u['loyalty_balance'] > amount:
                    user_balance = u['loyalty_balance']
                    user_balance1 = user_balance-amount
                    closing_balance = user_balance1
                    message ='%d points deducted from your loyalty points'% amount
                    db_loyalty.update({'user_id': int(user_id), 'signin_type': str(signin_type)},
                                      {'$set': {'loyalty_balance': user_balance1},
                                       '$push': {'recent_earnings': {'order_value': amount,
                                                                     'loyalty_type': 'redeemed',
                                                                     'earn_type': transaction_type,
                                                                     'order_type': order_type,
                                                                     'order_id': order_id,
                                                                     'transaction_id': transaction_id,
                                                                     'closing_balance': closing_balance,
                                                                     'current_balance': user_balance,
                                                                     'earn_date': datetime.datetime.now()}}})
                    result = 'Remaining balance in your loyalty points is %d'%int(user_balance)
                    return jsonify({'status': True, 'result': result, 'message': message})
                if u['loyalty_balance'] == 0:
                    return jsonify({'status': False, 'result': [],
                                    'message': 'You do not have loyalty points'})
                if u['loyalty_balance'] < 0:
                    return jsonify({'status': False, 'message':'You do not have sufficient loyalty points for this order',
                                    'result': []})

        else:
            return jsonify({'status': False, 'result': " ", 'message': 'Process failed. Please try again'})
    except Exception as e:
        return jsonify({'status':False, 'result': str(e), 'message': 'fail'})


#-------------------------------------- Get loyalty points by user id & signin type ------------------------------------
@app.route('/owo/get_loyalty_points/<user_id>/<signin_type>', methods=['GET'])
def getLoyaltyPoints(user_id, signin_type):
    data = mongo.db.OWO
    db = data.loyalty
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        if int(u_id) == int(user_id) and str(s_type) == str(signin_type):
            output.append({'loyalty_points': i['loyalty_balance']})
            return jsonify({'status': True, 'message': 'Loyalty points get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'currently you dont have loyalty points', 'result': output})


# ------------------------------------------------- rate_product ------------------------------------------------------
@app.route('/owo/rate_product', methods=['POST'])
@jwt_required
def rate():
    data = mongo.db.OWO
    db = data.rating
    output = []
    user_count = 1
    total_rate = 0
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    email_id = request.json['email_id']
    mobile_number = request.json['mobile_number']
    order_id = request.json['order_id']
    product_id = request.json['product_id']
    product_name = request.json['product_name']
    rating = request.json['rating']
    rating_date_time = datetime.datetime.now()
    for j in db.find():
        id = j['product_id']
        p_name = j['product_name']
        r_history = j['rating_history']
        if str(id) == str(product_id) and str(p_name) == str(product_name):
            for k in r_history:
                user_count1 = len(r_history)
                user_count = 1 + user_count1
                rate = k['rating']
                total_rate += rate
            total = (total_rate + rating) / user_count
            total_rating = round(total, 2)
            db.find_one_and_update({'product_id': str(product_id), 'product_name': str(product_name)},
                                   {'$set': {'current_rating': float(total_rating)},
                                    '$push': {'rating_history': {'user_id': user_id,
                                                                 'signin_type': signin_type,
                                                                 'mobile_number': mobile_number,
                                                                 'email_id': email_id,
                                                                 'order_id': order_id,
                                                                 'rating_date_time': rating_date_time,
                                                                 'rating': float(rating)}}})
            output.append({'product_id': product_id, 'product_name': product_name, 'user_id': user_id,
                           'signin_type': signin_type, 'mobile_number': mobile_number, 'email_id': email_id,
                           'order_id': order_id, 'rating_date_time': rating_date_time,
                           'current_rating': float(total_rating)})

            return jsonify({'status': True, 'message': 'rating added successfully', 'result': output})
    db.find_one_and_update({'product_id': str(product_id), 'product_name': str(product_name)},
                           {'$set': {'current_rating': float(rating)},
                            '$push': {'rating_history': {'user_id': user_id,
                                                         'signin_type': signin_type,
                                                         'mobile_number': mobile_number,
                                                         'email_id': email_id,
                                                         'order_id': order_id,
                                                         'rating_date_time': rating_date_time,
                                                         'rating': float(rating)}}})
    output.append({'product_id': product_id, 'product_name': product_name, 'user_id': user_id,
                   'signin_type': signin_type, 'mobile_number': mobile_number, 'email_id': email_id,
                   'order_id': order_id, 'rating_date_time': rating_date_time,
                   'current_rating': float(rating)})
    return jsonify({'status': True, 'message': 'rating added successfully', 'result': output})


# ----------------------------------------------------- Get All Brands ------------------------------------------------
@app.route('/owo/get_all_brands_based_on_city', methods=['POST'])
@jwt_required
def getAllBrandsbasedoncityname():
    data = mongo.db.OWO
    db = data.companies
    output = []
    city_name = request.json['city_name']
    for i in db.find():
        try:
            brand = i['brand']
            for j in brand:
                city_name = city_name.lower()
                available_city = j['available_city']
                active_status = j['active_status']
                available_city = available_city.lower()
                if str(city_name) == str(available_city) and active_status is True:
                    brand_id = j['brand_id']
                    brand_name = j['brand_name']
                    brand_photo = j['brand_photo']
                    brand_description = j['brand_description']
                    output.append({'brand_id': brand_id, 'brand_name': brand_name, 'brand_description': brand_description,
                                   'brand_photo': brand_photo,
                                  })
        except KeyError or ValueError:
            pass
    return jsonify({"status": True, 'message': (city_name + ' brands details'), 'result': output})


# -------------------------------------------------------- Get All Companies ------------------------------------------
@app.route('/owo/get_all_company_details_based_on_city', methods=['POST'])
@jwt_required
def getAllCompaniesbasedoncity():
    data = mongo.db.OWO
    db = data.companies
    output = []
    city_name = request.json['city_name']
    for i in db.find():
        temp = {}
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        if str(city_name) == str(city):
            temp['city_name'] = i['city_name']
            temp['company_id'] = i['company_id']
            temp['company_name'] = i['company_name']
            temp['company_description'] = i['company_description']
            temp['address'] = i['address']
            temp['primary_contact_number'] = i['primary_contact_number']
            temp['email_id'] = i['email_id']
            if 'company_photo' not in i.keys():
                temp['company_photo'] = ''
            else:
                temp['company_photo'] = i['company_photo']
                # print(i['company_photo'])
            if 'active_status' not in i.keys():
                temp['active_status'] = ''
            else:
                temp['active_status'] = i['active_status']
            output.append(temp)
    return jsonify({"status": True, 'message': (city_name + ' company details'), 'result': output})


# --------------------------------------- Get All Products ------------------------------------------------------------
# @app.route('/owo/get_products_based_on_city', methods=['POST'])
# @jwt_required
# def getProductsbasedoncity():
#     data = mongo.db.OWO
#     db = data.products
#     db_r = data.rating
#     output = []
#     rating = 0
#     product_no_of_ratings = 0
#     city_name = request.json['city_name']
#     for i in db.find({'active_status': True}):
#         city = i['city_name']
#         if 'product_image' not in i.keys():
#             product_image = []
#         else:
#             product_image = i['product_image']
#         city = city.lower()
#         city_name = city_name.lower()
#         if str(city) == str(city_name):
#             try:
#                 p_type = i['package_type']
#                 p_id = i['product_id']
#                 for j in p_type:
#                     for k in db_r.find():
#                         if p_id == k['product_id']:
#                             if 'current_rating' not in k.keys():
#                                 rating = 0,
#                             else:
#                                 rating = k['current_rating']
#                             if 'rating_history' not in k.keys():
#                                 product_no_of_ratings = 0,
#                             else:
#                                 product_no_of_ratings = len(k['rating_history'])
#                     output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
#                                    'product_image': product_image, 'available_quantity': i['product_quantity'],
#                                    'brand_name': i['brand_name'], 'company_name': i['company_name'],
#                                    'package_id': j['package_id'], 'product_rating': rating,
#                                    'package_type': j['package_type'], 'purchase_price': j['purchase_price'],
#                                    'unit_price': j['mrp'], 'product_no_of_rating': product_no_of_ratings,
#                                    'discount_in_percentage': j['discount_in_percentage'],
#                                    'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
#             except KeyError or ValueError:
#                 pass
#     return jsonify({"status": True, 'message': 'get all products success', 'result': output})

@app.route('/owo/get_products_based_on_city', methods=['POST'])
@jwt_required
def getProductsbasedoncity():
    data = mongo.db.OWO
    db = data.products
    db_r = data.rating
    output = []
    rating = 0
    product_no_of_ratings = 0
    city_name = request.json['city_name']
    sorting_type = request.json['sorting_type']
    if sorting_type == 'DESCENDING':
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                city = i['city_name']
                if 'product_image' not in i.keys():
                    product_image = []
                else:
                    product_image = i['product_image']
                city = city.lower()
                city_name = city_name.lower()
                if str(city) == str(city_name):
                    try:
                        p_type = i['package_type']
                        p_id = i['product_id']
                        for j in p_type:
                            purchase_price = j['purchase_price']
                            for k in db_r.find():
                                if p_id == k['product_id']:
                                    if 'current_rating' not in k.keys():
                                        rating = 0,
                                    else:
                                        rating = k['current_rating']
                                    if 'rating_history' not in k.keys():
                                        product_no_of_ratings = 0,
                                    else:
                                        product_no_of_ratings = len(k['rating_history'])
                            output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
                                           'product_image': product_image, 'available_quantity': i['product_quantity'],
                                           'brand_name': i['brand_name'], 'company_name': i['company_name'],
                                           'package_id': j['package_id'], 'product_rating': rating,
                                           'package_type': j['package_type'], 'purchase_price': purchase_price,
                                           'unit_price': j['mrp'], 'product_no_of_rating': product_no_of_ratings,
                                           'discount_in_percentage': j['discount_in_percentage'],
                                           'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
                            output.sort(reverse=True, key=lambda e: int(e['purchase_price']))
                    except KeyError or ValueError:
                        pass
        return jsonify({"status": True, 'message': 'get all products success', 'result': output})
    elif sorting_type == 'ASCENDING':
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                city = i['city_name']
                if 'product_image' not in i.keys():
                    product_image = []
                else:
                    product_image = i['product_image']
                city = city.lower()
                city_name = city_name.lower()
                if str(city) == str(city_name):
                    try:
                        p_type = i['package_type']
                        p_id = i['product_id']
                        for j in p_type:
                            for k in db_r.find():
                                if p_id == k['product_id']:
                                    if 'current_rating' not in k.keys():
                                        rating = 0,
                                    else:
                                        rating = k['current_rating']
                                    if 'rating_history' not in k.keys():
                                        product_no_of_ratings = 0,
                                    else:
                                        product_no_of_ratings = len(k['rating_history'])
                            output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
                                           'product_image': product_image, 'available_quantity': i['product_quantity'],
                                           'brand_name': i['brand_name'], 'company_name': i['company_name'],
                                           'package_id': j['package_id'], 'product_rating': rating,
                                           'package_type': j['package_type'], 'purchase_price': j['purchase_price'],
                                           'unit_price': j['mrp'], 'product_no_of_rating': product_no_of_ratings,
                                           'discount_in_percentage': j['discount_in_percentage'],
                                           'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
                            output.sort(reverse=False, key=lambda e: int(e['purchase_price']))
                    except KeyError or ValueError:
                        pass
        return jsonify({"status": True, 'message': 'get all products success', 'result': output})
    else:
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                city = i['city_name']
                if 'product_image' not in i.keys():
                    product_image = []
                else:
                    product_image = i['product_image']
                city = city.lower()
                city_name = city_name.lower()
                if str(city) == str(city_name):
                    try:
                        p_type = i['package_type']
                        p_id = i['product_id']
                        for j in p_type:
                            purchase_price = j['purchase_price']
                            for k in db_r.find():
                                if p_id == k['product_id']:
                                    if 'current_rating' not in k.keys():
                                        rating = 0,
                                    else:
                                        rating = k['current_rating']
                                    if 'rating_history' not in k.keys():
                                        product_no_of_ratings = 0,
                                    else:
                                        product_no_of_ratings = len(k['rating_history'])
                            output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
                                           'product_image': product_image, 'available_quantity': i['product_quantity'],
                                           'brand_name': i['brand_name'], 'company_name': i['company_name'],
                                           'package_id': j['package_id'], 'product_rating': rating,
                                           'package_type': j['package_type'], 'purchase_price': purchase_price,
                                           'unit_price': j['mrp'], 'product_no_of_rating': product_no_of_ratings,
                                           'discount_in_percentage': j['discount_in_percentage'],
                                           'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
                    except KeyError or ValueError:
                        pass
        return jsonify({"status": True, 'message': 'get all products success', 'result': output})


# --------------------------------------------------- Trending brands ---------------------------------------------------
@app.route('/owo/trending_brands_based_on_city', methods=['POST'])
@jwt_required
def trendingbrandsbasedoncity():
    data = mongo.db.OWO
    db = data.companies
    output = []
    city_name = request.json['city_name']
    for i in db.find({'brand.trending_brand': True}):
        try:
            brand = i['brand']
            for j in brand:
                city = j['available_city']
                active_status = j['active_status']
                city = city.lower()
                city_name = city_name.lower()
                if str(city_name) == str(city) and active_status is True:
                    brand_id = j['brand_id']
                    brand_name = j['brand_name']
                    brand_photo = j['brand_photo']
                    brand_description = j['brand_description']
                    output.append({'brand_id': brand_id, 'brand_name': brand_name, 'brand_description': brand_description,
                                   'brand_photo': brand_photo, 'order': order,
                                   'available_city': city_name,
                                   'trending_brand': trending_brand,
                                   'active_status': active_status})
        except KeyError or ValueError:
            pass

    return jsonify({"status": True, 'message': (city_name + ' trending brand details'), 'result': output})


# ------------------------------------------------ new arrival product details -----------------------------------------
@app.route('/owo/get_products_new_arrival_based_on_city', methods=['POST'])
@jwt_required
def getProductnewarrivalbasedoncity():
    data = mongo.db.OWO
    db = data.products
    output = []
    city_name = request.json['city_name']
    details = db.find({'new_arrival': True, 'active_status': True})
    for i in details:
        p_type = i['package_type']
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        active_status = i['active_status']
        if str(city_name) == str(city) and active_status is True:
            for j in p_type:
                temp = {}
                temp['city_name'] = city
                temp['company_name'] = i['company_name']
                temp['brand_name'] = i['brand_name']
                temp['product_id'] = i['product_id']
                temp['product_name'] = i['product_name']
                temp['product_logo'] = i['product_logo']
                temp['plant_name'] = i['plant_name']
                temp['active_status'] = active_status
                temp['new_arrival'] = i['new_arrival']
                temp['you_may_also_like'] = i['you_may_also_like']
                if 'product_image' not in i.keys():
                    temp['product_image'] = '',
                else:
                    temp['product_image'] = i['product_image']
                temp['unit_price'] = j['mrp']
                temp['discount_in_percentage'] = j['discount_in_percentage']
                temp['purchase_price'] = j['purchase_price']
                temp['package_type'] = j['package_type']
                temp['gst'] = j['gst']
                temp['mrp'] = j['mrp']
                temp['package_id'] = j['package_id']
                output.append(temp)
    return jsonify({"status": True, 'message': (city_name + ' new_arrival product details'), 'result': output})


# --------------------------------------------------------you may like product details ---------------------------------
@app.route('/owo/get_products_you_may_also_like_based_on_city', methods=['POST'])
@jwt_required
def getProductyoumayalsolikebasedoncity():
    data = mongo.db.OWO
    db = data.products
    output = []
    city_name = request.json['city_name']
    details = db.find({'you_may_also_like': True, 'active_status': True})
    for i in details:
        p_type = i['package_type']
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        active_status = i['active_status']
        if str(city_name) == str(city) and active_status is True:
            for j in p_type:
                temp = {}
                temp['city_name'] = city
                temp['company_name'] = i['company_name']
                temp['brand_name'] = i['brand_name']
                temp['product_id'] = i['product_id']
                temp['product_name'] = i['product_name']
                temp['product_logo'] = i['product_logo']
                temp['plant_name'] = i['plant_name']
                temp['active_status'] = active_status
                temp['new_arrival'] = i['new_arrival']
                temp['you_may_also_like'] = i['you_may_also_like']
                if 'product_image' not in i.keys():
                    temp['product_image'] = '',
                else:
                    temp['product_image'] = i['product_image']
                temp['unit_price'] = j['mrp']
                temp['discount_in_percentage'] = j['discount_in_percentage']
                temp['purchase_price'] = j['purchase_price']
                temp['package_type'] = j['package_type']
                temp['gst'] = j['gst']
                temp['mrp'] = j['mrp']
                temp['package_id'] = j['package_id']
                output.append(temp)
    return jsonify({"status": True, 'message': (city_name + ' new_arrival product details'), 'result': output})


# --------------------------------------------- Get app banners based on city ------------------------------------------
@app.route("/owo/get_app_banner_based_on_city", methods=['POST'])
@jwt_required
def getappbannersbasedoncity():
    data = mongo.db.OWO
    db = data.banners
    output = []
    city_name = request.json['city_name']
    hstb = []
    hsbb = []
    hstc20 = []
    hstc10 = []
    tb = []
    hsumla = []
    for i in db.find():
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        if str(city) == str(city_name):
            s_name = i['screen_name']
            if s_name == "Home_screen_top_banner":
                hstb.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_brand_banner":
                hsbb.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_top_categories_20_ltrs":
                hstc20.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_top_categories_10_ltrs":
                hstc10.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Trending_brands":
                tb.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_you_may_also_like":
                hsumla.append({'image': i['banner_image'], 'order': i['order']})
    hsbb = sorted(hsbb, key=lambda i: i['order'])
    hstb = sorted(hstb, key=lambda i: i['order'])
    hstc20 = sorted(hstc20, key=lambda i: i['order'])
    hstc10 = sorted(hstc10, key=lambda i: i['order'])
    tb = sorted(tb, key=lambda i: i['order'])
    hsumla = sorted(hsumla, key=lambda i: i['order'])
    return jsonify({'status': True, 'message': 'get banners success',  'Home_screen_top_banner': hstb,
                    'Home_screen_brand_banner': hsbb, 'Home_screen_top_categories_20_ltrs': hstc20,
                    'Home_screen_top_categories_10_ltrs': hstc10, 'Trending_brands': tb, 'Home_screen_you_may_also_like': hsumla})


# --------------------------------------------- city based home screen -------------------------------------------------
@app.route("/owo/home_screen_details", methods=['POST'])
@jwt_required
def homescreendetails():
    data = mongo.db.OWO
    db_b = data.banners
    db_p = data.products
    db_c = data.companies
    db_cat = data.category
    youmaylike = []
    category = []
    brands = []
    trendingbrand = []
    new_arrival = []
    cat20 = []
    cat10 = []
    city_name = request.json['city_name']
    hstb = []
    hsbb = []
    hstc20 = []
    hstc10 = []
    tb = []
    hsumla = []
    for i in db_b.find():
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        if str(city) == str(city_name):
            s_name = i['screen_name']
            if s_name == "Home_screen_top_banner":
                hstb.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_brand_banner":
                hsbb.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_top_categories_20_ltrs":
                hstc20.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_top_categories_10_ltrs":
                hstc10.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Trending_brands":
                tb.append({'image': i['banner_image'], 'order': i['order']})
            if s_name == "Home_screen_you_may_also_like":
                hsumla.append({'image': i['banner_image'], 'order': i['order']})
    hsbb = sorted(hsbb, key=lambda i: i['order'])
    hstb = sorted(hstb, key=lambda i: i['order'])
    hstc20 = sorted(hstc20, key=lambda i: i['order'])
    hstc10 = sorted(hstc10, key=lambda i: i['order'])
    tb = sorted(tb, key=lambda i: i['order'])
    hsumla = sorted(hsumla, key=lambda i: i['order'])
    for i in db_cat.find({'active_category': True}):
        city_name = city_name.lower()
        city = i['available_city']
        city = city.lower()
        if str(city_name) == str(city):
            temp = {}
            temp['order'] = i['order']
            temp['available_city'] = i['available_city']
            temp['category_id'] = i['category_id']
            temp['category_image'] = i['category_image']
            temp['category_type'] = i['category_type']
            temp['active_category'] = i['active_category']
            category.append(temp)
    category = sorted(category, key=lambda i: i['order'])
    for i in db_c.find():
        try:
            brand = i['brand']
            for j in brand:
                city = j['available_city']
                active_status = j['active_status']
                city = city.lower()
                city_name = city_name.lower()
                if str(city_name) == str(city) and active_status is True:
                    temp = {}
                    temp['brand_id'] = j['brand_id']
                    temp['brand_name'] = j['brand_name']
                    temp['brand_photo'] = j['brand_photo']
                    temp['brand_description'] = j['brand_description']
                    temp['order'] = j['order']
                    brands.append(temp)
        except KeyError or ValueError:
            pass
    brands = sorted(brands, key=lambda i: i['order'])
    for i in db_c.find({'brand.trending_brand': True}):
        try:
            brand = i['brand']
            for j in brand:
                city = j['available_city']
                active_status = j['active_status']
                trending_brand = j['trending_brand']
                city = city.lower()
                city_name = city_name.lower()
                if str(city_name) == str(city) and active_status is True and trending_brand is True:
                    temp = {}
                    temp['brand_id'] = j['brand_id']
                    temp['brand_name'] = j['brand_name']
                    temp['brand_photo'] = j['brand_photo']
                    temp['brand_description'] = j['brand_description']
                    temp['order'] = j['order']
                    trendingbrand.append(temp)
                    # print(trendingbrand)
        except KeyError or ValueError:
            pass
    trendingbrand = sorted(trendingbrand, key=lambda i: i['order'])
    details = db_p.find({'new_arrival': True, 'active_status': True})
    for i in details:
        p_type = i['package_type']
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        active_status = i['active_status']
        if str(city_name) == str(city) and active_status is True:
            for j in p_type:
                temp = {}
                temp['company_name'] = i['company_name']
                temp['brand_name'] = i['brand_name']
                temp['product_id'] = i['product_id']
                temp['product_name'] = i['product_name']
                temp['discount_in_percentage'] = j['discount_in_percentage']
                temp['expiry_date'] = j['expiry_date']
                # temp['active_status'] = active_status
                temp['unit_price'] = j['mrp']
                temp['purchase_price'] = j['purchase_price']
                if 'product_image' not in i.keys():
                    temp['product_image'] = '',
                else:
                    temp['product_image'] = i['product_image']
                temp['return_policy'] = j['return_policy']
                temp['package_type'] = j['package_type']
                temp['package_id'] = j['package_id']
                new_arrival.append(temp)
    details1 = db_p.find({'you_may_also_like': True, 'active_status': True})
    for i in details1:
        p_type = i['package_type']
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        active_status = i['active_status']
        if str(city_name) == str(city) and active_status is True:
            for j in p_type:
                temp = {}
                temp['company_name'] = i['company_name']
                temp['brand_name'] = i['brand_name']
                temp['product_id'] = i['product_id']
                temp['product_name'] = i['product_name']
                temp['discount_in_percentage'] = j['discount_in_percentage']
                temp['expiry_date'] = j['expiry_date']
                # temp['active_status'] = active_status
                temp['unit_price'] = j['mrp']
                temp['purchase_price'] = j['purchase_price']
                if 'product_image' not in i.keys():
                    temp['product_image'] = '',
                else:
                    temp['product_image'] = i['product_image']
                temp['return_policy'] = j['return_policy']
                temp['package_type'] = j['package_type']
                temp['package_id'] = j['package_id']
                youmaylike.append(temp)
    details2 = db_p.find({'active_status': True})
    for i in details2:
        p_type = i['package_type']
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        active_status = i['active_status']
        if str(city_name) == str(city):
            for j in p_type:
                if str(j['package_type']) == '10 Litres':
                    temp = {}
                    temp['company_name'] = i['company_name']
                    temp['brand_name'] = i['brand_name']
                    temp['product_id'] = i['product_id']
                    temp['product_name'] = i['product_name']
                    temp['discount_in_percentage'] = j['discount_in_percentage']
                    temp['expiry_date'] = j['expiry_date']
                    # temp['active_status'] = active_status
                    temp['unit_price'] = j['mrp']
                    temp['purchase_price'] = j['purchase_price']
                    if 'product_image' not in i.keys():
                        temp['product_image'] = '',
                    else:
                        temp['product_image'] = i['product_image']
                    temp['return_policy'] = j['return_policy']
                    temp['package_type'] = j['package_type']
                    temp['package_id'] = j['package_id']
                    cat10.append(temp)
    details3 = db_p.find({'active_status': True})
    for i in details3:
        p_type = i['package_type']
        city = i['city_name']
        city = city.lower()
        city_name = city_name.lower()
        active_status = i['active_status']
        if str(city_name) == str(city):
            for j in p_type:
                if str(j['package_type']) == '20 Litres':
                    temp = {}
                    temp['company_name'] = i['company_name']
                    temp['brand_name'] = i['brand_name']
                    temp['product_id'] = i['product_id']
                    temp['product_name'] = i['product_name']
                    temp['discount_in_percentage'] = j['discount_in_percentage']
                    temp['expiry_date'] = j['expiry_date']
                    # temp['active_status'] = active_status
                    temp['unit_price'] = j['mrp']
                    temp['purchase_price'] = j['purchase_price']
                    if 'product_image' not in i.keys():
                        temp['product_image'] = '',
                    else:
                        temp['product_image'] = i['product_image']
                    temp['return_policy'] = j['return_policy']
                    temp['package_type'] = j['package_type']
                    temp['package_id'] = j['package_id']
                    cat20.append(temp)
    return jsonify({'status': True, 'message': 'get banners success',  'Home_screen_top_banner': hstb,
                    'Home_screen_brand_banner': hsbb, 'Home_screen_top_categories_20_ltrs': hstc20,
                    'Home_screen_top_categories_10_ltrs': hstc10, 'Trending_brands': tb, 'Home_screen_you_may_also_like': hsumla,
                    'category': category, 'trending_brand': trendingbrand, 'youmaylike': youmaylike,
                    "new_arrival": new_arrival, 'category_10_liters_products': cat10, 'brand': brands,
                    'category_20_liters_products': cat20})


#----------------------------------------------- Get category ----------------------------------------------------------
@app.route('/owo/get_category_based_on_city', methods=['POST'])
@jwt_required
def getcategorybasedoncity():
    data = mongo.db.OWO
    db = data.category
    output = []
    city_name = request.json['city_name']
    for i in db.find({'active_category': True}):
        city_name = city_name.lower()
        city = i['available_city']
        city = city.lower()
        if str(city_name) == str(city):
            temp = {}
            temp['available_city'] = city
            temp['category_id'] = i['category_id']
            temp['category_image'] = i['category_image']
            temp['category_type'] = i['category_type']
            output.append(temp)
    return jsonify({'status': True, 'message': (city_name + ' category details'), 'result': output})


#--------------------------------------------------- Cancel Plans -------------------------------------------------------
@app.route('/owo/cancel_plans', methods=['POST'])
def cancelOrders():
    data = mongo.db.OWO
    db1= data.event_management
    db2 = data.instant_delivery_management
    db3 = data.owo_users_wallet
    db = data.product_subscription_test
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    wallet_id = request.json['wallet_id']
    #subscription_amount = int()
    #total_amount = int()
    #instant_amount = int()
    c_balance = int()
    wallet_amount = []
    for i in db.find({'user_id':user_id,'signin_type':signin_type}):
        subscription_id = i['subscription_id']
        db.update_many({'subscription_id':subscription_id},{'$set':{'subscription_status':"cancelled"}})
        for k in db1.find({'user_id':user_id,'signin_type':signin_type,'order_status':"confirmed"}):
            event_id = k['event_id']
            total_amount = k['sub_total']
            db1.update_many({'event_id': event_id}, {'$set': {'order_status': "cancelled"}})
            for l in db2.find({'user_id':user_id,'signin_type':signin_type,'order_status':"confirmed"}):
                instant_id = l['instant_id']
                instant_amount = l['sub_total']
                db2.update_many({'instant_id':instant_id},{'$set':{'order_status': "cancelled"}})
                for j in db3.find({'subscription_id':subscription_id}):
                    subscription_amount = j['subscription_amount']
                    current_balance =j['current_balance']
                    c_balance = current_balance+subscription_amount+instant_amount+total_amount
                    db3.update_many({'wallet_id':wallet_id},{'$set':{'current_balance':c_balance,'subscription_amount':subscription_amount}})
                    #output.append({'subscription_amount':subscription_amount,'event_amount':total_amount,'instant_amount':instant_amount,'current_balance':c_balance})
    wallet_amount.append({'current_balance':c_balance})
    return jsonify({'status': True, 'message': 'you have cancelled your orders',
                                'result':wallet_amount})


#--------------------------------------------- Default address cancel Orders--------------------------------------------
@app.route('/owo/default_address_cancelOrders', methods=['POST'])
@jwt_required
def setDefaultCancelOrders():
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    db2= data.event_management
    db3 = data.instant_delivery_management
    db4 = data.owo_users_wallet
    db5= data.product_subscription_test
    output = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    address_id = request.json['address_id']
    wallet_id = request.json['wallet_id']
    transaction_time_stamp = datetime.datetime.now()
    transaction_type = "orderscancellation"
    payment_type = "refund"
    order_id = transaction_type[:8].upper() + str(random.randint(100000, 999999))
    transaction_id = order_id
    c_balance = int()
    total_amount = int()
    instant_amount = int()

    if str(signin_type) == 'corporate':
        for i in db.find({'user_id':int(user_id),'signin_type':str(signin_type)}):
            u_id = i['user_id']
            if int(u_id) == int(user_id):
                print("ok userid")
                try:
                    u_address = i['user_address']
                    for j in u_address:
                        d_address = j['default_address']
                        a_id = j['address_id']
                        print("ok address")
                        if int(a_id) == int(address_id):
                            if d_address == True:
                                return jsonify({'status': False, 'message': 'address_already set as default address',
                                                'result': output})
                        else:
                            print("address_not_found")
                            db.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                           {'$set': {'user_address.$[].default_address': False}})
                            db.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                           {'$set': {'user_address.$.default_address': True}})
                            output.append({'user_id': user_id, 'address_id': address_id, 'default_address': True})
                            for s_id in db5.find({'user_id':int(user_id),'signin_type':str(signin_type)}):
                                subscription_id = s_id['subscription_id']
                                print(subscription_id)
                                db5.update_many({'subscription_id': int(subscription_id)},
                                               {'$set': {'subscription_status': "cancelled",
                                                         'payment_status': 'refund'}})
                                try:
                                    db5.update_many({'subscription_id':subscription_id},{'$set': {'products.$[].product_status': "disabled"}})
                                    # db5.update_many({'subscription_id': subscription_id},
                                    #             {'$unset': {'products': ""}})
                                except KeyError or ValueError:
                                    pass
                            for k in db2.find({'user_id':int(user_id),'signin_type':str(signin_type),
                                                   'order_status': "confirmed"}):
                                event_id = k['event_id']
                                total_amount = int(k['sub_total'])
                                db2.update_many({'event_id': int(event_id)}, {'$set': {'order_status': "cancelled"
                                                                                      ,'delivery_status':"cancelled"}})
                            for l in db3.find({'user_id':int(user_id),'signin_type':str(signin_type),
                                                       'order_status': "confirmed"}):
                                instant_id = l['instant_id']
                                instant_amount = int(l['sub_total'])
                                db3.update_many({'instant_id': int(instant_id)},
                                                {'$set': {'order_status': "cancelled"
                                                                  ,'delivery_status':"cancelled"}})
                            for m in db4.find({'wallet_id': int(wallet_id)}):
                                subscription_amount = m['subscription_amount']
                                current_balance = m['current_balance']
                                a = current_balance - subscription_amount
                                c_balance = current_balance + int(instant_amount) + int(total_amount)
                                refund_amount = subscription_amount + int(instant_amount) + int(total_amount)
                                db4.update_many({'wallet_id': int(wallet_id)}, {
                                    '$set': {'current_balance': c_balance,
                                             'subscription_amount':0},
                                    '$push': {'recent_transactions':
                                                  {'amount':refund_amount,
                                                   'payment_type':payment_type,
                                                   'transaction_id':transaction_id,
                                                   'transaction_type':transaction_type,
                                                   'transaction_date': transaction_time_stamp,
                                                   'order_id':order_id,
                                                   'status':"success",
                                                   'current_balance': current_balance,
                                                   'closing_balance': a + refund_amount}}})
                                print("ok_wallet")
                                # output.append({'subscription_amount':subscription_amount,'event_amount':total_amount,'instant_amount':instant_amount,'current_balance':c_balance})
                            message = 'Your default address is changed,your orders got cancelled, your updated wallet balance is Rs.%d' % c_balance
                            return jsonify({'status': True, 'message': message, 'result': output})
                except KeyError or ValueError:
                    u_address = ''
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    elif str(signin_type) == 'individual':
        for ind in db1.find({'user_id':int(user_id),'signin_type':str(signin_type)}):
            u_id = ind['user_id']
            if int(u_id) == int(user_id):
                print("ok user")
                try:
                    u_address = ind['user_address']
                    for j in u_address:
                        d_address = j['default_address']
                        a_id = j['address_id']
                        print("ok1")
                        if int(a_id) == int(address_id):
                            if d_address == True:
                                print("ok address")
                                return jsonify({'status': False, 'message': 'address_already set as default address',
                                                'result': output})
                        else:
                            print("not ok")
                            db1.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                           {'$set': {'user_address.$[].default_address': False}})
                            db1.update_many({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                           {'$set': {'user_address.$.default_address': True}})
                            output.append({'user_id': int(user_id), 'address_id': address_id, 'default_address': True})
                            for s_id in db5.find({'user_id':int(user_id),'signin_type':str(signin_type)}):
                                subscription_id = s_id['subscription_id']
                                db5.update_many({'subscription_id': int(subscription_id)},
                                               {'$set': {'subscription_status': "cancelled",
                                                         'payment_status': 'refund'}})
                                try:
                                    db5.update_many({'subscription_id': int(subscription_id)},
                                                    {'$set': {'products.$[].product_status': "disabled"}})
                                    # db5.update_many({'subscription_id': int(subscription_id)},
                                    #                 {'$unset': {'products': ""}})
                                except KeyError or ValueError:
                                    pass
                            for k in db2.find({'user_id':int(user_id),'signin_type':str(signin_type),
                                                   'order_status': "confirmed"}):
                                event_id = k['event_id']
                                total_amount = k['sub_total']
                                db2.update_many({'event_id': int(event_id)}, {'$set': {'order_status': "cancelled"
                                                                                      ,'delivery_status':"cancelled"}})
                            for l in db3.find({'user_id':int(user_id),'signin_type':str(signin_type),
                                                       'order_status': "confirmed"}):
                                instant_id = l['instant_id']
                                instant_amount = l['sub_total']
                                db3.update_many({'instant_id': int(instant_id)},
                                                {'$set': {'order_status': "cancelled"
                                                          ,'delivery_status':"cancelled"}})
                            for m in db4.find({'wallet_id': int(wallet_id)}):
                                subscription_amount = m['subscription_amount']
                                current_balance = m['current_balance']
                                a = current_balance - subscription_amount
                                c_balance = current_balance + instant_amount + total_amount
                                refund_amount = int(subscription_amount)+int(instant_amount)+int(total_amount)
                                print(c_balance)
                                db4.update_many({'wallet_id': int(wallet_id)}, {
                                    '$set': {'current_balance': c_balance,
                                             'subscription_amount': 0}, '$push': {
                                        'recent_transactions': {'amount': refund_amount,
                                                                'payment_type': payment_type,
                                                                'transaction_id': transaction_id,
                                                                'transaction_type': transaction_type,
                                                                'transaction_date': transaction_time_stamp,
                                                                'order_id': order_id,
                                                                'status': "success",
                                                                'current_balance': current_balance,
                                                                'closing_balance': a + refund_amount}}})
                                # output.append({'subscription_amount':subscription_amount,'event_amount':total_amount,'instant_amount':instant_amount,'current_balance':c_balance})
                            message = 'Your default address is changed,your orders got cancelled, your updated wallet balance is Rs.%d' % c_balance
                            return jsonify({'status': True, 'message': message, 'result': output})
                except KeyError or ValueError:
                    u_address = ''
        return jsonify({'status': False, 'message': 'invalid user_id', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid signin_type', 'result': output})


#---------------------------------------------- checking same city -----------------------------------------------------
@app.route('/owo/checking_same_city', methods=['POST'])
def checkingsamecity():
    data = mongo.db.OWO
    db = data.corporate_users
    db1 = data.individual_users
    output = []
    d_city = ''
    city = ''
    user_id = request.json['user_id']
    address_id = request.json['address_id']
    signin_type = request.json['signin_type']
    if str(signin_type) == "individual":
        for i in db1.find({'user_id': int(user_id)}):
            try:
                u_address = i['user_address']
                for j in u_address:
                    d_address = j['default_address']
                    a_id = (j['address_id'])
                    if int(address_id) == a_id:
                        city = j['city_name']
                    if d_address is True:
                        d_city = j['city_name']
                d_city = d_city.lower()
                city = city.lower()
                if d_city in city:
                    output.append(
                        {'user_id': user_id, 'address_id': address_id, 'sighin_type': signin_type, 'city_name': city})
                    return jsonify({'status': True, 'message': 'city name is same', 'result': output})
                elif d_city != city:
                    return jsonify({'status': False, 'message': 'city name is not matched', 'result': output})
            except KeyError or ValueError:
                pass
    elif str(signin_type) == "corporate":
        for i in db.find({'user_id': int(user_id)}):
            try:
                u_address = i['user_address']
                for j in u_address:
                    d_address = j['default_address']
                    a_id = (j['address_id'])
                    if int(address_id) == a_id:
                        city = j['city_name']
                    if d_address is True:
                        d_city = j['city_name']
                d_city = d_city.lower()
                city = city.lower()
                if d_city in city:
                    output.append(
                        {'user_id': user_id, 'address_id': address_id, 'sighin_type': signin_type, 'city_name': city})
                    return jsonify({'status': True, 'message': 'city name is same', 'result': output})
                elif d_city != city:
                    return jsonify({'status': False, 'message': 'city name is not matched', 'result': output})
            except KeyError or ValueError:
                pass
    return jsonify({'status': False, 'message': 'invalid signin type', 'result': output})


#---------------------------------------- checking city available ------------------------------------------------------
@app.route('/owo/checking_city_available', methods=['POST'])
@jwt_required
def checkingcityavailable():
    data = mongo.db.OWO
    db = data.city_management
    output = []
    city_name = request.json['city_name']
    for i in db.find():
        city_name = city_name.lower()
        city = i['city_name']
        city = city.lower()
        if city_name == city:
            output.append({'city_name': i['city_name']})
            return jsonify({'status': True, 'message': 'city name', 'result': output})
    return jsonify({'status': False, 'message': 'city not found', 'result': output})


#--------------------------------------------------  Membership --------------------------------------------------------
@app.route('/owo/membership', methods=['POST'])
@jwt_required
def memberShip():
    data = mongo.db.OWO
    db = data.membership
    db_sub = data.product_subscription_test
    output = []

    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    b1 = 0

    for i in db_sub.find({'payment_status': "success"}):
        id = i['user_id']
        e_id = i['email_id']
        m_num = i['mobile_number']
        s_type = i['signin_type']
        buy_plan = i['buy_plan']
        s_id = i['subscription_id']
        if str(user_id) == str(id) and str(signin_type) == str(s_type):
            try:
                osp = i['old_subscription_plan']
                for a in osp:
                    b_plan = a['buy_plan']
                    b1 += b_plan
                    print(b1)
                    print('ok')
                if 29 < b1 < 90:
                    for j in db.find():
                        uid = j['user_id']
                        stype = j['signin_type']
                        if str(user_id) == str(uid) and str(stype) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Silver Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type, 'membership': 'Silver Membership'})
                            return jsonify(
                                {'status': True, 'message': 'Congrats you won Silver Membership', 'result': output})
                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Silver Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Silver Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Silver Membership', 'result': output})

                elif 89 < b1 < 180:
                    for j in db.find():
                        uid = j['user_id']
                        stype = j['signin_type']
                        if str(user_id) == str(uid) and str(stype) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Gold Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type,
                                           'membership': 'Gold Membership'})
                            return jsonify({'status': True, 'message': 'Congrats you won gold membership', 'result': output})

                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Gold Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Gold Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Gold Membership', 'result': output})

                elif 179 < b1 < 270:
                    for j in db.find():
                        uid = j['user_id']
                        stype = j['signin_type']
                        if str(user_id) == str(uid) and str(stype) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Platinum Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type,
                                           'membership': 'Platinum Membership'})
                            return jsonify({'status': True, 'message': 'Congrats you won platinum membership',
                                            'result': output})
                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Platinum Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Platinum Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Platinum Membership', 'result': output})

                elif b1 > 269:
                    for j in db.find():
                        uid = j['user_id']
                        stype = j['signin_type']
                        if str(user_id) == str(uid) and str(stype) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Titanium Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type,
                                           'membership': 'Titanium Membership'})
                            return jsonify({'status': True, 'message': 'Congrats you won Titanium membership',
                                            'result': output})
                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Titanium Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Titanium Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Titanium Membership', 'result': output})

            except KeyError or ValueError:
                b1 = buy_plan
                if 29 < b1 < 90:
                    for j in db.find():
                        u1id = j['user_id']
                        s1type = j['signin_type']
                        if str(user_id) == str(u1id) and str(s1type) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Silver Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type,
                                 'membership': 'Silver Membership'})
                            return jsonify({'status': True, 'message': 'Congrats you won Silver Membership', 'result': output})
                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Silver Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Silver Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Silver Membership', 'result': output})

                elif 89 < b1 < 180:
                    for j in db.find():
                        u1id = j['user_id']
                        s1type = j['signin_type']
                        if str(user_id) == str(u1id) and str(s1type) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Gold Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type,
                                           'membership': 'Gold Membership'})
                            return jsonify({'status': True, 'message': 'Congrats you won gold membership', 'result': output})

                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Gold Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Gold Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Gold Membership', 'result': output})

                elif 179 < b1 < 270:
                    for j in db.find():
                        u1id = j['user_id']
                        s1type = j['signin_type']
                        if str(user_id) == str(u1id) and str(s1type) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Platinum Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type,
                                           'membership': 'Platinum Membership'})
                            return jsonify({'status': True, 'message': 'Congrats you won platinum membership',
                                            'result': output})
                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Platinum Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Platinum Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Platinum Membership', 'result': output})

                elif b1 > 269:
                    for j in db.find():
                        u1id = j['user_id']
                        s1type = j['signin_type']
                        if str(user_id) == str(u1id) and str(s1type) == str(signin_type):
                            db.find_one_and_update({'user_id': user_id, 'signin_type': signin_type},
                                                   {'$set': {'membership': 'Titanium Membership'}})
                            output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num,
                                           'signin_type': signin_type,
                                           'membership': 'Titanium Membership'})
                            return jsonify({'status': True, 'message': 'Congrats you won Titanium membership',
                                            'result': output})
                    db.insert({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                               'membership': 'Titanium Membership', 'subscription_id': s_id})
                    output.append({'user_id': user_id, 'email_id': e_id, 'mobile_number': m_num, 'signin_type': signin_type,
                                   'membership': 'Titanium Membership', 'subscription_id': s_id})
                    return jsonify({'status': True, 'message': 'Congrats you won Titanium Membership', 'result': output})
    return jsonify({'status': False, 'message': 'you do not have subscription yet', 'result': output})


#----------------------------------------------- Get membership  ------------------------------------------------------
@app.route('/owo/get_membership', methods = ['POST'])
@jwt_required
def getMembership():
    data = mongo.db.OWO
    db = data.membership
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    output = []

    for i in db.find({'user_id':user_id,'signin_type':signin_type}):
        member_ship = i['membership']
        output.append({'membership':member_ship})
        return jsonify({'status': True, 'message':'membership details','result': output})
    return jsonify({'status': False, 'message': 'currently you dont have a membership', 'result': output})


#------------------------------------------- Get loyalty redeem points -------------------------------------------------
@app.route('/owo/get_loyalty_redeemed/<user_id>/<signin_type>', methods=['GET'])
def loyaltyRedeemed(user_id, signin_type):
    data = mongo.db.OWO
    db = data.loyalty
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        r_earning = i['recent_earnings']
        if str(s_type) == str(signin_type) and int(u_id) == int(user_id):
            for j in r_earning:
                e_type = j['earn_type']
                if str(e_type) == 'instant' or str(e_type) == 'event' or str(e_type) == 'subscription':
                    temp = {}
                    temp['order_type'] = j['order_type']
                    temp['order_id'] = j['order_id']
                    temp['transaction_date'] = j['earn_date']
                    temp['current_balance'] = i['current_balance']
                    temp['redeemed_points'] = j['order_value']
                    temp['closing_balance'] = j['closing_balance']
                    output.append(temp)
    return jsonify({'status': True, 'message': 'redeemed loyalty points', 'result': output})


#--------------------------------------------- Get all loyalty Transactions --------------------------------------------
@app.route('/owo/get_all_loyalty_transactions/<user_id>/<signin_type>', methods=['GET'])
def loyaltyRedeemed1(user_id, signin_type):
    data = mongo.db.OWO
    db = data.loyalty
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        r_earning = i['recent_earnings']
        if str(s_type) == str(signin_type) and int(u_id) == int(user_id):
            for j in r_earning:
                e_type = j['earn_type']
                if j['loyalty_type'] == 'redeemed':
                    order_type = j['earn_type']
                    transaction_id = j['transaction_id']
                    transaction_date = j['earn_date']
                    current_balance = i['loyalty_balance']
                    loyalty_points = j['order_value']
                    output.append({'order_type': order_type,'loyalty_type': 'redeemed', 'transaction_id': transaction_id,
                                   'transaction_date': transaction_date,
                                   'current_balance': current_balance, 'loyalty_points': loyalty_points})
                if j['loyalty_type'] == "earned":
                    try:
                        order_type = j['earn_type']
                    except KeyError or ValueError:
                        order_type = ''
                    try:
                        transaction_id = j['transaction_id']
                    except KeyError or ValueError:
                        transaction_id = ''
                    transaction_date = j['earn_date']
                    current_balance = i['loyalty_balance']
                    loyalty_points = j['earn_points']
                    output.append({'order_type': order_type, 'loyalty_type': 'earned', 'transaction_id': transaction_id, 'transaction_date': transaction_date,
                                   'current_balance': current_balance, 'loyalty_points': loyalty_points})
    return jsonify({'status': True, 'message': 'All loyalty points transactions data get successfully', 'result': output})


#------------------------------------------------------ Subscription Management ----------------------------------------
@app.route('/owo/add_multipleProducts', methods=['POST'])
@jwt_required
def addMultipleProductsSubcription():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db_cu = data.corporate_users
    db_iu = data.individual_users
    mobile_number = int()
    email_id = str()
    output = []
    user_id = request.json['user_id']
    products = request.json['products']
    signin_type = request.json['signin_type']
    try:
        subscription_id_list = [i['subscription_id'] for i in db.find()]
        if len(subscription_id_list) is 0:
            subscription_id = 1
        else:
            subscription_id = int(subscription_id_list[-1]) + 1
    except KeyError or ValueError:
        subscription_id = int(1)
    # for j in db_cu.find():
    #     for k in db_iu.find():
    #         for l in j, k:
    #             if str(signin_type) == str(l['signin_type']) and int(user_id) == int(l['user_id']):
    #                 print(user_id)
    #                 print(signin_type)
    #                 mobile_number = l['mobile_number']
    #                 signin_type = l['signin_type']
    #                 email_id = l['email_id']

    if signin_type == "individual":
        for l in db_iu.find():
            if str(signin_type) == str(l['signin_type']) and int(user_id) == int(l['user_id']):
                mobile_number = l['mobile_number']
                signin_type = l['signin_type']
                email_id = l['email_id']
    elif signin_type == "corporate":
        for l in db_cu.find():
            if str(signin_type) == str(l['signin_type']) and int(user_id) == int(l['user_id']):
                mobile_number = l['mobile_number']
                signin_type = l['signin_type']
                email_id = l['email_id']

    for i in db.find():
        if str(signin_type) == str(i['signin_type']) and int(user_id) == int(i['user_id']):
            try:
                product = i['products']
            except KeyError or ValueError:
                product = []
            result_id = [dict(item, **{'product_status': "enabled"}) for item in products]
            prod = result_id
            lookup = {x['product_id']: x for x in prod}
            lookup.update({x['product_id']: x for x in product})
            result1 = list(lookup.values())
            print(result1)
            db.update_many({'subscription_id': i['subscription_id']},
                           {'$set': {'products': result1,
                                     'signin_type': signin_type, 'mobile_number': mobile_number,
                                     'email_id': email_id, 'subscription_status': "active"}})
            output.append({'user_id': user_id, 'signin_type': signin_type, 'products': products})
            return jsonify({'status': 'success', 'message': 'subscription to user updated successfully found',
                            'result': output})
    results_id = [dict(item, **{'product_status': "enabled"}) for item in products]
    db.insert_one({'user_id': user_id, 'products': results_id, 'subscription_id': subscription_id,
                   'signin_type': signin_type, 'mobile_number': mobile_number,
                   'email_id': email_id, 'subscription_status': "active"})
    output.append({'user_id': user_id, 'signin_type': signin_type, 'products': products})
    return jsonify({'status': 'success', 'message': 'subscription for user added success', 'result': output})


@app.route('/owo/get_products_modify', methods=['POST'])
@jwt_required
def getSubscriptionProductsModify():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db1 = data.products
    output = []
    product_count = int()
    user_id = request.json['user_id']
    sub_id = int()
    signin_type = request.json['signin_type']
    frequency =str()
    buy_plan = int()
    subscription_id = int()
    for i in db.find({'user_id': int(user_id), 'signin_type': str(signin_type)}):
        u_id = i['user_id']
        s_type = i['signin_type']
        subscription_id = i['subscription_id']
        try:
           frequency = i['frequency']
        except KeyError or ValueError:
            frequency = ""
        try:
           buy_plan = i['buy_plan']
        except KeyError or ValueError:
            buy_plan = 0
        if int(user_id) == int(u_id) and str(signin_type) == str(s_type):
            try:
                products = i['products']
                for j in products:
                    p_id = j['product_id']
                    # if j['product_status'] == "enabled":
                    try:
                        set_quantity = j['set_quantity']
                    except KeyError or ValueError:
                        set_quantity = []
                    for k in db1.find():
                        p_type = k['package_type']
                        if str(p_id) == str(k['product_id']):
                            product_count += 1
                            if 'product_image' not in k.keys():
                                product_image = '',
                            else:
                                product_image = k['product_image']
                            package_type = ''
                            u_price = 0
                            for l in p_type:
                                u_price = l['unit_price']
                                if 'package_type' not in l.keys():
                                    package_type = '',
                                else:
                                    package_type = l['package_type']
                            output.append({'product_id': p_id, 'product_images': product_image, 'user_id': u_id,
                                               'signin_type': signin_type, 'product_name': k['product_name'],
                                               'package_type': package_type,
                                               'starting_date': i['starting_date'],
                                               'plan_expiry_date': i['plan_expiry_date'],
                                               'set_quantity': set_quantity,
                                               'unit_price': u_price, 'purchase_price': j['purchase_price'],
                                               'subscription_id': i['subscription_id']})
            except KeyError or ValueError:
                pass
    return jsonify({'status': True, 'message': 'get images by subscription product_', 'result': output,
                    'frequency': frequency, 'buy_plan': buy_plan,
                    'count': product_count, 'subscription_id': subscription_id})


@app.route('/owo/get_carttotal', methods=['POST'])
# @jwt_required
def cartTotal():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    output = []
    output1 = []
    gstprice = []
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    products = request.json['products']
    signin_type = request.json['signin_type']
    buy_plan = request.json['buy_plan']
    starting_date = request.json['starting_date']
    s_date = datetime.datetime.strptime(starting_date, "%Y-%m-%d")
    modified_date = s_date + datetime.timedelta(days=buy_plan)
    plan_expiry_date = datetime.datetime.strftime(modified_date, "%Y-%m-%d")
    start_day = request.json['start_day']
    subscription_id = request.json['subscription_id']
    frequency = request.json['frequency']
    product_count = []
    wallet_id = request.json['wallet_id']
    wallet_amount = int()
    required_amount = int()
    for wallet in db_wallet.find({'wallet_id': wallet_id}):
        wallet_amount = wallet['current_balance']
    for i in products:
        set_quantity = i['set_quantity']
        purchase_price = i['purchase_price']
        total_price = calculatePrice(set_quantity, purchase_price, buy_plan, start_day)
        total_quantity = calculateProductQuant(buy_plan, start_day, set_quantity)
        print(total_quantity)
        product_count.append({'total_quantity': total_quantity})
        print(product_count)
        result2 = defaultdict(int)
        for elm in product_count:
            for k, v in elm.items():
                result2[k] += v
        print(result2)
        productcount = [result2[val] for val in result2 if result2[val] > 1]
        print(productcount)
        str3 = int(''.join(str(i) for i in productcount))
        print(str3)
        for j in db.find():
            if str(signin_type) == str(j['signin_type']) and int(user_id) == int(j['user_id']):
                id = j['subscription_id']
                print(subscription_id)
                result_id = [dict(item, **{'product_status': "enabled"}) for item in products]
                db.update_many({'subscription_id': int(subscription_id)}, {
                    '$set': {'products': result_id, 'buy_plan': buy_plan, 'starting_date': starting_date,
                             'start_day': start_day, 'plan_expiry_date': plan_expiry_date,
                             'subscription_status': "active", 'frequency': frequency}})
        output1.append({'total_price': round(total_price)})
        result = defaultdict(int)
        for elm in output1:
            for k, v in elm.items():
                result[k] += v
        print(result)
        total_cart_value = [result[val] for val in result if result[val] > 1]
        print(total_cart_value)
        str1 = int(''.join(str(i) for i in total_cart_value))
        print(str1)
        amount = str1
        delivery_charges = SubscriptionDelivery_charges(signin_type, amount)
        total_value = str1 + int(delivery_charges)
        print(total_value)
        if wallet_amount < total_value:
          required_amount = total_value - wallet_amount
          print(required_amount)
        total_cart_value = str1
        sub_details = getSubscriptionProductByDate(subscription_id, products, buy_plan, start_day)
        print(sub_details)
    db.update_many({'subscription_id': subscription_id}, {'$set': {'total_price': str1,
                                                                   'product_count': str3,
                                                                   'delivery_charges': delivery_charges}})
    output.append({'subscription_plan': buy_plan, 'delivery_charge': delivery_charges,
                   'total_cart_value': total_value,
                   'subscription_id': subscription_id, 'sub_total': str1})
    return jsonify({'status': "success", 'message': "success", 'result': output, 'required_balance': required_amount,
                    'current_wallet_balance': wallet_amount, 'product_details': sub_details})


@app.route('/owo/add_money_subscription', methods=['POST'])
# @jwt_required
def add_subscription_wallet():
    try:
        data = mongo.db.OWO
        db = data.owo_users_wallet
        db1 = data.product_subscription_test
        wallet_id = request.json['wallet_id']
        transaction_id = request.json['transaction_id']
        subscription_id = request.json['subscription_id']
        payment_type = request.json['payment_type']
        transaction_type = request.json['transaction_type']
        amount = request.json['amount']
        status = request.json['status']
        delivery_address = request.json['delivery_address']
        transaction_time_stamp = datetime.datetime.now()
        order_id = transaction_type[:5].upper() + str(random.randint(100000, 999999))
        recent_transactions = []
        ts = calendar.timegm(time.gmtime())
        w_s_type = "subscription-refund"
        order_refund = w_s_type[:].upper() + str(ts)
        output = []
        for j in db1.find({'subscription_id': subscription_id}):
             if status == "success":
                 for i in db.find({'wallet_id': wallet_id}):
                     if status == "success":
                         print(wallet_id)
                         print(i['wallet_id'])
                         try:
                            subscription_amount = i['subscription_amount']
                         except KeyError or ValueError:
                             subscription_amount = int()
                             c_b = i['current_balance']
                             db1.update_many({'subscription_id': subscription_id},
                                             {'$set': {'products.$[].cart_status': "deactive"}})
                             db1.update_many({'subscription_id': subscription_id}, {
                                 '$set': {'payment_status': status, 'is_subscribed': True, 'order_id': order_id,
                                          'transaction_id': transaction_id, 'delivery_address': delivery_address,
                                          'subscription_status': "active", 'transaction_date': transaction_time_stamp}})
                             db.update_many({'wallet_id': wallet_id}, {
                                 '$set': {'current_balance': c_b, 'subscription_id': subscription_id,
                                          'subscription_amount': amount}, '$push': {
                                     'recent_transactions': {'amount': amount, 'payment_type': payment_type,
                                                             'transaction_id': transaction_id,
                                                             'transaction_type': transaction_type,
                                                             'transaction_date': transaction_time_stamp,
                                                             'order_id': order_id, 'status': status,
                                                             'current_balance': c_b,
                                                             'closing_balance': c_b - amount}}})

                             output.append({'wallet_id': wallet_id, 'status': status, 'amount': amount,
                                            'transaction_id': transaction_id, 'payment_type': payment_type,
                                            'transaction_type': transaction_type,
                                            'transaction_date': transaction_time_stamp, 'order_id': order_id,
                                            'closing_balance': c_b})
                             SubscriptionSuccess(wallet_id, order_id)
                             SubscriptionSuccessEmail(wallet_id, order_id)
                             SubscriptionSuccessSMS(wallet_id, order_id)
                             return jsonify(
                                 {'status': 'success', 'result': output, 'message': 'subscription amount successfully'})
                         current_balance = i['current_balance']
                         if amount < subscription_amount:
                             remaining_balance = subscription_amount - amount
                             db1.update_many({'subscription_id': subscription_id},
                                             {'$set': {'products.$[].cart_status': "deactive"}})
                             db1.update_many({'subscription_id': subscription_id}, {
                                 '$set': {'payment_status': status, 'is_subscribed': True, 'order_id': order_id,
                                          'transaction_id': transaction_id, 'subscription_status': "active",
                                          'delivery_address': delivery_address, 'transaction_date': transaction_time_stamp}})
                             db.update_many({'wallet_id': wallet_id}, {
                                 '$set': {'current_balance': current_balance + remaining_balance ,
                                          'subscription_id': subscription_id,
                                          'subscription_amount': amount}, '$push': {
                                     'recent_transactions': {'amount': remaining_balance, 'payment_type': "refund",
                                                             'transaction_id': transaction_id,
                                                             'transaction_type': "subscription_refund",
                                                             'transaction_date': transaction_time_stamp,
                                                             'order_id': order_refund, 'status': status,
                                                             'current_balance': current_balance,
                                                             'closing_balance': current_balance - amount}}})
                             c_balance = i['current_balance']
                             db.update_many({'wallet_id': wallet_id},{'$set': {'current_balance': c_balance},
                                                                      '$push': {
                                     'recent_transactions': {'amount': amount, 'payment_type': "subscription",
                                                             'transaction_id': transaction_id,
                                                             'transaction_type': "subscription_modify",
                                                             'transaction_date': transaction_time_stamp,
                                                             'order_id': order_id, 'status': status,
                                                             'current_balance': c_balance,
                                                             'closing_balance': current_balance - amount}}})
                             for subs in db1.find({'subscription_id': subscription_id}):
                                 # old_subscription_plan.append({'user_id':subs['user_id'],'signin_type':subs['signin_type'],'buy_plan':subs['buy_plan'],'starting_date':subs['starting_date'],'plan_expiry_date':subs['plan_expiry_date'],'total_amount':subs['total_price'],'product_count':subs['product_count']})
                                 db1.update_many({'subscription_id': subscription_id}, {'$push': {
                                     'old_subscription_plan': {'user_id': subs['user_id'],
                                                               'signin_type': subs['signin_type'],
                                                               'buy_plan': subs['buy_plan'],
                                                               'starting_date': subs['starting_date'],
                                                               'plan_expiry_date': subs['plan_expiry_date'],
                                                               'total_amount': subs['total_price'],
                                                               'product_count': subs['product_count'],
                                                               'products': subs['products']}}})

                             output.append({'wallet_id': wallet_id, 'status': status, 'amount': remaining_balance,
                                            'transaction_id': transaction_id, 'payment_type': "refund",
                                            'transaction_type': "subscription_refund",
                                            'transaction_date': transaction_time_stamp, 'order_id': order_refund,
                                            'closing_balance': current_balance})
                             SubscriptionSuccess(wallet_id, order_id)
                             SubscriptionSuccessEmail(wallet_id,order_id)
                             SubscriptionSuccessSMS(wallet_id, order_id)
                             return jsonify(
                                 {'status': 'success', 'result': output, 'message': 'Amount refunded successfully'})
                         elif amount > current_balance:
                             return jsonify(
                                 {'status': 'failed', 'result': [], 'message': 'please refill your wallet to place order'})
                         else:
                             db1.update_many({'subscription_id': subscription_id},
                                             {'$set': {'products.$[].cart_status': "deactive"}})
                             db1.update_many({'subscription_id': subscription_id}, {
                                 '$set': {'payment_status': status, 'is_subscribed': True, 'order_id': order_id,
                                          'transaction_id': transaction_id, 'delivery_address': delivery_address,
                                          'subscription_status': "active", 'transaction_date': transaction_time_stamp}})
                             db.update_many({'wallet_id': wallet_id}, {
                                 '$set': {'current_balance': current_balance, 'subscription_id': subscription_id,
                                          'subscription_amount': amount}, '$push': {
                                     'recent_transactions': {'amount': amount, 'payment_type': payment_type,
                                                             'transaction_id': transaction_id,
                                                             'transaction_type': transaction_type,
                                                             'transaction_date': transaction_time_stamp,
                                                             'order_id': order_id, 'status': status,
                                                             'current_balance': current_balance,
                                                             'closing_balance': current_balance - amount}}})
                             for subs in db1.find({'subscription_id': subscription_id}):
                                 db1.update_many({'subscription_id': subscription_id},
                                                 {'$push':
                                                 {'old_subscription_plan':
                                                      {'user_id': subs['user_id'],
                                                       'signin_type': subs['signin_type'],
                                                       'buy_plan': subs['buy_plan'],
                                                       'starting_date': subs['starting_date'],
                                                       'plan_expiry_date': subs['plan_expiry_date'],
                                                       'total_amount': subs['total_price'],
                                                       'product_count': subs['product_count'],
                                                       'products': subs['products']
                                                       }
                                                  }
                                                  }
                                                 )
                             output.append({'wallet_id': wallet_id, 'status': status, 'amount': amount,
                                            'transaction_id': transaction_id, 'payment_type': payment_type,
                                            'transaction_type': transaction_type,
                                            'transaction_date': transaction_time_stamp, 'order_id': order_id,
                                            'closing_balance': current_balance})
                             SubscriptionSuccess(wallet_id, order_id)
                             SubscriptionSuccessEmail(wallet_id,order_id)
                             SubscriptionSuccessSMS(wallet_id, order_id)
                             return jsonify(
                                 {'status': 'success', 'result': output, 'message': 'Amount updated successfully'})
    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e), 'result': []})


@app.route('/owo/get_product_images_subscription', methods=['POST'])
@jwt_required
def getSubscriptionProductsImages():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db1 = data.products
    output = []
    product_count = int()
    user_id = request.json['user_id']
    sub_id = int()
    signin_type = request.json['signin_type']
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        if int(user_id) == int(u_id) and str(signin_type) == str(s_type):
            s_i = i['subscription_id']
            sub_id = s_i
            try:
                products = i['products']
                for j in products:
                    if j['product_status'] == "enabled":
                        if j['cart_status'] == "active" or j['cart_status'] == "deactive":
                            p_id = j['product_id']
                            for k in db1.find():
                                p_type = k['package_type']
                                if str(p_id) == str(k['product_id']):
                                    product_count += 1
                                    if 'product_image' not in k.keys():
                                        product_image = '',
                                    else:
                                        product_image = k['product_image']
                                    package_type = ''
                                    u_price = 0
                                    for l in p_type:
                                        u_price = l['unit_price']
                                        if 'package_type' not in l.keys():
                                            package_type = '',
                                        else:
                                            package_type = l['package_type']
                                    output.append({'product_id': p_id, 'product_images': product_image, 'user_id': u_id,
                                                   'signin_type': signin_type, 'product_name': k['product_name'],
                                                   'package_type': package_type,
                                                   'unit_price': u_price, 'purchase_price': j['purchase_price'],
                                                   'subscription_id': i['subscription_id']})
            except KeyError or ValueError:
                pass
    return jsonify(
        {'status': True, 'message': 'get images by subscription product_', 'result': output, 'count': product_count,
         'subscription_id': sub_id})


@app.route('/owo/delete_subscription_by_product_id', methods=['POST'])
@jwt_required
def deleteSubscriptionByProductId():
    try:
        data = mongo.db.OWO
        db = data.product_subscription_test
        db1 = data.products
        output = []
        user_id = request.json['user_id']
        signin_type = request.json['signin_type']
        product_id = request.json['product_id']
        p_id = []
        for i in db.find({'user_id':user_id,'signin_type':signin_type}):
            for j in i['products']:
                if j['product_id'] == product_id and j['cart_status'] == "deactive":
                    db.find_one_and_update({'user_id':user_id,
                                            'signin_type':signin_type,
                                            'products.product_id': str(product_id)},
                                           {'$set': {'products.$.product_status':"disabled"}})
                    p_id.append(product_id)
                    return jsonify({"status": True, 'message': "subscription for product_id deleted", 'result':p_id})
        db.find_one_and_update({'user_id':user_id,'signin_type':signin_type,
                                'products.product_id': str(product_id)},
                               {'$pull': {"products": {'product_id': str(product_id)}}})
        output.append(product_id)
        return jsonify({"status": True, 'message': "subscription for product_id deleted", 'result': output})
    except Exception as e:
        return jsonify({'status':False, 'message': str(e),'result':[]})


@app.route('/owo/get_list_bydate', methods=['POST'])
@jwt_required
def getSubscriptionProductsByDate():
    data = mongo.db.OWO
    db2 = data.subscription_history
    db = data.product_subscription_test
    db1 = data.products
    output = []
    res = []
    delivery_status = str()
    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    date = request.json['date']
    check_date = date
    day = request.json['day']
    subscription_status = str()
    subscription_id = int()
    order_id = str()
    for s_status in db.find({'user_id': int(user_id), 'signin_type': str(signin_type)}):
        subscription_status =  s_status['subscription_status']
        if subscription_status == 'cancelled' or subscription_status == 'expired':
            return jsonify({'status': False, 'message': 'your subscription orders got ' + subscription_status,
                            'result': [], 'subscription_status': subscription_status, 'order_id': ""})
    for sub_status in db.find({'user_id': int(user_id), 'signin_type': str(signin_type)}):
        is_sub = sub_status['is_subscribed']
        if is_sub is False:
            return jsonify({'status': False, 'message': "You dont have a subscription please select subscription",
                            'result': output})
    for s_id in db.find({'user_id': user_id, 'signin_type': signin_type}):
        subscription_id = s_id['subscription_id']
        # print(subscription_id)
    for ds in db2.find({'date': date}):
        if str(date) == str(ds['date']):
            for ord in ds['order_history']:
                if int(subscription_id) == int(ord['subscription_id']):
                    # print("ok3")
                    delivery_status = ord['delivery_status']
                    order_id = ord['order_id']
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        if int(user_id) == int(u_id) and str(signin_type) == str(s_type) and i['is_subscribed'] == True:
            subscription_status = i['subscription_status']
            payment_status = i['payment_status']
            if subscription_status == "active" and payment_status == "success" or subscription_status == 'pause':
                try:
                    for j in i['products']:
                        if j['cart_status'] == "deactive":
                            set_quantity = j['set_quantity']
                            plan_start_date = i['starting_date']
                            plan_expiry_date = i['plan_expiry_date']
                            plan_sd = plan_start_date
                            plan_ed = plan_expiry_date
                            if plan_sd <= check_date <= plan_ed:
                                for qua in set_quantity:
                                    mydict = qua
                                    for key in mydict:
                                        if key == day:
                                            quantity = mydict[key]
                                            p_i = j['purchase_price']
                                            total_price = p_i * quantity
                                            for k in db1.find():
                                                p_type = k['package_type']
                                                if str(j['product_id']) == str(k['product_id']):
                                                    if 'product_image' not in k.keys():
                                                        product_image = '',
                                                    else:
                                                        product_image = k['product_image']
                                                    for l in p_type:
                                                        u_price = l['unit_price']
                                                        if 'package_type' not in l.keys():
                                                            package_type = '',
                                                        else:
                                                            package_type = l['package_type']
                                                        s_id = i['subscription_id']
                                                        output.append(
                                                            {'product_id': j['product_id'], 'product_image': product_image,
                                                             'user_id': u_id,
                                                             'signin_type': signin_type, 'product_name': k['product_name'],
                                                             'subscription_id': i['subscription_id'],
                                                             'delivery_status': delivery_status,
                                                             'subscription_plan': i['buy_plan'],
                                                             'subscription_status': i['subscription_status'],
                                                             'package_type': package_type, 'product_quantity': quantity,
                                                             'product_total_price': total_price,
                                                             'unit_price': u_price, 'purchase_price': j['purchase_price']})
                                                        res = [i for i in output if not (i['product_quantity'] == 0)]
                except KeyError or ValueError:
                    pass
            else:
                return jsonify({'status': False, 'message': "You dont have a subscription please select subscription",
                                'result': output})
    return jsonify({'status': True, 'message': 'get images by subscription product',
                    'result': res, 'subscription_status': subscription_status, 'order_id': order_id})


# --------------------------------------- Get All Products based on sort function---------------------------------------
@app.route('/owo/sort_products_based_on_city', methods=['POST'])
@jwt_required
def SortgetProductsbasedoncity():
    data = mongo.db.OWO
    db = data.products
    db_r = data.rating
    output = []
    rating = 0
    product_no_of_ratings = 0
    city_name = request.json['city_name']
    sorting_type = request.json['sorting_type']
    if sorting_type == 'DESCENDING':
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                city = i['city_name']
                if 'product_image' not in i.keys():
                    product_image = []
                else:
                    product_image = i['product_image']
                city = city.lower()
                city_name = city_name.lower()
                if str(city) == str(city_name):
                    try:
                        p_type = i['package_type']
                        p_id = i['product_id']
                        for j in p_type:
                            purchase_price = j['purchase_price']
                            for k in db_r.find():
                                if p_id == k['product_id']:
                                    if 'current_rating' not in k.keys():
                                        rating = 0,
                                    else:
                                        rating = k['current_rating']
                                    if 'rating_history' not in k.keys():
                                        product_no_of_ratings = 0,
                                    else:
                                        product_no_of_ratings = len(k['rating_history'])
                            output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
                                           'product_image': product_image, 'available_quantity': i['product_quantity'],
                                           'brand_name': i['brand_name'], 'company_name': i['company_name'],
                                           'package_id': j['package_id'], 'product_rating': rating,
                                           'package_type': j['package_type'], 'purchase_price': purchase_price,
                                           'unit_price': j['mrp'], 'product_no_of_rating': product_no_of_ratings,
                                           'discount_in_percentage': j['discount_in_percentage'],
                                           'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
                            output.sort(reverse=True, key=lambda e: int(e['purchase_price']))
                    except KeyError or ValueError:
                        pass
        return jsonify({"status": True, 'message': 'get all products success', 'result': output})
    elif sorting_type == 'ASCENDING':
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                city = i['city_name']
                if 'product_image' not in i.keys():
                    product_image = []
                else:
                    product_image = i['product_image']
                city = city.lower()
                city_name = city_name.lower()
                if str(city) == str(city_name):
                    try:
                        p_type = i['package_type']
                        p_id = i['product_id']
                        for j in p_type:
                            for k in db_r.find():
                                if p_id == k['product_id']:
                                    if 'current_rating' not in k.keys():
                                        rating = 0,
                                    else:
                                        rating = k['current_rating']
                                    if 'rating_history' not in k.keys():
                                        product_no_of_ratings = 0,
                                    else:
                                        product_no_of_ratings = len(k['rating_history'])
                            output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
                                           'product_image': product_image, 'available_quantity': i['product_quantity'],
                                           'brand_name': i['brand_name'], 'company_name': i['company_name'],
                                           'package_id': j['package_id'], 'product_rating': rating,
                                           'package_type': j['package_type'], 'purchase_price': j['purchase_price'],
                                           'unit_price': j['mrp'], 'product_no_of_rating': product_no_of_ratings,
                                           'discount_in_percentage': j['discount_in_percentage'],
                                           'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
                            output.sort(reverse=False, key=lambda e: int(e['purchase_price']))
                    except KeyError or ValueError:
                        pass
        return jsonify({"status": True, 'message': 'get all products success', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid sorting type', 'result': output})


# --------------------------------------- Get sorted product by brand name ---------------------------------------------
@app.route('/owo/get_sorted_products_by_brand_name', methods=['POST'])
@jwt_required
def getSortedProductsByBrandName():
    data = mongo.db.OWO
    db = data.products
    db_r = data.rating
    output = []
    brand_name = request.json['brand_name']
    city_name = request.json['city_name']
    sorting_type = request.json['sorting_type']
    if sorting_type == "DESCENDING":
        for i in db.find({'city_name': city_name}):
            try:
                prd = i['package_type']
                for j in prd:
                    b_id = i['brand_name']
                    brand_name = brand_name.lower()
                    brands_name = b_id.lower()
                    if str(brand_name) == str(brands_name):
                        temp = {}
                        temp['brand_name'] = i['brand_name']
                        temp['company_name'] = i['company_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0,
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                            print(i['product_id'])
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=True, key=lambda e: int(e['purchase_price']))
            except KeyError or ValueError:
                pass
        return jsonify({"status": True, "message": "get products by brand_name success", 'result': output})
    elif sorting_type == 'ASCENDING':
        for i in db.find({'city_name': city_name}):
            try:
                prd = i['package_type']
                for j in prd:
                    b_id = i['brand_name']
                    brand_name = brand_name.lower()
                    brands_name = b_id.lower()
                    if str(brand_name) == str(brands_name):
                        temp = {}
                        temp['brand_name'] = i['brand_name']
                        temp['company_name'] = i['company_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0,
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                            print(i['product_id'])
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=False, key=lambda e: int(e['purchase_price']))
            except KeyError or ValueError:
                pass
        return jsonify({"status": True, "message": "get products by brand_name success", 'result': output})
    else:
        return jsonify({'status': False, 'message': 'invalid sorting_type', 'result': output})


#----------------------------------------------- get_sort_ products_by_product_type ------------------------------------
@app.route('/owo/get_sort_products_by_product_type', methods=['POST'])
@jwt_required
def getSortProductsByProductType():
    data = mongo.db.OWO
    db = data.products
    db_r = data.rating
    output = []
    city_name = request.json['city_name']
    package_type = request.json['package_type']
    sorting_type = request.json['sorting_type']
    if sorting_type == "DESCENDING":
        for i in db.find():
            a_status = i['active_status']
            if a_status is True:
                c_name = i['city_name']
                for j in i['package_type']:
                    p_type = j['package_type']
                    if str(package_type) == str(p_type) and str(c_name) == str(city_name):
                        temp = {}
                        temp['company_name'] = i['company_name']
                        temp['brand_name'] = i['brand_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=True, key=lambda e: int(e['purchase_price']))
        return jsonify({"status": True, 'message': "product details get by product_type success", 'result': output})
    elif sorting_type == 'ASCENDING':
        for i in db.find(sort=[('purchase_price', pymongo.DESCENDING)]):
            a_status = i['active_status']
            if a_status is True:
                c_name = i['city_name']
                for j in i['package_type']:
                    p_type = j['package_type']
                    if str(package_type) == str(p_type) and str(c_name) == str(city_name):
                        temp = {}
                        temp['company_name'] = i['company_name']
                        temp['brand_name'] = i['brand_name']
                        temp['package_type'] = j['package_type']
                        temp['package_id'] = j['package_id']
                        temp['purchase_price'] = j['purchase_price']
                        temp['unit_price'] = j['mrp']
                        temp['discount_in_percentage'] = j['discount_in_percentage']
                        temp['return_policy'] = j['return_policy']
                        temp['expiry_date'] = j['expiry_date']
                        temp['product_rating'] = 0
                        temp['product_no_of_rating'] = 0
                        if 'product_quantity' not in i.keys():
                            temp['available_quantity'] = 0
                        else:
                            temp['available_quantity'] = i['product_quantity']
                        if 'product_id' not in i.keys():
                            temp['product_id'] = '',
                        else:
                            temp['product_id'] = i['product_id']
                        if 'product_name' not in i.keys():
                            temp['product_name'] = '',
                        else:
                            temp['product_name'] = i['product_name']
                        if 'product_image' not in i.keys():
                            temp['product_image'] = '',
                        else:
                            temp['product_image'] = i['product_image']
                        if 'purchase_price' not in j.keys():
                            temp['purchase_price'] = '',
                        else:
                            temp['purchase_price'] = j['purchase_price']
                        for k in db_r.find():
                            p_id = k['product_id']
                            r_history = k['rating_history']
                            try:
                                if str(p_id) == str(temp['product_id']):
                                    user_count = len(r_history)
                                    temp['product_no_of_rating'] = user_count
                                    temp['product_rating'] = k['current_rating']
                            except KeyError or ValueError:
                                pass
                        output.append(temp)
                        output.sort(reverse=False, key=lambda e: int(e['purchase_price']))
        return jsonify({"status": True, 'message': "product details get by product_type success", 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid sorting type', 'result': output})


if __name__ == '__main__':
    # app.run(debug=True)
      app.run(host='0.0.0.0', port=6002, debug=True, threaded=True)