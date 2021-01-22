import os
import time
import pymongo
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
from time import strftime
from random import randint
import smtplib, requests, re
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required)
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager
import base64
import random
import string, sys
from flask import Flask, render_template, url_for, request, redirect, jsonify, json, session, flash
import datetime
from datetime import datetime, timedelta
# from dateutil.parser import parse
from flask_bcrypt import Bcrypt
# from datetime import datetime
import calendar
import datetime
from dateutil.parser import parse

app = Flask(__name__)
app.config["MONGO_DBNAME"] = "OWO"
# app.config["MONGO_URI"] = "mongodb://owoadmin:sukeshfug@35.154.239.192:6909/OWO"
app.config["MONGO_URI"] = "mongodb://owoadmin:sukeshfug@13.235.150.131:6909/OWO"
mongo = PyMongo(app)
cors = CORS(app, resources={r"/owo/*": {"origins": "*"}})

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = "/var/www/html/owo/images/product_images/"
ALLOWED_EXTENSIONS = set(['mp4', 'mov', 'wmv', 'flv', 'avi'])
FILE_ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'doc', 'docx'])

UPLOAD = os.path.join(APP_ROOT, 'files')
if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD, exist_ok=True)
UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

s = URLSafeTimedSerializer('12345')
login_manager = LoginManager()
login_manager.init_app(app)
mail = Mail(app)


def findDay(date):
    day, month, year = (int(i) for i in date.split('-'))
    dayNumber = calendar.weekday(day, month, year)
    days = ["Mon", "Tue", "Wed", "Thu",
            "Fri", "Sat", "Sun"]
    return (days[dayNumber])


# --------------------------------------------------- Super admin login ------------------------------------------------
@app.route('/owo/super_admin/login', methods=['POST', 'GET'])
def super_admin():
    try:
        data = mongo.db.OWO
        db_s = data.Super_Admin
        output = []

        email_id = request.json['email_id']
        password = request.json['password']
        login_time = request.json['login_time']
        session_status = request.json['session_status']
        roles_id = int(1)
        if email_id == "superadmin@gmail.com" and password == "admin@123" and roles_id == 1:
            db_s.update({'email_id': email_id}, {'$set': {'login_time': login_time, 'session_status': session_status,
                                                          'email_verified': 1, 'mobile_verified': 1}})
            output.append({'email_id': email_id, 'password': password, 'roles_id': 1, 'roles_name': 'superadmin',
                           'login_time': login_time, 'session_status': session_status, 'email_verified': 1,
                           'mobile_verified': 1})
            return jsonify({'status': True, 'message': 'Login success', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid credentials.Please try again'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# --------------------------------------------------- Add admin user --------------------------------------------------
@app.route('/owo/add_user_admin', methods=['POST'])
@jwt_required
def addAdminUser():
    data = mongo.db.OWO
    db = data.Sub_Admin
    output = []
    # -------------------------------------------------------------------------------
    added_by = request.json['added_by']
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email_id = str(request.json['email_id'])
    mobile_number = request.json['mobile_number']
    role_name = request.json['role_name']
    password = request.json['password']
    roles_id = int(2)  # Input Parameters
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    email_result = db.find({'email_id': email_id})
    mobile_result = db.find({'mobile_number': int(mobile_number)})
    # --------------------------------------------------------------------------------------
    if email_result.count() != 0 or mobile_result.count() != 0:
        return jsonify({'status': False, 'message': 'admin user is already registered'})
    # --------------------------------------------------------------------------------------
    admin_id_list = [i['admin_id'] for i in db.find()]
    if len(admin_id_list) == 0:
        admin_id = 1
    else:  # It creates a unique Admin_Id
        admin_id = int(admin_id_list[-1]) + 1
    # -----------------------------------------------------------------------------------------------------------------
    db.insert({'first_name': first_name, 'last_name': last_name, 'email_id': email_id,
               'mobile_number': int(mobile_number), 'profile_pic': '',
               'role_name': role_name, 'password': password, 'date_of_creation': date_of_creation,
               'roles_id': 2, 'admin_id': int(admin_id), 'active_admin': True,
               'added_by': added_by, 'mobile_verified': 0, 'email_verified': 0})
    output.append({'first_name': first_name, 'last_name': last_name, 'email_id': email_id,
                   'mobile_number': int(mobile_number), 'profile_pic': '',
                   'role_name': role_name, 'password': password, 'date_of_creation': date_of_creation,
                   'rolesid': 2, 'admin_id': int(admin_id), 'active_admin': True,
                   'added_by': added_by, 'mobile_verified': 0, 'email_verified': 0})
    return jsonify({'status': True, 'message': "Added successfully", 'result': output})


# ---------------------------------------------- send mobile OTP for Admin User --------------------------------------
@app.route('/owo/send_mobile_otp_admin_user', methods=['POST'])
@jwt_required
def sendMobileOTPSubAdmin():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        admin_id = request.json['admin_id']
        mobile_number = request.json['mobile_number']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            a_id = i['admin_id']
            if str(a_id) == str(admin_id) and str(m_number) == str(mobile_number):
                otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                      str(otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'admin_id': int(a_id)}, {'$set': {'otp': str(otp)}})
                output.append({'mobile_number': m_number, 'otp': str(otp), 'admin_id': a_id})
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------- Verify mobile OTP admin user ---------------------------------------------------------
@app.route('/owo/verify_mobile_otp_admin_user', methods=['POST'])
@jwt_required
def verifyMobileOTPAdminUser():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    otp_entered = request.json['otp_entered']
    mobile_number = request.json['mobile_number']
    output = []
    details = coll.find()
    print("ok")
    for k in details:
        if str(mobile_number) == str(k['mobile_number']) and str(otp_entered) == str(k['otp']):
            coll.update_many({'mobile_number': int(mobile_number)}, {'$set': {'mobile_verified': 1}})
            output.append({'admin_id': k['admin_id'], 'email_id': k['email_id'], 'first_name': k['first_name'],
                           'last_name': k['last_name'], 'date_of_creation': k['date_of_creation'],
                           'mobile_number': k['mobile_number'], 'roles_id': k['roles_id']})
            return jsonify({'status': True, 'message': 'Mobile otp verified successfully', 'result': output,
                            'mobile_verified': 1, 'email_verified': k['email_verified']})
    else:
        return jsonify(
            {'status': False, 'message': 'Invalid Credentials. Please check and try again', 'result': output})


# ----------------------------------------------- send Email OTP admin user ----------------------------------------
@app.route('/owo/send_email_otp_admin_user', methods=['POST'])
@jwt_required
def sendEmailOTPSubAdmin():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        admin_id = request.json['admin_id']
        email_id = request.json['email_id']
        details = coll.find()
        for i in details:
            id = i['admin_id']
            e_id = i['email_id']
            if str(id) == str(admin_id) and str(e_id) == str(email_id):
                email_otp = random.randint(1000, 9999)
                msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com", recipients=[email_id])
                print(i['email_id'])
                msg.body = 'Welcome to OWO \n\n Your mail verification OTP' + str(email_otp)
                mail.send(msg)
                coll.update_one({'email_id': email_id}, {'$set': {'email_otp': str(email_otp)}})
                output.append({'email_id': email_id, 'email_otp': str(email_otp), 'admin_id': admin_id})
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid email_id'})

    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------------- Verify Email OTP admin user  ---------------------------------------------
@app.route('/owo/verify_email_otp_admin_user', methods=['POST'])
@jwt_required
def verifyEmailOTPAdminUser():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    email_otp_entered = request.json['email_otp_entered']
    email_id = request.json['email_id']
    output = []
    details = coll.find()
    print("ok")
    for j in details:
        if str(email_id) == str(j['email_id']) and str(email_otp_entered) == str(j['email_otp']):
            coll.update_many({'email_id': email_id}, {'$set': {'email_verified': 1}})
            output.append({'admin_id': j['admin_id'], 'email_id': j['email_id'], 'first_name': j['first_name'],
                           'last_name': j['last_name'],
                           'mobile_number': j['mobile_number'],
                           'date_of_creation': j['date_of_creation']})
            return jsonify({'status': True, 'message': 'Email otp verified successfully', 'result': output,
                            'email_verified': 1, 'mobile_verified': j['mobile_verified']})
    else:
        return jsonify({'status': False, 'message': 'Invalid Credentials please check and try again', 'result': output})


# -------------------------------------------- Resend Email OTP admin user -----------------------------------------
@app.route('/owo/resend_email_otp_admin_user', methods=['POST'])
@jwt_required
def resendEmailOTPSubAdmin():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        admin_id = request.json['admin_id']
        email_id = request.json['email_id']
        details = coll.find()
        for i in details:
            e_id = i['email_id']
            if str(e_id) == str(email_id):
                email_otp = random.randint(1000, 9999)
                msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com", recipients=[email_id])
                print(i['email_id'])
                msg.body = 'Welcome to OWO \n\n Your mail verification OTP' + str(email_otp)
                mail.send(msg)
                coll.update_one({'email_id': email_id}, {'$set': {'email_otp': str(email_otp)}})
                output.append({'email_id': email_id, 'email_otp': str(email_otp), 'admin_id': admin_id})
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid email_id'})

    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------------------------------- Resend mobile OTP admin users --------------------------------
@app.route('/owo/resend_mobile_otp_admin_user', methods=['POST'])
@jwt_required
def resendMobileOTPAdminUser():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        mobile_number = request.json['mobile_number']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            a_id = i['admin_id']
            if str(mobile_number) == str(m_number):
                otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(mobile_number) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n This is mobile number verification from OWO \n\n Please enter the OTP:" + \
                      str(otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'admin_id': int(a_id)}, {'$set': {'otp': str(otp)}})
                output.append({'mobile_number': m_number, 'otp': str(otp), 'admin_id': a_id})
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ------------------------------------------------ Forgot password for admin user --------------------------------------
@app.route('/owo/forgot_password_admin_user', methods=['POST'])
def forgotPasswordAdminUser():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        user_name = request.json['user_name']
        details = coll.find()
        for i in details:
            m_number = i['mobile_number']
            e_id = i['email_id']
            a_id = i['admin_id']
            a_admin = i['active_admin']
            print(a_admin)
            if str(user_name) == str(m_number):
                if a_admin == True:
                    # print(ok111)
                    f_otp = random.randint(1000, 9999)
                    url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(user_name) + \
                          "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n Please verify OTP to change your password \n\n Please enter the OTP:" + \
                          str(f_otp)
                    f = requests.get(url)
                    print(f)
                    coll.update_one({'admin_id': int(a_id)}, {'$set': {'f_otp': str(f_otp)}})
                    output.append({'user_name': str(user_name), 'f_otp': str(f_otp), 'admin_id': a_id})
                    return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
                else:
                    return jsonify({'status': False, 'message': 'Admin user is blocked', 'result': output})
            else:
                if str(user_name) == str(e_id):
                    if a_admin == True:
                        print("ok1")
                        f_otp = random.randint(1000, 9999)
                        msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com",
                                      recipients=[e_id])
                        print(i['email_id'])
                        msg.body = 'Welcome to OWO \n\n Please verify OTP to change your password' + str(f_otp)
                        mail.send(msg)
                        coll.update_one({'admin_id': int(a_id)}, {'$set': {'f_otp': str(f_otp)}})
                        output.append({'admin_id': int(a_id), 'f_otp': str(f_otp), 'user_name': str(user_name)})
                        return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
                    else:
                        return jsonify({'status': False, 'message': 'Admin user is blocked', 'result': output})

        else:
            return jsonify({'status': False, 'message': 'Invalid credentials'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ---------------------------------------- OTP verification for Forgot password ----------------------------------------
@app.route('/owo/otp_verification_forgot_password', methods=['POST'])
def OTPVerificationforgotPassword():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        user_name = request.json['user_name']
        f_otp_entered = request.json['f_otp_entered']
        details = coll.find()
        for i in details:
            if str(user_name) == str(i['mobile_number']) and str(f_otp_entered) == str(i['f_otp']):
                coll.update_many({'mobile_number': int(i['mobile_number'])}, {'$set': {'mobile_verified': 1}})
                output.append({'user_name': str(user_name), 'f_otp': str(f_otp_entered), 'admin_id': i['admin_id']})
                return jsonify(
                    {'status': True, 'message': 'Verified successfully', 'result': output, 'mobile_verified': 1})
            else:
                if str(user_name) == str(i['email_id']) and str(f_otp_entered) == str(i['f_otp']):
                    coll.update_many({'email_id': str(i['email_id'])}, {'$set': {'email_verified': 1}})
                    output.append({'f_otp': str(f_otp_entered), 'user_name': str(user_name), 'admin_id': i['admin_id']})
                    return jsonify({'status': True, 'message': 'Verified successfully', 'result': output,
                                    'email_verified': 1})
        else:
            return jsonify({'status': False, 'message': 'Invalid credentials', 'result': output})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# -------------------------------------------- Resend OTP for Admin User -----------------------------------------------
@app.route('/owo/resend_otp_admin_user', methods=['POST'])
def ResendOTPAdminUser():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        user_name = request.json['user_name']
        details = coll.find()
        for i in details:
            print("ok")
            m_number = i['mobile_number']
            e_id = i['email_id']
            a_id = i['admin_id']
            if str(user_name) == str(m_number):
                f_otp = random.randint(1000, 9999)
                url = "https://api.msg91.com/api/sendhttp.php?mobiles=" + str(user_name) + \
                      "&authkey=327291AVnDZUSxOgoq5ea3f8f3P1&route=4&sender=Owoooo&message=Welcome to OWO \n\n Please verify OTP to change your password \n\n Please enter the OTP:" + \
                      str(f_otp)
                f = requests.get(url)
                print(f)
                coll.update_one({'admin_id': int(a_id)}, {'$set': {'f_otp': str(f_otp)}})
                output.append({'user_name': str(user_name), 'f_otp': str(f_otp), 'admin_id': a_id})
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
            else:
                if str(user_name) == str(e_id):
                    f_otp = random.randint(1000, 9999)
                    msg = Message('Email verification mail from OWO', sender="ramadevig@fugenx.com", recipients=[e_id])
                    print(i['email_id'])
                    msg.body = 'Welcome to OWO \n\n Please verify OTP to change your password' + str(f_otp)
                    mail.send(msg)
                    coll.update_one({'admin_id': int(a_id)}, {'$set': {'f_otp': str(f_otp)}})
                    output.append({'admin_id': int(a_id), 'f_otp': str(f_otp), 'user_name': str(user_name)})
                    return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid credentials'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------------- Change Password admin users ------------------------------------------------
@app.route('/owo/change_password_admin_user', methods=['POST'])
@jwt_required
def changePasswordAdminUser():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        new_password = request.json['new_password']
        admin_id = request.json['admin_id']
        details = coll.find()
        for i in details:
            a_id = i['admin_id']
            if str(a_id) == str(admin_id):
                print("ok")
                coll.update_one({'admin_id': int(admin_id)}, {'$set': {'password': str(new_password)}})
                print("all ok")
                output.append({'admin_id': admin_id, 'password': new_password})
                return jsonify({'status': True, 'message': 'Password updated successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid admin id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# -------------------------------------------- Reset password for admin user ------------------------------------------
@app.route('/owo/reset_password_admin_user', methods=['POST'])
def resetPasswordAdminUser():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        reset_password = request.json['reset_password']
        confirm_password = request.json['confirm_password']
        admin_id = request.json['admin_id']
        if str(reset_password) != str(confirm_password):
            return jsonify({'status': False, 'message': 'please enter same password'})
        details = coll.find()
        for i in details:
            a_id = i['admin_id']
            if str(a_id) == str(admin_id):
                print("ok")
                coll.update_one({'admin_id': int(admin_id)}, {'$set': {'password': str(reset_password)}})
                print("all ok")
                output.append({'admin_id': admin_id, 'password': reset_password})
                return jsonify({'status': True, 'message': 'Password updated successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid admin id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------------------------- Get Admin User by ID ----------------------------------------
@app.route('/owo/get_admin_user/<admin_id>', methods=['GET'])
def getAdminUserByID(admin_id):
    data = mongo.db.OWO
    db = data.Sub_Admin
    output = []
    for i in db.find():
        temp = {}
        a_id = i['admin_id']
        if int(a_id) == int(admin_id):
            temp['admin_id'] = i['admin_id']
            temp['first_name'] = i['first_name']
            temp['last_name'] = i['last_name']
            temp['mobile_number'] = i['mobile_number']
            temp['email_id'] = i['email_id']
            temp['profile_pic'] = i['profile_pic']
            temp['mobile_verified'] = i['mobile_verified']
            temp['email_verified'] = i['email_verified']
            temp['password'] = i['password']
            temp['role_name'] = i['role_name']
            temp['active_admin'] = i['active_admin']

            if 'role_id' not in i.keys():
                temp['role_id'] = ''
            else:
                temp['role_id'] = i['role_id']
            temp['date_of_creation'] = i['date_of_creation']
            if 'date_of_modification' not in i.keys():
                temp['date_of_modification'] = '',
            else:
                temp['date_of_modification'] = i['date_of_modification']

            output.append(temp)
            return jsonify({'status': True, 'message': 'Admin user data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid admin_id', 'result': output})


# -------------------------------------------------- Get All Admin Users -----------------------------------------------
@app.route('/owo/get_Admin1', methods=['GET'])
def getadmin12():
    data = mongo.db.OWO
    db = data.Sub_Admin
    output = []
    details = db.find()
    for i in details:
        temp = {}
        temp['admin_id'] = i['admin_id']
        temp['first_name'] = i['first_name']
        temp['last_name'] = i['last_name']
        temp['mobile_number'] = i['mobile_number']
        temp['email_id'] = i['email_id']
        temp['profile_pic'] = i['profile_pic']
        temp['mobile_verified'] = i['mobile_verified']
        temp['email_verified'] = i['email_verified']
        temp['password'] = i['password']
        temp['role_name'] = i['role_name']
        temp['active_admin'] = i['active_admin']
        temp['added_by'] = i['added_by']
        temp['date_of_creation'] = i['date_of_creation']
        if 'date_of_modification' not in i.keys():
            temp['date_of_modification'] = '',
        else:
            temp['date_of_modification'] = i['date_of_modification']
        output.append(temp)
    return jsonify({'status': True, 'message': 'Get successfully', 'result': output})


# ----------------------------------------------- Edit_Admin_user -----------------------------------------------------
@app.route('/owo/edit_admin_user', methods=["POST"])
@jwt_required
def editAdminUsers1():
    data = mongo.db.OWO
    db = data.Sub_Admin
    output = []
    admin_id = request.json['admin_id']
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    mobile_number = request.json['mobile_number']
    email_id = request.json['email_id']
    role_name = request.json['role_name']
    date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
    info = db.find()
    for i in info:
        a_id = i['admin_id']
        m_number = i['mobile_number']
        e_id = i['email_id']
        if str(a_id) == str(admin_id):
            if str(m_number) == str(mobile_number) and str(email_id) == str(e_id):
                db.find_one_and_update({'admin_id': int(admin_id)},
                                       {'$set': {'first_name': first_name,
                                                 'last_name': last_name,
                                                 'mobile_number': int(mobile_number),
                                                 'email_id': str(email_id),
                                                 'role_name': role_name,
                                                 'date_of_modification': date_of_modification,
                                                 'email_verified': i['email_verified'],
                                                 'mobile_verified': i['mobile_verified'],
                                                 }})
                output.append({'admin_id': int(admin_id), 'first_name': first_name, 'last_name': last_name,
                               'mobile_number': int(mobile_number), 'email_id': str(email_id), 'role_name': role_name,
                               'date_of_modification': date_of_modification})
                return jsonify({"status": True, "message": 'Profile updated', 'result': output,
                                'email_verified': i['email_verified'],
                                'mobile_verified': i['mobile_verified']})
            else:
                if str(m_number) != str(mobile_number) and str(email_id) != str(e_id):
                    db.find_one_and_update({'admin_id': int(admin_id)},
                                           {'$set': {'first_name': first_name,
                                                     'last_name': last_name,
                                                     'mobile_number': int(mobile_number),
                                                     'email_id': str(email_id),
                                                     'role_name': role_name,
                                                     'date_of_modification': date_of_modification,
                                                     'email_verified': 0,
                                                     'mobile_verified': 0
                                                     }})
                    output.append({'admin_id': int(admin_id), 'first_name': first_name, 'last_name': last_name,
                                   'mobile_number': mobile_number, 'email_id': str(email_id), 'role_name': role_name,
                                   'date_of_modification': date_of_modification})
                    return jsonify({'status': True,
                                    'message': 'Profile updated please verify mobile number and email_id',
                                    'email_verified': 0,
                                    'mobile_verified': 0,
                                    'result': output})
                elif str(m_number) != str(mobile_number):
                    db.find_one_and_update({'admin_id': int(admin_id)},
                                           {'$set': {'first_name': first_name,
                                                     'last_name': last_name,
                                                     'mobile_number': int(mobile_number),
                                                     'email_id': str(email_id),
                                                     'role_name': role_name,
                                                     'date_of_modification': date_of_modification,
                                                     'email_verified': i['email_verified'],
                                                     'mobile_verified': 0}})
                    output.append({'admin_id': int(admin_id), 'first_name': first_name, 'last_name': last_name,
                                   'mobile_number': mobile_number, 'email_id': str(email_id), 'role_name': role_name,
                                   'date_of_modification': date_of_modification})
                    return jsonify({'status': True, 'message': 'Profile updated please verify mobile number',
                                    'email_verified': i['email_verified'],
                                    'mobile_verified': 0,
                                    'result': output})
                elif str(email_id) != str(e_id):
                    db.find_one_and_update({'admin_id': int(admin_id)},
                                           {'$set': {'first_name': first_name,
                                                     'last_name': last_name,
                                                     'mobile_number': int(mobile_number),
                                                     'email_id': str(email_id),
                                                     'role_name': role_name,
                                                     'date_of_modification': date_of_modification,
                                                     'email_verified': 0,
                                                     'mobile_verified': i['mobile_verified']}})
                    output.append({'admin_id': int(admin_id), 'first_name': first_name, 'last_name': last_name,
                                   'mobile_number': mobile_number, 'email_id': str(email_id), 'role_name': role_name,
                                   'date_of_modification': date_of_modification})
                    return jsonify({'status': True, 'message': 'Profile updated please verify email_id',
                                    'email_verified': 0,
                                    'mobile_verified': i['mobile_verified'],
                                    'result': output})
    else:
        return jsonify({"status": False, "message": 'Invalid user id', 'result': output})


# --------------------------------------------------- Edit Admin User Profile Pic -------------------------------------
@app.route('/owo/edit_admin_user_profile_pic', methods=['POST'])
@jwt_required
def editAdminUserProfilePic():
    data = mongo.db.OWO
    db = data.Sub_Admin
    output = []
    admin_id = request.json['admin_id']
    ts = calendar.timegm(time.gmtime())
    a = str(admin_id) + str(ts)
    profile_pic = request.json['profile_pic']
    profile_pic = profile_pic.encode()
    profile_pic_path = '/var/www/html/owo/images/profile_images/' + str(a) + '.' + 'jpg'
    mongo_db_path = '/owo/images/profile_images/' + str(a) + '.' + 'jpg'
    with open(profile_pic_path, 'wb') as p1:
        p1.write(base64.decodebytes(profile_pic))
    date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
    info = db.find()
    for j in info:
        a_id = j['admin_id']
        if str(a_id) == str(admin_id):
            db.find_one_and_update({'admin_id': int(admin_id)}, {'$set': {'profile_pic': mongo_db_path,
                                                                          'date_of_modification': date_of_modification}})
            output.append({'admin_id': admin_id, 'profile_pic': mongo_db_path,
                           'date_of_modification': date_of_modification})
            return jsonify({'status': True, 'message': 'Admin user profile pic updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid admin id', 'result': output})


# -------------------------------------------------- Delete Admin users ----------------------------------------------
@app.route('/owo/delete_admin_user/<admin_id>', methods=['POST'])
@jwt_required
def deleteUser(admin_id):
    data = mongo.db.OWO
    db = data.Sub_Admin
    for i in db.find():
        u_id = i['admin_id']
        if int(u_id) == int(admin_id):
            db.remove({'admin_id': int(admin_id)})
            return jsonify({'status': True, 'message': 'Admin deleted'})
    return jsonify({'status': False, 'message': 'Invalid admin id'})


# -------------------------------------------------- Enable/Disable Admin User -------------------------------------
@app.route('/owo/admin_change_status', methods=['POST'])
@jwt_required
def enableAdmin():
    data = mongo.db.OWO
    db = data.Sub_Admin
    output = []
    admin_id = request.json['admin_id']
    active_admin = request.json['active_admin']
    for i in db.find():
        a_id = i['admin_id']
        if str(a_id) == str(admin_id):
            db.find_one_and_update({'admin_id': int(admin_id)}, {'$set': {'active_admin': active_admin}})
            output.append({'admin_id': int(admin_id), 'active_admin': active_admin})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid admin_id', 'result': output}))


# ---------------------------------------------------- Get Admin User Profile by ID ----------------------------------
@app.route('/owo/get_admin_user_profile/<admin_id>', methods=['GET'])
def getAdminUserProfileByID(admin_id):
    data = mongo.db.OWO
    db = data.Sub_Admin
    db1 = data.Super_Admin
    output = []
    for i in db.find():
        temp = {}
        a_id = i['admin_id']
        if int(a_id) == int(admin_id):
            temp['first_name'] = i['first_name']
            temp['last_name'] = i['last_name']
            temp['mobile_number'] = i['mobile_number']
            temp['email_id'] = i['email_id']
            temp['roles_id'] = i['roles_id']
            temp['profile_pic'] = i['profile_pic']
            temp['mobile_verified'] = i['mobile_verified']
            temp['email_verified'] = i['email_verified']
            output.append(temp)
            return jsonify({'status': True, 'message': 'Admin user profile data get successfully', 'result': output})
    for i in db1.find():
        temp = {}
        a_id = i['admin_id']
        if int(a_id) == int(admin_id):
            if 'first_name' not in i.keys():
                temp['first_name'] = ''
            else:
                temp['first_name'] = i['first_name']
            if 'last_name' not in i.keys():
                temp['last_name'] = ''
            else:
                temp['last_name'] = i['last_name']
            if 'mobile_number' not in i.keys():
                temp['mobile_number'] = ''
            else:
                temp['mobile_number'] = i['mobile_number']
            temp['email_id'] = i['email_id']
            if 'profile_pic' not in i.keys():
                temp['profile_pic'] = ' '
            else:
                temp['profile_pic'] = i['profile_pic']
            temp['mobile_verified'] = i['mobile_verified']
            temp['email_verified'] = i['email_verified']
            temp['roles_id'] = i['roles_id']
            output.append(temp)
            return jsonify({'status': True, 'message': 'Admin user profile data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid admin_id', 'result': output})


# ----------------------------------------- Change password for admin user profile ------------------------------------
@app.route('/owo/change_password_admin_user_profile', methods=['POST'])
@jwt_required
def changePasswordAdminUserProfile():
    data = mongo.db.OWO
    coll = data.Sub_Admin
    output = []
    try:
        current_password = request.json['current_password']
        new_password = request.json['new_password']
        confirm_new_password = request.json['confirm_new_password']
        admin_id = request.json['admin_id']
        if str(new_password) != str(confirm_new_password):
            return jsonify({'status': False, 'message': 'Please enter same password'})
        details = coll.find()
        for i in details:
            a_id = i['admin_id']
            if str(a_id) == str(admin_id):
                coll.find_one_and_update({'admin_id': int(admin_id)}, {'$set': {'password': str(new_password)}})
                output.append({'admin_id': admin_id, 'password': new_password, 'current_password': current_password})
                return jsonify({'status': True, 'message': 'Password updated successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid admin id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# --------------------------------------- Admin Pannel Login -----------------------------------------------------------
@app.route("/owo/login_admin_pannel", methods=["POST"])
def adminPannelLogin():
    data = mongo.db.OWO
    db = data.Sub_Admin
    db1 = data.Super_Admin
    db2 = data.role_management
    output = []
    user_name = request.json['user_name']
    password = request.json['password']
    for j in db1.find({'email_id': user_name, 'password': password}):
        if j['email_verified'] == 1 and j['mobile_verified'] == 1:
            access_token = create_access_token(identity=user_name, expires_delta=datetime.timedelta(days=2))
            db1.update({'email_id': user_name}, {'$set': {'access_token': access_token}})
            output.append({'email_id': j['email_id'], 'password': j['password'], 'roles_id': 1,
                           'admin_id': j['admin_id'], 'access_token': access_token})
            return jsonify({'status': True, 'message': 'Super admin login sucess', 'result': output,
                            'email_verified': j['email_verified'],
                            'mobile_verified': j['mobile_verified']})
        else:
            return jsonify({'status': False, 'message': 'Email and mobile is not verified', 'result': output})

    info = db.find()
    for i in info:
        name = i['email_id']
        print(name)
        m_number = i['mobile_number']
        pwd = i['password']
        if str(user_name) == str(name) or str(user_name) == str(m_number):
            if str(pwd) == str(password):
                if i['active_admin'] == True:
                    if i['email_verified'] == 0 and i['mobile_verified'] == 0:
                        output.append({'admin_id': i['admin_id'], 'first_name': i['first_name'],
                                       'last_name': i['last_name'], 'email_id': i['email_id'],
                                       'mobile_number': i['mobile_number'], 'roles_id': 2})
                        return jsonify({'status': False, 'message': 'OTP not verified', 'result': output,
                                        'mobile_verified': i['mobile_verified'],
                                        'email_verified': i['email_verified']})
                    else:
                        if i['email_verified'] == 1:
                            if i['mobile_verified'] == 1:
                                access_token = create_access_token(identity=user_name,
                                                                   expires_delta=datetime.timedelta(days=2))
                                db.update({'admin_id': i['admin_id']}, {'$set': {'access_token': access_token}})
                                output.append({'admin_id': i['admin_id'], 'first_name': i['first_name'],
                                               'last_name': i['last_name'], 'email_id': name, 'mobile_number': m_number,
                                               'roles_id': 2, 'access_token': access_token})
                                return jsonify({'status': True, 'message': 'Sub admin login successfully',
                                                'result': output, 'email_verified': i['email_verified'],
                                                'mobile_verified': i['mobile_verified']})
                            else:
                                output.append({'admin_id': i['admin_id'], 'first_name': i['first_name'],
                                               'last_name': i['last_name'], 'email_id': i['email_id'],
                                               'mobile_number': i['mobile_number'], 'roles_id': 2})
                                return jsonify({'status': False, 'message': 'Mobile OTP not verified', 'result': output,
                                                'mobile_verified': i['mobile_verified'], 'email_verified': 1})
                        else:
                            output.append({'admin_id': i['admin_id'], 'first_name': i['first_name'],
                                           'last_name': i['last_name'],
                                           'email_id': i['email_id'], 'mobile_number': i['mobile_number'],
                                           'roles_id': 2})
                            return jsonify({'status': False, 'message': 'Email OTP not verified', 'result': output,
                                            'email_verified': i['email_verified'], 'mobile_verified': 1})
                else:
                    return jsonify({'status': False, 'message': 'Admin user is not active', 'result': output})
            else:
                return jsonify({'status': False, 'message': 'Invalid password', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid credentials. Please try again', 'result': output})


# -------------------------------------------- Role access ------------------------------------------------------------
@app.route('/owo/access1/<admin_id>', methods=['GET'])
def adminAccess(admin_id):
    data = mongo.db.OWO
    db = data.Sub_Admin
    db_s = data.Super_Admin
    db_r = data.role_management
    output = []
    try:
        for su_a in db_s.find():
            if int(admin_id) == int(su_a['admin_id']):
                print(admin_id)
                print(su_a['admin_id'])
                role_name = su_a['role_name']
                print(role_name)
                for m in db_r.find({'modules.role_name': role_name}):
                    for mod in m['modules']:
                        module_name = mod['module_name'][0]
                        output.append({'admin_id': int(admin_id), 'role_name': role_name, 'module_name': module_name})
                return jsonify({'status': True, 'message': 'Details', 'result': output})
    except KeyError or ValueError:
        pass
    for k in db.find():
        if int(admin_id) == int(k['admin_id']):
            role_name = k['role_name']
            print(role_name)
            for i in db_r.find({'modules.role_name': role_name}):
                for j in i['modules']:
                    module_name = j['module_name'][0]
                    output.append({'admin_id': int(admin_id), 'role_name': role_name, 'module_name': module_name})
    return jsonify({'status': True, 'message': 'Details', 'result': output})


# -------------------------------------------------- City Management --------------------------------------------------
# ------------------------------------------------- Add city ----------------------------------------------------------
@app.route('/owo/add_city', methods=['POST'])
@jwt_required
def add_city():
    try:
        data = mongo.db.OWO
        db = data.Super_Admin
        db1 = data.city_management
        output = []
        admin_id = request.json['admin_id']
        admin_userName = request.json['admin_userName']
        city_name = request.json['city_name']
        date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
        city_id_list = [i['city_id'] for i in db1.find()]
        if len(city_id_list) is 0:
            city_id = 1
        else:
            city_id = int(city_id_list[-1]) + 1
        for i in db1.find():
            c_name = i['city_name']
            if str(c_name) == str(city_name):
                return jsonify({'status': False,
                                'message': 'Entered City name is already available in list so please enter another City name',
                                'result': output})
        db1.insert_one({'admin_id': int(admin_id), 'admin_userName': admin_userName, 'city_id': city_id,
                        'city_name': city_name, 'date_of_creation': date_of_creation, 'active_city': True})
        output.append({'admin_id': int(admin_id), 'admin_userName': admin_userName, 'city_id': city_id,
                       'city_name': city_name, 'date_of_creation': date_of_creation, 'active_city': True})
        return jsonify({'status': True, 'message': 'City added success', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


# ------------------------------------------------------ Edit City ----------------------------------------------------
@app.route('/owo/edit_city', methods=['POST'])
@jwt_required
def edit_city():
    try:
        data = mongo.db.OWO
        db = data.city_management
        output = []
        admin_id = request.json['admin_id']
        city_name = request.json['city_name']
        city_id = request.json['city_id']
        modified_on = strftime("%d/%m/%Y %H:%M:%S")
        city_result = db.find({'city_name': city_name})
        if city_result.count() > 1:
            return jsonify({'status': False, 'message': 'city already exists', 'result': output})
        info = db.find()
        for i in info:
            c_id = i['city_id']
            if str(c_id) == str(city_id):
                db.find_one_and_update({'city_id': int(city_id)}, {'$set': {'modified_by': int(admin_id),
                                                                            'city_name': city_name,
                                                                            'modified_on': modified_on}})
                output.append({'city_id': city_id, 'city_name': city_name, 'modified_by': admin_id,
                               'modified_on': modified_on})
                return jsonify({'status': True, 'message': 'Updated city success', 'result': output})
        return jsonify({'status': False, 'message': 'Enter valid credentials', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


# --------------------------------------- Delete_City -----------------------------------------------------------------
@app.route('/owo/delete_city/<city_id>', methods=['POST'])
@jwt_required
def delete_city(city_id):
    data = mongo.db.OWO
    db = data.city_management
    info = db.find()
    for i in info:
        id = i['city_id']
        if str(id) == str(city_id):
            db.remove({'city_id': int(city_id)})
            return jsonify({'status': True, 'message': 'City deleted successfully'})
    return jsonify({'status': False, 'message': 'Please try again'})


# ------------------------------------------- Get All cities ----------------------------------------------------------
@app.route('/owo/get_all_city', methods=['GET'])
def get_city():
    data = mongo.db.OWO
    db = data.city_management
    output = []
    for i in db.find():
        temp = {}
        temp['city_id'] = i['city_id']
        temp['city_name'] = i['city_name']
        temp['date_of_creation'] = i['date_of_creation']
        temp['admin_userName'] = i['admin_userName']
        temp['admin_id'] = i['admin_id']
        temp['active_city'] = i['active_city']
        if 'modified_on' not in i.keys():
            temp['modified_on'] = ''
        else:
            temp['modified_on'] = i['modified_on']
        output.append(temp)
    return jsonify({'status': True, 'message': 'Get all city success', 'result': output})


# ----------------------------------------- Get City By ID ------------------------------------------------------------
@app.route('/owo/get_city_by_id/<city_id>', methods=['GET'])
def get_city_by_id(city_id):
    data = mongo.db.OWO
    db = data.city_management
    output = []
    for i in db.find():
        c_id = i['city_id']
        if str(c_id) == str(city_id):
            temp = {}
            temp['city_id'] = i['city_id']
            temp['city_name'] = i['city_name']
            temp['date_of_creation'] = i['date_of_creation']
            temp['admin_userName'] = i['admin_userName']
            temp['active_city'] = i['active_city']
            if 'modified_on' not in i.keys():
                temp['modified_on'] = ''
            else:
                temp['modified_on'] = i['modified_on']
            output.append(temp)
            return jsonify({'status': True, 'message': 'Get city success', 'result': output})
    return jsonify({'status': False, 'message': 'Please try again', 'result': output})


# -----------------------------------------------Get All City Names ---------------------------------------------------
@app.route('/owo/get_all_cityName', methods=['GET'])
def get_all_cityName():
    data = mongo.db.OWO
    db = data.city_management
    output = []
    info = db.find({'active_city': True})
    for i in info:
        output.append({'city_name': i['city_name']})
    return jsonify({'status': True, 'message': 'All city name get successfully', 'result': output})


# --------------------------------------- city enable disable ----------------------------------------------------------
@app.route('/owo/city_change_active_status', methods=['POST'])
@jwt_required
def enableDisableCity():
    data = mongo.db.OWO
    db = data.city_management
    db_cate = data.category
    db_cmp = data.companies
    db_plant = data.plant
    db_prd = data.products
    db_wallet = data.owo_users_wallet
    db_instant = data.instant_delivery_management
    db_event = data.event_management
    db_subsc = data.product_subscription_test
    output = []
    products = []
    date_time = datetime.datetime.now()
    city_id = request.json['city_id']
    active_city = request.json['active_city']
    for i in db.find():
        c_id = i['city_id']
        c_name = i['city_name']
        if str(c_id) == str(city_id):
            db.update_many({'city_id': int(city_id)}, {'$set': {'active_city': active_city}})
            for j in db_cate.find():
                a_c = j['available_city']
                print(a_c)
                print("OK")
                if str(c_name) == str(a_c):
                    print('MATCHED')
                    db_cate.update_many({'available_city': a_c}, {'$set': {'active_category': active_city}})
            for k in db_prd.find():
                cty_name = k['city_name']
                print(cty_name)
                print("OKKKK")
                if str(cty_name) == str(c_name):
                    print('matched')
                    db_prd.update_many({'city_name': str(cty_name)}, {'$set': {'active_status': active_city}})
            for l in db_cmp.find():
                try:
                    brand = l['brand']
                    for m in brand:
                        avb_cty = m['available_city']
                        if str(avb_cty) == str(c_name):
                            db_cmp.update_many({'brand.available_city': str(avb_cty)},
                                               {'$set': {'brand.$.active_status': active_city}})
                except KeyError or ValueError:
                    pass
            for m in db_cmp.find():
                cc_name = m['city_name']
                if str(cc_name) == str(c_name):
                    print('MaTcHeD')
                    db_cmp.update_many({'city_name': str(cc_name)}, {'$set': {'active_status': active_city}})

            for n in db_plant.find():
                p_c_name = n['city_name']
                if str(p_c_name) == str(c_name):
                    print('mAtChEd')
                    db_plant.update_many({'city_name': str(p_c_name)}, {'$set': {'active_status': active_city}})

            if active_city is False:
                print('LOOP')
                for u in db_prd.find():
                    p_ct_name = u['city_name']
                    if str(p_ct_name) == str(c_name):
                        products.append(u['product_id'])
                        print(products)
                        print("OK")

                # ----------------------------------------- Event Cancel orders -------------------------------------------------------
                for k in db_event.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = k['products']
                    u_id = k['user_id']
                    s_type = k['signin_type']
                    try:
                        sub_t = k['sub_total']
                    except KeyError or ValueError:
                        sub_t = 0
                    try:
                        dev_charges = k['delivery_charges']
                    except KeyError or ValueError:
                        dev_charges = 0
                    count = 1
                    for l in pro:
                        pro_id = l['product_id']
                        if pro_id in products:
                            db_event.update_many({'products.product_id': str(pro_id)},
                                                 {'$set': {'delivery_status': 'cancelled',
                                                           'order_status': 'cancelled'}})

                            for v in db_wallet.find():
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = v['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        db_wallet.update_many(
                                            {'user_id': int(v['user_id']), 'signin_type': str(v['signin_type'])},
                                            {'$set': {
                                                'current_balance': c_balance},
                                                '$push': {
                                                    'recent_transactions': {'amount': refund_amount,
                                                                            'payment_type': "wallet",
                                                                            'transaction_id': transaction_id,
                                                                            'transaction_type': 'event refund',
                                                                            'transaction_date': date_time,
                                                                            'order_id': k['event_id'],
                                                                            'status': 'success',
                                                                            'current_balance': current_balance,
                                                                            'closing_balance': c_balance
                                                                            }}})
                # ----------------------------------------- Instant instant orders -----------------------------------------------------
                for a in db_instant.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['sub_total']
                    except KeyError or ValueError:
                        sub_t = 0
                    try:
                        dev_charges = a['delivery_charges']
                    except KeyError or ValueError:
                        dev_charges = 0
                    count = 1
                    for b in pro:
                        pro_id = b['product_id']
                        if pro_id in products:
                            db_instant.update_many({'products.product_id': str(pro_id)},
                                                   {'$set': {'delivery_status': 'cancelled',
                                                             'order_status': 'cancelled', }})
                            for c in db_wallet.find():
                                w_u_id = c['user_id']
                                w_s_type = c['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = c['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        db_wallet.update_many({'user_id': int(c['user_id']),
                                                               'signin_type': str(c['signin_type'])},
                                                              {'$set': {
                                                                  'current_balance': c_balance},
                                                                  '$push': {
                                                                      'recent_transactions': {'amount': refund_amount,
                                                                                              'payment_type': "wallet",
                                                                                              'transaction_id': transaction_id,
                                                                                              'transaction_type': 'instant refund',
                                                                                              'transaction_date': date_time,
                                                                                              'order_id': a[
                                                                                                  'instant_id'],
                                                                                              'status': 'success',
                                                                                              'current_balance': current_balance,
                                                                                              'closing_balance': c_balance
                                                                                              }}})
                # -------------------------------------- Cancel subscription orders ----------------------------------------------------
                for a in db_subsc.find({'is_subscribed': True, 'subscription_status': 'active'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['total_price']
                    except KeyError or ValueError:
                        sub_t = 0
                    count = 1
                    for b in pro:
                        type = b['product_id']
                        if type in products:
                            db_subsc.update_many({'products.product_id': str(type)},
                                                 {'$set': {'subscription_status': 'cancelled'}})
                            for v in db_wallet.find():
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = v['current_balance']
                                        subc_amount = v['subscription_amount']
                                        refund_amount = subc_amount + current_balance
                                        db_wallet.update_many({'user_id': int(v['user_id']),
                                                               'signin_type': str(v['signin_type'])},
                                                              {'$set': {
                                                                  'subscription_amount': 0},
                                                                  '$push': {
                                                                      'recent_transactions': {
                                                                          'amount': subc_amount,
                                                                          'payment_type': "wallet",
                                                                          'transaction_id': transaction_id,
                                                                          'transaction_type': 'subscription refund',
                                                                          'transaction_date': date_time,
                                                                          'order_id': a['subscription_id'],
                                                                          'status': 'success',
                                                                          'closing_balance': current_balance,
                                                                          "current_balance": current_balance
                                                                      }}})
            output.append({'city_id': int(city_id), 'active_city': active_city})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid city id', 'result': output}))


# ----------------------------------------------------Role Management -------------------------------------------------
# ----------------------------------------------------Add Role --------------------------------------------------------
@app.route('/owo/add_role', methods=['POST'])
@jwt_required
def add_role():
    data = mongo.db.OWO
    db = data.role_management
    output = []
    role_name = request.json['role_name']
    module_name = request.json['module_name']
    for i in db.find():
        r_name = i['modules'][0]['role_name']
        if str(r_name) == str(role_name):
            return jsonify({'status': False, 'message': 'role_name is already exist', 'result': output})
    role_id_list = [i['role_id'] for i in db.find()]
    if len(role_id_list) == 0:
        role_id = 1
    else:
        role_id = int(role_id_list[-1]) + 1
    created_date_time = strftime("%d/%m/%Y %H:%M:%S")
    db.insert({'role_id': role_id, 'active_role': True, 'modules': [
        {'role_name': role_name, 'module_name': module_name, 'created_date_time': created_date_time}]})
    output.append({'role_id': role_id, 'active_role': True, 'modules': [
        {'role_name': role_name, 'module_name': module_name, 'created_date_time': created_date_time}]})
    return jsonify({'status': True, 'result': output, 'message': 'Role added successfully'})


# ------------------------------------------ Edit Role ----------------------------------------------------------------
@app.route('/owo/edit_role', methods=['POST'])
@jwt_required
def edit_role():
    data = mongo.db.OWO
    db = data.role_management
    output = []
    role_id = request.json['role_id']
    role_name = request.json['role_name']
    module_name = request.json['module_name']
    date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
    for i in db.find():
        r_id = i['role_id']
        if str(role_id) == str(r_id):
            db.update({'role_id': int(role_id)}, {'$set': {'modules.$[].module_name': module_name,
                                                           'modules.$[].date_of_modification': date_of_modification}})
            output.append({'role_id': role_id, 'modules': [{'role_name': role_name, 'module_name': module_name,
                                                            'date_of_modification': date_of_modification}]})
            return jsonify({'status': True, 'result': output, 'message': 'Role edited successfully'})
    return jsonify({'status': False, 'message': 'Invalid role id', 'result': output})


# ------------------------------------------------ Get Role -----------------------------------------------------------
@app.route('/owo/get_rolee', methods=['GET'])
def get_rolee():
    data = mongo.db.OWO
    db = data.role_management
    output = []
    details = db.find()
    for i in details:
        role_id = (i['role_id'])
        try:
            active_role = i['active_role']
        except KeyError or ValueError:
            active_role = ''
        role_name = (i['modules'][0]['role_name'])
        created_date_time = (i['modules'][0]['created_date_time'])
        try:
            date_of_modification = (i['modules'][0]['date_of_modification'])
        except KeyError:
            date_of_modification = ""
        output.append({'role_id': role_id, 'active_role': active_role, 'role_name': role_name,
                       'created_date_time': created_date_time,
                       'date_of_modification': date_of_modification})
    return jsonify({'status': True, 'result': output, 'message': 'Roles data get successfully'})


# --------------------------------------------------------- Get_role by id---------------------------------------------
@app.route('/owo/get_role_ById/<role_id>', methods=['GET'])
def getRoleById(role_id):
    data = mongo.db.OWO
    db = data.role_management
    output = []
    details = db.find()
    for i in details:
        role_name = (i['modules'][0]['role_name'])
        created_date_time = (i['modules'][0]['created_date_time'])
        module_name = (i['modules'][0]['module_name'][0])
        try:
            date_of_modification = (i['modules'][0]['date_of_modification'])
        except KeyError:
            date_of_modification = ""
        try:
            active_role = (i['active_role'])
        except KeyError or ValueError:
            active_role = ""
        if str(role_id) == str(i['role_id']):
            output.append({'role_id': i['role_id'], 'active_role': active_role, 'role_name': role_name,
                           'module_name': module_name, 'created_date_time': created_date_time,
                           'date_of_modification': date_of_modification})
            return jsonify({'status': True, 'result': output, 'message': 'Roles data get successfully'})
    print("fail")
    return jsonify({'status': False, 'message': 'Failed to get details', 'result': output})


# ------------------------------------- Get Role Name -----------------------------------------------------------------
@app.route('/owo/get_role_name', methods=['GET'])
def get_rolee_name():
    data = mongo.db.OWO
    db = data.role_management
    output = []
    details = db.find({'active_role': True})
    for i in details:
        role_name = i['modules'][0]['role_name']
        output.append({'role_name': role_name})
    return jsonify({'status': True, 'result': output, 'message': 'Get all roles name successfully'})


# ------------------------------------------------------ Delete_Role---------------------------------------------------
@app.route('/owo/delete_role/<role_id>', methods=['POST'])
@jwt_required
def delete_role(role_id):
    data = mongo.db.OWO
    db = data.role_management
    output = []
    details = db.find()
    for i in details:
        r_id = i['role_id']
        if int(r_id) == int(role_id):
            db.remove({'role_id': int(role_id)})
            output.append({'role_id': role_id})
            return jsonify({'status': True, 'message': 'Delete role success', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid role id', 'result': output})


# ----------------------------------------------- Role Change Status --------------------------------------------------
@app.route('/owo/role_change_status', methods=['POST'])
@jwt_required
def enableDisableRole():
    data = mongo.db.OWO
    db = data.role_management
    db_sub_admin = data.Sub_Admin
    output = []
    role_id = request.json['role_id']
    active_role = request.json['active_role']
    for i in db.find():
        c_id = i['role_id']
        if str(c_id) == str(role_id):
            r_name = i['modules'][0]['role_name']
            print(r_name)
            db.update_many({'role_id': int(role_id)}, {'$set': {'active_role': active_role}})
            for j in db_sub_admin.find():
                rl_name = j['role_name']
                if str(rl_name) == str(r_name):
                    db_sub_admin.update_many({'role_name': str(rl_name)}, {'$set': {'active_admin': active_role}})
            output.append({'role_id': int(role_id), 'active_role': active_role})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid role id', 'result': output}))


# ---------------------------------------------------- Slot Management ------------------------------------------------
# ---------------------------------------------------- Add New Slot  --------------------------------------------------
@app.route('/owo/add_slot', methods=['POST'])
@jwt_required
def addSlot():
    data = mongo.db.OWO
    db = data.slot
    output = []
    # ------------------------------- Request parameters ------------------------------------------------------------------
    admin_id = request.json['admin_id']
    slot_start_time = request.json['slot_start_time']
    slot_end_time = request.json['slot_end_time']
    available_slot = request.json['available_slot']
    monday = request.json['monday']
    tuesday = request.json['tuesday']
    wednesday = request.json['wednesday']
    thursday = request.json['thursday']
    friday = request.json['friday']
    saturday = request.json['saturday']
    sunday = request.json['sunday']
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")

    # ----------------------------------- Generate Unique Slot id ---------------------------------------------------------
    slot_id_list = [i['slot_id'] for i in db.find()]
    if len(slot_id_list) is 0:
        slot_id = 1
    else:
        slot_id = int(slot_id_list[-1]) + 1

    # ---------------------------------------- Finds admin and slot -------------------------------------------------------
    for j in db.find():
        av_s = j['available_slot']
        a = j['slot_start_time']
        b = j['slot_end_time']
        if str(av_s) == str(available_slot):
            return jsonify({'status': False, 'message': 'Slot already added', 'result': output})
        if str(a) < str(slot_start_time) < str(b):
            return jsonify({'status': False, 'message': 'Slot cannot be add in between time interval',
                            'result': output})
    db.insert({'admin_id': admin_id, 'slot_start_time': slot_start_time, 'slot_end_time': slot_end_time,
               'available_slot': available_slot, 'date_of_creation': date_of_creation, 'slot_id': int(slot_id),
               'active_slot': True, 'monday': monday, 'tuesday': tuesday, 'wednesday': wednesday,
               'thursday': thursday, 'friday': friday, 'saturday': saturday, 'sunday': sunday})
    output.append({'admin_id': admin_id, 'slot_id': slot_id, 'slot_start_time': slot_start_time,
                   'slot_end_time': slot_end_time, 'available_slot': available_slot,
                   'date_of_creation': date_of_creation, 'active_slot': True, 'monday': monday,
                   'tuesday': tuesday, 'wednesday': wednesday, 'thursday': thursday, 'friday': friday,
                   'saturday': saturday, 'sunday': sunday})
    return jsonify({'status': True, 'message': 'Slot added successfully', 'result': output})


# ----------------------------------------------- Edit Slot -----------------------------------------------------------
@app.route('/owo/edit_slot', methods=['POST'])
@jwt_required
def editSlot():
    try:
        data = mongo.db.OWO
        db = data.slot
        output = []
        admin_id = request.json['admin_id']
        slot_id = request.json['slot_id']
        slot_start_time = request.json['slot_start_time']
        slot_end_time = request.json['slot_end_time']
        available_slot = request.json['available_slot']
        monday = request.json['monday']
        tuesday = request.json['tuesday']
        wednesday = request.json['wednesday']
        thursday = request.json['thursday']
        friday = request.json['friday']
        saturday = request.json['saturday']
        sunday = request.json['sunday']
        date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
        info = db.find({'slot_id': slot_id})
        for i in info:
            ik = i['slot_id']
            if int(ik) == int(slot_id):
                db.find_one_and_update({'slot_id': int(slot_id)},
                                       {'$set': {'slot_start_time': slot_start_time, 'slot_end_time': slot_end_time,
                                                 'date_of_modification': date_of_modification,
                                                 'available_slot': available_slot, 'monday': monday, 'tuesday': tuesday,
                                                 'wednesday': wednesday, 'thursday': thursday, 'friday': friday,
                                                 'saturday': saturday, 'sunday': sunday}})
                output.append({'slot_id': slot_id, 'admin_id': admin_id, 'slot_start_time': slot_start_time,
                               'slot_end_time': slot_end_time, 'date_of_modification': date_of_modification,
                               'available_slot': available_slot, 'monday': monday, 'tuesday': tuesday,
                               'wednesday': wednesday, 'thursday': thursday, 'friday': friday, 'saturday': saturday,
                               'sunday': sunday})
                return jsonify({'status': True, 'message': 'Slot updated successfully', 'result': output})
            else:
                return jsonify({'status': False, 'message': 'Invalid slot_Id'})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


# ---------------------------------------- Get Slot by Slot_Id ---------------------------------------------------------
@app.route('/owo/get_slot/<slot_id>', methods=['GET'])
def getSlotById(slot_id):
    try:
        data = mongo.db.OWO
        db = data.slot
        output = []
        info = db.find()
        for i in info:
            try:
                date_of_modification = i['date_of_modification']
            except KeyError or ValueError:
                date_of_modification = ''
            s_id = i['slot_id']
            if s_id == int(slot_id):
                output.append({'slot_id': i['slot_id'], 'slot_start_time': i['slot_start_time'],
                               'slot_end_time': i['slot_end_time'], 'admin_id': i['admin_id'],
                               'date_of_creation': i['date_of_creation'], 'date_of_modification': date_of_modification,
                               'active_slot': i['active_slot'], 'available_slot': i['available_slot'],
                               'monday': i['monday'], 'tuesday': i['tuesday'], 'wednesday': i['wednesday'],
                               'thursday': i['thursday'], 'friday': i['friday'], 'saturday': i['saturday'],
                               'sunday': i['sunday']})
        return jsonify({'status': True, 'message': 'Get by id success', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


# ----------------------------------------- Get Slots ---------------------------------------------------------
@app.route('/owo/get_all_slot', methods=['GET'])
def getSlot():
    try:
        data = mongo.db.OWO
        db = data.slot
        output = []
        for i in db.find():
            try:
                date_of_modification = i['date_of_modification']
            except KeyError or ValueError:
                date_of_modification = ''
            output.append({'slot_id': i['slot_id'], 'slot_start_time': i['slot_start_time'],
                           'slot_end_time': i['slot_end_time'], 'admin_id': i['admin_id'],
                           'date_of_creation': i['date_of_creation'], 'date_of_modification': date_of_modification,
                           'active_slot': i['active_slot'], 'monday': i['monday'], 'tuesday': i['tuesday'],
                           'wednesday': i['wednesday'], 'thursday': i['thursday'], 'friday': i['friday'],
                           'saturday': i['saturday'], 'sunday': i['sunday'], 'available_slot': i['available_slot']})
        return jsonify({'status': True, 'message': 'List of slots', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


# --------------------------------------- Delete Slot ------------------------------------------------------------------
@app.route('/owo/delete_slot', methods=['POST'])
@jwt_required
def deleteSlot():
    try:
        data = mongo.db.OWO
        db = data.slot
        slot_id = request.json['slot_id']
        for q in db.find():
            id = q['slot_id']
            if str(id) == str(slot_id):
                db.remove({'slot_id': int(slot_id)})
                return jsonify({'status': True, 'message': 'Deleted successfully'})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


# ------------------------------------------------- Enable disable slot ------------------------------------------------
@app.route('/owo/enable_or_disable_slot', methods=['POST'])
@jwt_required
def enableordisableslot():
    data = mongo.db.OWO
    db = data.slot
    output = []
    slot_id = request.json['slot_id']
    active_slot = request.json['active_slot']
    for i in db.find():
        s_id = i['slot_id']
        if int(s_id) == int(slot_id):
            db.update_many({'slot_id': slot_id}, {'$set': {'active_slot': active_slot}})
            output.append({'slot_id': slot_id, 'active_slot': active_slot})
            return jsonify(({'status': True, 'message': 'Change status success', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid slot', 'result': output}))


# --------------------------------------------------- Enable Slot ------------------------------------------------------
@app.route('/owo/enable_slot', methods=['POST'])
@jwt_required
def enableSlot():
    data = mongo.db.OWO
    db = data.slot
    output = []
    slot_id = request.json['slot_id']
    active_slot = request.json['active_slot']

    for i in db.find():
        s_id = i['slot_id']
        if int(s_id) == int(slot_id):
            db.update_many({'slot_id': slot_id}, {'$set': {'active_slot': 'Active'}})
            output.append({'slot_id': slot_id, 'active_slot': active_slot})
            return jsonify(({'status': True, 'message': 'Enabled successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid slot', 'result': output}))


# ---------------------------------------- Disable Slot ---------------------------------------------------------------
@app.route('/owo/disable_slot', methods=['POST'])
@jwt_required
def disableSlot():
    data = mongo.db.OWO
    db = data.slot
    output = []
    slot_id = request.json['slot_id']
    active_slot = request.json['active_slot']

    for i in db.find():
        s_id = i['slot_id']
        if int(s_id) == int(slot_id):
            db.update_many({'slot_id': slot_id}, {'$set': {'active_slot': 'In Active'}})
            output.append({'slot_id': slot_id, 'active_slot': active_slot})
            return jsonify(({'status': True, 'message': 'Disabled successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid slot', 'result': output}))


# ------------------------------------------------- Add new company ----------------------------------------------------
@app.route('/owo/add_company', methods=['POST'])
@jwt_required
def addCompany():
    data = mongo.db.OWO
    db = data.companies
    output = []
    city_name = request.json['city_name']
    company_name = request.json['company_name']
    company_photo = request.json['company_photo']
    company_photo = company_photo.encode()
    company_description = request.json['company_description']
    primary_contact_number = request.json['primary_contact_number']
    alternative_contact_number = request.json['alternative_contact_number']
    email_id = request.json['email_id']
    address = request.json['address']
    created_by_user_name = request.json['created_by_user_name']
    created_by_admin_role_id = request.json['created_by_admin_role_id']
    role_name = request.json['role_name']
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    company_id_list = [i['company_id'] for i in db.find()]
    # print('ok1')
    if len(company_id_list) is 0:
        company_id = 1
    else:
        company_id = int(company_id_list[-1]) + 1
    company_photo_path = '/var/www/html/owo/images/company_images/' + str(company_id) + '.' + 'jpg'
    mongo_db_path = '/owo/images/company_images/' + str(company_id) + '.' + 'jpg'
    with open(company_photo_path, 'wb') as pl:
        pl.write(base64.decodebytes(company_photo))
    count = 0
    for i in db.find():
        c_id = i['company_id']
        city = i['city_name']
        c_name = i['company_name']
        c_email = i['email_id']
        if str(c_name) == str(company_name) and str(city) == str(city_name):
            count += 1
            if count >= 1:
                output.append(company_name)
                return jsonify(
                    {'status': False, 'message': 'Seems like ' + company_name + ' is already exist in ' + city_name,
                     'result': output})
    db.insert_one({'city_name': city_name, 'company_id': company_id, 'company_name': company_name,
                   'company_description': company_description, 'email_id': email_id,
                   'primary_contact_number': int(primary_contact_number), 'address': address,
                   'alternative_contact_number': int(alternative_contact_number),
                   'company_photo': mongo_db_path, 'active_status': True,
                   'date_of_creation': date_of_creation, 'created_by_user_name': created_by_user_name,
                   'created_by_admin_role_id': int(created_by_admin_role_id)})
    output.append({'city_name': city_name, 'company_id': company_id, 'company_name': company_name,
                   'company_description': company_description, 'email_id': email_id,
                   'primary_contact_number': int(primary_contact_number), 'address': address,
                   'alternative_contact_number': int(alternative_contact_number), 'active_status': True,
                   'role_name': role_name, 'company_photo': mongo_db_path,
                   'date_of_creation': date_of_creation, 'created_by_user_name': created_by_user_name,
                   'created_by_admin_role_id': int(created_by_admin_role_id)})
    return jsonify({'status': True, 'message': 'company added success', 'result': output})


# ---------------------------------------------------- Edit company ----------------------------------------------------
@app.route('/owo/edit_company/<roles_id>', methods=['POST'])
@jwt_required
def editCompany(roles_id):
    data = mongo.db.OWO
    db = data.companies
    db_a = data.Sub_Admin
    dbs_a = data.Super_Admin
    ds_p = data.products
    db_plant = data.plant
    output = []
    company_name = request.json['company_name']
    city_name = request.json['city_name']
    company_id = request.json['company_id']
    company_description = request.json['company_description']
    primary_contact_number = request.json['primary_contact_number']
    alternative_contact_number = request.json['alternative_contact_number']
    email_id = request.json['email_id']
    address = request.json['address']
    modified_admin_id = request.json['modified_admin_id']
    modified_on = time.strftime("%d/%m/%Y %H:%M:%S")
    company_name_result = db.find({'company_name': company_name})
    if company_name_result.count() > 1:
        return jsonify({'status': False, 'message': 'Company name already exist', 'result': output})
    for j in db.find():
        c_id = j['company_id']
        name = j['company_name']
        if int(c_id) == int(company_id):
            db.update_many({'company_id': int(company_id)},
                           {'$set': {'city_name': city_name,
                                     'company_name': company_name,
                                     'company_description': company_description,
                                     'primary_contact_number': int(primary_contact_number),
                                     'alternative_contact_number':
                                         int(alternative_contact_number), 'email_id': email_id,
                                     'address': address,
                                     'modified_admin_id': modified_admin_id,
                                     'modified_on': modified_on}})
            ds_p.update_many({'company_name': str(name)}, {'$set': {'company_name': company_name,
                                                                    'city_name': city_name}})
            db_plant.update_many({'company_name': str(name)}, {'$set': {'company_name': company_name,
                                                                        'city_name': city_name}})
            output.append(
                {'company_id': int(company_id), 'city_name': city_name,
                 'company_name': company_name, 'company_description': company_description,
                 'primary_contact_number': int(primary_contact_number), 'alternative_contact_number':
                     int(alternative_contact_number), 'email_id': email_id, 'address': address,
                 'modified_on': modified_on})
            return jsonify({'status': True, 'message': 'Updated company details', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid company_id', 'result': output})


# -------------------------------------- Edit Company Image -----------------------------------------------------------
@app.route('/owo/edit_company_image/<roles_id>', methods=['POST'])
@jwt_required
def editCompanyImg(roles_id):
    data = mongo.db.OWO
    db = data.companies
    db_a = data.Sub_Admin
    dbs_a = data.Super_Admin
    output = []
    company_id = request.json['company_id']
    company_photo = request.json['company_photo']
    ts = calendar.timegm(time.gmtime())
    a = str(company_id) + str(ts)
    company_photo = company_photo.encode()
    company_photo_path = '/var/www/html/owo/images/company_images/' + str(a) + '.' + 'jpg'
    mongo_db_path = '/owo/images/company_images/' + str(a) + '.' + 'jpg'
    with open(company_photo_path, 'wb') as pl:
        pl.write(base64.decodebytes(company_photo))
    for i in db.find():
        c_id = i['company_id']
        if int(c_id) == int(company_id):
            db.update_many({'company_id': int(company_id)}, {'$set': {'company_photo': mongo_db_path}})
            output.append({'company_id': company_id, 'company_photo': mongo_db_path})
            return jsonify({'status': True, 'message': 'Company_photo updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Company_id is not found', 'result': output})


# -------------------------------------------------------- Get All Companies ------------------------------------------
@app.route('/owo/get_all_company', methods=['GET'])
def getAllCompanies():
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find(sort=[('date_of_creation' and 'modified_on', pymongo.DESCENDING)]):
        temp = {}
        temp['city_name'] = i['city_name']
        temp['company_id'] = i['company_id']
        temp['company_name'] = i['company_name']
        temp['company_description'] = i['company_description']
        temp['address'] = i['address']
        temp['primary_contact_number'] = i['primary_contact_number']
        temp['email_id'] = i['email_id']
        temp['date_of_creation'] = i['date_of_creation']
        temp['created_by_user_name'] = i['created_by_user_name']
        temp['created_by_admin_role_id'] = i['created_by_admin_role_id']
        if 'alternative_contact_number' not in i.keys():
            temp['alternative_contact_number'] = ''
        else:
            temp['alternative_contact_number'] = i['alternative_contact_number']
        if 'company_photo' not in i.keys():
            temp['company_photo'] = ''
        else:
            temp['company_photo'] = i['company_photo']
            print(i['company_photo'])
        if 'modified_admin_id' not in i.keys():
            temp['modified_admin_id'] = ''
        else:
            temp['modified_admin_id'] = i['modified_admin_id']
        if 'modified_on' not in i.keys():
            temp['modified_on'] = ''
        else:
            temp['modified_on'] = i['modified_on']
        if 'active_status' not in i.keys():
            temp['active_status'] = ''
        else:
            temp['active_status'] = i['active_status']
        output.append(temp)
    return jsonify({"status": True, 'message': 'Get company details success', 'result': output})


# ------------------------------------------ Get Company By ID --------------------------------------------------------
@app.route('/owo/get_company_by_id/<company_id>', methods=['GET'])
def getCompanyById(company_id):
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find():
        id = i['company_id']
        # print(id)
        if str(company_id) == str(id):
            temp = {}
            temp['city_name'] = i['city_name']
            temp['company_id'] = i['company_id']
            temp['company_name'] = i['company_name']
            temp['company_description'] = i['company_description']
            temp['address'] = i['address']
            temp['primary_contact_number'] = i['primary_contact_number']
            temp['email_id'] = i['email_id']
            temp['date_of_creation'] = i['date_of_creation']
            temp['created_by_user_name'] = i['created_by_user_name']
            temp['created_by_admin_role_id'] = i['created_by_admin_role_id']
            if 'alternative_contact_number' not in i.keys():
                temp['alternative_contact_number'] = ''
            else:
                temp['alternative_contact_number'] = i['alternative_contact_number']
            if 'company_photo' not in i.keys():
                temp['company_photo'] = ''
            else:
                temp['company_photo'] = i['company_photo']
            if 'modified_admin_id' not in i.keys():
                temp['modified_admin_id'] = ''
            else:
                temp['modified_admin_id'] = i['modified_admin_id']
            if 'modified_on' not in i.keys():
                temp['modified_on'] = ''
            else:
                temp['modified_on'] = i['modified_on']
            if 'active_status' not in i.keys():
                temp['active_status'] = ''
            else:
                temp['active_status'] = i['active_status']
            output.append(temp)
            return jsonify({"status": True, 'message': 'Get company details success', 'result': output})
    return jsonify({"status": False, 'message': 'Company_id is not valid', 'result': output})


# --------------------------------------------- Delete company -------------------------------------------------------
@app.route('/owo/delete_company/<company_id>', methods=['POST'])
@jwt_required
def delete_company(company_id):
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find():
        id = i['company_id']
        # print(id)
        if int(company_id) == int(id):
            # print("success")
            db.remove({'company_id': int(company_id)})
            return jsonify({"status": True, 'message': 'Delete company success', 'result': output})
    return jsonify({"status": False, 'message': 'Company_id is not valid', 'result': output})


# --------------------------------------- Edit Product Logo ------------------------------------------------------------
@app.route('/owo/edit_product_logo', methods=['POST'])
@jwt_required
def editProductLogo():
    data = mongo.db.OWO
    db = data.products
    output = []
    product_id = request.json['product_id']
    ts = calendar.timegm(time.gmtime())
    a = str(product_id) + str(ts)
    product_logo = request.json['product_logo']
    product_logo = product_logo.encode()
    product_logo_path = '/var/www/html/owo/images/product_images/' + str(a) + '.' + 'jpg'
    mongo_db_path1 = '/owo/images/product_images/' + str(a) + '.' + 'jpg'
    with open(product_logo_path, 'wb') as pl:
        pl.write(base64.decodebytes(product_logo))
    info = db.find()
    for j in info:
        p_id = j['product_id']
        if str(p_id) == str(product_id):
            db.update({'product_id': product_id}, {'$set': {'product_logo': mongo_db_path1}})
            output.append({'product_id': product_id, 'product_logo': mongo_db_path1})
            return jsonify({'status': True, 'message': 'Product logo updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Product id not found'})


# ---------------------------------------- Enable/Disable Products ----------------------------------------------------
@app.route("/owo/enable_or_disable_products", methods=['POST'])
@jwt_required
def enableordisableproducts():
    data = mongo.db.OWO
    db_p = data.products
    db_instant = data.instant_delivery_management
    db_event = data.event_management
    db_subsc = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    product_id = request.json['product_id']
    active_status = request.json['active_status']
    date_time = datetime.datetime.now()
    output = []
    products = []
    for i in db_p.find():
        id = i['product_id']
        if str(product_id) == str(id):
            db_p.update_many({'product_id': str(id)},
                             {'$set': {
                                 'active_status': active_status
                             }
                             })
            if active_status is False:
                # ---------------------------------------- Instant Cancel orders -------------------------------------------------------
                for a in db_instant.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['sub_total']
                    except KeyError or ValueError:
                        sub_t = 0
                    try:
                        dev_charges = a['delivery_charges']
                    except KeyError or ValueError:
                        dev_charges = 0
                    count = 1
                    for b in pro:
                        pro_id = b['product_id']
                        if str(pro_id) == str(product_id):
                            db_instant.update_many({'products.product_id': str(pro_id)},
                                                   {'$set': {'delivery_status': 'cancelled',
                                                             'order_status': 'cancelled'}})
                            for c in db_wallet.find():
                                w_u_id = c['user_id']
                                w_s_type = c['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        print(transaction_id)
                                        current_balance = c['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        print(c_balance)
                                        db_wallet.update_many({'user_id': int(c['user_id']),
                                                               'signin_type': str(c['signin_type'])},
                                                              {'$set': {
                                                                  'current_balance': c_balance},
                                                                  '$push': {
                                                                      'recent_transactions': {'amount': refund_amount,
                                                                                              'payment_type': "wallet",
                                                                                              'transaction_id': transaction_id,
                                                                                              'transaction_type': 'instant refund',
                                                                                              'transaction_date': date_time,
                                                                                              'order_id': a[
                                                                                                  'instant_id'],
                                                                                              'status': 'success',
                                                                                              'closing_balance': c_balance,
                                                                                              'current_balance': current_balance
                                                                                              }}})

                # ---------------------------------------- Event Cancel orders ---------------------------------------------------------
                for k in db_event.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = k['products']
                    u_id = k['user_id']
                    s_type = k['signin_type']
                    try:
                        sub_t = k['sub_total']
                    except KeyError or ValueError:
                        sub_t = 0
                    try:
                        dev_charges = k['delivery_charges']
                    except KeyError or ValueError:
                        dev_charges = 0
                    count = 1
                    for l in pro:
                        pro_id = l['product_id']
                        if str(pro_id) == str(product_id):
                            db_event.update_many({'products.product_id': str(pro_id)},
                                                 {'$set': {'delivery_status': 'cancelled',
                                                           'order_status': 'cancelled'}})
                            print('entered into event')
                            for v in db_wallet.find():
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = v['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        print(c_balance)
                                        db_wallet.update_many(
                                            {'user_id': int(v['user_id']), 'signin_type': str(v['signin_type'])},
                                            {'$set': {
                                                'current_balance': c_balance},
                                                '$push': {
                                                    'recent_transactions': {'amount': refund_amount,
                                                                            'payment_type': "wallet",
                                                                            'transaction_id': transaction_id,
                                                                            'transaction_type': 'event refund',
                                                                            'transaction_date': date_time,
                                                                            'order_id': k['event_id'],
                                                                            'status': 'success',
                                                                            'closing_balance': c_balance,
                                                                            'current_balance': current_balance
                                                                            }}})
                # -------------------------------------- Cancel subscription orders ----------------------------------------------------
                for a in db_subsc.find({'is_subscribed': True, 'subscription_status': 'active'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['total_price']
                    except KeyError or ValueError:
                        sub_t = 0
                    count = 1
                    for b in pro:
                        type = b['product_id']
                        if str(type) == str(product_id):
                            db_subsc.update_many({'products.product_id': str(type)},
                                                 {'$set': {'subscription_status': 'cancelled'}})
                            for v in db_wallet.find():
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = v['current_balance']
                                        subc_amount = v['subscription_amount']
                                        refund_amount = subc_amount + current_balance
                                        db_wallet.update_many({'user_id': int(v['user_id']),
                                                               'signin_type': str(v['signin_type'])},
                                                              {'$set': {
                                                                  'subscription_amount': 0},
                                                                  '$push': {
                                                                      'recent_transactions': {
                                                                          'amount': subc_amount,
                                                                          'payment_type': "wallet",
                                                                          'transaction_id': transaction_id,
                                                                          'transaction_type': 'subscription refund',
                                                                          'transaction_date': date_time,
                                                                          'order_id': a['subscription_id'],
                                                                          'status': 'success',
                                                                          'closing_balance': current_balance,
                                                                          'current_balance': current_balance
                                                                      }}})
            output.append({'product_id': id, 'active_status': active_status, 'product_name': i['product_name']})
            return jsonify({"status": True, 'message': 'Change status success', 'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid product details', 'result': output})


# --------------------------------------- Upload Multiple Images -----------------------------------------------------
@app.route('/owo/upload_multiple_images/<product_id>', methods=['POST'])
@jwt_required
def addPhotos(product_id):
    output = []
    db = mongo.db.OWO
    coll = db.products
    upload_documents = []
    image_path1 = []
    if request.method == 'POST' and 'product_images' in request.files:
        for i in request.files.getlist('product_images'):
            os.makedirs(os.path.join(UPLOAD_FOLDER), exist_ok=True)
            filename = secure_filename(i.filename)
            upload_documents.append(filename)
            mongo_db_path1 = "/owo/files/" + filename
            filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_path1.append(mongo_db_path1)
            i.save(filepath1)
            coll.find_one_and_update({'product_id': str(product_id)}, {'$set': {'product_image': image_path1}})
            output.append({'product_id': str(product_id), 'product_image': mongo_db_path1})
        return jsonify({"status": True, "result": output, "message": 'Images saved successfully'})
    else:
        return jsonify({"status": False, "message": 'Error Occured, Please Try again', 'result': output})


# ------------------------------------------------- Get product images by product id -----------------------------------
@app.route('/owo/get_product_images/<product_id>', methods=['GET'])
def getProductImages(product_id):
    data = mongo.db.OWO
    db = data.products
    output = []
    output1 = []
    for i in db.find():
        p_id = i['product_id']
        if str(p_id) == str(product_id):
            try:
                p_im = i['product_image']
            except KeyError or ValueError:
                p_im = ''
            if len(p_im) != 0:
                for j in p_im:
                    output1.append({'product_image': j})
                return jsonify({'status': True, 'message': 'List of product images', 'result': output1})
            return jsonify({'status': False, 'message': 'Product images not found', 'result': output})
    return jsonify({'status': False, 'message': 'Product_id is not exist', 'result': output})


# --------------------------------------------------- Get Products list -----------------------------------------------
@app.route('/owo/get_products_list', methods=['GET'])
def getProductsList():
    data = mongo.db.OWO
    db = data.products
    output = []
    for i in db.find():
        for j in i['package_type']:
            output.append({'product_id': i['product_id'], 'product_name': i['product_name'],
                           'plant_name': i['plant_name'], 'brand_name': i['brand_name'],
                           'company_name': i['company_name'], 'package_type': i['package_type'],
                           'package_type': j['package_type'], 'purchase_price': j['purchase_price'],
                           'discount_in_percentage': j['discount_in_percentage'],
                           'return_policy': j['return_policy'], 'expiry_date': j['expiry_date']})
    return jsonify({'status': True, 'message': ' Product details', 'result': output})


# ------------------------------------------ order management ---------------------------------------------------------
@app.route('/owo/orders_success', methods=['GET'])
def get_order_status():
    data = mongo.db.OWO
    db = data.orders
    output = []
    details = db.find()
    for i in details:
        order = i['orders']
        for k in order:
            temp = {}
            temp['user_id'] = i['user_id']
            temp['signin_type'] = i['signin_type']
            temp['order_id'] = order['id']
            temp['order_amount'] = order['amount']
            temp['payment_id'] = order['receipt']
            temp['order_created_at'] = order['created_at']
            temp['order_status'] = i['order_status']
            temp['ordered_date_time'] = i['ordered_date_time']
            output.append(temp)
        return jsonify({"status": True, 'message': "Product by id details get success", 'result': output})


# -------------------------------------------------- get all company names --------------------------------------------
# ------------------------------------------- get all companies by company name --------------------------------------
@app.route('/owo/get_allCompanyNames', methods=['GET'])
def getByCompanyNames():
    data = mongo.db.OWO
    db = data.companies
    output = []
    output1 = []
    details = db.find()
    for i in details:
        company_name = i['company_name']
        company_id = i['company_id']
        output1.append({'company_id': company_id, 'company_name': company_name})
    return jsonify({'status': True, 'message': 'Company names displayed successfully', 'result': output1})


# ----------------------------------- Get All Brand And Company Name --------------------------------------------------
@app.route('/owo/get_all_brandNamesAndComapnyNames', methods=['GET'])
def get_AllBrandByNamesAndCompanyNames():
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find():
        try:
            brand = i['brand']
            for j in brand:
                output.append(
                    {'company_name': i['company_name'], 'company_id': i['company_id'], 'brand_id': j['brand_id'],
                     'brand_name': j['brand_name']})
        except KeyError or ValueError:
            brand = " "
    return jsonify({"status": True, 'message': 'Get all brands names success', 'result': output})


# ---------------------------------------------- Get All Brand Names --------------------------------------------------
@app.route('/owo/get_all_brandNames', methods=['GET'])
def get_AllBrandByNames():
    data = mongo.db.OWO
    db = data.companies
    output = []
    brand_name = str()
    for i in db.find():
        c_id = i['company_id']
        try:
            brand = i['brand']
            for j in brand:
                brand_name = j['brand_name']
                output.append({'brand_name': j['brand_name']})
        except KeyError or ValueError:
            brand = " "
    return jsonify({"status": True, 'message': 'Get all brands names success', 'result': output})


# ----------------------------------------------- Get Brand Details Based on Company Name -----------------------------
@app.route('/owo/get_companyId_basedComapnyName', methods=['POST'])
def get_companyId_basedComapnyName():
    data = mongo.db.OWO
    db = data.companies
    company_name = request.json['company_name']
    output = []
    for i in db.find():
        c_name = i['company_name']
        active_status = i['active_status']
        # print(c_name)
        try:
            brand = i['brand']
            for j in brand:
                if str(company_name) == str(c_name) and active_status is True:
                    output.append({'brand_id': j['brand_id'],
                                   'brand_name': j['brand_name']})
        except KeyError or ValueError:
            brand = " "
    return jsonify({"status": True, 'message': 'Get details by company name success', 'result': output})


# -------------------------------------- Get Subscription Plan Individual Users ---------------------------------------
@app.route('/owo/get_subscription_plan_individual_users', methods=['GET'])
def getSubscriptionPlanIndividualUsers():
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    for i in db.find():
        try:
            subscription_plan = i['subscription_plan']
            for j in subscription_plan:
                output.append({'subscription_id': j['subscription_id'], 'customer_id': i['user_id'],
                               'mobile_number': i['mobile_number'], 'email_id': i['email_id'],
                               'customer_type': i['signin_type'], 'frequency': j['frequency'],
                               'product_count': j['total_quantity'], 'sub_total': j['total_price']})
        except KeyError or ValueError:
            pass
    return jsonify({'status': True, 'message': "Get subscription plan details", 'result': output})


# ---------------------------------------- Get Subscription Plan for Corporate Users -----------------------------------
@app.route('/owo/get_subscription_plan_corporate_users', methods=['GET'])
def getSubscriptionPlanCorporateUsers():
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    for i in db.find():
        try:
            subscription_plan = i['subscription_plan']
            for j in subscription_plan:
                output.append({'subscription_id': j['subscription_id'], 'customer_id': i['user_id'],
                               'mobile_number': i['mobile_number'],
                               'email_id': i['email_id'], 'customer_type': i['signin_type'],
                               'frequency': j['frequency'],
                               'product_count': j['total_quantity'], 'sub_total': j['total_price']})
        except KeyError or ValueError:
            pass
    return jsonify({'status': True, 'message': "Get subscription plan datails", 'result': output})


# ------------------------------------------------- Add Individual Users -----------------------------------------------
@app.route('/owo/admin_adding_individual_user', methods=["POST"])
@jwt_required
def userIndividualRegistration():
    data = mongo.db.OWO
    db = data.individual_users
    user_wallet = data.owo_users_wallet
    output = []
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    session_id = request.json['session_id']
    password = request.json['password']
    signin_type = request.json['signin_type']
    date_of_join = request.json['date_of_join']
    mobile_number = request.json['mobile_number']
    email_id = request.json['email_id']
    address_type = request.json['address_type']
    building_number = request.json['building_number']
    address = request.json['address']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    landmark = request.json['landmark']
    city_name = request.json['city_name']
    confirm_password = request.json['confirm_password']
    email_result = db.find({'email_id': email_id})
    mobile_result = db.find({'mobile_number': int(mobile_number)})
    name = str(first_name) + str(last_name)
    if str(password) == str(confirm_password):

        invite_code = name[:2].upper() + str(random.randint(10, 99)) + name[2:4].upper() + str(random.randint(10, 99))
        # print(invite_code)

        # -------------------------------- System generate user id ---------------------------------------------------
        try:
            user_id_list = [i['user_id'] for i in db.find()]
            if len(user_id_list) is 0:
                user_id = 1
            else:
                user_id = int(user_id_list[-1]) + 1
        except KeyError or ValueError:
            user_id = int(1)

        # ----------------------------------- System generate wallet id -----------------------------------------------
        try:
            wallet_id_list = [i['wallet_id'] for i in user_wallet.find()]
            if len(wallet_id_list) is 0:
                wallet_id = 1
            else:
                wallet_id = int(wallet_id_list[-1]) + 1
        except KeyError or ValueError:
            wallet_id = int(1)

        # ----------------------------------- System generate address id ----------------------------------------------
        try:
            address_id_list = [l['address_id'] for l in db.find()]
            if len(address_id_list) is 0:
                address_id = 1
            else:
                address_id = int(address_id_list[-1]) + 1
        except KeyError or ValueError:
            address_id = int(1)

        # ---------------------------------- Checks the user is registered --------------------------------------------
        if email_result.count() != 0 or mobile_result.count() != 0:
            return jsonify({'status': False, 'message': 'User is already registered'})
        else:
            db.insert_one({'first_name': first_name, 'last_name': last_name, 'mobile_number': int(mobile_number),
                           'email_id': str(email_id), 'user_id': user_id, 'session_id': session_id,
                           'password': str(password), 'confirm_password': confirm_password, 'wallet_id': wallet_id,
                           'date_of_join': date_of_join, 'signin_type': signin_type, 'email_verified': 0,
                           'mobile_verified': 0, 'active_user': True, 'invite_code': invite_code,
                           'user_address': [{'building_number': building_number, 'address_type': address_type,
                                             'address': address, 'address_id': address_id, 'latitude': str(latitude),
                                             'longitude': str(longitude), 'landmark': landmark, 'city_name': city_name,
                                             'default_address': True}]})
            user_wallet.insert_one({'wallet_id': wallet_id, 'signin_type': signin_type, 'user_id': user_id,
                                    'current_balance': 0})
            output.append({'first_name': first_name, 'last_name': last_name, 'mobile_number': int(mobile_number),
                           'email_id': str(email_id), 'user_id': user_id, 'session_id': session_id,
                           'password': password, 'address_id': address_id, 'confirm_password': confirm_password,
                           'date_of_join': date_of_join, 'signin_type': signin_type, 'email_verified': 0,
                           'mobile_verified': 0, 'building_number': building_number, 'address_type': address_type,
                           'address': address, 'latitude': latitude, 'city_name': city_name, 'longitude': longitude,
                           'landmark': landmark, 'wallet_id': wallet_id, 'active_user': True})
            return jsonify({"status": True, "message": "User Added successfully", 'result': output})
    return jsonify({"status": False, "message": "Confirm password does not match", 'result': output})


# -------------------------------------------Edit_individual user------------------------------------------------------
@app.route('/owo/edit_individual_user', methods=["POST"])
@jwt_required
def editIndividualUser():
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    user_id = request.json['user_id']
    address_id = request.json['address_id']
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    mobile_number = request.json['mobile_number']
    email_id = request.json['email_id']
    building_number = request.json['building_number']
    address = request.json['address']
    landmark = request.json['landmark']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    city_name = request.json['city_name']
    address_type = request.json['address_type']
    date_of_modified = strftime("%d/%m/%Y %H:%M:%S")
    info = db.find()
    for i in info:
        u_id = i['user_id']
        m_number = i['mobile_number']
        e_id = i['email_id']
        try:
            u_address = i['user_address']
            for j in u_address:
                a_id = j['address_id']
                if str(u_id) == str(user_id) and str(a_id) == str(address_id):
                    if str(m_number) == str(mobile_number) and str(email_id) == str(e_id):
                        db.find_one_and_update({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                               {'$set': {'first_name': first_name,
                                                         'last_name': last_name,
                                                         'mobile_number': int(mobile_number),
                                                         'email_id': str(email_id),
                                                         'modified_on': date_of_modified,
                                                         'email_verified': i['email_verified'],
                                                         'mobile_verified': i['mobile_verified'],
                                                         'user_address.$.building_number': building_number,
                                                         'user_address.$.address': address,
                                                         'user_address.$.city_name': city_name,
                                                         'user_address.$.landmark': landmark,
                                                         'user_address.$.latitude': str(latitude),
                                                         'user_address.$.longitude': str(longitude),
                                                         'user_address.$.address_type': address_type}})
                        output.append({'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                       'mobile_number': str(mobile_number), 'email_id': str(email_id),
                                       'building_number': building_number, 'address': address,
                                       'address_type': address_type, 'landmark': landmark, 'latitude': latitude,
                                       'address_id': int(address_id), 'longitude': longitude, 'city_name': city_name,
                                       'modified_on': date_of_modified})
                        return jsonify({"status": True, "message": 'Profile updated', 'result': output,
                                        'email_verified': i['email_verified'], 'mobile_verified': i['mobile_verified']})
                    else:
                        if str(m_number) != str(mobile_number) and str(email_id) != str(e_id):
                            db.find_one_and_update(
                                {'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                {'$set': {'first_name': first_name, 'last_name': last_name,
                                          'mobile_number': int(mobile_number),
                                          'email_id': str(email_id),
                                          'modified_on': date_of_modified,
                                          'email_verified': 0,
                                          'mobile_verified': 0,
                                          'user_address.$.building_number': building_number,
                                          'user_address.$.address': address,
                                          'user_address.$.city_name': city_name,
                                          'user_address.$.landmark': landmark,
                                          'user_address.$.latitude': str(latitude),
                                          'user_address.$.longitude': str(longitude),
                                          'user_address.$.address_type': address_type}})
                            output.append(
                                {'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                 'mobile_number': str(mobile_number), 'city_name': city_name,
                                 'email_id': str(email_id), 'building_number': building_number, 'latitude': latitude,
                                 'longitude': longitude, 'address': address, 'address_type': address_type,
                                 'landmark': landmark, 'address_id': int(address_id),
                                 'modified_on': date_of_modified})
                            return jsonify({'status': True,
                                            'message': 'Profile updated please verify mobile number and email_id',
                                            'result': output, 'email_verified': 0, 'mobile_verified': 0})
                        elif str(m_number) != str(mobile_number):
                            db.find_one_and_update(
                                {'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                {'$set': {'first_name': first_name, 'last_name': last_name,
                                          'mobile_number': int(mobile_number),
                                          'email_id': str(email_id),
                                          'modified_on': date_of_modified,
                                          'email_verified': i['email_verified'],
                                          'mobile_verified': 0,
                                          'user_address.$.building_number': building_number,
                                          'user_address.$.address': address,
                                          'user_address.$.landmark': landmark,
                                          'user_address.$.city_name': city_name,
                                          'user_address.$.latitude': str(latitude),
                                          'user_address.$.longitude': str(longitude),
                                          'user_address.$.address_type': address_type}})
                            output.append(
                                {'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                 'mobile_number': str(mobile_number), 'city_name': city_name,
                                 'email_id': str(email_id), 'building_number': building_number, 'latitude': latitude,
                                 'longitude': longitude, 'address_id': int(address_id),
                                 'address': address, 'address_type': address_type, 'landmark': landmark,
                                 'modified_on': date_of_modified})
                            return jsonify({"status": True, "message": 'Profile updated please verify mobile number',
                                            'result': output, 'email_verified': i['email_verified'],
                                            'mobile_verified': 0})
                        elif str(email_id) != str(e_id):
                            db.find_one_and_update(
                                {'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                {'$set': {'first_name': first_name, 'last_name': last_name,
                                          'mobile_number': int(mobile_number),
                                          'email_id': str(email_id),
                                          'modified_on': date_of_modified,
                                          'email_verified': 0,
                                          'mobile_verified': i['mobile_verified'],
                                          'user_address.$.building_number': building_number,
                                          'user_address.$.address': address,
                                          'user_address.$.landmark': landmark,
                                          'user_address.$.city_name': city_name,
                                          'user_address.$.latitude': str(latitude),
                                          'user_address.$.longitude': str(longitude),
                                          'user_address.$.address_type': address_type
                                          }})
                            output.append(
                                {'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                 'mobile_number': str(mobile_number), 'city_name': city_name,
                                 'email_id': str(email_id), 'building_number': building_number, 'latitude': latitude,
                                 'longitude': longitude, 'address': address, 'address_type': address_type,
                                 'landmark': landmark, 'modified_on': date_of_modified})
                            return jsonify({"status": True, "message": 'Profile updated please verify email_id',
                                            'result': output, 'email_verified': 0,
                                            'mobile_verified': i['mobile_verified']})
        except KeyError or ValueError:
            u_address = 0
    else:
        return jsonify({"status": False, "message": "Invalid user_id", 'result': output})


# --------------------------------------------- Send Email OTP Individual user ----------------------------------------
@app.route('/owo/send_email_otp_individual_user', methods=['POST'])
@jwt_required
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
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid email_id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# -------------------------------------- Verify Email OTP individual user  ---------------------------------------------
@app.route('/owo/verify_email_otp_individual', methods=['POST'])
@jwt_required
def verifyEmailOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    email_otp_entered = request.json['email_otp_entered']
    email_id = request.json['email_id']
    output = []
    details = coll.find()
    for j in details:
        if str(email_id) == str(j['email_id']) and str(email_otp_entered) == str(j['email_otp']):
            coll.update_many({'email_id': email_id}, {'$set': {'email_verified': 1}})
            output.append({'user_id': j['user_id'], 'email_id': j['email_id'], 'first_name': j['first_name'],
                           'last_name': j['last_name'], 'mobile_number': j['mobile_number'],
                           'session_id': j['session_id'], 'date_of_join': j['date_of_join'],
                           'wallet_id': j['wallet_id']})
            return jsonify({'status': True, 'message': 'Email otp verified successfully', 'result': output,
                            'email_verified': 1, 'mobile_verified': j['mobile_verified']})
    else:
        return jsonify({'status': False, 'message': 'Invalid otp', 'result': output})


# -------------------------------------------- send mobile OTP for individual users------------------------------------
@app.route('/owo/send_mobile_otp_individual', methods=['POST'])
@jwt_required
def sendMobileOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        user_id = request.json['user_id']
        mobile_number = request.json['mobile_number']
        details = coll.find()
        for i in details:
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
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Individual mobile_number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# --------------------------- Verify mobile OTP individual user -------------------------------------------------------
@app.route('/owo/verify_mobile_otp_individual', methods=['POST'])
@jwt_required
def verifyMobileOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    otp_entered = request.json['otp_entered']
    mobile_number = request.json['mobile_number']
    output = []
    details = coll.find()
    for k in details:
        if str(mobile_number) == str(k['mobile_number']) and str(otp_entered) == str(k['otp']):
            coll.update_many({'mobile_number': int(mobile_number)}, {'$set': {'mobile_verified': 1}})
            output.append({'user_id': k['user_id'], 'email_id': k['email_id'], 'first_name': k['first_name'],
                           'last_name': k['last_name'],
                           'mobile_number': k['mobile_number'], 'session_id': k['session_id'],
                           'wallet_id': k['wallet_id']})
            return jsonify({'status': True, 'message': 'Mobile otp verified successfully', 'result': output,
                            'mobile_verified': 1, 'email_verified': k['email_verified']})
    else:
        return jsonify({'status': False, 'message': 'Invalid otp', 'result': output})


# ------------------------------------------- Resend Email OTP Individual user ----------------------------------------
@app.route('/owo/resend_email_otp_individual_user', methods=['POST'])
@jwt_required
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
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid email_id'})

    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------------------------- Resend mobile OTP individual users ----------------------------
@app.route('/owo/resend_mobile_otp_individual', methods=['POST'])
@jwt_required
def resendMobileOTPIndividual():
    data = mongo.db.OWO
    coll = data.individual_users
    output = []
    try:
        mobile_number = request.json['mobile_number']
        details = coll.find()
        for i in details:
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
                return jsonify({'status': True, 'message': 'Otp sent successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Individual mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# -------------------------------------- Get all individual users -----------------------------------------------------
@app.route('/owo/get_customers/individual', methods=['GET'])
def get_individualeCustomer():
    try:
        data = mongo.db.OWO
        db = data.individual_users
        details = db.find()
        output = []
        for i in details:
            temp = {}
            temp['user_id'] = i['user_id']
            temp['first_name'] = i['first_name']
            temp['last_name'] = i['last_name']
            temp['email_id'] = i['email_id']
            temp['mobile_number'] = i['mobile_number']
            temp['date_of_join'] = i['date_of_join']
            temp['email_verified'] = i['email_verified']
            temp['mobile_verified'] = i['mobile_verified']
            if 'active_user' not in i.keys():
                temp['active_user'] = ''
            else:
                temp['active_user'] = i['active_user']
            if 'profile_pic' not in i.keys():
                temp['profile_pic'] = ''
            else:
                temp['profile_pic'] = i['profile_pic']
            output.append(temp)
        return jsonify({"status": True, 'message': 'Get all individual users success', 'result': output})
    except Exception as e:
        return jsonify(status=False, message=str(e))


#  --------------------------------------------- Get Profile Individual -----------------------------------------------
@app.route('/owo/get_profile_individual/<user_id>', methods=['GET'])
def get_individual_user_by_id1(user_id):
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
            # date_of_join = i['date_of_join']
            if 'modified_on' not in i.keys():
                modified_on = ''
            else:
                modified_on = i['modified_on']
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
                            try:
                                city_name = j['city_name']
                            except KeyError or ValueError:
                                city_name = ''
                            default_address = j['default_address']
                            address_type = j['address_type']
                            output.append({'user_id': user_id, 'signin_type': signin_type, 'first_name': first_name,
                                           'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                           'password': password, 'modified_on': modified_on, 'city_name': city_name,
                                           'building_number': building_number, 'address_id': address_id,
                                           'address': address, 'landmark': landmark, 'latitude': latitude,
                                           'longitude': longitude, 'default_address': default_address,
                                           'address_type': address_type})
                            return jsonify({'status': True, 'message': 'Individual user data get successfully',
                                            'result': output})

                    except KeyError or ValueError:
                        pass
                        output.append({'user_id': user_id, 'signin_type': signin_type, 'first_name': first_name,
                                       'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                       'password': password, 'modified_on': modified_on})
                        return jsonify({'status': True, 'message': 'Individual user data get successfully',
                                        'result': output})
            except KeyError or ValueError:
                pass
            output.append({'user_id': user_id, 'signin_type': signin_type, 'first_name': first_name,
                           'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                           'password': password, 'modified_on': modified_on})
            return jsonify({'status': True, 'message': 'Individual user data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'User not found', 'result': output})


# ---------------------------------------------------- delete_individual_user -----------------------------------------
@app.route('/owo/delete_individual_user', methods=['POST'])
@jwt_required
def delete_individual_user():
    data = mongo.db.OWO
    db = data.individual_users
    user_id = request.json['user_id']
    for i in db.find():
        u_id = i['user_id']
        if int(u_id) == int(user_id):
            db.remove({'user_id': user_id})
            return jsonify({'status': True, 'message': 'User deleted'})
    return jsonify({'status': False, 'message': 'User not found'})


# --------------------------------------------- individual user change status -----------------------------------------
@app.route('/owo/individualUser_change_status', methods=['POST'])
@jwt_required
def enableDisableIndividualUser():
    data = mongo.db.OWO
    db = data.individual_users
    output = []
    user_id = request.json['user_id']
    active_user = request.json['active_user']
    for i in db.find():
        u_id = i['user_id']
        if str(u_id) == str(user_id):
            db.update_many({'user_id': int(user_id)}, {'$set': {'active_user': active_user}})
            output.append({'user_id': int(user_id), 'active_user': active_user})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid user id', 'result': output}))


# ------------------------------------------------- Get all subscription plan ------------------------------------------
@app.route('/owo/get_subscription_plan', methods=['GET'])
def getSubscription():
    data = mongo.db.OWO
    db = data.subscription
    db_cu = data.corporate_users
    db_iu = data.individual_users
    output = []
    for i in db.find():
        if str(i['signin_type']) == "corporate":
            for j in db_cu.find():
                output.append(
                    {'subscription_id': i['subscription_id'], 'buy_plan': i['buy_plan'], 'customer_id': i['user_id'],
                     'frequency': i['frequency'], 'product_id': i['product_id'], 'purchase_price': i['purchase_price'],
                     'total_quantity': i['total_quantity'], 'total_price': i['total_price'],
                     'plan_start_date': i['plan_start_date'],
                     'subscription_status': i['subscription_status'],
                     'mobile_number': j['mobile_number'], 'email': j['email_id']})
        elif str(i['signin_type']) == "individual":
            for j in db_iu.find():
                output.append(
                    {'subscription_id': i['subscription_id'], 'buy_plan': i['buy_plan'], 'customer_id': i['user_id'],
                     'frequency': i['frequency'], 'product_id': i['product_id'], 'purchase_price': i['purchase_price'],
                     'total_quantity': i['total_quantity'], 'total_price': i['total_price'],
                     'plan_start_date': i['plan_start_date'],
                     'subscription_status': i['subscription_status'],
                     'mobile_number': j['mobile_number'], 'email': j['email_id']})
    return jsonify({'status': True, 'message': 'Get subscription plans success', 'result': output})


# ------------------------------------------- Get subscription plan by date --------------------------------------------
# @app.route('/owo/get_subscription_plan_by_date', methods=['POST'])
# @jwt_required
# def getSubscriptionByDate():
#     data = mongo.db.OWO
#     db = data.product_subscription_test
#     db_p = data.products
#     output = []
#     customer = []
#     date = request.json['date']
#     date_object = datetime.datetime.strptime(date, '%Y-%m-%d')
#     set_q = date_object.strftime("%a")
#     for i in db.find({'is_subscribed': True, 'products.cart_status': "deactive", "subscription_status": "active"}):
#         products = []
#         count = 0
#         customer_id = i['user_id']
#         customer.append(customer_id)
#         if str(i['starting_date']) <= str(date) < str(i['plan_expiry_date']):
#             try:
#                 prd = i['products']
#                 count = len(prd)
#                 for j in prd:
#                     set_qnt = j['set_quantity']
#                     for k in set_qnt:
#                         key_list = list(k.keys())
#                         # val_list = list(k.values())
#                         if set_q in key_list:
#                             qnt = {set_q: k[set_q] for set_q in k.keys() and [set_q]}
#                             qnt = list(qnt.values())
#                             if qnt[0] != 0:
#                                 p_id = j['product_id']
#                                 for l in db_p.find({'product_id': p_id}):
#                                     products.append({'package_type': j['package_type'],
#                                                      'product_id': j['product_id'],
#                                                      'product_quantity': qnt[0],
#                                                      'product_name': l['product_name']
#                                                      })
#             except KeyError or ValueError:
#                 pass
#         if len(products) == 0:
#             pass
#         else:
#             output.append({'customer_id': i['user_id'],
#                            'customer_type': i['signin_type'],
#                            'mobile_number': i['mobile_number'], 'email': i['email_id'],
#                            'subscription_id': i['subscription_id']
#                            })
#     return jsonify({'status': True, 'message': 'Get subscription plans success', 'result': output})


#------------------------------------------- 22nd Jan 2021 12:11 PM --------------------------------------------
@app.route('/owo/get_subscription_plan_by_date', methods=['POST'])
@jwt_required
def getSubscriptionByDate():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db_p = data.products
    output = []
    customer = []
    date = request.json['date']
    date_object = datetime.datetime.strptime(date, '%Y-%m-%d')
    set_q = date_object.strftime("%a")
    for i in db.find({'is_subscribed': True, 'products.cart_status': "deactive", "subscription_status": "active"}):
        products = []
        count = 0
        customer_id = i['user_id']
        customer.append(customer_id)
        if str(i['starting_date']) <= str(date) < str(i['plan_expiry_date']):
            try:
                prd = i['products']
                count = len(prd)
                for j in prd:
                    set_qnt = j['set_quantity']
                    for k in set_qnt:
                        key_list = list(k.keys())
                        # val_list = list(k.values())
                        if set_q in key_list:
                            qnt = {set_q: k[set_q] for set_q in k.keys() and [set_q]}
                            qnt = list(qnt.values())
                            if qnt[0] != 0:
                                p_id = j['product_id']
                                for l in db_p.find({'product_id': p_id}):
                                    # products.append({'package_type': j['package_type'],
                                    #                  'product_id': j['product_id'],
                                    #                  'product_quantity': qnt[0],
                                    #                  'product_name': l['product_name']
                                    #                  })
                                    output.append({'customer_id': i['user_id'],
                                                   'customer_type': i['signin_type'],
                                                   'mobile_number': i['mobile_number'], 'email': i['email_id'],
                                                   'package_type': j['package_type'],
                                                   'product_id': j['product_id'],
                                                   'product_quantity': qnt[0],
                                                   'product_name': l['product_name']
                                                   })
            except KeyError or ValueError:
                pass
    return jsonify({'status': True, 'message': 'Get subscription plans success', 'result': output})

# -------------------------------------------- Get subscription plan by subscription id --------------------------------
@app.route("/owo/get_plan_by_subscription_id/<subscription_id>", methods=['GET'])
def getPlanBySubscriptionId(subscription_id):
    data = mongo.db.OWO
    db = data.product_subscription_test
    db_product = data.products
    output = []
    for i in db.find({'is_subscribed': True, 'products.cart_status': "deactive"}):
        prd = i['products']
        try:
            prd = i['products']
        except KeyError or ValueError:
            pass
        for j in prd:
            p_id = j['product_id']
            for a in db_product.find():
                pro_id = a['product_id']
                if str(pro_id) == str(p_id):
                    pro_name = a['product_name']
                    try:
                        s_qnt = j['set_quantity']
                        for k in s_qnt:
                            if int(subscription_id) == int(i['subscription_id']):
                                output.append({'product_id': p_id, 'mon': k['Mon'], 'tue': k['Tue'], 'wed': k['Wed'],
                                               'thurs': k['Thu'], 'fri': k['Fri'], 'sat': k['Sat'], 'sun': k['Sun'],
                                               'product_name': pro_name})
                    except KeyError or ValueError:
                        pass
    return jsonify({'status': True, 'message': 'Get plan success', 'result': output})


# ------------------------------------------------- Subscription history -----------------------------------------------
@app.route("/owo/subscription_history", methods=['POST'])
@jwt_required
def subscriptionHistoryy():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db1 = data.subscription_history
    date = request.json['date']
    output = []
    out = []
    for i in db1.find({'date': date}):
        for j in i['order_history']:
            if j['delivery_status'] == "delivered" or j['delivery_status'] == "cancelled":
                subscription_id = j['subscription_id']
                for s_id in db.find({'subscription_id': subscription_id}):
                    output.append(
                        {'customer_id': s_id['user_id'], 'mobile_number': s_id['mobile_number'],
                         'email_id': s_id['email_id'], 'customer_type': s_id['signin_type'],
                         'subscription_id': j['subscription_id'], 'product_count': j['product_count'],
                         'sub_total': j['total_price'], 'discount': j['discount'], 'gst': j['gst'],
                         'delivery_charges': s_id['delivery_charges'], 'total_price': s_id['total_price'],
                         'order_id': j['order_id'], 'transaction_id': j['transaction_id'],
                         'delivery_address': s_id['delivery_address'], 'plan_starting_date': s_id['starting_date'],
                         'plan_expire_date': s_id['plan_expiry_date'],
                         'subscription_status': s_id['subscription_status'], 'delivery_status': j['delivery_status'],
                         'buy_plan': s_id['buy_plan']})
    res_list = {frozenset(item.items()): item for item in output}.values()
    out.append(res_list)
    return jsonify({'status': True, 'message': 'Get subscription data success', 'return': list(res_list)})


# --------------------------------------------------- Edit change delivery statsu--------------------------------------
@app.route("/owo/edit_change_delivery_status", methods=['POST'])
@jwt_required
def editDeliveryStatus():
    data = mongo.db.OWO
    db = data.subscription_history
    db_m = data.membership
    db_c = data.config_loyalty
    db_loyalty = data.loyalty
    db1 = data.owo_users_wallet
    db_sc = data.product_subscription_test
    points = []
    date = request.json['date']
    subscription_id = request.json['subscription_id']
    delivery_status = request.json['delivery_status']
    status_result = db.find({'delivery_status': 'delivered'})
    transaction_type = "subscription"
    order_id = transaction_type[:5].upper() + str(random.randint(1000, 9999))
    transaction_id = transaction_type[:7].upper() + str(random.randint(1000, 9999))
    output = []
    amount = int()
    for i in db.find({'date': date, 'order_history.subscription_id': subscription_id}):
        for ord in i['order_history']:
            id = ord['subscription_id']
            o_id = ord['order_id']
            if delivery_status == 'delivered' and int(subscription_id) == int(id):
                amount = ord['total_price']
                print(amount)
                try:
                    for a in db_sc.find():
                        sid = a['subscription_id']
                        if int(sid) == int(subscription_id):
                            userid = a['user_id']
                            signintype = a['signin_type']
                            for k in db_m.find():
                                s_id = k['subscription_id']
                                u_id = k['user_id']
                                s_type = k['signin_type']
                                try:
                                    if int(s_id) == int(sid) and str(signintype) == str(s_type) and int(userid) == int(
                                            u_id):
                                        m_type = k['membership']
                                        for l in db_c.find():
                                            membership = l['loyalty_type']
                                            if str(m_type) == str(membership):
                                                loyalty = l['loyalty_points']
                                                points1 = int(amount) * (loyalty / 100)
                                                points = round(points1)
                                                for n in db_loyalty.find():
                                                    uid = n['user_id']
                                                    stype = n['signin_type']
                                                    t_earned = n['loyalty_balance']
                                                    if int(u_id) == int(uid) and str(stype) == str(s_type):
                                                        t_earned1 = t_earned + points
                                                        db_loyalty.find_one_and_update(
                                                            {'user_id': int(u_id), 'signin_type': str(s_type)},
                                                            {'$set': {'loyalty_balance': int(t_earned1)},
                                                             '$push': {'recent_earnings':
                                                                           {'order_id': o_id,
                                                                            'order_value': ord['total_price'],
                                                                            'loyalty_type': 'earned',
                                                                            'earn_points': int(points),
                                                                            'earn_date': datetime.datetime.now(),
                                                                            'earn_type': 'subscribed',
                                                                            'current_balance': int(t_earned),
                                                                            'closing_balance': int(t_earned1),
                                                                            }}})
                                                        db.update_one({'date': date,
                                                                       "order_history.subscription_id": subscription_id},
                                                                      {'$set': {
                                                                          'order_history.$.delivery_status': delivery_status}})
                                                        output.append({'subscription': subscription_id,
                                                                       'delivery_status': delivery_status})
                                                        return jsonify({'status': True,
                                                                        'message': 'Updated delivery_status changes',
                                                                        'result': output})

                                                db_loyalty.insert_one({'user_id': int(u_id), 'signin_type': s_type,
                                                                       'mobile_number': k['mobile_number'],
                                                                       'email_id': k['email_id'],
                                                                       'loyalty_balance': int(points),
                                                                       'recent_earnings': [{'order_id': o_id,
                                                                                            'order_value': ord[
                                                                                                'total_price'],
                                                                                            'loyalty_type': 'earned',
                                                                                            'earn_points': int(points),
                                                                                            'earn_date': datetime.datetime.now(),
                                                                                            'earn_type': "subscribed",
                                                                                            'current_balance': 0,
                                                                                            'closing_balance': int(
                                                                                                points)}]})
                                                db.update_one(
                                                    {'date': date, "order_history.subscription_id": subscription_id},
                                                    {'$set': {'order_history.$.delivery_status': delivery_status}})
                                                output.append(
                                                    {'subscription': subscription_id,
                                                     'delivery_status': delivery_status})
                                                return jsonify({'status': True,
                                                                'message': 'Updated delivery_status changes',
                                                                'result': output})
                                except KeyError or ValueError:
                                    pass
                except KeyError or ValueError:
                    pass
                db.update_one({'date': date, "order_history.subscription_id": subscription_id},
                              {'$set': {'order_history.$.delivery_status': delivery_status}})
                output.append({'subscription': subscription_id, 'delivery_status': delivery_status})
                return jsonify({'status': True, 'message': 'Updated delivery_status changes', 'result': output})

            elif delivery_status == "cancelled":
                for j in db1.find({'subscription_id': subscription_id}):
                    current_balance = j['current_balance'] - amount
                    subscription_amount = j['subscription_amount'] - amount
                    db1.update_many({'subscription_id': subscription_id},
                                    {'$set': {'subscription_amount': subscription_amount,
                                              'current_balance': current_balance}, '$push':
                                         {'recent_transactions': {'amount': amount,
                                                                  'closing_balance': current_balance,
                                                                  'transaction_type': transaction_type,
                                                                  'payment_type': "wallet",
                                                                  'current_balance': current_balance,
                                                                  'transaction_id': transaction_id,
                                                                  'order_id': order_id, 'status': "success",
                                                                  'transaction_time': datetime.datetime.now()}}})
                    db.update_one({'date': date, "order_history.subscription_id": subscription_id},
                                  {'$set': {'order_history.$.delivery_status': delivery_status}})
                    output.append({'subscription': subscription_id, 'delivery_status': delivery_status})
                return jsonify({'status': True, 'message': 'Updated delivery_status changes', 'result': output})
    return jsonify({'status': False, 'message': 'Please valid credentials', 'result': output})


# ------------------------------------------- Subscription stock management --------------------------------------------
@app.route('/owo/stock_management_subscription', methods=['POST'])
@jwt_required
def stockManagementSubscription():
    data = mongo.db.OWO
    db_s = data.product_subscription_test
    db_p = data.products
    db_sh = data.subscription_history
    output = []
    date = request.json['date']
    subscription_id = request.json['subscription_id']
    delivery_status = request.json['delivery_status']
    for i in db_sh.find():
        d = i['date']
        if str(date) == str(d):
            a = i['order_history']
            for j in a:
                p_c = j['product_count']
                s_id = j['subscription_id']
                print(s_id)
                for l in db_s.find():
                    id = l['subscription_id']
                    b = l['products']
                    if str(s_id) == str(id):
                        for m in b:
                            p_id = m['product_id']
                            for n in db_p.find():
                                pro_id = n['product_id']
                                p_quantity = n['product_quantity']
                                if str(pro_id) == str(p_id):
                                    print('Ok')
                                    var = p_quantity - p_c
                                    print(var)
                                    db_p.find_one_and_update({'product_id': pro_id},
                                                             {'$set': {'product_quantity': var}})
                                    output.append({'subscription_id': subscription_id,
                                                   'delivery_status': delivery_status})
    return jsonify({'status': True, 'message': 'List', 'result': output})


# ----------------------------------------------------- Get orders ------------------------------------------------------
@app.route('/owo/get_orders', methods=['GET'])
def get_orders():
    data = mongo.db.OWO
    db_p = data.products
    db_o = data.orders
    output = []
    for o in db_o.find(sort=[('ordered_date_time', pymongo.DESCENDING)]):
        print(o)
        try:
            if o['order_status'] == "success" and o['delivery_status'] == "un_delivered":
                try:
                    ord_id = o['orders']['id']
                    s_total = o['orders']['amount']
                    print(ord_id)
                except KeyError or ValueError:
                    pass
                output.append({'user_id': o['user_id'], 'signin_type': o['signin_type'], 'ord_id': o['ord_id'],
                               'mobile_number': o['mobile_number'], 'email_id': o['email_id'],
                               'delivery_slot': o['delivery_slot'], 'product_id': o['product_id'], 'product_count': 1,
                               'order_date_time': o['ordered_date_time'], 'delivery_status': o['delivery_status'],
                               'address': o['address'], 'order_id': ord_id, 'sub_total': o['total_price'],
                               'transaction_id': o['transaction_id'], 'order_status': "waiting for delivery",
                               })
        except KeyError or ValueError:
            pass
    return jsonify({'status': True, 'message': 'Order details', 'result': output})


# ------------------------------------------------- Get product details ------------------------------------------------
@app.route('/owo/get_product_details', methods=['POST'])
@jwt_required
def getOrderedProductDetails():
    data = mongo.db.OWO
    db_p = data.products
    db_o = data.orders
    ord_id = request.json['ord_id']
    output = []
    for o in db_o.find():
        if int(ord_id) == int(o['ord_id']):
            product_id = o['product_id']
            try:
                for p in db_p.find():
                    p_id = p['product_id']
                    if str(p_id) == str(product_id):
                        company_name = p['company_name']
                        brand_name = p['brand_name']
                        product_name = p['product_name']
                        p_type = p['package_type']
                        print("ok5")
                        for k in p_type:
                            package_type = k['package_type']
                            purchase_price = k['purchase_price']
                            print("ok6")
                            output.append({'ord_id': ord_id, 'company_name': company_name, 'brand_name': brand_name,
                                           'product_name': product_name, 'package_type': package_type,
                                           'purchase_price': purchase_price})
                            return jsonify({'status': True, 'message': 'Order details', 'result': output})
            except KeyError or ValueError:
                pass
    return jsonify({'status': False, 'message': ' Product_id not found', 'result': output})


# -------------------------------------------- Change instant delivery status ----------------------------------------
@app.route('/owo/change_insta_delivery_status', methods=['POST'])
@jwt_required
def changeInstantDeliveryStatus():
    try:
        data = mongo.db.OWO
        db_o = data.orders
        ord_id = request.json['ord_id']
        delivery_status = request.json['delivery_status']
        output = []
        for i in db_o.find():
            if int(ord_id) == int(i['ord_id']):
                db_o.update_many({'ord_id': ord_id}, {'$set': {'delivery_status': delivery_status}})
                output.append({'ord_id': ord_id, 'delivery_status': delivery_status})
        return jsonify({'status': True, 'message': 'Success', 'result': output})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------------------------- Get order history -----------------------------------------------
@app.route('/owo/get_orderhistory', methods=['GET'])
def getOrdersHistory():
    data = mongo.db.OWO
    db_o = data.orders
    output = []
    for o in db_o.find():
        print(o)
        try:
            if o['order_status'] == "success" and o['delivery_status'] != 'un_delivered':
                try:
                    delivery_charges = o['delivery_charges']
                    loyalty_point = o['loyalty_points']
                    product_count = o['product_count']
                except KeyError or ValueError:
                    gst = int()
                    delivery_charges = int()
                    discount = int()
                    loyalty_point = int()
                    product_count = int()
                try:
                    ord_id = o['orders']['id']
                    s_total = o['orders']['amount']
                    amount_paid = o['orders']['amount_paid']
                    print(ord_id)
                except KeyError or ValueError:
                    pass

                output.append({'user_id': o['user_id'], 'signin_type': o['signin_type'], 'ord_id': o['ord_id'],
                               'mobile_number': o['mobile_number'], 'email_id': o['email_id'],
                               'delivered_date_and_time': o['delivery_slot'], 'delivery_charges': 0,
                               'delivery_slot': o['delivery_slot'], 'product_id': o['product_id'],
                               'transaction_id': o['transaction_id'], 'paid_amount': s_total, 'product_count': 1,
                               'order_id': ord_id, 'address': o['address'], 'ordered_date': o['ordered_date_time'],
                               'delivery_status': o['delivery_status'], 'order_status': o['order_status'],
                               'sub_total': o['total_price'], 'total': o['total_price'],
                               'order_date_and_time': o['ordered_date_time']})
        except KeyError or ValueError:
            pass
    return jsonify({'status': True, 'message': 'Order details', 'result': output})


# ------------------------------------------------- Get all company name ----------------------------------------------
@app.route('/owo/get_allCompanyNamesTest', methods=['GET'])
def getByCompanyNamesTest():
    data = mongo.db.OWO
    db = data.companies
    output = []
    output1 = []
    details = db.find({'active_status': True})
    for i in details:
        company_name = i['company_name']
        company_id = i['company_id']
        active_status = i['active_status']
        if active_status is True:
            output1.append({'company_id': company_id, 'company_name': company_name})
    return jsonify({'status': True, 'message': 'Company names displayed successfully', 'result': output1})


# --------------------------------------- Get all brand name and company name -------------------------------------------
@app.route('/owo/get_all_brandNamesAndComapnyNamesTest', methods=['GET'])
def get_AllBrandByNamesAndCompanyNamesTest():
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find():
        try:
            brand = i['brand']
            for j in brand:
                output.append(
                    {'company_name': i['company_name'], 'company_id': i['company_id'], 'brand_id': j['brand_id'],
                     'brand_name': j['brand_name']})
        except KeyError or ValueError:
            brand = " "
    return jsonify({"status": True, 'message': 'Get all brands names success', 'result': output})


# ------------------------------------------------- Get  all brand name  -----------------------------------------------
@app.route('/owo/get_all_brandNamesTest', methods=['GET'])
def get_AllBrandByNamesTest():
    data = mongo.db.OWO
    db = data.companies_test
    output = []
    brand_name = str()
    for i in db.find():
        c_id = i['company_id']
        try:
            brand = i['brand']
            for j in brand:
                brand_name = j['brand_name']
                output.append({'brand_name': j['brand_name']})
        except KeyError or ValueError:
            brand = " "
    return jsonify({"status": True, 'message': 'Get all brands names success', 'result': output})


# ------------------------------------------- Category change active status --------------------------------------------
@app.route('/owo/category_change_active_status', methods=['POST'])
@jwt_required
def enableDisableCategory():
    data = mongo.db.OWO
    db = data.category
    db_prd = data.products
    db_event = data.event_management
    db_instant = data.instant_delivery_management
    db_subsc = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    output = []
    products = []
    category_id = request.json['category_id']
    active_status = request.json['active_status']
    date_time = datetime.datetime.now()
    for i in db.find():
        c_id = i['category_id']
        category_type = i['category_type']
        if str(c_id) == str(category_id):
            db.update_many({'category_id': int(category_id)}, {'$set': {'active_category': active_status}})
            try:
                for j in db_prd.find():
                    p_t = j['package_type']
                    for k in p_t:
                        p_type = k['package_type']
                        if str(p_type) == str(category_type):
                            db_prd.update_many({'package_type.package_type': str(p_type)},
                                               {'$set': {
                                                   'active_status': active_status
                                               }
                                               })
                            if active_status is False:
                                if str(category_type) == str(p_type):
                                    products.append(k['package_type'])
                                # ------------------------------------ Cancel Event orders -------------------------------------------------------------
                                for k in db_event.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                                    print('ok event')
                                    pro = k['products']
                                    u_id = k['user_id']
                                    s_type = k['signin_type']
                                    try:
                                        sub_t = k['sub_total']
                                    except KeyError or ValueError:
                                        sub_t = 0
                                    try:
                                        dev_charges = k['delivery_charges']
                                    except KeyError or ValueError:
                                        dev_charges = 0
                                    total = int(sub_t) + int(dev_charges)
                                    count = 1
                                    for l in pro:
                                        type = l['package_type']
                                        if type in products:
                                            print("ok event 2")
                                            db_event.find_one_and_update({'products.package_type': str(type)},
                                                                         {'$set': {'order_status': 'cancelled',
                                                                                   'delivery_status': 'cancelled'}})
                                            for v in db_wallet.find():
                                                print('ok event entered into wallet')
                                                w_u_id = v['user_id']
                                                w_s_type = v['signin_type']
                                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                                        count = count + 1
                                                        ts = calendar.timegm(time.gmtime())
                                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                                        print(transaction_id)
                                                        current_balance = v['current_balance']
                                                        refund_amount = int(sub_t)
                                                        c_balance = int(refund_amount) + int(current_balance)
                                                        print(c_balance)
                                                        db_wallet.update_many({'user_id': int(v['user_id']),
                                                                               'signin_type': str(v['signin_type'])},
                                                                              {'$set': {
                                                                                  'current_balance': c_balance},
                                                                                  '$push': {
                                                                                      'recent_transactions': {
                                                                                          'amount': refund_amount,
                                                                                          'payment_type': "wallet",
                                                                                          'transaction_id': transaction_id,
                                                                                          'transaction_type': 'event refund',
                                                                                          'transaction_date': date_time,
                                                                                          'order_id': k['event_id'],
                                                                                          'status': 'success',
                                                                                          'closing_balance': c_balance,
                                                                                          'current_balance': current_balance
                                                                                      }}})

                                # --------------------------------------- Cancel Instant orders -------------------------------------------------------
                                for k in db_instant.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                                    print("ok instant")
                                    pro = k['products']
                                    u_id = k['user_id']
                                    s_type = k['signin_type']
                                    try:
                                        sub_t = k['sub_total']
                                    except KeyError or ValueError:
                                        sub_t = 0
                                    try:
                                        dev_charges = k['delivery_charges']
                                    except KeyError or ValueError:
                                        dev_charges = 0
                                    total = int(sub_t) + int(dev_charges)
                                    count = 1
                                    for l in pro:
                                        type = l['package_type']
                                        if type in products:
                                            db_instant.update_many({'products.package_type': str(type)},
                                                                   {'$set': {'order_status': 'cancelled',
                                                                             'delivery_status': 'cancelled'}})
                                            for v in db_wallet.find():
                                                w_u_id = v['user_id']
                                                w_s_type = v['signin_type']
                                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                                        count = count + 1
                                                        ts = calendar.timegm(time.gmtime())
                                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                                        print(transaction_id)
                                                        current_balance = v['current_balance']
                                                        refund_amount = int(sub_t)
                                                        c_balance = int(refund_amount) + int(current_balance)
                                                        db_wallet.update_many({'user_id': int(v['user_id']),
                                                                               'signin_type': str(v['signin_type'])},
                                                                              {'$set': {
                                                                                  'current_balance': c_balance},
                                                                                  '$push': {
                                                                                      'recent_transactions': {
                                                                                          'amount': refund_amount,
                                                                                          'payment_type': "wallet",
                                                                                          'transaction_id': transaction_id,
                                                                                          'transaction_type': 'instant refund',
                                                                                          'transaction_date': date_time,
                                                                                          'order_id': k['instant_id'],
                                                                                          'status': 'success',
                                                                                          'closing_balance': c_balance,
                                                                                          'current_balance': current_balance
                                                                                      }}})
                                # ------------------------------------ Cancel Subscription orders -----------------------------------------------------
                                for a in db_subsc.find({'is_subscribed': True, 'subscription_status': 'active'}):
                                    pro = a['products']
                                    u_id = a['user_id']
                                    s_type = a['signin_type']
                                    try:
                                        sub_t = a['total_price']
                                    except KeyError or ValueError:
                                        sub_t = 0
                                    count = 1
                                    for b in pro:
                                        type = b['package_type']
                                        if type in products:
                                            db_subsc.update_many({'products.package_type': str(p_type)},
                                                                 {'$set': {'subscription_status': 'cancelled'}})
                                            for v in db_wallet.find():
                                                w_u_id = v['user_id']
                                                w_s_type = v['signin_type']
                                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                                        count = count + 1
                                                        ts = calendar.timegm(time.gmtime())
                                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                                        current_balance = v['current_balance']
                                                        subc_amount = v['subscription_amount']
                                                        refund_amount = subc_amount + current_balance
                                                        db_wallet.update_many({'user_id': int(v['user_id']),
                                                                               'signin_type': str(v['signin_type'])},
                                                                              {'$set': {
                                                                                  'subscription_amount': 0},
                                                                                  '$push': {
                                                                                      'recent_transactions': {
                                                                                          'amount': subc_amount,
                                                                                          'payment_type': "wallet",
                                                                                          'transaction_id': transaction_id,
                                                                                          'transaction_type': 'subscription refund',
                                                                                          'transaction_date': date_time,
                                                                                          'order_id': a[
                                                                                              'subscription_id'],
                                                                                          'status': 'success',
                                                                                          'current_balance': current_balance,
                                                                                          'closing_balance': current_balance
                                                                                      }}})
                            output.append(
                                {'company_id': id, 'active_status': active_status, 'plant_name': i['plant_name']})
                            return jsonify({"status": True, 'message': 'change status success', 'result': output})
            except KeyError or ValueError:
                pass
            output.append({'category_id': int(category_id), 'active_category': active_status})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid category id', 'result': output}))


# ------------------------------------------------- Add new plant -----------------------------------------------
@app.route('/owo/add_new_plant', methods=['POST'])
@jwt_required
def addNewPlant():
    data = mongo.db.OWO
    db = data.plant
    db_c = data.companies
    output = []
    city_name = request.json['city_name']
    # city_id = request.json['city_id']
    plant_name = request.json['plant_name']
    company_name = request.json['company_name']
    # company_id = request.json['company_id']
    brand_name = request.json['brand_name']
    # brand_id = request.json['brand_id']
    plant_address = request.json['plant_address']
    plant_location = request.json['plant_location']
    gst = request.json['gst']
    pan = request.json['pan']
    cin = request.json['cin']
    contact_person_name = request.json['contact_person_name']
    contact_person_email_id = request.json['contact_person_email_id']
    contact_person_contact_number = request.json['contact_person_contact_number']
    created_by_user_name = request.json['created_by_user_name']
    created_by_admin_role_id = request.json['created_by_admin_role_id']
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    active_status = request.json['active_status']
    plant_id_list = [i['plant_id'] for i in db.find()]
    if len(plant_id_list) is 0:
        plant_id = 1
    else:
        plant_id = int(plant_id_list[-1]) + 1
    for i in db.find():
        p_id = i['plant_id']
        p_name = i['plant_name']
        if str(plant_name) == str(p_name):
            return jsonify({'status': False, 'message': 'Plant name is already exist', 'result': output})
    for j in db_c.find():
        c_name = j['company_name']
        c_id = j['company_id']
        try:
            brand = j['brand']
            for k in brand:
                b_name = k['brand_name']
                b_id = k['brand_id']
                if str(company_name) == str(c_name):
                    if str(brand_name) == str(b_name):
                        db.insert_one({'city_name': city_name, 'company_id': c_id,
                                       'company_name': company_name, 'brand_name': brand_name, 'brand_id': b_id,
                                       'plant_id': plant_id, 'plant_name': plant_name,
                                       'plant_address': plant_address,
                                       'plant_location': plant_location, 'gst': gst, 'pan': pan, 'cin': cin,
                                       'contact_person_name': contact_person_name, 'active_status': active_status,
                                       'contact_person_email_id': contact_person_email_id,
                                       'contact_person_contact_number': contact_person_contact_number,
                                       'date_of_creation': date_of_creation,
                                       'created_by_user_name': created_by_user_name,
                                       'created_by_admin_role_id': int(created_by_admin_role_id)})
                        output.append({'city_name': city_name, 'company_id': c_id,
                                       'company_name': company_name, 'brand_name': brand_name, 'brand_id': b_id,
                                       'plant_id': plant_id, 'plant_name': plant_name,
                                       'plant_address': plant_address,
                                       'plant_location': plant_location, 'gst': gst, 'pan': pan, 'cin': cin,
                                       'contact_person_name': contact_person_name, 'active_status': active_status,
                                       'contact_person_email_id': contact_person_email_id,
                                       'contact_person_contact_number': contact_person_contact_number,
                                       'date_of_creation': date_of_creation,
                                       'created_by_user_name': created_by_user_name,
                                       'created_by_admin_role_id': int(created_by_admin_role_id)})
                        return jsonify({'status': True, 'message': 'Plant added successfully', 'result': output})
        except KeyError or ValueError:
            pass
    return jsonify({'status': False, 'message': 'Please enter a valid credentials', 'result': output})


# ----------------------------------------------------- Edit New Plant ------------------------------------------------
@app.route('/owo/edit_new_plant', methods=['POST'])
@jwt_required
def editNewPlant():
    data = mongo.db.OWO
    db = data.plant
    db_p = data.products
    db_a = data.Sub_Admin
    dbs_a = data.Super_Admin
    output = []
    plant_id = request.json['plant_id']
    city_name = request.json['city_name']
    plant_name = request.json['plant_name']
    company_name = request.json['company_name']
    brand_name = request.json['brand_name']
    plant_address = request.json['plant_address']
    plant_location = request.json['plant_location']
    gst = request.json['gst']
    pan = request.json['pan']
    cin = request.json['cin']
    contact_person_name = request.json['contact_person_name']
    contact_person_email_id = request.json['contact_person_email_id']
    contact_person_contact_number = request.json['contact_person_contact_number']
    created_by_user_name = request.json['created_by_user_name']
    created_by_admin_role_id = request.json['created_by_admin_role_id']
    modified_date = strftime("%d/%m/%Y %H:%M:%S")
    for i in db.find():
        p_id = i['plant_id']
        p_name = i['plant_name']
        if int(plant_id) == int(p_id):
            for j in dbs_a.find():
                roles_id = j['roles_id']
                if int(roles_id) == int(created_by_admin_role_id):
                    # print("success3")
                    db.update_many({'plant_id': int(plant_id)},
                                   {'$set': {'city_name': city_name,
                                             'company_name': company_name, 'brand_name': brand_name,
                                             'plant_name': plant_name, 'plant_address': plant_address,
                                             'plant_location': plant_location, 'gst': gst, 'pan': pan, 'cin': cin,
                                             'contact_person_name': contact_person_name,
                                             'contact_person_email_id': contact_person_email_id,
                                             'contact_person_contact_number': contact_person_contact_number,
                                             'modified_date': modified_date,
                                             'created_by_user_name': created_by_user_name,
                                             'created_by_admin_role_id': int(created_by_admin_role_id)}})
                    db_p.update_many({'plant_id': int(plant_id)},
                                     {'$set': {'plant_name': plant_name}})
                    output.append({'city_name': city_name,
                                   'company_name': company_name, 'brand_name': brand_name,
                                   'plant_id': plant_id, 'plant_name': plant_name, 'plant_address': plant_address,
                                   'plant_location': plant_location, 'gst': gst, 'pan': pan, 'cin': cin,
                                   'contact_person_name': contact_person_name,
                                   'contact_person_email_id': contact_person_email_id,
                                   'contact_person_contact_number': contact_person_contact_number,
                                   'modified_date': modified_date, 'created_by_user_name': created_by_user_name,
                                   'created_by_admin_role_id': int(created_by_admin_role_id)})
                    return jsonify({'status': True, 'message': 'Plant updated successfully', 'result': output})
            for k in db_a.find():
                roles_id = k['roles_id']
                if int(roles_id) == int(created_by_admin_role_id):
                    db.update_many({'plant_id': int(plant_id), 'plant_name': str(plant_name)},
                                   {'$set': {'city_name': city_name,
                                             'plant_id': plant_id, 'plant_name': plant_name,
                                             'plant_address': plant_address,
                                             'plant_location': plant_location, 'gst': gst, 'pan': pan, 'cin': cin,
                                             'contact_person_name': contact_person_name,
                                             'contact_person_email_id': contact_person_email_id,
                                             'contact_person_contact_number': contact_person_contact_number,
                                             'modified_date': modified_date,
                                             'created_by_user_name': created_by_user_name,
                                             'created_by_admin_role_id': int(created_by_admin_role_id)}})
                    db_p.update_many({'plant_id': int(plant_id)},
                                     {'$set': {'plant_name': plant_name}})
                    output.append({'city_name': city_name,
                                   'company_name': company_name, 'brand_name': brand_name,
                                   'plant_id': plant_id, 'plant_name': plant_name, 'plant_address': plant_address,
                                   'plant_location': plant_location, 'gst': gst, 'pan': pan, 'cin': cin,
                                   'contact_person_name': contact_person_name,
                                   'contact_person_email_id': contact_person_email_id,
                                   'contact_person_contact_number': contact_person_contact_number,
                                   'modified_date': modified_date, 'created_by_user_name': created_by_user_name,
                                   'created_by_admin_role_id': int(created_by_admin_role_id)})
                    return jsonify({'status': True, 'message': 'Plant updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid credentials', 'result': output})


# ---------------------------------------------------- Get All Plants ------------------------------------------------
@app.route('/owo/get_plant', methods=['GET'])
def getPlant():
    data = mongo.db.OWO
    db = data.plant
    output = []
    for i in db.find():
        output.append({'city_name': i['city_name'], 'company_id': i['company_id'],
                       'company_name': i['company_name'], 'brand_name': i['brand_name'], 'brand_id': i['brand_id'],
                       'plant_id': i['plant_id'], 'plant_name': i['plant_name'], 'plant_address': i['plant_address'],
                       'plant_location': i['plant_location'], 'gst': i['gst'], 'pan': i['pan'], 'cin': i['cin'],
                       'contact_person_name': i['contact_person_name'], 'active_status': i['active_status'],
                       'contact_person_email_id': i['contact_person_email_id'],
                       'contact_person_contact_number': i['contact_person_contact_number'],
                       'date_of_creation': i['date_of_creation'], 'created_by_user_name': i['created_by_user_name'],
                       'created_by_admin_role_id': i['created_by_admin_role_id']
                       })
    return jsonify({'status': True, 'message': 'Plant data get successfully', 'result': output})


# --------------------------------------------------- Get Plant by ID ------------------------------------------------
@app.route('/owo/get_plant_by_id/<plant_id>', methods=['GET'])
def getPlantById(plant_id):
    data = mongo.db.OWO
    db = data.plant
    output = []
    for i in db.find():
        p_id = i['plant_id']
        if int(plant_id) == int(p_id):
            output.append({'city_name': i['city_name'], 'company_id': i['company_id'],
                           'company_name': i['company_name'], 'brand_name': i['brand_name'], 'brand_id': i['brand_id'],
                           'plant_name': i['plant_name'], 'plant_address': i['plant_address'],
                           'plant_location': i['plant_location'], 'gst': i['gst'], 'pan': i['pan'], 'cin': i['cin'],
                           'contact_person_name': i['contact_person_name'], 'active_status': i['active_status'],
                           'contact_person_email_id': i['contact_person_email_id'], 'plant_id': plant_id,
                           'contact_person_contact_number': i['contact_person_contact_number'],
                           'date_of_creation': i['date_of_creation'], 'created_by_user_name': i['created_by_user_name'],
                           'created_by_admin_role_id': i['created_by_admin_role_id']
                           })
            return jsonify({'status': True, 'message': 'Plant data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid plant_id', 'result': output})


# ------------------------------------------------- Delete Plant ------------------------------------------------------
@app.route('/owo/delete_plant', methods=['POST'])
@jwt_required
def deletePlant():
    data = mongo.db.OWO
    db = data.plant
    output = []
    plant_id = request.json['plant_id']
    for i in db.find():
        p_id = i['plant_id']
        if int(plant_id) == int(p_id):
            db.remove({'plant_id': int(plant_id)})
            output.append({'plant_id': int(plant_id), 'plant_name': i['plant_name']})
            return jsonify({'status': True, 'message': 'Plant deleted successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Plant_id not found', 'result': output})


# ------------------------------------------------- List of Plant Names ----------------------------------------------
@app.route('/owo/list_of_plant_name', methods=['GET'])
def listOfPlantNames():
    data = mongo.db.OWO
    db = data.plant
    output = []
    for i in db.find({'active_status': True}):
        output.append({'plant_name': i['plant_name'], 'plant_id': i['plant_id']})
    return jsonify({'status': True, 'message': 'List of plant names', 'result': output})


# ------------------------------------------- Corporate user registration ---------------------------------------------
@app.route('/owo/Admin_adding_corporate_users', methods=["POST"])
@jwt_required
def adminAddingCorporateUserRegistration():
    data = mongo.db.OWO
    db = data.corporate_users
    user_wallet = data.owo_users_wallet
    output = []
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    session_id = request.json['session_id']
    password = request.json['password']
    confirm_password = request.json['confirm_password']
    signin_type = request.json['signin_type']
    date_of_join = request.json['date_of_join']
    company_name = request.json['company_name']
    gst_number = request.json['gst_number']
    state = request.json['state']
    official_email_id = request.json['official_email_id']
    contact_number = request.json['contact_number']
    legal_name_of_business = request.json['legal_name_of_business']
    pan_number = request.json['pan_number']
    building_number = request.json['building_number']
    address = request.json['address']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    landmark = request.json['landmark']
    city_name = request.json['city_name']
    address_type = request.json['address_type']
    email_result = db.find({'email_id': official_email_id})
    mobile_result = db.find({'mobile_number': int(contact_number)})
    name = str(first_name) + str(last_name)
    if str(password) == str(confirm_password):

        # -------------------------------------------- invite_code ----------------------------------------------------

        invite_code = name[:2].upper() + str(random.randint(10, 99)) + name[2:4].upper() + str(random.randint(10, 99))
        # print(invite_code)

        # ----------------------------------- User system Id generate -------------------------------------------------
        try:
            user_id_list = [i['user_id'] for i in db.find()]
            if len(user_id_list) is 0:
                user_id = 1
            else:
                user_id = int(user_id_list[-1]) + 1
        except KeyError or ValueError:
            user_id = int(1)

        # ----------------------------------- Wallet system Id generate -----------------------------------------------
        try:
            wallet_id_list = [i['wallet_id'] for i in user_wallet.find()]
            if len(wallet_id_list) is 0:
                wallet_id = 1
            else:
                wallet_id = int(wallet_id_list[-1]) + 1
        except KeyError or ValueError:
            wallet_id = int(1)

        # -------------------------------------- Generate Address Id --------------------------------------------------
        try:
            address_id_list = [l['address_id'] for l in db.find()]
            if len(address_id_list) is 0:
                address_id = 1
            else:
                address_id = int(address_id_list[-1]) + 1
        except KeyError or ValueError:
            address_id = int(1)

        # ------------------------------------ Checks the user is registered ------------------------------------------
        if email_result.count() != 0 or mobile_result.count() != 0:
            return jsonify({'status': False, 'message': 'User already existed'})
        else:
            db.insert_one({'first_name': first_name, 'last_name': last_name, 'mobile_number': int(contact_number),
                           'email_id': str(official_email_id),
                           'password': password, 'confirm_password': confirm_password,
                           'company_name': company_name, 'gst_number': str(gst_number), 'session_id': session_id,
                           'user_id': int(user_id), 'legal_name_of_business': legal_name_of_business,
                           'pan_number': str(pan_number), 'date_of_join': date_of_join, 'state': state,
                           'signin_type': signin_type, 'email_verified': 0, 'mobile_verified': 0,
                           'wallet_id': wallet_id, 'active_user': True, 'invite_code': invite_code,
                           'user_address': [{'building_number': building_number, 'address_type': address_type,
                                             'address_id': address_id, 'city_name': city_name,
                                             'address': address, 'latitude': str(latitude), 'longitude': str(longitude),
                                             'landmark': landmark, 'default_address': True}]
                           })
            user_wallet.insert_one({'wallet_id': wallet_id, 'signin_type': signin_type, 'user_id': user_id,
                                    'current_balance': 0})
            output.append({'first_name': first_name, 'last_name': last_name, 'mobile_number': int(contact_number),
                           'official_email_id': official_email_id, 'company_name': company_name,
                           'gst_number': str(gst_number), 'session_id': session_id,
                           'user_id': user_id, 'active_user': True, 'city_name': city_name,
                           'legal_name_of_business': legal_name_of_business, 'pan_number': pan_number,
                           'date_of_join': date_of_join, 'state': state, 'signin_type': signin_type,
                           'wallet_id': wallet_id, 'building_number': building_number, 'address_id': address_id,
                           'address': address, 'latitude': latitude, 'longitude': longitude,
                           'address_type': address_type, 'landmark': landmark})
            return jsonify({'status': True, 'message': 'User register successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Confirm password does not match', 'result': output})


# ------------------------------------ edit_corporate_user ------------------------------------------------------------
@app.route('/owo/edit_corporate_user', methods=["POST"])
@jwt_required
def editCorporateUsers():
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    user_id = request.json['user_id']
    address_id = request.json['address_id']
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    mobile_number = request.json['mobile_number']
    email_id = request.json['email_id']
    building_number = request.json['building_number']
    address = request.json['address']
    state = request.json['state']
    landmark = request.json['landmark']
    address_type = request.json['address_type']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    city_name = request.json['city_name']
    date_of_modified = strftime("%d/%m/%Y %H:%M:%S")
    info = db.find()
    for i in info:
        u_id = i['user_id']
        m_number = i['mobile_number']
        e_id = i['email_id']
        try:
            u_address = i['user_address']
            for j in u_address:
                a_id = j['address_id']
                if str(u_id) == str(user_id) and str(a_id) == str(address_id):
                    # print("ok")
                    if str(m_number) == str(mobile_number) and str(email_id) == str(e_id):
                        # print("ok..")
                        db.find_one_and_update({'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                               {'$set': {'first_name': first_name,
                                                         'last_name': last_name,
                                                         'mobile_number': int(mobile_number),
                                                         'email_id': str(email_id),
                                                         'state': state,
                                                         'modified_on': date_of_modified,
                                                         'email_verified': i['email_verified'],
                                                         'mobile_verified': i['mobile_verified'],
                                                         'user_address.$.building_number': building_number,
                                                         'user_address.$.address': address,
                                                         'user_address.$.city_name': city_name,
                                                         'user_address.$.landmark': landmark,
                                                         'user_address.$.latitude': str(latitude),
                                                         'user_address.$.longitude': str(longitude),
                                                         'user_address.$.address_type': address_type
                                                         }})
                        output.append({'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                       'mobile_number': int(mobile_number),
                                       'email_id': str(email_id), 'building_number': building_number,
                                       'address_id': int(address_id), 'city_name': city_name,
                                       'state': state, 'address': address, 'latitude': latitude, 'longitude': longitude,
                                       'landmark': landmark, 'address_type': address_type,
                                       'modified_on': date_of_modified})
                        return jsonify({"status": True, "message": 'Profile updated', 'result': output,
                                        'email_verified': i['email_verified'], 'mobile_verified': i['mobile_verified']})
                    else:
                        if str(m_number) != str(mobile_number) and str(email_id) != str(e_id):
                            db.find_one_and_update(
                                {'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                {'$set': {'first_name': first_name,
                                          'last_name': last_name,
                                          'mobile_number': int(mobile_number),
                                          'email_id': str(email_id),
                                          'modified_on': date_of_modified,
                                          'state': state,
                                          'email_verified': 0,
                                          'mobile_verified': 0,
                                          'user_address.$.building_number': building_number,
                                          'user_address.$.address': address,
                                          'user_address.$.landmark': landmark,
                                          'user_address.$.city_name': city_name,
                                          'user_address.$.latitude': str(latitude),
                                          'user_address.$.longitude': str(longitude),
                                          'user_address.$.address_type': address_type}})
                            output.append(
                                {'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                 'mobile_number': str(mobile_number), 'city_name': city_name,
                                 'email_id': str(email_id), 'building_number': building_number, 'state': state,
                                 'address': address, 'address_id': int(address_id), ''
                                                                                    'landmark': landmark,
                                 'address_type': address_type, 'modified_on': date_of_modified})
                            return jsonify(
                                {'status': True, 'message': 'Profile updated please verify mobile number and email_id',
                                 'result': output,
                                 'email_verified': 0, 'mobile_verified': 0})
                        elif str(m_number) != str(mobile_number):
                            db.find_one_and_update(
                                {'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                {'$set': {'first_name': first_name,
                                          'last_name': last_name,
                                          'mobile_number': int(mobile_number),
                                          'email_id': str(email_id),
                                          'modified_on': date_of_modified,
                                          'state': state,
                                          'email_verified': i['email_verified'],
                                          'mobile_verified': 0,
                                          'user_address.$.building_number': building_number,
                                          'user_address.$.address': address,
                                          'user_address.$.city_name': city_name,
                                          'user_address.$.latitude': str(longitude),
                                          'user_address.$.longitude': str(longitude),
                                          'user_address.$.landmark': landmark,
                                          'user_address.$.address_type': address_type}})
                            output.append(
                                {'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                 'mobile_number': str(mobile_number), 'city_name': city_name,
                                 'email_id': str(email_id), 'building_number': building_number, 'state': state,
                                 'address': address, 'address_id': int(address_id),
                                 'landmark': landmark, 'address_type': address_type, 'modified_on': date_of_modified})
                            return jsonify({"status": True, "message": 'Profile updated please verify mobile number',
                                            'result': output, 'email_verified': i['email_verified'],
                                            'mobile_verified': 0})
                        elif str(email_id) != str(e_id):
                            db.find_one_and_update(
                                {'user_id': int(user_id), 'user_address.address_id': int(address_id)},
                                {'$set': {'first_name': first_name,
                                          'last_name': last_name,
                                          'mobile_number': int(mobile_number),
                                          'email_id': str(email_id),
                                          'modified_on': date_of_modified,
                                          'email_verified': 0,
                                          'mobile_verified': i['mobile_verified'],
                                          'state': state,
                                          'user_address.$.building_number': building_number,
                                          'user_address.$.address': address,
                                          'user_address.$.latitude': str(longitude),
                                          'user_address.$.longitude': str(longitude),
                                          'user_address.$.landmark': landmark,
                                          'user_address.$.city_name': city_name,
                                          'user_address.$.address_type': address_type}})
                            output.append({'user_id': user_id, 'first_name': first_name, 'last_name': last_name,
                                           'address_id': int(address_id), 'city_name': city_name,
                                           'mobile_number': str(mobile_number), 'email_id': str(email_id),
                                           'building_number': building_number, 'state': state, 'address': address,
                                           'landmark': landmark, 'address_type': address_type,
                                           'modified_on': date_of_modified})
                            return jsonify({'status': True, 'message': 'Profile updated please verify email_id',
                                            'result': output, 'email_verified': 0,
                                            'mobile_verified': i['mobile_verified']})
        except KeyError or ValueError:
            u_address = 0
    else:
        return jsonify({"status": False, "message": 'Invalid user id', 'result': output})


# --------------------------------------- send email OTP corporate users ----------------------------------------------
@app.route('/owo/send_email_otp_corporate', methods=['POST'])
@jwt_required
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
                return jsonify({'status': True, 'message': 'Otp send successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid email_id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# -------------------------------------- Verify email OTP corporate user ----------------------------------------------
@app.route('/owo/verify_email_otp_corporate', methods=['POST'])
@jwt_required
def verifyEmailOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    email_otp_entered = request.json['email_otp_entered']
    official_email_id = request.json['official_email_id']
    output = []
    details = coll.find()
    print("ok")
    for j in details:
        if str(official_email_id) == str(j['email_id']) and str(email_otp_entered) == str(j['email_otp']):
            print("otp")
            coll.update_many({'email_id': official_email_id}, {'$set': {'email_verified': 1}})
            output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'], 'first_name': j['first_name'],
                           'last_name': j['last_name'], 'company_name': j['company_name'],
                           'gst_number': j['gst_number'],
                           'session_id': j['session_id'], 'pan_number': j['pan_number'],
                           'date_of_join': j['date_of_join'], 'state': j['state'],
                           'signin_type': j['signin_type'], 'wallet_id': j['wallet_id'],
                           'contact_number': j['mobile_number'], 'otp_entered': j['email_otp']})
            return jsonify({'status': True, 'message': 'Email otp verified successfully', 'result': output,
                            'email_verified': 1, 'mobile_verified': j['mobile_verified']})
    else:
        return jsonify({'status': False, 'message': 'Invalid otp', 'result': output})


# ---------------------------------------------- send mobile OTP corporate user ----------------------------------------
@app.route('/owo/send_mobile_otp_corporate', methods=['POST'])
@jwt_required
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
                return jsonify({'status': True, 'message': 'Otp resend successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Individual mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# --------------------------------------------- Verify mobile OTP corporate user ---------------------------------------
@app.route('/owo/verify_mobile_otp_corporate', methods=['POST'])
@jwt_required
def verifyMobileOTP_corporate():
    data = mongo.db.OWO
    coll = data.corporate_users
    otp_entered = request.json['otp_entered']
    mobile_number = request.json['mobile_number']
    output = []
    details = coll.find()
    print("ok")
    for j in details:
        print('oki')
        if str(mobile_number) == str(j['mobile_number']) and str(otp_entered) == str(j['otp']):
            coll.update_many({'mobile_number': int(mobile_number)}, {'$set': {'mobile_verified': 1}})
            output.append({'user_id': j['user_id'], 'official_email_id': j['email_id'], 'first_name': j['first_name'],
                           'last_name': j['last_name'], 'company_name': j['company_name'],
                           'gst_number': j['gst_number'],
                           'session_id': j['session_id'], 'pan_number': j['pan_number'],
                           'date_of_join': j['date_of_join'], 'state': j['state'],
                           'signin_type': j['signin_type'], 'wallet_id': j['wallet_id'],
                           'contact_number': j['mobile_number'], 'otp_entered': j['otp']})
            return jsonify({'status': True, 'message': 'User mobile otp verified successfully', 'result': output,
                            'mobile_verified': 1, 'email_verified': j['email_verified']})
    else:
        return jsonify({'status': False, 'message': 'Invalid otp', 'result': output})


# ------------------------------------------ Resend Email OTP for corporate user -------------------------------------
@app.route('/owo/resend_email_otp_corporate', methods=['POST'])
@jwt_required
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
                return jsonify({'status': True, 'message': 'Otp send successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid email_id'})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ----------------------------------- Resend Mobile OTP for corporate user --------------------------------------------
@app.route('/owo/resend_mobile_otp_corporate', methods=['POST'])
@jwt_required
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
                return jsonify({'status': True, 'message': 'Otp resend successfully', 'result': output})
        else:
            return jsonify({'status': False, 'message': 'Invalid mobile number'})
    except Exception as e:
        return jsonify(status=False, message=str(e))



# ----------------------------------------------------- Get Corporate User  -------------------------------------------
@app.route('/owo/get_customers', methods=['POST', 'GET'])
def get_corporateCustomer():
    try:
        data = mongo.db.OWO
        db = data.corporate_users
        details = db.find(sort=[('user_id', pymongo.ASCENDING)])
        output = []
        for i in details:
            temp = {}
            temp['user_id'] = i['user_id']
            temp['first_name'] = i['first_name']
            temp['last_name'] = i['last_name']
            temp['email_id'] = i['email_id']
            temp['company_name'] = i['company_name']
            temp['gst_number'] = i['gst_number']
            temp['legal_name_of_business'] = i['legal_name_of_business']
            temp['pan_number'] = i['pan_number']
            temp['email_verified'] = i['email_verified']
            temp['mobile_verified'] = i['mobile_verified']
            temp['mobile_number'] = i['mobile_number']
            temp['date_of_join'] = i['date_of_join']
            # temp['date_of_creation'] = i['date_of_creation']
            if 'active_user' not in i.keys():
                temp['active_user'] = ''
            else:
                temp['active_user'] = i['active_user']
            if 'profile_pic' not in i.keys():
                temp['profile_pic'] = ''
            else:
                temp['profile_pic'] = i['profile_pic']
            output.append(temp)
        return jsonify({"status": True, 'message': 'Get customers success', 'result': output})
    except Exception as e:
        return jsonify(status=False, message=str(e))


# ---------------------------------------- Get Profile Corporate -----------------------------------------------------
@app.route('/owo/get_corporate_user/<user_id>', methods=['GET'])
def get_profile_corporate(user_id):
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    for i in db.find():
        u_id = i['user_id']
        if int(u_id) == int(user_id):
            user_id = i['user_id']
            first_name = i['first_name']
            last_name = i['last_name']
            mobile_number = i['mobile_number']
            email_id = i['email_id']
            company_name = i['company_name']
            gst_number = i['gst_number']
            legal_name_of_business = i['legal_name_of_business']
            pan_number = i['pan_number']
            state = i['state']
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
                            try:
                                city_name = j['city_name']
                            except KeyError or ValueError:
                                city_name = ''
                            default_address = j['default_address']
                            address_type = j['address_type']
                            output.append({'user_id': user_id, 'first_name': first_name,
                                           'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                           'company_name': company_name, 'gst_number': gst_number,
                                           'legal_name_of_business': legal_name_of_business, 'pan_number': pan_number,
                                           'state': state, 'building_number': building_number, 'address_id': address_id,
                                           'address': address, 'landmark': landmark, 'latitude': latitude,
                                           'longitude': longitude, 'default_address': default_address,
                                           'city_name': city_name,
                                           'address_type': address_type})
                            return jsonify({'status': True, 'message': 'Corporate user data get successfully',
                                            'result': output})
                    except KeyError or ValueError:
                        pass
                        output.append({'user_id': user_id, 'first_name': first_name,
                                       'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                                       'company_name': company_name, 'gst_number': gst_number,
                                       'legal_name_of_business': legal_name_of_business, 'pan_number': pan_number,
                                       'state': state})
                        return jsonify(
                            {'status': True, 'message': 'Corporate user data get successfully', 'result': output})
            except KeyError or ValueError:
                pass
            output.append({'user_id': user_id, 'first_name': first_name,
                           'last_name': last_name, 'mobile_number': mobile_number, 'email_id': email_id,
                           'company_name': company_name, 'gst_number': gst_number,
                           'legal_name_of_business': legal_name_of_business, 'pan_number': pan_number,
                           'state': state})
            return jsonify({'status': True, 'message': 'Corporate user data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid user_id', 'result': output})


# --------------------------------------- delete corporate user --------------------------------------------------------
@app.route('/owo/delete_corporate_user', methods=['POST'])
@jwt_required
def delete_corporate_user():
    data = mongo.db.OWO
    db = data.corporate_users

    user_id = request.json['user_id']

    for i in db.find():
        u_id = i['user_id']
        if int(u_id) == int(user_id):
            db.remove({'user_id': user_id})
            return jsonify({'status': True, 'message': 'User deleted'})
    return jsonify({'status': False, 'message': 'User not found'})


# ----------------------------------------------- corporate user status change ----------------------------------------
@app.route('/owo/corporateUser_change_status', methods=['POST'])
@jwt_required
def enableDisableCorporateUser():
    data = mongo.db.OWO
    db = data.corporate_users
    output = []
    user_id = request.json['user_id']
    active_user = request.json['active_user']
    for i in db.find():
        u_id = i['user_id']
        if str(u_id) == str(user_id):
            db.update_many({'user_id': int(user_id)}, {'$set': {'active_user': active_user}})
            output.append({'user_id': int(user_id), 'active_user': active_user})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid user id', 'result': output}))


# ------------------------------------------------------ FAQ Management ------------------------------------------------
# ------------------------------------------------------ Add Question --------------------------------------------------
@app.route('/owo/add_question', methods=['POST'])
@jwt_required
def addQuestion():
    data = mongo.db.OWO
    db = data.FAQ_management
    question_id = int(1)
    output = []
    admin_id = request.json['admin_id']
    admin_userName = request.json['admin_userName']
    question_title = request.json['question_title']
    question_category = request.json['question_category']
    question_description = request.json['question_description']
    date_of_creation = time.strftime("%d/%m/%Y %H:%M:%S")
    for i in db.find():
        q_category = i['question_category']
        try:
            category = i['category']
        except KeyError or ValueError:
            category = 0
        if str(question_category) == str(q_category):
            if category != 0:
                question_id_list = [i['question_id'] for i in category]
                if len(question_id_list) is 0:
                    question_id = 1
                else:
                    question_id = int(question_id_list[-1]) + 1
                db.update_many({'question_category': question_category, 'active_question': True},
                               {'$push': {'category':
                                              {'question_title': question_title, 'admin_id': int(admin_id),
                                               'admin_userName': admin_userName,
                                               'question_description': question_description,
                                               'question_id': int(question_id),
                                               'date_of_creation': date_of_creation, 'modified_on': " ",
                                               'question_status': True}}})
                output.append(
                    {'admin_id': int(admin_id), 'admin_username': admin_userName, 'question_title': question_title,
                     'question_description': question_description, 'question_category': question_category,
                     'question_id': int(question_id), 'date_of_creation': date_of_creation, 'modified_on': " ",
                     'active_question': True})
                return jsonify({'status': True, 'message': 'Question added', 'result': output})

    db.insert(
        {'question_category': question_category, 'active_question': True,
         'category': [{'question_title': question_title, 'question_description': question_description,
                       'admin_id': int(admin_id), 'admin_userName': admin_userName,
                       'question_id': int(question_id), 'date_of_creation': date_of_creation, 'modified_on': " ",
                       'question_status': True}]})
    output.append({'admin_id': int(admin_id), 'admin_userName': admin_userName, 'question_title': question_title,
                   'question_category': question_category, 'question_description': question_description,
                   'question_id': int(question_id), 'date_of_creation': date_of_creation, 'modified_on': " ",
                   'active_question': True})
    return jsonify({'status': True, 'message': 'Question added', 'result': output})


# ----------------------------------------------------- Edit_Question --------------------------------------------------
@app.route('/owo/edit_question', methods=['POST'])
@jwt_required
def editQuestion():
    data = mongo.db.OWO
    db = data.FAQ_management
    output = []
    admin_id = request.json['admin_id']
    question_id = request.json['question_id']
    question_title = request.json['question_title']
    question_category = request.json['question_category']
    question_description = request.json['question_description']
    admin_userName = request.json['admin_userName']
    modified_on = time.strftime("%d/%m/%Y %H:%M:%S")
    info = db.find()
    for i in info:
        q_category = i['question_category']
        category = i['category']
        for j in category:
            q_id = j['question_id']
            if str(q_category) == str(question_category) and int(q_id) == int(question_id):
                db.find_one_and_update({'question_category': str(question_category),
                                        'category.question_id': int(question_id)},
                                       {'$set': {'category.$.admin_userName': admin_userName,
                                                 'category.$.admin_id': int(admin_id),
                                                 'category.$.question_title': question_title,
                                                 'category.$.question_description': question_description,
                                                 'category.$.modified_on': modified_on}})
                output.append({'question_title': question_title, 'modified_by': int(admin_id),
                               'question_description': question_description,
                               'question_category': question_category, 'question_id': int(question_id),
                               'modified_on': modified_on, 'admin_userName': admin_userName})
                return jsonify({'status': True, 'message': 'Question edited', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid question_id', 'result': output})


# ------------------------------------------------- Get all questions ---------------------------------------------------
@app.route('/owo/get_all_questions', methods=['GET'])
def getAllQuestions():
    data = mongo.db.OWO
    db = data.FAQ_management
    output = []
    for i in db.find():
        for j in i['category']:
            temp = {}
            temp['question_id'] = j['question_id']
            temp['question_title'] = j['question_title']
            temp['question_category'] = i['question_category']
            temp['question_description'] = j['question_description']
            temp['date_of_creation'] = j['date_of_creation']
            temp['admin_id'] = j['admin_id']
            temp['admin_userName'] = j['admin_userName']
            temp['question_status'] = j['question_status']
            if 'modified_on' not in j.keys():
                temp['modified_on'] = ''
            else:
                temp['modified_on'] = j['modified_on']
            if 'modified_by' not in j.keys():
                temp['modified_by'] = ''
            else:
                temp['modified_by'] = j['modified_by']
            output.append(temp)
    return jsonify({'status': True, 'message': 'Question data get successfully', 'result': output})


# ----------------------------------------- Delete Question -----------------------------------------------------------
@app.route('/owo/delete_question', methods=['POST'])
@jwt_required
def delete_question():
    data = mongo.db.OWO
    db = data.FAQ_management
    output = []
    question_id = request.json['question_id']
    question_category = request.json['question_category']
    for i in db.find():
        q_category = i['question_category']
        try:
            category = i['category']
            for j in category:
                q_id = j['question_id']
                if str(q_id) == str(j['question_id']) and str(q_category) == str(question_category):
                    print(q_id)
                    db.update_one({'question_category': str(question_category)},
                                  {'$pull': {'category': {'question_id': int(question_id)}}})
                    return jsonify({'status': True, 'message': 'Deleted question success', 'result': output})
        except KeyError or ValueError:
            pass
    return jsonify({'status': False, 'message': 'Invalid credential', 'result': output})


# ---------------------------------------------------Get Question By ID -----------------------------------------------
@app.route('/owo/get_question_by_id', methods=['POST'])
@jwt_required
def getQuestionByID():
    data = mongo.db.OWO
    db = data.FAQ_management
    output = []
    question_id = request.json['question_id']
    question_category = request.json['question_category']
    info = db.find()
    for j in info:
        q_category = j['question_category']
        print(q_category)
        try:
            category = j['category']
        except KeyError or ValueError:
            category = 0
        for i in category:
            q_id = i['question_id']
            if str(q_category) == str(question_category):
                if int(q_id) == int(question_id):
                    temp = {}
                    temp['question_id'] = i['question_id']
                    temp['question_title'] = i['question_title']
                    temp['question_category'] = j['question_category']
                    temp['question_description'] = i['question_description']
                    temp['date_of_creation'] = i['date_of_creation']
                    temp['admin_id'] = i['admin_id']
                    temp['admin_userName'] = i['admin_userName']
                    if 'modified_on' not in i.keys():
                        temp['modified_on'] = ''
                    else:
                        temp['modified_on'] = i['modified_on']
                    if 'modified_by' not in i.keys():
                        temp['modified_by'] = ''
                    else:
                        temp['modified_by'] = i['modified_by']
                    output.append(temp)
                    return jsonify({'status': True, 'message': 'FAQ data get successfully', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid question id', 'result': output})


# ------------------------------------------- question change active status --------------------------------------------
@app.route('/owo/question_change_active_status', methods=['POST'])
@jwt_required
def enableDisableQuestion():
    data = mongo.db.OWO
    db = data.FAQ_management
    output = []
    question_category = request.json['question_category']
    question_id = request.json['question_id']
    question_status = request.json['question_status']
    for i in db.find():
        q_category = i['question_category']
        if str(q_category) == str(question_category):
            try:
                category = i['category']
            except KeyError or ValueError:
                category = 0
            for j in category:
                q_id = j['question_id']
                if int(q_id) == int(question_id):
                    db.update_many({'question_category': question_category, 'category.question_id': int(question_id)},
                                   {'$set': {'category.$.question_status': question_status}})
                    output.append({'question_category': question_category, 'question_status': question_status})
                    return jsonify(
                        ({'status': True, 'message': 'Active status changed successfully', 'result': output}))

    return jsonify(({'status': False, 'message': 'Invalid question category', 'result': output}))


# ---------------------------------------------------------- uploading_files -------------------------------------------
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD = os.path.join(APP_ROOT, 'files')
if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
FILE_ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'doc', 'docx'])
UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def alloweded_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in FILE_ALLOWED_EXTENSIONS


@app.route('/owo/uploading_page_contant_files/<page_title>', methods=['POST'])
@jwt_required
def pageContactFiles(page_title):
    data = mongo.db.OWO
    db1 = data.page_contant_management
    output = []
    id_list = [i['id'] for i in db1.find()]
    if len(id_list) is 0:
        id = 1
    else:
        id = int(id_list[-1]) + 1
    for j in db1.find():
        p_title = j['page_title']
        if str(p_title) == str(page_title):
            return jsonify({'status': False, 'message': 'Page title already exist', 'result': output})
    if request.method == 'POST':
        file = request.files['file']
        print("ok")
        filename = secure_filename(file.filename)
        mongo_db_path = "/owo/files/" + filename
        print("ok1")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        target = file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file.save(target)
        print("ok2")
        db1.insert({'id': int(id), 'page_title': page_title, 'file_path': mongo_db_path})
        output.append({'id': int(id), 'page_title': page_title, 'file_path': mongo_db_path})
        return jsonify({"status": True, "result": output, "message": 'File data saved successfully'})
    return jsonify({'status': False, 'message': 'Some error occured', 'result': output})


# ---------------------------------------------- Edit_Page_Contant File ----------------------------------------------
@app.route('/owo/edit_page_contant_file/<id>', methods=['POST'])
@jwt_required
def editPageContantFile(id):
    data = mongo.db.OWO
    db = data.page_contant_management
    output = []
    for i in db.find():
        f_id = i['id']
        if str(id) == str(f_id):
            if request.method == 'POST':
                file = request.files['file']
                filename = secure_filename(file.filename)
                mongo_db_path = "/owo/files/" + filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                target = file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file.save(target)
                db.find_one_and_update({'id': int(id)}, {'$set': {'file_path': mongo_db_path}})
                output.append({'id': int(id), 'page_title': i['page_title'], 'file_path': mongo_db_path})
                return jsonify({"status": True, "result": output, "message": 'File data updated successfully'})

            return jsonify({'status': False, 'message': 'Some error occured', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid id', 'result': output})


# ----------------------------------------------------- Delete Page Contant File --------------------------------------
@app.route('/owo/delete_page_contant_file/<id>', methods=['POST'])
@jwt_required
def deletePageContantFile(id):
    data = mongo.db.OWO
    db = data.page_contant_management
    output = []
    for i in db.find():
        f_id = i['id']
        if str(f_id) == str(id):
            db.remove({'id': int(id)})
            return jsonify({'status': True, 'message': 'File deleted successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid id', 'result': output})


# ------------------------------------------------------------ Get_Page_Contant_File -----------------------------------
@app.route('/owo/get_page_contant_files', methods=['GET'])
def getPageContantFiles():
    data = mongo.db.OWO
    db = data.page_contant_management
    output = []
    for i in db.find():
        output.append({'id': i['id'], 'page_title': i['page_title'], 'file_path': i['file_path']})
    return jsonify({'status': True, 'message': 'Files data get', 'result': output})


# --------------------------------------------------- Get Page Contant By ID ------------------------------------------
@app.route('/owo/get_page_contant/<id>', methods=['GET'])
def getPageContantById(id):
    data = mongo.db.OWO
    db = data.page_contant_management
    output = []
    for i in db.find():
        f_id = i['id']
        if str(f_id) == str(id):
            output.append({'id': i['id'], 'page_title': i['page_title'], 'file_path': i['file_path']})
            return jsonify({'status': True, 'message': 'File data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid id', 'result': output})


# ------------------------------------------- Add delivery charges -----------------------------------------------------
@app.route('/owo/add_delivery_charge', methods=['POST'])
@jwt_required
def adddeliverycharge():
    data = mongo.db.OWO
    db_dc = data.delivery_charge_management
    output = []
    delivery_type = request.json['delivery_type']
    lower_range = request.json['lower_range']
    upper_range = request.json['upper_range']
    delivery_charge = request.json['delivery_charge']
    delivery_added_date = time.strftime("%d/%m/%Y %H:%M:%S")
    delivery_id_list = [i['delivery_id'] for i in db_dc.find()]
    if len(delivery_id_list) is 0:
        delivery_id = 1
    else:
        delivery_id = int(delivery_id_list[-1]) + 1
    if str(delivery_type) == "subscription-individual":
        for i in db_dc.find():
            if str(delivery_type) == str(i['delivery_type']):
                if int(lower_range) == int(i['lower_range']) or int(upper_range) == int(i['upper_range']):
                    output.append({'delivery_type': i['delivery_type'], 'lower_range': int(lower_range),
                                   'upper_range': int(upper_range),
                                   'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id']})
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
                if i['lower_range'] <= int(lower_range) <= i['upper_range'] or \
                        i['lower_range'] <= int(upper_range) <= i['upper_range']:
                    output.append({'delivery_type': i['delivery_type'], 'lower_range': int(lower_range),
                                   'upper_range': int(upper_range),
                                   'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id']})
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
        if int(lower_range) < int(upper_range):
            db_dc.insert_one(
                {'delivery_id': delivery_id, 'delivery_type': delivery_type, 'lower_range': int(lower_range),
                 'upper_range': int(upper_range),
                 'delivery_charge': int(delivery_charge), 'delivery_added_date': delivery_added_date})
            output.append({'delivery_id': delivery_id, 'delivery_type': delivery_type, 'lower_range': lower_range,
                           'upper_range': upper_range,
                           'delivery_charge': delivery_charge, 'delivery_added_date': delivery_added_date})
            return jsonify({'status': True, 'message': 'Added delivery charge success', 'result': output})
        return jsonify({'status': False, 'message': 'Upper_range is not less-than lower_range', 'result': output})
    if str(delivery_type) == "subscription-corporate":
        for i in db_dc.find():
            if str(delivery_type) == str(i['delivery_type']):
                if int(lower_range) == int(i['lower_range']) or int(upper_range) == int(i['upper_range']):
                    output.append({'delivery_type': i['delivery_type'], 'lower_range': int(lower_range),
                                   'upper_range': int(upper_range),
                                   'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id']})
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
                if i['lower_range'] <= int(lower_range) <= i['upper_range'] or \
                        i['lower_range'] <= int(upper_range) <= i['upper_range']:
                    output.append({'delivery_type': i['delivery_type'], 'lower_range': int(lower_range),
                                   'upper_range': int(upper_range),
                                   'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id']})
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
        if int(lower_range) < int(upper_range):
            db_dc.insert_one(
                {'delivery_id': delivery_id, 'delivery_type': delivery_type, 'lower_range': int(lower_range),
                 'upper_range': int(upper_range),
                 'delivery_charge': int(delivery_charge), 'delivery_added_date': delivery_added_date})
            output.append({'delivery_id': delivery_id, 'delivery_type': delivery_type, 'lower_range': lower_range,
                           'upper_range': upper_range,
                           'delivery_charge': delivery_charge, 'delivery_added_date': delivery_added_date})
            return jsonify({'status': True, 'message': 'Added delivery charge success', 'result': output})
        return jsonify({'status': False, 'message': 'Upper_range is not less-than lower_range', 'result': output})
    if str(delivery_type) == "event-instant":
        for i in db_dc.find():
            if str(delivery_type) == str(i['delivery_type']):
                if int(lower_range) == int(i['lower_range']) or int(upper_range) == int(i['upper_range']):
                    output.append({'delivery_type': i['delivery_type'], 'lower_range': int(lower_range),
                                   'upper_range': int(upper_range),
                                   'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id']})
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
                if i['lower_range'] <= int(lower_range) <= i['upper_range'] or \
                        i['lower_range'] <= int(upper_range) <= i['upper_range']:
                    output.append({'delivery_type': i['delivery_type'], 'lower_range': int(lower_range),
                                   'upper_range': int(upper_range),
                                   'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id']})
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
        if int(lower_range) < int(upper_range):
            db_dc.insert_one(
                {'delivery_id': delivery_id, 'delivery_type': delivery_type, 'lower_range': int(lower_range),
                 'upper_range': int(upper_range),
                 'delivery_charge': int(delivery_charge), 'delivery_added_date': delivery_added_date})
            output.append({'delivery_id': delivery_id, 'delivery_type': delivery_type, 'lower_range': int(lower_range),
                           'upper_range': int(upper_range),
                           'delivery_charge': delivery_charge, 'delivery_added_date': delivery_added_date})
            return jsonify({'status': True, 'message': 'Added delivery charge success', 'result': output})
        return jsonify({'status': False, 'message': 'Upper_range is not less-than lower_range', 'result': output})
    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})


# ---------------------------------------------- Get all delivery charges -----------------------------------------------
@app.route('/owo/get_all_delivery_charge', methods=['GET'])
def getAlldeliverycharge():
    data = mongo.db.OWO
    db_dc = data.delivery_charge_management
    output = []
    for i in db_dc.find():
        try:
            modify_on = i['modify_on']
        except KeyError or ValueError:
            modify_on = ''
        output.append(
            {'delivery_type': i['delivery_type'], 'lower_range': i['lower_range'], 'upper_range': i['upper_range'],
             'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id'],
             'delivery_added_date': i['delivery_added_date'], 'modify_on': modify_on})
    return jsonify({'status': True, 'message': 'Get all details for delivery charges success', 'result': output})


# -------------------------------------------- Get delivery charges by id -----------------------------------------------
@app.route('/owo/get_by_id_delivery_charge/<delivery_id>', methods=['POST'])
def getbyIddeliverycharge(delivery_id):
    data = mongo.db.OWO
    db_dc = data.delivery_charge_management
    output = []
    # delivery_id = request.json['delivery_id']
    for i in db_dc.find():
        if int(delivery_id) == i['delivery_id']:
            try:
                modify_on = i['modify_on']
            except KeyError or ValueError:
                modify_on = ''
            output.append(
                {'delivery_type': i['delivery_type'], 'lower_range': i['lower_range'], 'upper_range': i['upper_range'],
                 'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id'],
                 'delivery_added_date': i['delivery_added_date'], 'modify_on': modify_on})
            return jsonify(
                {'status': True, 'message': 'Get all details for delivery_charges success', 'result': output})
    return jsonify({'status': False, 'message': 'Enter a valid delivery_id', 'result': output})


# ---------------------------------------------- Delete delivery charges -----------------------------------------------
@app.route('/owo/delete_by_id_delivery_charge/<delivery_id>', methods=['POST'])
@jwt_required
def deletebyIddeliverycharge(delivery_id):
    data = mongo.db.OWO
    db_dc = data.delivery_charge_management
    output = []
    # delivery_id = request.json['delivery_id']
    for i in db_dc.find():
        if int(delivery_id) == int(i['delivery_id']):
            try:
                modify_on = i['modify_on']
            except KeyError or ValueError:
                modify_on = ''
            db_dc.remove({'delivery_id': int(delivery_id)})
            output.append(
                {'delivery_type': i['delivery_type'], 'lower_range': ['lower_range'], 'upper_range': i['upper_range'],
                 'delivery_charge': i['delivery_charge'], 'delivery_id': i['delivery_id'], 'modify_on': modify_on})
            return jsonify({'status': True, 'message': 'Delete details for delivery_charges success', 'result': output})
    return jsonify({'status': False, 'message': 'Enter a valid delivery_id', 'result': output})


# -------------------------------------------- Edit delivery charges ---------------------------------------------------
@app.route('/owo/edit_by_id_delivery_charge', methods=['POST'])
@jwt_required
def editbyIddeliverycharge():
    data = mongo.db.OWO
    db_dc = data.delivery_charge_management
    output = []
    delivery_id = request.json['delivery_id']
    delivery_type = request.json['delivery_type']
    delivery_charge = request.json['delivery_charge']
    lower_range = request.json['lower_range']
    upper_range = request.json['upper_range']
    modify_on = time.strftime("%d/%m/%Y %H:%M:%S")
    if int(lower_range) > int(upper_range):
        return jsonify({'status': False, 'message': 'Upper range is not less than lower range', 'result': output})
    count = 0
    for k in db_dc.find({'delivery_id': delivery_id}):
        if delivery_type == str(k['delivery_type']):
            if int(lower_range) == k['lower_range'] and int(upper_range) == k['upper_range']:
                db_dc.update_many({'delivery_id': int(delivery_id)},
                                  {'$set': {
                                      'delivery_charge': int(delivery_charge),
                                      'modify_on': modify_on
                                  }})
                output.append(
                    {'delivery_type': k['delivery_type'], 'lower_range': lower_range, 'upper_range': upper_range,
                     'delivery_charge': delivery_charge, 'delivery_id': k['delivery_id'], 'modify_on': modify_on})
                return jsonify({'status': True, 'message': 'Updated delivery charges successfully', 'result': output})
    for i in db_dc.find():
        if delivery_type == str(i['delivery_type']):
            if int(lower_range) == i['lower_range'] or int(upper_range) == i['upper_range'] \
                    and int(lower_range) == i['upper_range'] or int(upper_range) == i['lower_range'] and count >= 1:
                count = count + 1
                if count >= 1:
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
            elif i['lower_range'] <= int(lower_range) <= i['upper_range'] or \
                    i['lower_range'] <= int(upper_range) <= i['upper_range'] and count >= 1:
                count = count + 1
                if count >= 1:
                    return jsonify({'status': False, 'message': 'Order range is already added', 'result': output})
    for j in db_dc.find():
        if int(delivery_id) == j['delivery_id'] and delivery_type == str(j['delivery_type']) and count < 1:
            db_dc.update_many({'delivery_id': int(delivery_id)},
                              {'$set': {
                                  'lower_range': int(lower_range),
                                  'upper_range': int(upper_range),
                                  'delivery_charge': int(delivery_charge),
                                  'modify_on': modify_on
                              }})
            output.append(
                {'delivery_type': j['delivery_type'], 'lower_range': lower_range, 'upper_range': upper_range,
                 'delivery_charge': delivery_charge, 'delivery_id': j['delivery_id'], 'modify_on': modify_on})
            return jsonify({'status': True, 'message': 'Updated delivery charges successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Enter a valid delivery id', 'result': output})


# -------------------------------------------- Stock Management --------------------------------------------------------
# ------------------------------------------- Get available stocks -----------------------------------------------------
@app.route('/owo/get_stocks', methods=['GET'])
def listOfStocks():
    data = mongo.db.OWO
    db = data.products
    output = []
    for i in db.find():
        product_id = i['product_id']
        product_name = i['product_name']
        product_quantity = i['product_quantity']
        print(type(product_quantity))
        p_type = i['package_type']
        if int(product_quantity) < 0:
            product_quantity1 = 0
        else:
            product_quantity1 = product_quantity
        for j in p_type:
            package_type = j['package_type']
        output.append({'product_id': product_id, 'product_name': product_name,
                       'product_quantity': product_quantity1, 'package_type': package_type})
    return jsonify({'status': True, 'message': 'List of product quantity', 'result': output})


# ----------------------------------------------- List of modify details -----------------------------------------------
@app.route('/owo/get_history_of_stocks/<product_id>', methods=['GET'])
def listOfModifyHistoryStocks(product_id):
    data = mongo.db.OWO
    db = data.stock_history
    output = []
    for i in db.find():
        p_id = i['product_id']
        if str(product_id) == str(p_id):
            try:
                history = i['history_of modify']
                for j in history:
                    modify_on = j['modify_on']
                    product_quantity = j['product_quantity']
                    output.append({'product_id': product_id,
                                   'product_quantity': product_quantity,
                                   'modify_on': modify_on})

            except KeyError or ValueError:
                history = []
                output.append({'product_id': product_id,
                               'product_quantity': product_quantity,
                               'modify_on': ''})
    return jsonify({'status': True, 'message': 'List of product quantity', 'result': output})


# -------------------------------------------- Get stock by product id ---------------------------------------------
@app.route('/owo/stocks_get_by_product_id/<product_id>', methods=['GET'])
def stocksGetById(product_id):
    data = mongo.db.OWO
    db = data.products
    output = []
    for i in db.find():
        p_id = i['product_id']
        p_quantity = i['product_quantity']
        if str(p_id) == str(product_id):
            if int(p_quantity) < 0:
                product_quantity1 = 0
            else:
                product_quantity1 = p_quantity
            output.append({'product_id': product_id, 'product_name': i['product_name'],
                           'product_quantity': product_quantity1})
            return jsonify({'status': True, 'message': 'Details of get by id', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid product id', 'result': output})


# ----------------------------------------------- Edit stock -----------------------------------------------------------
@app.route('/owo/edit_stock_product', methods=['POST'])
@jwt_required
def editStock():
    data = mongo.db.OWO
    db = data.products
    db1 = data.stock_history
    output = []
    product_quantity = request.json['product_quantity']
    product_id = request.json['product_id']
    history_of_modify_product_quantity = time.strftime("%d/%m/%Y %H:%M:%S")
    for i in db.find():
        p_id = i['product_id']
        if str(p_id) == str(product_id):
            for j in db1.find():
                sp_id = j['product_id']
                if str(sp_id) == str(p_id):
                    db.update_many({'product_id': product_id},
                                   {'$set': {'product_quantity': product_quantity}})
                    db1.update_many({'product_id': str(product_id)},
                                    {'$push': {'history_of modify': {'modify_on': history_of_modify_product_quantity,
                                                                     'product_quantity': product_quantity}}})
                    output.append({'product_id': product_id, 'product_quantity': product_quantity})
                    return jsonify({'status': True, 'message': 'Quantity updated', 'result': output})

            db.update_many({'product_id': product_id},
                           {'$set': {'product_quantity': product_quantity}})
            db1.insert(
                {'product_id': product_id, 'history_of modify': [{'modify_on': history_of_modify_product_quantity,
                                                                  'product_quantity': product_quantity}]})
            output.append({'product_id': product_id, 'product_quantity': product_quantity})
            return jsonify({'status': True, 'message': 'Quantity updated', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid product id', 'result': output})


# --------------------------------------------------- App Notification Text Management --------------------------------
# ------------------------------------------------------- Add App Notification Text -----------------------------------
@app.route('/owo/add_app_notification_text', methods=['POST'])
@jwt_required
def addNotificationText():
    data = mongo.db.OWO
    db = data.app_notification_text
    db1 = data.Super_Admin
    output = []
    admin_id = request.json['admin_id']
    admin_userName = request.json['admin_userName']
    notification_type = request.json['notification_type']
    notification_title = request.json['notification_title']
    notification_text_description = request.json['notification_text_description']
    notification_text_id_list = [i['notification_text_id'] for i in db.find()]
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    if len(notification_text_id_list) == 0:
        notification_text_id = 1
    else:
        notification_text_id = int(notification_text_id_list[-1]) + 1
    for j in db.find():
        n_type = j['notification_type']
        if str(n_type) == str(notification_type):
            return jsonify({'status': False, 'message': 'Notification type is already exist', 'result': output})
    # for i in db1.find():
    #     a_id = i['roles_id']
    #     user_name = i['email_id']
    #     if str(a_id) == str(admin_id):
    db.insert({'admin_id': int(admin_id), 'admin_userName': admin_userName, 'notification_type': notification_type,
               'notification_title': notification_title,
               'notification_text_description': notification_text_description,
               'notification_text_id': int(notification_text_id),
               'date_of_creation': date_of_creation, 'status': True})
    output.append({'admin_id': int(admin_id), 'admin_userName': admin_userName,
                   'notification_type': notification_type, 'notification_title': notification_title,
                   'notification_text_description': notification_text_description,
                   'notification_text_id': int(notification_text_id),
                   'date_of_creation': date_of_creation, 'status': True})
    return jsonify({'status': True, 'message': 'App notification text added successfully', 'result': output})


# ------------------------------------------------ Edit App Notification Text -----------------------------------------
@app.route('/owo/edit_app_notification_text', methods=['POST'])
@jwt_required
def editAppNotificationText():
    data = mongo.db.OWO
    db = data.app_notification_text
    output = []
    admin_id = request.json['admin_id']
    notification_text_id = request.json['notification_text_id']
    notification_type = request.json['notification_type']
    notification_title = request.json['notification_title']
    notification_text_description = request.json['notification_text_description']
    date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
    notification_type_result = db.find({'notification_type': notification_type})
    if notification_type_result.count() > 1:
        return jsonify({'status': False, 'message': 'Notification type is already exist', 'result': output})
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.find_one_and_update({'notification_text_id': int(notification_text_id)},
                                   {'$set': {'modified_by': int(admin_id),
                                             'notification_type': notification_type,
                                             'notification_title': notification_title,
                                             'notification_text_description': notification_text_description,
                                             'date_of_modification': date_of_modification
                                             }})
            output.append({'notification_text_id': int(notification_text_id), 'modified_by': int(admin_id),
                           'notification_type': notification_type, 'notification_title': notification_title,
                           'notification_text_Description': notification_text_description,
                           'date_of_modification': date_of_modification})
            return jsonify({'status': True, 'message': 'App notification text updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# --------------------------------------------- Delete App Notification Text ------------------------------------------
@app.route('/owo/delete_app_notification_text/<notification_text_id>', methods=['POST'])
@jwt_required
def deleteAppNotificationText(notification_text_id):
    data = mongo.db.OWO
    db = data.app_notification_text
    output = []
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.remove({'notification_text_id': int(notification_text_id)})
            return jsonify({'status': True, 'message': 'App notification text deleted successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# --------------------------------------- Get All App Notification Text -----------------------------------------------
@app.route('/owo/get_all_app_notification_text', methods=['GET'])
def getAllAppNotificationText():
    data = mongo.db.OWO
    db = data.app_notification_text
    output = []
    for i in db.find():
        temp = {}
        temp['admin_id'] = i['admin_id']
        temp['admin_userName'] = i['admin_userName']
        temp['notification_text_id'] = i['notification_text_id']
        temp['notification_type'] = i['notification_type']
        temp['notification_title'] = i['notification_title']
        temp['notification_text_description'] = i['notification_text_description']
        temp['date_of_creation'] = i['date_of_creation']
        temp['status'] = i['status']
        if 'date_of_modification' not in i.keys():
            temp['date_of_modification'] = ''
        else:
            temp['date_of_modification'] = i['date_of_modification']
        if 'modified_by' not in i.keys():
            temp['modified_by'] = ''
        else:
            temp['modified_by'] = i['modified_by']
        output.append(temp)
    return jsonify({'status': True, 'message': 'Get all app notification text', 'result': output})


# ------------------------------------------- Get App Notification Text By ID ------------------------------------------
@app.route('/owo/get_app_notification_text_by_id/<notification_text_id>', methods=['GET'])
def getAppNotificationTextByID(notification_text_id):
    data = mongo.db.OWO
    db = data.app_notification_text
    output = []
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            temp = {}
            temp['admin_id'] = i['admin_id']
            temp['admin_userName'] = i['admin_userName']
            temp['notification_text_id'] = i['notification_text_id']
            temp['notification_type'] = i['notification_type']
            temp['notification_title'] = i['notification_title']
            temp['notification_text_description'] = i['notification_text_description']
            temp['date_of_creation'] = i['date_of_creation']
            temp['status'] = i['status']
            if 'date_of_modification' not in i.keys():
                temp['date_of_modification'] = ''
            else:
                temp['date_of_modification'] = i['date_of_modification']
            if 'modified_by' not in i.keys():
                temp['modified_by'] = ''
            else:
                temp['modified_by'] = i['modified_by']
            output.append(temp)
            return jsonify({'status': True, 'message': 'App notification text data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# ------------------------------------------ Enable/Disable status ----------------------------------------------------
@app.route('/owo/appNotificationText_change_status', methods=['POST'])
@jwt_required
def enableDisableAppNotificationText():
    data = mongo.db.OWO
    db = data.app_notification_text
    output = []
    notification_text_id = request.json['notification_text_id']
    status = request.json['status']
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.update_many({'notification_text_id': int(notification_text_id)}, {'$set': {'status': status}})
            output.append({'notification_text_id': int(notification_text_id), 'status': status})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid notification_text_id', 'result': output}))


# --------------------------------------------------- SMS Notification Text Management --------------------------------
# ------------------------------------------------------- Add SMS Notification Text -----------------------------------
@app.route('/owo/add_SMS_notification_text', methods=['POST'])
@jwt_required
def addSMSNotificationText():
    data = mongo.db.OWO
    db = data.SMS_notification_text
    db1 = data.Super_Admin
    output = []
    admin_id = request.json['admin_id']
    admin_userName = request.json['admin_userName']
    notification_type = request.json['notification_type']
    notification_title = request.json['notification_title']
    notification_text_description = request.json['notification_text_description']
    notification_text_id_list = [i['notification_text_id'] for i in db.find()]
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    if len(notification_text_id_list) == 0:
        notification_text_id = 1
    else:
        notification_text_id = int(notification_text_id_list[-1]) + 1
    for j in db.find():
        n_type = j['notification_type']
        if str(n_type) == str(notification_type):
            return jsonify({'status': False, 'message': 'Notification type is already exist', 'result': output})
    db.insert({'admin_id': int(admin_id), 'admin_userName': admin_userName, 'notification_type': notification_type,
               'notification_title': notification_title,
               'notification_text_description': notification_text_description,
               'notification_text_id': int(notification_text_id),
               'date_of_creation': date_of_creation, 'status': True})
    output.append({'admin_id': int(admin_id), 'admin_userName': admin_userName,
                   'notification_type': notification_type, 'notification_title': notification_title,
                   'notification_text_description': notification_text_description,
                   'notification_text_id': int(notification_text_id),
                   'date_of_creation': date_of_creation, 'status': True})
    return jsonify({'status': True, 'message': 'SMS notification text added successfully', 'result': output})


# ------------------------------------------------- Edit SMS Notification Text ----------------------------------------
@app.route('/owo/edit_SMS_notification_text', methods=['POST'])
@jwt_required
def editSMSNotificationText():
    data = mongo.db.OWO
    db = data.SMS_notification_text
    output = []
    admin_id = request.json['admin_id']
    notification_text_id = request.json['notification_text_id']
    notification_type = request.json['notification_type']
    notification_title = request.json['notification_title']
    notification_text_description = request.json['notification_text_description']
    date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
    notification_type_result = db.find({'notification_type': notification_type})
    if notification_type_result.count() > 1:
        return jsonify({'status': False, 'message': 'Notification type is already exist', 'result': output})
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.find_one_and_update({'notification_text_id': int(notification_text_id)},
                                   {'$set': {'modified_by': int(admin_id),
                                             'notification_type': notification_type,
                                             'notification_title': notification_title,
                                             'notification_text_description': notification_text_description,
                                             'date_of_modification': date_of_modification
                                             }})
            output.append({'notification_text_id': int(notification_text_id), 'modified_by': int(admin_id),
                           'notification_type': notification_type, 'notification_title': notification_title,
                           'notification_text_Description': notification_text_description,
                           'date_of_modification': date_of_modification})
            return jsonify({'status': True, 'message': 'SMS notification text updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# --------------------------------------------- Delete SMS Notification Text ------------------------------------------
@app.route('/owo/delete_SMS_notification_text/<notification_text_id>', methods=['POST'])
@jwt_required
def deleteSMSNotificationText(notification_text_id):
    data = mongo.db.OWO
    db = data.SMS_notification_text
    output = []
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.remove({'notification_text_id': int(notification_text_id)})
            return jsonify({'status': True, 'message': 'SMS notification text deleted successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# --------------------------------------- Get All SMS Notification Text -----------------------------------------------
@app.route('/owo/get_all_SMS_notification_text', methods=['GET'])
def getAllSMSNotificationText():
    data = mongo.db.OWO
    db = data.SMS_notification_text
    output = []
    for i in db.find():
        temp = {}
        temp['admin_id'] = i['admin_id']
        temp['admin_userName'] = i['admin_userName']
        temp['notification_text_id'] = i['notification_text_id']
        temp['notification_type'] = i['notification_type']
        temp['notification_title'] = i['notification_title']
        temp['notification_text_description'] = i['notification_text_description']
        temp['date_of_creation'] = i['date_of_creation']
        temp['status'] = i['status']
        if 'date_of_modification' not in i.keys():
            temp['date_of_modification'] = ''
        else:
            temp['date_of_modification'] = i['date_of_modification']
        if 'modified_by' not in i.keys():
            temp['modified_by'] = ''
        else:
            temp['modified_by'] = i['modified_by']
        output.append(temp)
    return jsonify({'status': True, 'message': 'Get all SMS notification text', 'result': output})


# ------------------------------------------- Get SMS Notification Text By ID -----------------------------------------
@app.route('/owo/get_SMS_notification_text_by_id/<notification_text_id>', methods=['GET'])
def getSMSNotificationTextByID(notification_text_id):
    data = mongo.db.OWO
    db = data.SMS_notification_text
    output = []
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            temp = {}
            temp['admin_id'] = i['admin_id']
            temp['admin_userName'] = i['admin_userName']
            temp['notification_text_id'] = i['notification_text_id']
            temp['notification_type'] = i['notification_type']
            temp['notification_title'] = i['notification_title']
            temp['notification_text_description'] = i['notification_text_description']
            temp['date_of_creation'] = i['date_of_creation']
            temp['status'] = i['status']
            if 'date_of_modification' not in i.keys():
                temp['date_of_modification'] = ''
            else:
                temp['date_of_modification'] = i['date_of_modification']
            if 'modified_by' not in i.keys():
                temp['modified_by'] = ''
            else:
                temp['modified_by'] = i['modified_by']
            output.append(temp)
            return jsonify({'status': True, 'message': 'SMS notification text data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# ------------------------------------------ Enable/Disable status ----------------------------------------------------
@app.route('/owo/SMSNotificationText_change_status', methods=['POST'])
@jwt_required
def enableDisableSMSNotificationText():
    data = mongo.db.OWO
    db = data.SMS_notification_text
    output = []
    notification_text_id = request.json['notification_text_id']
    status = request.json['status']
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.update_many({'notification_text_id': int(notification_text_id)}, {'$set': {'status': status}})
            output.append({'notification_text_id': int(notification_text_id), 'status': status})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid notification_text_id', 'result': output}))


# --------------------------------------------------- Email Notification Text Management ------------------------------
# ------------------------------------------------------- Add Email Notification Text ---------------------------------
@app.route('/owo/add_email_notification_text', methods=['POST'])
@jwt_required
def addEmailNotificationText():
    data = mongo.db.OWO
    db = data.email_notification_text
    db1 = data.Super_Admin
    output = []
    admin_id = request.json['admin_id']
    admin_userName = request.json['admin_userName']
    notification_type = request.json['notification_type']
    notification_title = request.json['notification_title']
    notification_text_description = request.json['notification_text_description']
    notification_text_id_list = [i['notification_text_id'] for i in db.find()]
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    if len(notification_text_id_list) == 0:
        notification_text_id = 1
    else:
        notification_text_id = int(notification_text_id_list[-1]) + 1
    for j in db.find():
        n_type = j['notification_type']
        if str(n_type) == str(notification_type):
            return jsonify({'status': False, 'message': 'Notification type is already exist', 'result': output})
    db.insert({'admin_id': int(admin_id), 'admin_userName': admin_userName, 'notification_type': notification_type,
               'notification_title': notification_title,
               'notification_text_description': notification_text_description,
               'notification_text_id': int(notification_text_id),
               'date_of_creation': date_of_creation, 'status': True})
    output.append({'admin_id': int(admin_id), 'admin_userName': admin_userName,
                   'notification_type': notification_type, 'notification_title': notification_title,
                   'notification_text_description': notification_text_description,
                   'notification_text_id': int(notification_text_id),
                   'date_of_creation': date_of_creation, 'status': True})
    return jsonify({'status': True, 'message': 'Email notification text added successfully', 'result': output})


# ----------------------------------------------- Edit Email Notification Text ----------------------------------------
@app.route('/owo/edit_email_notification_text', methods=['POST'])
@jwt_required
def editEmailNotificationText():
    data = mongo.db.OWO
    db = data.email_notification_text
    output = []
    admin_id = request.json['admin_id']
    notification_text_id = request.json['notification_text_id']
    notification_type = request.json['notification_type']
    notification_title = request.json['notification_title']
    notification_text_description = request.json['notification_text_description']
    date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
    notification_type_result = db.find({'notification_type': notification_type})
    if notification_type_result.count() > 1:
        return jsonify({'status': False, 'message': 'Notification type is already exist', 'result': output})
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.find_one_and_update({'notification_text_id': int(notification_text_id)},
                                   {'$set': {'modified_by': int(admin_id),
                                             'notification_type': notification_type,
                                             'notification_title': notification_title,
                                             'notification_text_description': notification_text_description,
                                             'date_of_modification': date_of_modification
                                             }})
            output.append({'notification_text_id': int(notification_text_id), 'modified_by': int(admin_id),
                           'notification_type': notification_type, 'notification_title': notification_title,
                           'notification_text_Description': notification_text_description,
                           'date_of_modification': date_of_modification})
            return jsonify(
                {'status': True, 'message': 'Email notification text updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# --------------------------------------------- Delete Email Notification Text ----------------------------------------
@app.route('/owo/delete_email_notification_text/<notification_text_id>', methods=['POST'])
@jwt_required
def deleteEmailNotificationText(notification_text_id):
    data = mongo.db.OWO
    db = data.email_notification_text
    output = []
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.remove({'notification_text_id': int(notification_text_id)})
            return jsonify(
                {'status': True, 'message': 'Email notification text deleted successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# --------------------------------------- Get All Email Notification Text ---------------------------------------------
@app.route('/owo/get_all_email_notification_text', methods=['GET'])
def getAllEmailNotificationText():
    data = mongo.db.OWO
    db = data.email_notification_text
    output = []
    for i in db.find():
        temp = {}
        temp['admin_id'] = i['admin_id']
        temp['admin_userName'] = i['admin_userName']
        temp['notification_text_id'] = i['notification_text_id']
        temp['notification_type'] = i['notification_type']
        temp['notification_title'] = i['notification_title']
        temp['notification_text_description'] = i['notification_text_description']
        temp['date_of_creation'] = i['date_of_creation']
        temp['status'] = i['status']
        if 'date_of_modification' not in i.keys():
            temp['date_of_modification'] = ''
        else:
            temp['date_of_modification'] = i['date_of_modification']
        if 'modified_by' not in i.keys():
            temp['modified_by'] = ''
        else:
            temp['modified_by'] = i['modified_by']
        output.append(temp)
    return jsonify({'status': True, 'message': 'Get all email notification text', 'result': output})


# ------------------------------------------- Get Email Notification Text By ID ---------------------------------------
@app.route('/owo/get_email_notification_text_by_id/<notification_text_id>', methods=['GET'])
def getEmailNotificationTextByID(notification_text_id):
    data = mongo.db.OWO
    db = data.email_notification_text
    output = []
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            temp = {}
            temp['admin_id'] = i['admin_id']
            temp['admin_userName'] = i['admin_userName']
            temp['notification_text_id'] = i['notification_text_id']
            temp['notification_type'] = i['notification_type']
            temp['notification_title'] = i['notification_title']
            temp['notification_text_description'] = i['notification_text_description']
            temp['date_of_creation'] = i['date_of_creation']
            temp['status'] = i['status']
            if 'date_of_modification' not in i.keys():
                temp['date_of_modification'] = ''
            else:
                temp['date_of_modification'] = i['date_of_modification']
            if 'modified_by' not in i.keys():
                temp['modified_by'] = ''
            else:
                temp['modified_by'] = i['modified_by']
            output.append(temp)
            return jsonify(
                {'status': True, 'message': 'Email notification text data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# --------------------------------- Email notification text description by id -----------------------------------------
@app.route('/owo/get_emailNotificationTextDescription_by_id/<notification_text_id>', methods=['GET'])
def getEmailNotificationTextDescriptionByID(notification_text_id):
    data = mongo.db.OWO
    db = data.email_notification_text
    output = []
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            temp = {}
            temp['notification_text_id'] = i['notification_text_id']
            temp['notification_text_description'] = i['notification_text_description']
            output.append(temp)
            return jsonify({'status': True, 'message': 'Email notification text description data get successfully',
                            'result': output})
    return jsonify({'status': False, 'message': 'Invalid notification text id', 'result': output})


# ------------------------------------------ Enable/Disable status ----------------------------------------------------
@app.route('/owo/EmailNotificationText_change_status', methods=['POST'])
@jwt_required
def enableDisableEmailNotificationText():
    data = mongo.db.OWO
    db = data.email_notification_text
    output = []
    notification_text_id = request.json['notification_text_id']
    status = request.json['status']
    for i in db.find():
        n_id = i['notification_text_id']
        if str(n_id) == str(notification_text_id):
            db.update_many({'notification_text_id': int(notification_text_id)}, {'$set': {'status': status}})
            output.append({'notification_text_id': int(notification_text_id), 'status': status})
            return jsonify(({'status': True, 'message': 'Status changed successfully', 'result': output}))
    return jsonify(({'status': False, 'message': 'Invalid notification_text_id', 'result': output}))


# ------------------------------------------------- Get all shopping cart details ---------------------------------------
@app.route('/owo/get_all_shopping_cart_details', methods=['GET'])
def getallshoppingcartdetails():
    data = mongo.db.OWO
    db_sc = data.shoppingcart
    db_dc = data.delivery_charge_management
    output = []
    delivery_charge = int()
    total_save_price = int()
    total_gst = int()
    # total_price = int()
    for i in db_sc.find():
        u_id = i['customer_id']
        u_type = i['customer_type']
        ord_type = i['order_type']
        product = i['products']
        if int(u_id) == int(u_id) and str(u_type) == str(u_type):
            product_count = int()
            sub_total = int()
            for j in product:
                try:
                    product_rating = j['product_rating']
                    product_no_of_ratings = j['product_no_of_ratings']
                except KeyError or ValueError:
                    product_rating = "4"
                    product_no_of_ratings = "100"
                purchase_price = int(j['purchase_price'])
                product_quantity = int(j['product_quantity'])
                total_save_price += int(j['save_price'])
                sub_total += (purchase_price * product_quantity)
                product_count = product_count + 1
                total_gst += int(j['gst'])
            product_count = product_count
            total_save_price = total_save_price
            for s in db_dc.find():
                d_type = s['delivery_type']
                # if str(d_type) == str(ord_type):
                if str(ord_type) == 'event' or str(ord_type) == 'instant':
                    if int(s['lower_range']) < int(sub_total) < int(s['upper_range']):
                        d_charge = s['delivery_charge']
                        delivery_charge = d_charge
            total_price = abs(int(sub_total) + int(delivery_charge))
            output.append({'customer_id': u_id, 'customer_type': u_type, 'gst': total_gst,
                           'order_type': ord_type, 'cart_id': i['cart_id'],
                           'sub_total': sub_total, 'contact_number': i['mobile_number'],
                           'email_id': i['email_id'], 'added_date_and_time': i['cart_added_date'],
                           'product_count': product_count, 'delivery_charge': delivery_charge,
                           'total_Discount': total_save_price, 'total_price': total_price
                           })
    return jsonify({'status': True, 'message': "User cart list data get success", 'result': output})


# -------------------------------------- get_all_product_details_shopping_cart_details ---------------------------------
@app.route('/owo/get_all_product_details_shopping_cart_details', methods=['POST'])
@jwt_required
def getallproductdetailsshoppingcartdetails():
    data = mongo.db.OWO
    db_sc = data.shoppingcart
    output = []
    customer_id = request.json['customer_id']
    customer_type = request.json['customer_type']
    for i in db_sc.find():
        u_id = i['customer_id']
        u_type = i['customer_type']
        ord_type = i['order_type']
        product = i['products']
        if int(u_id) == int(customer_id) and str(u_type) == str(customer_type):
            sub_total = int()
            for j in product:
                try:
                    product_rating = j['product_rating']
                    product_no_of_ratings = j['product_no_of_ratings']
                except KeyError or ValueError:
                    product_rating = "4"
                    product_no_of_ratings = "100"
                purchase_price = int(j['purchase_price'])
                product_quantity = int(j['product_quantity'])
                sub_total = abs(int(purchase_price) * int(product_quantity))
                output.append({'product_quantity': product_quantity, 'plant_name': j['plant_name'],
                               'purchase_price': purchase_price,
                               'company_name': j['company_name'], 'company_id': j['company_id'],
                               'brand_id': j['brand_id'],
                               'brand_name': j['brand_name'], 'product_id': j['product_id'],
                               'package_type': j['package_type'],
                               'product_name': j['product_name'], 'unit_price': j['unit_price'],
                               'discount_in_percentage': j['discount_in_percentage'],
                               'return_policy': j['return_policy'], 'sub_total': sub_total,
                               'purchase_price': j['purchase_price'], 'gst': j['gst']})
            return jsonify({'status': True, 'message': 'Get product_details success', 'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid credentials', 'result': output})


# ---------------------------------- Wallet Magement Admin pannel ------------------------------------------------------
@app.route('/owo/admin_wallet_management', methods=['GET'])
def adminWalletManagement():
    data = mongo.db.OWO
    db_iu = data.individual_users
    db_cp = data.corporate_users
    db = data.owo_users_wallet
    output = []
    for i in db.find():
        user_id = i['user_id']
        signin_type = i['signin_type']
        wallet_id = i['wallet_id']
        if 'recent_transactions' not in i.keys():
            recent_transactions = ''
        else:
            recent_transactions = i['recent_transactions']
        closing_balance = 0
        current_balance = 0
        if 'subscription_amount' not in i.keys():
            subscription_amount = 0
        else:
            subscription_amount = i['subscription_amount']
        for j in db_cp.find():
            u_id = j['user_id']
            s_type = j['signin_type']
            if int(user_id) == int(u_id) and str(signin_type) == str(s_type):
                for c in recent_transactions:
                    try:
                        closing_balance = c['closing_balance']
                    except KeyError or ValueError:
                        closing_balance = 0
                    try:
                        current_balance = c['current_balance']
                    except KeyError or ValueError:
                        current_balance = 0
                mobile_number = j['mobile_number']
                email_id = j['email_id']
                output.append({'user_id': user_id, 'signin_type': signin_type, 'wallet_id': wallet_id,
                               'current_balance': current_balance, 'subscription_amount': subscription_amount,
                               'mobile_number': mobile_number, 'email_id': email_id,
                               'closing_balance': closing_balance})
        for k in db_iu.find():
            u_id1 = k['user_id']
            s_type1 = k['signin_type']
            if user_id == u_id1 and signin_type == s_type1:
                for c in recent_transactions:
                    try:
                        closing_balance = c['closing_balance']
                    except KeyError or ValueError:
                        closing_balance = 0
                    try:
                        current_balance = c['current_balance']
                    except KeyError or ValueError:
                        current_balance = 0
                mobile_number = k['mobile_number']
                email_id = k['email_id']
                output.append({'user_id': user_id, 'signin_type': signin_type, 'wallet_id': wallet_id,
                               'current_balance': current_balance, 'subscription_amount': subscription_amount,
                               'mobile_number': mobile_number, 'email_id': email_id,
                               'closing_balance': closing_balance})
    return jsonify({'status': True, 'message': 'List of wallet', 'result': output})


# ---------------------------------------------- View wallet transaction history---------------------------------------
@app.route('/owo/view_transaction_history', methods=['POST'])
@jwt_required
def viewTransactionHistory():
    data = mongo.db.OWO
    db = data.owo_users_wallet
    output = []

    user_id = request.json['user_id']
    signin_type = request.json['signin_type']
    wallet_id = request.json['wallet_id']
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        w_id = i['wallet_id']
        # current_balance = i['current_balance']
        if str(user_id) == str(u_id) and str(signin_type) == str(s_type) and str(wallet_id) == str(w_id):
            try:
                rt = i['recent_transactions']
                for j in rt:
                    transaction_id = j['transaction_id']
                    transaction_type = j['payment_type']
                    transaction_date = j['transaction_date']
                    transaction_amount = j['amount']
                    # current_balance = j['current_balance']
                    if 'current_balance' not in j.keys():
                        current_balance = 0
                    else:
                        current_balance = j['current_balance']
                    if 'closing_balance' not in j.keys():
                        closing_balance = 0
                    else:
                        closing_balance = j['closing_balance']
                    output.append({'transaction_id': transaction_id, 'payment_type': transaction_type,
                                   'current_balance': current_balance, 'closing_balance': closing_balance,
                                   'transaction_date': transaction_date, 'transaction_amount': transaction_amount})
                return jsonify({'status': True, 'message': 'List of transaction',
                                'result': sorted(output, key=lambda a: a['transaction_date'], reverse=True),
                                'user_id': user_id, 'signin_type': signin_type, 'wallet_id': wallet_id})
            except KeyError or ValueError:
                rt = []
            return jsonify({'status': True, 'message': 'List of details', 'result': output, 'user_id': user_id,
                            'signin_type': signin_type, 'wallet_id': wallet_id})

    return jsonify({'status': False, 'message': " Invalid user id  and signin_type", 'result': output})


# ----------------------------------------------------- Admin Dashboard -----------------------------------------------
@app.route('/owo/admin_dashboard', methods=['GET'])
def adminDashBoard1():
    global total_brand
    data = mongo.db.OWO
    db_cu = data.corporate_users
    db_iu = data.individual_users
    db_c = data.companies
    db_p = data.products
    # db_o = data.orders
    # db_os = data.orders_status
    db_ps = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    db_event = data.event_management
    db_instant = data.instant_delivery_management
    output = []
    total_order_instant = 0
    total_order_event = 0
    total_15_days_plan_subscribed_corporate_users = 0
    total_15_days_plan_subscribed_individual_users = 0
    total_30_days_plan_subscribed_corporate_users = 0
    total_30_days_plan_subscribed_individual_users = 0
    total_90_days_plan_subscribed_corporate_users = 0
    total_90_days_plan_subscribed_individual_users = 0
    total_180_days_plan_subscribed_corporate_users = 0
    total_180_days_plan_subscribed_individual_users = 0
    total_365_days_plan_subscribed_corporate_users = 0
    total_365_days_plan_subscribed_individual_users = 0
    available_cash_in_wallet = 0
    total_instant_payment = 0
    total_event_payment = 0
    total_subscription_payment = 0
    total_brand1 = 0
    total_brand = 0
    total_corporate_user = db_cu.find().count()
    total_individual_user = db_iu.find().count()
    total_companies = db_c.find().count()
    # total_order_booking = db_o.find().count()
    total_product_available = db_p.find().count()
    for i in db_ps.find():
        s_type = i['signin_type']
        try:
            b_plan = i['buy_plan']
        except KeyError or ValueError:
            b_plan = 0
        if s_type == 'corporate' and b_plan == 15:
            total_15_days_plan_subscribed_corporate_users += 1
        elif s_type == 'individual' and b_plan == 15:
            total_15_days_plan_subscribed_individual_users += 1
        if s_type == 'corporate' and b_plan == 30:
            total_30_days_plan_subscribed_corporate_users += 1
        elif s_type == 'individual' and b_plan == 30:
            total_30_days_plan_subscribed_individual_users += 1
        if s_type == 'corporate' and b_plan == 90:
            total_90_days_plan_subscribed_corporate_users += 1
        elif s_type == 'individual' and b_plan == 90:
            total_90_days_plan_subscribed_individual_users += 1
        if s_type == 'corporate' and b_plan == 180:
            total_180_days_plan_subscribed_corporate_users += 1
        elif s_type == 'individual' and b_plan == 180:
            total_180_days_plan_subscribed_individual_users += 1
        if s_type == 'corporate' and b_plan == 365:
            total_365_days_plan_subscribed_corporate_users += 1
        elif s_type == 'individual' and b_plan == 365:
            total_365_days_plan_subscribed_individual_users += 1

    for l in db_c.find():
        try:
            brand = l['brand']
            for m in brand:
                total_brand = len(brand)
                print(total_brand)
            total_brand1 += total_brand
            print(total_brand1)
        except KeyError or ValueError:
            brand = " "

    for l in db_instant.find():
        try:
            instant_payment = l['sub_total']
        except KeyError or ValueError:
            instant_payment = 0
        total_instant_payment += int(instant_payment)
        # print(total_instant_payment)

    for m in db_event.find():
        try:
            event_payment = m['sub_total']
        except KeyError or ValueError:
            event_payment = 0
        total_event_payment += int(event_payment)

    for n in db_ps.find():
        try:
            t_price = n['total_price']
        except KeyError or ValueError:
            t_price = 0
        total_subscription_payment += t_price

    for k in db_wallet.find():
        c_balance = k['current_balance']
        available_cash_in_wallet += c_balance
        print(available_cash_in_wallet)

    for g in db_instant.find():
        try:
            p_status = g['payment_status']
        except KeyError or ValueError:
            p_status = ""
        if p_status == "success":
            total_order_instant += 1

    for g in db_event.find():
        try:
            p_status = g['payment_status']
        except KeyError or ValueError:
            p_status = ""
        if p_status == "success":
            total_order_event += 1

    output.append({'total_brand': total_brand1, 'total_corporate_user': total_corporate_user,
                   'total_individual_user': total_individual_user,
                   'total_companies': total_companies, 'total_order_booking': total_order_event + total_order_instant,
                   'total_payment_received': total_instant_payment + total_event_payment + total_subscription_payment,
                   'total_product_available': total_product_available,
                   'available_cash_in_wallet': available_cash_in_wallet,
                   'total_15_days_plan_subscribed_corporate_users': total_15_days_plan_subscribed_corporate_users,
                   'total_15_days_plan_subscribed_individual_users': total_15_days_plan_subscribed_individual_users,
                   'total_30_days_plan_subscribed_corporate_users': total_30_days_plan_subscribed_corporate_users,
                   'total_30_days_plan_subscribed_individual_users': total_30_days_plan_subscribed_individual_users,
                   'total_90_days_plan_subscribed_corporate_users': total_90_days_plan_subscribed_corporate_users,
                   'total_90_days_plan_subscribed_individual_users': total_90_days_plan_subscribed_individual_users,
                   'total_180_days_plan_subscribed_corporate_users': total_180_days_plan_subscribed_corporate_users,
                   'total_180_days_plan_subscribed_individual_users': total_180_days_plan_subscribed_individual_users,
                   'total_365_days_plan_subscribed_corporate_users': total_365_days_plan_subscribed_corporate_users,
                   'total_365_days_plan_subscribed_individual_users': total_365_days_plan_subscribed_individual_users})
    return jsonify({'status': True, 'message': 'Admin Dashboard data', 'result': output})


# ------------------------------------- event delivery management ------------------------------------------------------
@app.route("/owo/get_all_users_event_details", methods=['GET'])
def getalluserseventdetails():
    data = mongo.db.OWO
    db = data.event_management
    output = []
    for i in db.find({'payment_status': "success", 'delivery_status': 'pending', 'order_status': 'confirmed'}):
        if str(i['delivery_status']) != "delivered" or str(i['delivery_status']) != "cancelled":
            count = int()
            address = ''
            event_id = i['event_id']
            email_id = i['email_id']
            mobile_number = i['mobile_number']
            user_id = i['user_id']
            signin_type = i['signin_type']
            order_id = i['order_id']
            event_type = i['event_type']
            delivery_date = i['date']
            delivery_time = i['time']
            venue = i['venue']
            for k in venue:
                address = k['address']
            if 'order_status' not in i.keys():
                order_status = ''
            else:
                order_status = i['order_status']
            if 'payment_type' not in i.keys():
                payment_type = ''
            else:
                payment_type = i['payment_type']
            if 'transaction_id' not in i.keys():
                transaction_id = ''
            else:
                transaction_id = i['transaction_id']
            if 'transaction_type' not in i.keys():
                transaction_type = ''
            else:
                transaction_type = i['transaction_type']
            if 'delivery_charges' not in i.keys():
                delivery_charges = ''
            else:
                delivery_charges = i['delivery_charges']
            for j in i['products']:
                count += 1
            product_count = count
            if 'sub_total' not in i.keys():
                sub_total = ''
            else:
                sub_total = i['sub_total']
            output.append({'event_id': event_id, 'email_id': email_id, 'mobile_number': mobile_number,
                           'user_id': user_id, 'signin_type': signin_type, 'order_id': order_id,
                           'event_type': event_type, 'delivery_date': delivery_date, 'delivery_time': delivery_time,
                           'address': address, 'product_count': product_count, 'order_status': order_status,
                           'payment_type': payment_type,
                           'transaction_id': transaction_id, 'transaction_type': transaction_type,
                           'delivery_charges': delivery_charges, 'sub_total': int(sub_total) - int(delivery_charges),
                           'total_price': int(sub_total)
                           })
    return jsonify({'status': True, 'message': 'Get all event details success', 'result': output})


# ------------------------------------------------- Event history ------------------------------------------------------
@app.route("/owo/event_history", methods=['GET'])
def eventhistory():
    data = mongo.db.OWO
    db = data.event_management
    output = []
    for i in db.find({'payment_status': "success"}):
        delivery = i['delivery_status']
        if str(delivery) == "delivered" or str(delivery) == "cancelled":
            count = int()
            address = ''
            if i['payment_type'] == 'loyality':
                loyalty_points = i['sub_total']
            else:
                loyalty_points = 0
            event_id = i['event_id']
            email_id = i['email_id']
            mobile_number = i['mobile_number']
            user_id = i['user_id']
            signin_type = i['signin_type']
            order_id = i['order_id']
            event_type = i['event_type']
            delivery_date = i['date']
            delivery_time = i['time']
            products = i['products']
            for j in products:
                count += 1
            product_count = count
            venue = i['venue']
            for j in venue:
                address = j['address']
            if 'order_status' not in i.keys():
                order_status = ''
            else:
                order_status = i['order_status']
            if 'payment_type' not in i.keys():
                payment_type = ''
            else:
                payment_type = i['payment_type']
            if 'transaction_id' not in i.keys():
                transaction_id = ''
            else:
                transaction_id = i['transaction_id']
            if 'transaction_type' not in i.keys():
                transaction_type = ''
            else:
                transaction_type = i['transaction_type']
            if 'sub_total' not in i.keys():
                sub_total = ''
            else:
                sub_total = i['sub_total']
            if 'delivery_charges' not in i.keys():
                delivery_charges = ''
            else:
                delivery_charges = i['delivery_charges']
            if 'delivery_status' not in i.keys():
                delivery_status = ''
            else:
                delivery_status = i['delivery_status']
            output.append({'event_id': event_id, 'email_id': email_id, 'mobile_number': mobile_number,
                           'user_id': user_id, 'signin_type': signin_type, 'order_id': order_id,
                           'event_type': event_type, 'delivery_date': delivery_date, 'delivery_time': delivery_time,
                           'product_count': product_count, 'address': address, 'order_status': order_status,
                           'payment_type': payment_type, 'transaction_id': transaction_id,
                           'transaction_type': transaction_type, 'sub_total': int(sub_total) - int(delivery_charges),
                           'delivery_charges': delivery_charges,
                           'total_amount': int(sub_total),
                           'delivery_status': delivery_status,
                           'loyalty_points': loyalty_points})
    return jsonify({'status': True, 'message': 'Event history get success', 'result': output})


# -------------------------------- Canceled event details for all users -----------------------------------------------
@app.route("/owo/canceled_event_details_for_all_users", methods=['GET'])
def canceledeventdetailsdatatousers():
    data = mongo.db.OWO
    db = data.event_management
    output = []
    for i in db.find({'payment_status': "success"}):
        try:
            delivery = i['delivery_status']
        except KeyError or ValueError:
            delivery = ''
        if str(delivery) == "cancelled":
            temp = {}
            temp['event_id'] = i['event_id']
            temp['email_id'] = i['email_id']
            temp['mobile_number'] = i['mobile_number']
            temp['user_id'] = i['user_id']
            temp['signin_type'] = i['signin_type']
            temp['order_id'] = i['order_id']
            temp['event_type'] = i['event_type']
            temp['delivery_date'] = i['date']
            temp['venue'] = i['venue']
            if 'order_status' not in i.keys():
                temp['order_status'] = ''
            else:
                temp['order_status'] = i['order_status']
            if 'payment_type' not in i.keys():
                temp['payment_type'] = ''
            else:
                temp['payment_type'] = i['payment_type']
            if 'sub_total' not in i.keys():
                temp['sub_total'] = ''
            else:
                temp['sub_total'] = i['sub_total']
            if 'transaction_id' not in i.keys():
                temp['transaction_id'] = ''
            else:
                temp['transaction_id'] = i['transaction_id']
            if 'transaction_type' not in i.keys():
                temp['transaction_type'] = ''
            else:
                temp['transaction_type'] = i['transaction_type']
            temp['total_amount'] = int(temp['sub_total']) + int(temp['delivery_charges'])
            temp['paid_amount'] = temp['total_amount']
            output.append(temp)
    return jsonify({'status': True, 'message': 'Canceled event details get success', 'result': output})


# ------------------------------------- Get eproduct details for event users -------------------------------------------
@app.route("/owo/get_event_user_product_details", methods=['POST'])
@jwt_required
def getproductdetailsforevent():
    data = mongo.db.OWO
    db = data.event_management
    db_p = data.products
    output = []
    event_id = request.json['event_id']
    for i in db.find({'payment_status': "success"}):
        if int(event_id) == i['event_id']:
            products = i['products']
            for j in products:
                product_id = j['product_id']
                for k in db_p.find():
                    package_type = k['package_type']
                    for l in package_type:
                        if str(product_id) == str(k['product_id']):
                            temp = {}
                            temp['product_id'] = j['product_id']
                            temp['product_name'] = j['product_name']
                            temp['plant_id'] = j['plant_id']
                            temp['plant_name'] = j['plant_name']
                            temp['company_id'] = j['company_id']
                            temp['company_name'] = j['company_name']
                            temp['brand_id'] = j['brand_id']
                            temp['brand_name'] = j['brand_name']
                            temp['product_image'] = j['product_image']
                            temp['product_logo'] = k['product_logo']
                            temp['description'] = k['description']
                            temp['specification'] = k['specification']
                            temp['unit_price'] = j['unit_price']
                            temp['discount_in_percentage'] = l['discount_in_percentage']
                            temp['return_policy'] = j['return_policy']
                            temp['package_type'] = j['package_type']
                            temp['product_quantity'] = j['product_quantity']
                            temp['sub_total'] = i['sub_total']
                            temp['gst'] = l['gst']
                            temp['purchase_price'] = j['purchase_price']
                            output.append(temp)
            return jsonify({'status': True, 'message': 'Get product to event success', 'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid event details', 'result': output})


def randomStringDigits(stringLength=4):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


# ----------------------------------------- Change Event Delivery Status ----------------------------------------------
@app.route("/owo/change_event_delivery_status", methods=['POST'])
@jwt_required
def changeeventdeliverystatus():
    data = mongo.db.OWO
    db = data.event_management
    db_p = data.products
    db_w = data.owo_users_wallet
    output = []
    event_id = request.json['event_id']
    delivery_status = request.json['delivery_status']
    date_time = datetime.datetime.now()
    for i in db.find({'payment_status': "success"}):
        user_id = i['user_id']
        signin_type = i['signin_type']
        if int(event_id) == i['event_id']:
            db.update_many({'event_id': int(event_id)},
                           {'$set': {'delivery_status': delivery_status,
                                     'order_status': delivery_status}})
            if delivery_status == 'delivered':
                a = i['products']
                for j in a:
                    p_id = j['product_id']
                    p_quantity = j['product_quantity']
                    print(p_quantity)
                    for n in db_p.find():
                        pro_id = n['product_id']
                        pro_quantity = n['product_quantity']
                        print(pro_quantity)
                        if str(pro_id) == str(p_id):
                            var = pro_quantity - p_quantity
                            db_p.find_one_and_update({'product_id': pro_id}, {'$set': {'product_quantity': var}})
            for w in db_w.find({'user_id': int(user_id)}):
                # print(user_id)
                if int(user_id) == int(user_id) and signin_type == w['signin_type'] and delivery_status == "cancelled":
                    ts = calendar.timegm(time.gmtime())
                    transaction_id = signin_type[:7].upper() + str(ts)
                    # print(transaction_id)
                    current_balance = w['current_balance']
                    refund_amount = int(i['sub_total'])
                    c_balance = int(refund_amount) + int(current_balance)
                    db_w.update_many({'user_id': int(w['user_id']), 'signin_type': str(w['signin_type'])},
                                     {'$set': {
                                         'current_balance': c_balance},
                                         '$push': {'recent_transactions': {'amount': refund_amount,
                                                                           'payment_type': "wallet",
                                                                           'transaction_id': transaction_id,
                                                                           'transaction_type': signin_type,
                                                                           'transaction_date': date_time,
                                                                           'order_id': i['order_id'],
                                                                           'status': 'success',
                                                                           'closing_balance': c_balance,
                                                                           'current_balance': current_balance
                                                                           }}})
            output.append({'event_id': event_id, 'delivery_status': delivery_status})
            return jsonify({'status': True, 'message': 'Delivery_status changed success', 'result': output})
    return jsonify(
        {'status': False, 'message': 'You entered event_id is not exist in event management', 'result': output})


# ------------------------------------------------ instant delivery management ----------------------------------------
@app.route("/owo/get_all_users_instant_delivery_details", methods=['GET'])
def getallusersinstantdeliverydetails():
    data = mongo.db.OWO
    db = data.instant_delivery_management
    output = []
    for i in db.find({'payment_status': "success", 'delivery_status': 'pending', 'order_status': 'confirmed'}):
        if str(i['delivery_status']) != "delivered" or str(i['delivery_status']) != "cancelled":
            count = int()
            if i['payment_type'] == 'loyality':
                loyalty_points = i['sub_total']
            else:
                loyalty_points = 0
            instant_id = i['instant_id']
            email_id = i['email_id']
            mobile_number = i['mobile_number']
            user_id = i['user_id']
            signin_type = i['signin_type']
            order_id = i['order_id']
            delivery_slot = i['available_slot']
            products = i['products']
            for j in products:
                count = count + 1
            product_count = count
            if 'delivery_address' not in i.keys():
                address = ''
            else:
                address = i['delivery_address']
            if 'order_status' not in i.keys():
                order_status = ''
            else:
                order_status = i['order_status']
            if 'ordered_date' not in i.keys():
                ordered_date = ''
            else:
                ordered_date = i['ordered_date']
            if 'payment_type' not in i.keys():
                payment_type = ''
            else:
                payment_type = i['payment_type']
            if 'transaction_id' not in i.keys():
                transaction_id = ''
            else:
                transaction_id = i['transaction_id']
            if 'transaction_type' not in i.keys():
                transaction_type = ''
            else:
                transaction_type = i['transaction_type']
            if 'sub_total' not in i.keys():
                sub_total = ''
            else:
                sub_total = i['sub_total']
            if 'delivery_charges' not in i.keys():
                delivery_charges = ''
            else:
                delivery_charges = i['delivery_charges']
            output.append({'instant_id': instant_id, 'loyalty_points': loyalty_points, 'email_id': email_id,
                           'mobile_number': mobile_number, 'user_id': user_id, 'signin_type': signin_type,
                           'order_id': order_id, 'delivery_slot': delivery_slot, 'product_count': product_count,
                           'address': address, 'order_status': order_status, 'ordered_date': ordered_date,
                           'payment_type': payment_type, 'transaction_id': transaction_id,
                           'sub_total': int(sub_total) - int(delivery_charges),
                           'transaction_type': transaction_type, 'total_price': int(sub_total),
                           'delivery_charges': delivery_charges
                           })
    return jsonify({'status': True, 'message': 'Get all instant details success', 'result': output})


# -------------------------------------- Instant delivery history ------------------------------------------------------
@app.route("/owo/instant_delivery_history", methods=['GET'])
def instantdeliveryhistory():
    data = mongo.db.OWO
    db = data.instant_delivery_management
    output = []
    for i in db.find({'payment_status': "success"}):
        try:
            delivery = i['delivery_status']
        except KeyError or ValueError:
            delivery = ''
        if str(delivery) == "delivered" or str(delivery) == 'cancelled':
            count = int()
            if i['payment_type'] == 'loyality':
                loyalty_points = i['sub_total']
            else:
                loyalty_points = 0
            instant_id = i['instant_id']
            email_id = i['email_id']
            mobile_number = i['mobile_number']
            user_id = i['user_id']
            signin_type = i['signin_type']
            order_id = i['order_id']
            delivery_slot = i['available_slot']
            products = i['products']
            for j in products:
                count += 1
            product_count = count
            if 'order_status' not in i.keys():
                order_status = ''
            else:
                order_status = i['order_status']
            if 'ordered_date' not in i.keys():
                ordered_date = ''
            else:
                ordered_date = i['ordered_date']
            if 'payment_type' not in i.keys():
                payment_type = ''
            else:
                payment_type = i['payment_type']
            if 'transaction_id' not in i.keys():
                transaction_id = ''
            else:
                transaction_id = i['transaction_id']
            if 'transaction_type' not in i.keys():
                transaction_type = ''
            else:
                transaction_type = i['transaction_type']
            if 'sub_total' not in i.keys():
                sub_total = ''
            else:
                sub_total = i['sub_total']
            if 'delivery_charges' not in i.keys():
                delivery_charges = ''
            else:
                delivery_charges = i['delivery_charges']
            if 'delivery_address' not in i.keys():
                address = ''
            else:
                address = i['delivery_address']
            total_amount = int(i['sub_total'])
            if 'delivery_status' not in i.keys():
                delivery_status = ''
            else:
                delivery_status = i['delivery_status']
            output.append({'instant_id': instant_id, 'email_id': email_id, 'mobile_number': mobile_number,
                           'user_id': user_id, 'signin_type': signin_type, 'order_id': order_id,
                           'delivery_slot': delivery_slot, 'product_count': product_count,
                           'order_status': order_status, 'ordered_date': ordered_date, 'payment_type': payment_type,
                           'transaction_id': transaction_id, 'transaction_type': transaction_type,
                           'sub_total': int(sub_total) - int(delivery_charges),
                           'delivery_charges': delivery_charges, 'address': address,
                           'total_amount': total_amount,
                           'delivery_status': delivery_status, 'loyalty_points': loyalty_points})
    return jsonify({'status': True, 'message': 'Instant history get success', 'result': output})


# ------------------------------------- Canceled instant details fro all users ----------------------------------------
@app.route("/owo/canceled_instant_details_for_all_users", methods=['GET'])
def canceledinstantdetailsdatatousers():
    data = mongo.db.OWO
    db = data.instant_delivery_management
    output = []
    for i in db.find({'payment_status': "success"}):
        try:
            delivery = i['delivery_status']
        except KeyError or ValueError:
            delivery = ''
        if str(delivery) == "cancelled":
            sub_total = int()
            discount = int()
            temp = {}
            temp['instant_id'] = i['instant_id']
            temp['email_id'] = i['email_id']
            temp['mobile_number'] = i['mobile_number']
            temp['user_id'] = i['user_id']
            temp['signin_type'] = i['signin_type']
            temp['order_id'] = i['order_id']
            temp['delivery_slot'] = i['available_slot']
            products = i['products']
            count = int()
            for j in products:
                count += 1
                sub_total += int(j['purchase_price'])
                discount += abs(int(j['unit_price']) - int(j['purchase_price']))
            temp['product_count'] = count
            # print(count)
            if 'order_status' not in i.keys():
                temp['order_status'] = ''
            else:
                temp['order_status'] = i['order_status']
            if 'ordered_date' not in i.keys():
                temp['ordered_date'] = ''
            else:
                temp['ordered_date'] = i['ordered_date']
            if 'payment_type' not in i.keys():
                temp['payment_type'] = ''
            else:
                temp['payment_type'] = i['payment_type']
            if 'transaction_id' not in i.keys():
                temp['transaction_id'] = ''
            else:
                temp['transaction_id'] = i['transaction_id']
            if 'transaction_type' not in i.keys():
                temp['transaction_type'] = ''
            else:
                temp['transaction_type'] = i['transaction_type']
            if 'sub_total' not in i.keys():
                temp['sub_total'] = ''
            else:
                temp['sub_total'] = i['sub_total']
            if 'delivery_charges' not in i.keys():
                temp['delivery_charges'] = ''
            else:
                temp['delivery_charges'] = i['delivery_charges']
            if 'total_gst' not in i.keys():
                temp['gst'] = ''
            else:
                temp['gst'] = i['total_gst']
            if 'loyalty_points' not in i.keys():
                temp['loyalty_points'] = ''
            else:
                temp['loyalty_points'] = i['loyalty_points']
            temp['discount'] = discount
            temp['total_amount'] = temp['sub_total'] + temp['delivery_charges']
            temp['paid_amount'] = temp['total_amount']
            output.append(temp)
    return jsonify({'status': True, 'message': 'Canceled instant details get success', 'result': output})


# ------------------------------------- Get product details for instant delivery users ---------------------------------
@app.route("/owo/get_product_details_for_instant_delivery_user", methods=['POST'])
@jwt_required
def getproductdetailsforinstant():
    data = mongo.db.OWO
    db = data.instant_delivery_management
    db_p = data.products
    output = []
    instant_id = request.json['instant_id']
    for i in db.find({'payment_status': "success"}):
        if int(instant_id) == i['instant_id']:
            products = i['products']
            for j in products:
                product_id = j['product_id']
                for k in db_p.find():
                    package_type = k['package_type']
                    for l in package_type:
                        if str(product_id) == str(k['product_id']):
                            temp = {}
                            temp['product_id'] = j['product_id']
                            temp['product_name'] = j['product_name']
                            temp['plant_id'] = j['plant_id']
                            temp['plant_name'] = j['plant_name']
                            temp['company_id'] = j['company_id']
                            temp['company_name'] = j['company_name']
                            temp['brand_id'] = j['brand_id']
                            temp['brand_name'] = j['brand_name']
                            temp['product_image'] = j['product_image']
                            temp['product_logo'] = k['product_logo']
                            temp['description'] = k['description']
                            temp['specification'] = k['specification']
                            temp['unit_price'] = j['unit_price']
                            temp['discount_in_percentage'] = l['discount_in_percentage']
                            temp['return_policy'] = j['return_policy']
                            temp['package_type'] = j['package_type']
                            temp['product_quantity'] = j['product_quantity']
                            temp['sub_total'] = i['sub_total']
                            temp['gst'] = l['gst']
                            temp['purchase_price'] = j['purchase_price']
                            output.append(temp)
            return jsonify({'status': True, 'message': 'Get product to instant success', 'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid instant details', 'result': output})


# -------------------------------------------- Change Instant Delivery Status -----------------------------------------
@app.route("/owo/change_instant_delivery_status", methods=['POST'])
@jwt_required
def changeinstantdeliverystatus():
    data = mongo.db.OWO
    db = data.instant_delivery_management
    db_p = data.products
    db_w = data.owo_users_wallet
    output = []
    instant_id = request.json['instant_id']
    delivery_status = request.json['delivery_status']
    date_time = datetime.datetime.now()
    for i in db.find({'delivery_status': 'pending'}):
        user_id = i['user_id']
        signin_type = i['signin_type']
        inst = i['instant_id']
        if int(instant_id) == i['instant_id']:
            db.update_many({'instant_id': int(instant_id)},
                           {'$set': {'delivery_status': delivery_status,
                                     'order_status': delivery_status}})
            if delivery_status == 'delivered':
                a = i['products']
                for j in a:
                    p_id = j['product_id']
                    p_quantity = j['product_quantity']
                    for n in db_p.find():
                        pro_id = n['product_id']
                        pro_quantity = n['product_quantity']
                        if str(pro_id) == str(p_id):
                            var = pro_quantity - p_quantity
                            db_p.find_one_and_update({'product_id': pro_id},
                                                     {'$set': {'product_quantity': var}})

            for w in db_w.find({'user_id': int(user_id)}):
                # print(user_id)
                if int(user_id) == int(user_id) and signin_type == w['signin_type'] and delivery_status == "cancelled":
                    ts = calendar.timegm(time.gmtime())
                    transaction_id = signin_type[:7].upper() + str(ts)
                    # print(transaction_id)
                    current_balance = w['current_balance']
                    refund_amount = int(i['sub_total'])
                    c_balance = int(refund_amount) + int(current_balance)
                    db_w.update_many({'user_id': int(w['user_id']), 'signin_type': str(w['signin_type'])},
                                     {'$set': {
                                         'current_balance': c_balance},
                                         '$push': {
                                             'recent_transactions': {'amount': refund_amount, 'payment_type': "wallet",
                                                                     'transaction_id': transaction_id,
                                                                     'transaction_type': signin_type,
                                                                     'transaction_date': date_time,
                                                                     'order_id': i['order_id'],
                                                                     'status': 'success',
                                                                     'closing_balance': c_balance,
                                                                     'current_balance': current_balance
                                                                     }}})

            output.append({'instant_id': instant_id, 'delivery_status': delivery_status})
            return jsonify({'status': True, 'message': 'Delivery_status changed success', 'result': output})
    return jsonify(
        {'status': False, 'message': 'You entered instant_id is not exist in event management', 'result': output})


# --------------------------------------------- Subscription orders ----------------------------------------------------
@app.route("/owo/subscription_orders", methods=['POST'])
@jwt_required
def subscriptionOrderHistory():
    data = mongo.db.OWO
    db = data.product_subscription_test
    db1 = data.subscription_history
    date = request.json['date']
    output = []
    out = []
    for i in db1.find({'date': date}):
        for j in i['order_history']:
            subscription_id = j['subscription_id']
            delivery_status = j['delivery_status']
            for s_id in db.find({'subscription_id': subscription_id}):
                if delivery_status == 'pending':
                    output.append({'customer_id': s_id['user_id'], 'mobile_number': s_id['mobile_number'],
                                   'email_id': s_id['email_id'], 'customer_type': s_id['signin_type'],
                                   'subscription_id': j['subscription_id'], 'product_count': j['product_count'],
                                   'sub_total': j['total_price'], 'discount': j['discount'], 'gst': j['gst'],
                                   'delivery_charges': s_id['delivery_charges'], 'total_price': s_id['total_price'],
                                   'order_id': j['order_id'], 'transaction_id': j['transaction_id'],
                                   'delivery_address': s_id['delivery_address'],
                                   'plan_starting_date': s_id['starting_date'],
                                   'plan_expire_date': s_id['plan_expiry_date'],
                                   'subscription_status': s_id['subscription_status'],
                                   'delivery_status': j['delivery_status'], 'buy_plan': s_id['buy_plan']})
    res_list = {frozenset(item.items()): item for item in output}.values()
    out.append(res_list)
    return jsonify({'status': True, 'message': 'Get subscription data success', 'return': list(res_list)})


# ------------------------------------- Company Disable/Enable --------------------------------------------------------
@app.route("/owo/enable_or_disable_company", methods=['POST'])
@jwt_required
def enableordisablecompany():
    data = mongo.db.OWO
    db_p = data.products
    db_c = data.companies
    db_pl = data.plant
    db_event = data.event_management
    db_instant = data.instant_delivery_management
    db_subsc = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    company_id = request.json['company_id']
    active_status = request.json['active_status']
    date_time = datetime.datetime.now()
    output = []
    products = []
    for i in db_c.find():
        id = i['company_id']
        a_st = i['active_status']
        if int(company_id) == int(id):
            db_c.update_many({'company_id': int(id)},
                             {'$set': {
                                 'active_status': active_status,
                             }
                             })
            try:
                brand = i['brand']
                for j in brand:
                    active = j['active_status']
                    db_c.update_many({'company_id': int(id)},
                                     {'$set': {
                                         'brand.$[].active_status': active_status
                                     }
                                     })
            except KeyError or ValueError:
                pass
            db_pl.update_many({'company_id': int(id)},
                              {'$set': {
                                  'active_status': active_status
                              }
                              })
            db_p.update_many({'company_id': int(id)},
                             {'$set': {
                                 'active_status': active_status
                             }
                             })
            if active_status is False:
                for u in db_p.find():
                    p_id = u['product_id']
                    c_id = u['company_id']
                    if str(company_id) == str(c_id):
                        products.append(p_id)
                # ----------------------------------------- Cancel the Event orders ---------------------------------------------------
                for k in db_event.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = k['products']
                    u_id = k['user_id']
                    s_type = k['signin_type']
                    try:
                        sub_t = k['sub_total']
                        dev_charges = k['delivery_charges']
                    except KeyError or ValueError:
                        sub_t = 0
                        dev_charges = 0
                    count = 1
                    for l in pro:
                        pro_id = l['product_id']
                        if pro_id in products:
                            db_event.update_many({'products.product_id': str(pro_id)},
                                                 {'$set': {'delivery_status': 'cancelled',
                                                           'order_status': 'cancelled'}})
                            for v in db_wallet.find():
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = v['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        db_wallet.update_many(
                                            {'user_id': int(v['user_id']), 'signin_type': str(v['signin_type'])},
                                            {'$set': {
                                                'current_balance': c_balance},
                                                '$push': {
                                                    'recent_transactions': {'amount': refund_amount,
                                                                            'payment_type': "wallet",
                                                                            'transaction_id': transaction_id,
                                                                            'transaction_type': 'event refund',
                                                                            'transaction_date': date_time,
                                                                            'order_id': k['event_id'],
                                                                            'status': 'success',
                                                                            'closing_balance': c_balance,
                                                                            'current_balance': current_balance
                                                                            }
                                                }})
                # ------------------------------------------- Cancel the Instant Orders ------------------------------------------------
                for a in db_instant.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['sub_total']
                    except KeyError or ValueError:
                        sub_t = 0
                    try:
                        dev_charges = a['delivery_charges']
                    except KeyError or ValueError:
                        dev_charges = 0
                    count = 1
                    for b in pro:
                        pro_id = b['product_id']
                        if pro_id in products:
                            db_instant.update_many({'products.product_id': str(pro_id)},
                                                   {'$set': {'delivery_status': 'cancelled',
                                                             'order_status': 'cancelled'}})
                            for c in db_wallet.find():
                                w_u_id = c['user_id']
                                w_s_type = c['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = c['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        db_wallet.update_many({'user_id': int(c['user_id']),
                                                               'signin_type': str(c['signin_type'])},
                                                              {'$set': {
                                                                  'current_balance': c_balance},
                                                                  '$push': {
                                                                      'recent_transactions': {'amount': refund_amount,
                                                                                              'payment_type': "wallet",
                                                                                              'transaction_id': transaction_id,
                                                                                              'transaction_type': 'instant refund',
                                                                                              'transaction_date': date_time,
                                                                                              'order_id': a[
                                                                                                  'instant_id'],
                                                                                              'status': 'success',
                                                                                              'closing_balance': c_balance,
                                                                                              'current_balance': current_balance
                                                                                              }
                                                                  }})

                # ----------------------------------------- Subscription cancel order -------------------------------------------------
                for a in db_subsc.find({'is_subscribed': True, 'subscription_status': 'active'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['total_price']
                    except KeyError or ValueError:
                        sub_t = 0
                    count = 1
                    for b in pro:
                        type = b['product_id']
                        if type in products:
                            db_subsc.update_many({'products.product_id': str(type)},
                                                 {'$set': {'subscription_status': 'cancelled'}})
                            for v in db_wallet.find():
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = v['current_balance']
                                        subc_amount = v['subscription_amount']
                                        refund_amount = subc_amount + current_balance
                                        db_wallet.update_many({'user_id': int(v['user_id']),
                                                               'signin_type': str(v['signin_type'])},
                                                              {'$set': {
                                                                  'subscription_amount': 0},
                                                                  '$push': {
                                                                      'recent_transactions': {
                                                                          'amount': subc_amount,
                                                                          'payment_type': "wallet",
                                                                          'transaction_id': transaction_id,
                                                                          'transaction_type': 'subscription refund',
                                                                          'transaction_date': date_time,
                                                                          'order_id': a['subscription_id'],
                                                                          'status': 'success',
                                                                          'closing_balance': current_balance,
                                                                          'current_balance': current_balance
                                                                      }}})
            output.append({'company_id': id, 'active_status': active_status, 'company_name': i['company_name']})
            return jsonify({"status": True, 'message': 'Change status success', 'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid company details', 'result': output})


# -------------------------------------------------- Enable Disable brands --------------------------------------------
@app.route("/owo/enable_or_disable_brand", methods=['POST'])
def enableordisablebrand():
    data = mongo.db.OWO
    db_p = data.products
    db_c = data.companies
    db_pl = data.plant
    db_event = data.event_management
    db_instant = data.instant_delivery_management
    db_subsc = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    company_id = request.json['company_id']
    brand_id = request.json['brand_id']
    active_status = request.json['active_status']
    date_time = datetime.datetime.now()
    output = []
    products = []
    for i in db_c.find({'brand.brand_id': int(brand_id)}):
        id = i['company_id']
        a_st = i['active_status']
        # print(id)
        try:
            brand = i['brand']
            for j in brand:
                b_id = j['brand_id']
                name = j['brand_name']
                if int(brand_id) == int(b_id) and int(company_id) == int(id):
                    # print(b_id)
                    db_c.update_many({'company_id': int(id), 'brand.brand_id': int(b_id)},
                                     {'$set': {
                                         'brand.$.active_status': active_status,
                                     }
                                     })
                    db_pl.update_many({'company_id': int(id), 'brand_id': int(b_id)},
                                      {'$set': {
                                          'active_status': active_status
                                      }
                                      })
                    db_p.update_many({'company_id': int(id), 'brand_id': int(b_id)},
                                     {'$set': {
                                         'active_status': active_status
                                     }
                                     })
                    if active_status is False:
                        # print('LOOP')
                        for u in db_p.find():
                            p_id = u['product_id']
                            c_id = u['company_id']
                            try:
                                brand = i['brand']
                                for j in brand:
                                    b_id = j['brand_id']
                                    if int(brand_id) == int(b_id) and int(company_id) == int(c_id):
                                        products.append(p_id)
                            except KeyError or ValueError:
                                pass
                        # ------------------------------------------- Cancel the Event orders --------------------------------------------------
                        for k in db_event.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                            pro = k['products']
                            u_id = k['user_id']
                            s_type = k['signin_type']
                            try:
                                sub_t = k['sub_total']
                                dev_charges = k['delivery_charges']
                            except KeyError or ValueError:
                                sub_t = 0
                                dev_charges = 0
                            # total = int(sub_t) + int(dev_charges)
                            count = 1
                            for l in pro:
                                pro_id = l['product_id']
                                if pro_id in products:
                                    db_event.update_many({'products.product_id': str(pro_id),
                                                          },
                                                         {'$set': {'delivery_status': 'cancelled',
                                                                   'order_status': 'cancelled'}})
                                    for v in db_wallet.find():
                                        w_u_id = v['user_id']
                                        w_s_type = v['signin_type']
                                        if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                            if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                                count = count + 1
                                                ts = calendar.timegm(time.gmtime())
                                                transaction_id = w_s_type[:7].upper() + str(ts)
                                                current_balance = v['current_balance']
                                                refund_amount = int(sub_t)
                                                c_balance = int(refund_amount) + int(current_balance)
                                                db_wallet.update_many({'user_id': int(v['user_id']),
                                                                       'signin_type': str(v['signin_type'])},
                                                                      {'$set': {
                                                                          'current_balance': c_balance},
                                                                          '$push': {
                                                                              'recent_transactions': {
                                                                                  'amount': refund_amount,
                                                                                  'payment_type': "wallet",
                                                                                  'transaction_id': transaction_id,
                                                                                  'transaction_type': 'event refund',
                                                                                  'transaction_date': date_time,
                                                                                  'order_id': k['event_id'],
                                                                                  'status': 'success',
                                                                                  'closing_balance': c_balance,
                                                                                  'current_balance': current_balance
                                                                              }
                                                                          }})
                        # ------------------------------------------- Cancel the Instant Orders ------------------------------------------------
                        for a in db_instant.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                            pro = a['products']
                            u_id = a['user_id']
                            s_type = a['signin_type']
                            try:
                                sub_t = a['sub_total']
                            except KeyError or ValueError:
                                sub_t = 0
                            try:
                                dev_charges = a['delivery_charges']
                            except KeyError or ValueError:
                                dev_charges = 0
                            # total = int(sub_t) + int(dev_charges)
                            count = 1
                            for b in pro:
                                pro_id = b['product_id']
                                if pro_id in products:
                                    db_instant.update_many({'products.product_id': str(pro_id)},
                                                           {'$set': {'delivery_status': 'cancelled',
                                                                     'order_status': 'cancelled'}})
                                    for c in db_wallet.find():
                                        w_u_id = c['user_id']
                                        w_s_type = c['signin_type']
                                        if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                            if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                                count = count + 1
                                                ts = calendar.timegm(time.gmtime())
                                                transaction_id = w_s_type[:7].upper() + str(ts)
                                                current_balance = c['current_balance']
                                                refund_amount = int(sub_t)
                                                c_balance = int(refund_amount) + int(current_balance)
                                                db_wallet.update_many({'user_id': int(c['user_id']),
                                                                       'signin_type': str(c['signin_type'])},
                                                                      {'$set': {
                                                                          'current_balance': c_balance},
                                                                          '$push': {
                                                                              'recent_transactions': {
                                                                                  'amount': refund_amount,
                                                                                  'payment_type': "wallet",
                                                                                  'transaction_id': transaction_id,
                                                                                  'transaction_type': 'instant refund',
                                                                                  'transaction_date': date_time,
                                                                                  'order_id': a['instant_id'],
                                                                                  'status': 'success',
                                                                                  'closing_balance': c_balance,
                                                                                  'current_balance': current_balance
                                                                              }
                                                                          }})

                        # ------------------------------------------- Subscription cancel order ------------------------------------------------
                        for a in db_subsc.find(
                                {'is_subscribed': True, 'subscription_status': 'active'}):
                            pro = a['products']
                            u_id = a['user_id']
                            s_type = a['signin_type']
                            try:
                                sub_t = a['total_price']
                            except KeyError or ValueError:
                                sub_t = 0
                            count = 1
                            for b in pro:
                                type = b['product_id']
                                if type in products:
                                    db_subsc.update_many({'products.product_id': str(type)},
                                                         {'$set': {'subscription_status': 'cancelled'}})
                                    for v in db_wallet.find():
                                        w_u_id = v['user_id']
                                        w_s_type = v['signin_type']
                                        if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                            if count == 1 and w_u_id == u_id and str(s_type) == str(
                                                    w_s_type):
                                                count = count + 1
                                                ts = calendar.timegm(time.gmtime())
                                                transaction_id = w_s_type[:7].upper() + str(ts)
                                                current_balance = v['current_balance']
                                                subc_amount = v['subscription_amount']
                                                refund_amount = subc_amount + current_balance
                                                db_wallet.update_many({'user_id': int(v['user_id']),
                                                                       'signin_type': str(
                                                                           v['signin_type'])},
                                                                      {'$set': {
                                                                          'subscription_amount': 0},
                                                                          '$push': {
                                                                              'recent_transactions': {
                                                                                  'amount': subc_amount,
                                                                                  'payment_type': "wallet",
                                                                                  'transaction_id': transaction_id,
                                                                                  'transaction_type': 'subscription refund',
                                                                                  'transaction_date': date_time,
                                                                                  'order_id': a['subscription_id'],
                                                                                  'status': 'success',
                                                                                  'closing_balance': current_balance,
                                                                                  'current_balance': current_balance
                                                                              }}})
                    output.append({'brand_id': brand_id, 'active_status': active_status, 'brand_name': name})
                    return jsonify({"status": True, 'message': 'Change status success', 'result': output})
        except KeyError or ValueError:
            pass
    return jsonify({'status': False, 'message': 'Please enter a valid brand details', 'result': output})


# --------------------------------------------- Plant Enable Disable --------------------------------------------------
@app.route("/owo/enable_or_disable_plant", methods=['POST'])
@jwt_required
def enableordisableplant():
    data = mongo.db.OWO
    db_p = data.plant
    db_prd = data.products
    db_event = data.event_management
    db_instant = data.instant_delivery_management
    db_subsc = data.product_subscription_test
    db_wallet = data.owo_users_wallet
    plant_id = request.json['plant_id']
    active_status = request.json['active_status']
    date_time = datetime.datetime.now()
    output = []
    products = []
    for i in db_p.find():
        id = i['plant_id']
        a_st = i['active_status']
        if int(plant_id) == int(id):
            db_p.update_many({'plant_id': int(id)},
                             {'$set': {
                                 'active_status': active_status
                             }
                             })
            db_prd.update_many({'plant_id': int(id)},
                               {'$set': {
                                   'active_status': active_status
                               }
                               })
            if active_status is False:
                print('LOOP')
                for u in db_prd.find():
                    p_id = u['plant_id']
                    if str(plant_id) == str(p_id):
                        products.append(u['product_id'])
                        print("OK")
                # ------------------------------------------ Cancel the Event orders ---------------------------------------------------
                for k in db_event.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = k['products']
                    u_id = k['user_id']
                    s_type = k['signin_type']
                    try:
                        sub_t = k['sub_total']
                    except KeyError or ValueError:
                        sub_t = 0
                    try:
                        dev_charges = k['delivery_charges']
                    except KeyError or ValueError:
                        dev_charges = 0
                    total = int(sub_t) + int(dev_charges)
                    count = 1
                    for l in pro:
                        pro_id = l['product_id']
                        if pro_id in products:
                            db_event.update_many({'products.product_id': str(pro_id)},
                                                 {'$set': {'delivery_status': 'cancelled',
                                                           'order_status': 'cancelled'}})

                            for v in db_wallet.find():
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        print(transaction_id)
                                        current_balance = v['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        print(c_balance)
                                        db_wallet.update_many(
                                            {'user_id': int(v['user_id']), 'signin_type': str(v['signin_type'])},
                                            {'$set': {
                                                'current_balance': c_balance},
                                                '$push': {
                                                    'recent_transactions': {'amount': refund_amount,
                                                                            'payment_type': "wallet",
                                                                            'transaction_id': transaction_id,
                                                                            'transaction_type': 'event refund',
                                                                            'transaction_date': date_time,
                                                                            'order_id': k['event_id'],
                                                                            'status': 'success',
                                                                            'closing_balance': c_balance,
                                                                            'current_balance': current_balance
                                                                            }}})

                # ------------------------------------------- Cancel the Instant Orders ------------------------------------------------
                for a in db_instant.find({'order_status': 'confirmed', 'delivery_status': 'pending'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['sub_total']
                    except KeyError or ValueError:
                        sub_t = 0
                    try:
                        dev_charges = a['delivery_charges']
                    except KeyError or ValueError:
                        dev_charges = 0
                    count = 1
                    for b in pro:
                        pro_id = b['product_id']
                        if pro_id in products:
                            db_instant.update_many({'products.product_id': str(pro_id)},
                                                   {'$set': {'delivery_status': 'cancelled',
                                                             'order_status': 'cancelled'}})
                            for c in db_wallet.find():
                                w_u_id = c['user_id']
                                w_s_type = c['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        print(transaction_id)
                                        current_balance = c['current_balance']
                                        refund_amount = int(sub_t)
                                        c_balance = int(refund_amount) + int(current_balance)
                                        print(c_balance)
                                        db_wallet.update_many({'user_id': int(c['user_id']),
                                                               'signin_type': str(c['signin_type'])},
                                                              {'$set': {
                                                                  'current_balance': c_balance},
                                                                  '$push': {
                                                                      'recent_transactions': {'amount': refund_amount,
                                                                                              'payment_type': "wallet",
                                                                                              'transaction_id': transaction_id,
                                                                                              'transaction_type': 'instant refund',
                                                                                              'transaction_date': date_time,
                                                                                              'order_id': a[
                                                                                                  'instant_id'],
                                                                                              'status': 'success',
                                                                                              'closing_balance': c_balance,
                                                                                              'current_balance': current_balance
                                                                                              }}})
                # -------------------------------------- Cancel Subscription orders ----------------------------------------
                for a in db_subsc.find({'is_subscribed': True, 'subscription_status': 'active'}):
                    pro = a['products']
                    u_id = a['user_id']
                    s_type = a['signin_type']
                    try:
                        sub_t = a['total_price']
                    except KeyError or ValueError:
                        sub_t = 0
                    count = 1
                    for b in pro:
                        type = b['package_type']
                        pro_id = b['product_id']
                        if pro_id in products:
                            print("ok subscription 1")
                            db_subsc.update_many({'products.product_id': str(pro_id)},
                                                 {'$set': {'subscription_status': 'cancelled'}})
                            for v in db_wallet.find():
                                print('ok subscription entered wallet"')
                                w_u_id = v['user_id']
                                w_s_type = v['signin_type']
                                if int(u_id) == int(w_u_id) and str(s_type) == str(w_s_type):
                                    if count == 1 and w_u_id == u_id and str(s_type) == str(w_s_type):
                                        count = count + 1
                                        ts = calendar.timegm(time.gmtime())
                                        transaction_id = w_s_type[:7].upper() + str(ts)
                                        current_balance = v['current_balance']
                                        subc_amount = v['subscription_amount']
                                        refund_amount = subc_amount + current_balance
                                        db_wallet.update_many({'user_id': int(v['user_id']),
                                                               'signin_type': str(v['signin_type'])},
                                                              {'$set': {
                                                                  'subscription_amount': 0},
                                                                  '$push': {
                                                                      'recent_transactions': {
                                                                          'amount': subc_amount,
                                                                          'payment_type': "wallet",
                                                                          'transaction_id': transaction_id,
                                                                          'transaction_type': 'subscription refund',
                                                                          'transaction_date': date_time,
                                                                          'order_id': a['subscription_id'],
                                                                          'status': 'success',
                                                                          'closing_balance': current_balance,
                                                                          'current_balance': current_balance
                                                                      }}})
                output.append({'company_id': id, 'active_status': active_status, 'plant_name': i['plant_name']})
                return jsonify({"status": True, 'message': 'Change status success', 'result': output})
            output.append({'company_id': id, 'active_status': active_status, 'plant_name': i['plant_name']})
            return jsonify({"status": True, 'message': 'Change status success', 'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid plant details', 'result': output})


# ------------------------------- new brand management -----------------------------------------------------------------
@app.route('/owo/add_new_brands', methods=['POST'])
@jwt_required
def addNewBrands():
    data = mongo.db.OWO
    db = data.companies
    # db_a = data.Sub_Admin
    # dbs_a = data.Super_Admin
    output = []
    admin_id = request.json['admin_id']
    admin_name = request.json['admin_name']
    company_name = request.json['company_name']
    company_id = request.json['company_id']
    brand_name = request.json['brand_name']
    available_city = request.json['available_city']
    brand_photo = request.json['brand_photo']
    order = request.json['order']
    brand_photo = brand_photo.encode()
    brand_description = request.json['brand_description']
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    try:
        trending_brand = request.json['trending_brand']
    except KeyError or ValueError:
        trending_brand = False
    city_count = int()
    for b in db.find():
        try:
            brand = b['brand']
            for brd in brand:
                city = brd['available_city']
                tb_true = brd['trending_brand']
                if str(city) == str(available_city):
                    if tb_true is True:
                        city_count = city_count + 1
                        # print(city_count)
                        if city_count == 5:
                            return jsonify({'status': False, 'message': (
                                    'city name ' + available_city + '  already having 5 trending brands'),
                                            'result': output})
        except KeyError or ValueError:
            pass
    for j in db.find():
        cmp_id = j['company_id']
        c_name = j['company_name']
        try:
            brand = j['brand']
        except KeyError or ValueError:
            brand = ''
        if int(cmp_id) == int(company_id):
            for k in brand:
                brand_id = k['brand_id']
                city_name = k['available_city']
                b_name = k['brand_name']
                if str(brand_name) == str(b_name) and str(city_name) == str(available_city):
                    return jsonify({'status': False, 'message': (
                            'In' + " " + available_city + " " + brand_name + " " + 'is already exist'),
                                    'result': output})
            brand_id_list = [id['brand_id'] for id in brand]
            if len(brand_id_list) is 0:
                brand_id = 1
            else:
                brand_id = int(brand_id_list[-1]) + 1
            brand_photo_path = '/var/www/html/owo/images/brand_images/' + str(brand_name) + '.' + 'jpg'
            mongo_db_path = '/owo/images/brand_images/' + str(brand_name) + '.' + 'jpg'
            with open(brand_photo_path, "wb") as fh:
                fh.write(base64.decodebytes(brand_photo))
            db.find_one_and_update({'company_id': int(company_id)},
                                   {'$push': {
                                       'brand': {'brand_id': int(brand_id), 'admin_id': admin_id,
                                                 'admin_name': admin_name,
                                                 'brand_name': str(brand_name),
                                                 'brand_photo': mongo_db_path,
                                                 'order': int(order),
                                                 'trending_brand': trending_brand,
                                                 'available_city': available_city,
                                                 'active_status': True,
                                                 'brand_description': str(brand_description),
                                                 'date_of_creation': date_of_creation}}})
            output.append(
                {'admin_id': admin_id,
                 'brand_id': int(brand_id), 'available_city': available_city,
                 'company_name': company_name, 'company_id': company_id,
                 'brand_name': str(brand_name), 'order': int(order), 'trending_brand': trending_brand,
                 'brand_photo': mongo_db_path, 'brand_description': str(brand_description),
                 'date_of_creation': date_of_creation})
            return jsonify({'status': True, 'message': 'Brand added successfully',
                            'result': output})
    return jsonify({'status': False, 'message': 'Please enter a valid credentials', 'result': output})


# ---------------------------------------------------Edit brand -------------------------------------------------------
@app.route('/owo/edit_brand', methods=['POST'])
@jwt_required
def editBrand():
    output = []
    data = mongo.db.OWO
    db = data.companies
    db_p = data.products
    db_plant = data.plant
    brandname = {""}
    count = int()
    admin_id = request.json['admin_id']
    company_name = request.json['company_name']
    company_id = request.json['company_id']
    brand_id = request.json['brand_id']
    available_city = request.json['available_city']
    brand_name = request.json['brand_name']
    brand_description = request.json['brand_description']
    order = request.json['order']
    modified_on = strftime("%d/%m/%Y %H:%M:%S")
    try:
        trending_brand = request.json['trending_brand']
    except KeyError or ValueError:
        trending_brand = False
    for i in db.find():
        c_id = i['company_id']
        cmp_name = i['company_name']
        try:
            brd = i['brand']
            for j in brd:
                brandname.add(j['brand_name'])
            # print(brandname)
            if brand_name in brandname:
                # print(brand_name)
                count = count + 1
            if count > 2:
                # print("success")
                # exit()
                output.append(
                    {'brand_name': brand_name, 'brand_id': brand_id, 'company_id': c_id, 'company_name': cmp_name})
                return jsonify({'status': False, 'message': (
                        'In' + " " + available_city + " " + brand_name + " " + 'is already exist'),
                                'result': output})
            else:
                if str(c_id) == str(company_id) and str(cmp_name) == str(company_name):
                    db.find_one_and_update({'company_id': int(company_id), 'brand.brand_id': int(brand_id)},
                                           {'$set':
                                                {'brand.$.modified_admin_id': admin_id,
                                                 'brand.$.brand_name': brand_name,
                                                 'brand.$.order': int(order),
                                                 'brand.$.trending_brand': trending_brand,
                                                 'brand.$.available_city': available_city,
                                                 'brand.$.modified_on': modified_on,
                                                 'brand.$.brand_description': brand_description,
                                                 }
                                            })
                    db_p.update_many({'brand.brand_id': int(brand_id), 'company_id': int(company_id)},
                                     {'$set': {'brand_name': str(brand_name)}})
                    db_plant.update_many({'brand_id': int(brand_id), 'company_id': int(company_id)},
                                         {'$set': {'brand_name': str(brand_name)}})
                    output.append(
                        {'brand_id': int(brand_id), 'admin_user_id': admin_id,
                         'company_name': company_name, "company_id": company_id, 'brand_name': brand_name,
                         'brand_description': brand_description, 'order': int(order), 'trending_brand': trending_brand,
                         'modified_on': modified_on})
                    return jsonify({'status': True, 'message': 'Brand updated successfully', 'result': output})
        except KeyError or ValueError:
            pass
    return jsonify({"status": False, "message": "Please enter a valid brand credentials", 'result': output})


# -------------------------------------------------------- Edit Brand image -------------------------------------------
@app.route('/owo/edit_brand_image/<company_id>/<brand_id>', methods=['POST'])
@jwt_required
def editBrandImg(company_id, brand_id):
    data = mongo.db.OWO
    db = data.companies
    db_a = data.Sub_Admin
    dbs_a = data.Super_Admin
    output = []
    # brand_id = request.json['brand_id']
    # company_id = request.json['company_id']
    brand_photo = request.json['brand_photo']
    ts = calendar.timegm(time.gmtime())
    a = str(brand_id) + str(ts)
    brand_photo = brand_photo.encode()
    brand_photo_path = '/var/www/html/owo/images/brand_images/' + str(a) + '.' + 'jpg'
    mongo_db_path = '/owo/images/brand_images/' + str(a) + '.' + 'jpg'
    with open(brand_photo_path, 'wb') as pl:
        pl.write(base64.decodebytes(brand_photo))
    for i in db.find():
        c_id = i['company_id']
        cmp_name = i['company_name']
        try:
            brd = i['brand']
            for j in brd:
                b_id = j['brand_id']
                if int(b_id) == int(brand_id) and int(c_id) == int(company_id):
                    db.update_many({'company_id': int(company_id), 'brand.brand_id': int(brand_id)},
                                   {'$set': {'brand.$.brand_photo': mongo_db_path}})
                    output.append({'brand_id': brand_id, 'brand_photo': mongo_db_path})
                    return jsonify({'status': True, 'message': 'Brand_photo updated successfully', 'result': output})
        except KeyError or ValueError:
            pass
    return jsonify({'status': False, 'message': 'Brand_id is not found', 'result': output})


# -------------------------------------------------------- Get Brand by Id --------------------------------------------
@app.route('/owo/get_brand_by_id/<company_id>/<brand_id>', methods=['GET'])
def getBrandById(brand_id, company_id):
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find():
        c_id = i['company_id']
        c_name = i['company_name']
        try:
            brd = i['brand']
            for j in brd:
                b_id = j['brand_id']
                if int(c_id) == int(company_id) and int(brand_id) == int(j['brand_id']):
                    temp = {}
                    temp['company_id'] = c_id
                    temp['company_name'] = i['company_name']
                    temp['admin_user_id'] = j['admin_id']
                    temp['brand_id'] = j['brand_id']
                    # temp['city_name'] = j['city_name']
                    temp['available_city'] = j['available_city']
                    temp['admin_name'] = j['admin_name']
                    temp['brand_name'] = j['brand_name']
                    temp['order'] = j['order']
                    temp['trending_brand'] = j['trending_brand']
                    temp['brand_description'] = j['brand_description']
                    temp['date_of_creation'] = j['date_of_creation']
                    if 'modified_admin_id' not in j.keys():
                        temp['modified_admin_id'] = ''
                    else:
                        temp['modified_admin_id'] = j['modified_admin_id']
                    if 'modified_on' not in j.keys():
                        temp['modified_on'] = ''
                    else:
                        temp['modified_on'] = j['modified_on']
                    if 'brand_photo' not in j.keys():
                        temp['brand_photo'] = ''
                    else:
                        temp['brand_photo'] = j['brand_photo']
                    if 'active_status' not in j.keys():
                        temp['active_status'] = ''
                    else:
                        temp['active_status'] = j['active_status']
                    if 'available_city' not in j.keys():
                        temp['available_city'] = ''
                    else:
                        temp['available_city'] = j['available_city']
                    output.append(temp)
                    return jsonify({"status": True, 'message': "Brand_id details get success", 'result': output})
        except KeyError or ValueError:
            pass
    return jsonify({"status": False, 'message': "Brand_id or company_name credentials are invalid", 'result': output})


# ----------------------------------------------------- Get All Brands ------------------------------------------------
@app.route('/owo/get_all_brand', methods=['GET'])
def getAllBrand():
    data = mongo.db.OWO
    db = data.companies
    output = []
    for i in db.find(sort=[('date_of_creation' and 'modified_on', pymongo.DESCENDING)]):
        c_name = i['company_name']
        c_id = i['company_id']
        try:
            brand = i['brand']
        except KeyError or ValueError:
            brand = 0
        if brand != 0:
            for j in brand:
                brand_id = j['brand_id']
                brand_name = j['brand_name']
                brand_photo = j['brand_photo']
                # city_name = j['city_name']
                available_city = j['available_city']
                brand_description = j['brand_description']
                created_by_admin_user_id = j['admin_id']
                created_by_admin_user_name = j['admin_name']
                date_of_creation = j['date_of_creation']
                trending_brand = j['trending_brand']
                order = j['order']
                if 'modified_on' not in j.keys():
                    date_of_modification = '',
                else:
                    date_of_modification = j['modified_on']
                if 'active_status' not in j.keys():
                    active_status = ''
                else:
                    active_status = j['active_status']
                if 'available_city' not in j.keys():
                    available_city = ''
                else:
                    available_city = j['available_city']

                output.append({'brand_id': brand_id, 'brand_name': brand_name, 'brand_description': brand_description,
                               'brand_photo': brand_photo, 'company_id': c_id, 'order': order,
                               'created_by_admin_user_id': created_by_admin_user_id,
                               'created_by_admin_user_name': created_by_admin_user_name,
                               'available_city': available_city,
                               'company_name': c_name, 'date_of_creation': date_of_creation,
                               'trending_brand': trending_brand,
                               'date_of_modification': date_of_modification, 'active_status': active_status})
    return jsonify({"status": True, 'message': 'Get all brands success', 'result': output})


# -------------------------------------------------------- Delete Brand -----------------------------------------------
@app.route('/owo/delete_brand', methods=['POST'])
@jwt_required
def deleteBrand():
    data = mongo.db.OWO
    db = data.companies
    output = []
    brand_id = request.json['brand_id']
    company_name = request.json['company_name']
    # print(brand_id)
    for i in db.find():
        c_name = i['company_name']
        try:
            brd = i['brand']
        except KeyError or ValueError:
            pass
        for j in brd:
            b_id = j['brand_id']
            if int(brand_id) == int(j['brand_id']) and str(c_name) == str(company_name):
                # print("ok success")
                # print(b_id)
                db.update_one({'company_name': str(company_name)},
                              {'$pull': {"brand": {'brand_id': int(brand_id)}}})
                return jsonify({"status": True, "message": "Deleted brand success", 'result': output})
    return jsonify({"status": False, "message": "Brand_id credentials wrong", 'result': output})


# ------------------------------------------------- company and city based get brands ---------------------------------
@app.route('/owo/company_city_based_get_brands', methods=['POST'])
@jwt_required
def companycitybasedgetbrands():
    data = mongo.db.OWO
    db = data.companies
    output = []
    cp_name = str()
    company_id = request.json['company_id']
    city = request.json['city']
    for i in db.find():
        cmp_id = i['company_id']
        if int(cmp_id) == int(company_id):
            cmp_name = i['company_name']
            cp_name = cmp_name
            try:
                brand = i['brand']
                for j in brand:
                    a_city = j['available_city']
                    if str(a_city) == str(city):
                        output.append(j)
                return jsonify({'status': True, 'message': ('Get details' + " " + city + " " +
                                                            "and company name is" + ' ' + cmp_name), 'result': output})
            except KeyError or ValueError:
                pass
    return jsonify({"status": False,
                    'message': ('No records found at' + ' ' + city + " " + "and comapny name is " + ' ' + cp_name),
                    'result': output})


# -------------------------------------------------- Trending brands ---------------------------------------------------
@app.route('/owo/trendingbrands', methods=['GET'])
def trendingbrands():
    data = mongo.db.OWO
    db = data.companies
    output = []
    city = []
    trending = db.find({'brand.trending_brand': True})
    for i in trending:
        try:
            brand = i['brand']
            for j in brand:
                city.append(j['available_city'])
        except KeyError or ValueError:
            pass
    result = list(dict.fromkeys(city))
    # print(result)
    for k in db.find({'brand.active_status': True}):
        try:
            brand = k['brand']
            for l in brand:
                scity = l['available_city']
                if scity in city:
                    output.append(l)
        except KeyError or ValueError:
            pass
    # print(output)
    return jsonify({"status": True, 'message': "Trending brand details", 'result': output})


# ----------------------------------------- Trending brands admin ------------------------------------------------------
@app.route('/owo/trending_brands_admin', methods=['GET'])
def trendingbrandsadmin():
    data = mongo.db.OWO
    db = data.companies
    output = []
    city = []
    trending = db.find({'brand.trending_brand': True})
    for i in trending:
        try:
            brand = i['brand']
            for j in brand:
                temp = {}
                temp['brand_id'] = j['brand_id']
                temp['brand_status'] = j['active_status']
                temp['brand_name'] = j['brand_name']
                temp['date_of_creation'] = j['date_of_creation']
                temp['available_city'] = j['available_city']
                output.append(temp)
        except KeyError or ValueError:
            pass
    return jsonify({'status': True, 'message': 'Trending Brands Details', 'result': output})


# --------------------------------------------------- Category Management ----------------------------------------------
# --------------------------------------------------- Add Category  ---------------------------------------------------
@app.route('/owo/add_category', methods=['POST'])
@jwt_required
def addCategory():
    data = mongo.db.OWO
    db = data.category
    dbs_a = data.Super_Admin
    output = []
    ts = calendar.timegm(time.gmtime())
    admin_id = request.json['admin_id']
    admin_userName = request.json['admin_userName']
    available_city = request.json['available_city']
    order = request.json['order']
    package_type = request.json['package_type']
    unit_type = request.json['unit_type']
    category_id_list = [i['category_id'] for i in db.find()]
    if len(category_id_list) is 0:
        category_id = 1
    else:
        category_id = int(category_id_list[-1]) + 1
    b = str(category_id) + str(ts)
    category_image = request.json['category_image']
    category_image = category_image.encode()
    image_path = '/var/www/html/owo/images/category_images/' + str(b) + '.' + 'jpg'
    mongo_db_path1 = '/owo/images/category_images/' + str(b) + '.' + 'jpg'
    print(mongo_db_path1)
    with open(image_path, 'wb') as pl:
        pl.write(base64.decodebytes(category_image))
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    category_type = package_type + " " + unit_type

    for j in db.find():
        c_type = j['category_type']
        a_city = j['available_city']
        if str(c_type) == str(category_type) and str(a_city) == str(available_city):
            return jsonify({'status': False,
                            'message': ('In' + " " + available_city + " " + category_type + " " + 'is already exist'),
                            'result': output})

    db.insert(
        {'admin_id': int(admin_id), 'admin_userName': admin_userName, 'available_city': available_city,
         'package_type': package_type, 'order': int(order),
         'unit_type': unit_type, 'category_type': category_type, 'active_category': True,
         'category_id': int(category_id), 'category_image': mongo_db_path1,
         'date_of_creation': date_of_creation})
    output.append(
        {'admin_id': int(admin_id), 'admin_userName': admin_userName, 'available_city': available_city,
         'package_type': package_type, 'order': int(order),
         'unit_type': unit_type, 'category_type': category_type, 'active_category': True,
         'category_id': int(category_id), 'category_image': mongo_db_path1,
         'date_of_creation': date_of_creation})
    return jsonify({'status': True, 'message': 'Category added successfully', 'result': output})


# --------------------------------------------------- Edit Category --------------------------------------------------
@app.route('/owo/edit_category', methods=['POST'])
@jwt_required
def editCategory():
    data = mongo.db.OWO
    db = data.category
    output = []
    admin_id = request.json['admin_id']
    category_id = request.json['category_id']
    available_city = request.json['available_city']
    package_type = request.json['package_type']
    unit_type = request.json['unit_type']
    modified_on = strftime("%d/%m/%Y %H:%M:%S")
    order = request.json['order']
    category_type = package_type + " " + unit_type
    category_type_result_and_city = db.find({'category_type': category_type, 'available_city': available_city})
    if category_type_result_and_city.count() > 1:
        return jsonify({'status': False, 'message': 'Category_type already exist', 'result': output})
    info = db.find()
    for i in info:
        id = i['category_id']
        if str(id) == str(category_id):
            db.find_one_and_update({'category_id': int(category_id)}, {'$set': {'modified_by': int(admin_id),
                                                                                'order': order,
                                                                                'package_type': package_type,
                                                                                'available_city': available_city,
                                                                                'unit_type': unit_type,
                                                                                'category_type': category_type,
                                                                                'modified_on': modified_on}})
            output.append(
                {'category_id': int(category_id), 'available_city': available_city, 'order': order,
                 'package_type': package_type, 'unit_type': unit_type, 'category_type': category_type,
                 'modified_by': admin_id, 'modified_on': modified_on})
            return jsonify({'status': True, 'message': 'Category data updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid category_id'})


# --------------------------------------------------- Edit Category Image----------------------------------------------
@app.route('/owo/edit_category_image', methods=['POST'])
@jwt_required
def editCategoryImage():
    data = mongo.db.OWO
    db = data.category
    output = []
    category_id = request.json['category_id']
    ts = calendar.timegm(time.gmtime())
    a = str(category_id) + str(ts)
    modified_on = strftime("%d/%m/%Y %H:%M:%S")
    category_image = request.json['category_image']
    category_image = category_image.encode()
    category_image_path = '/var/www/html/owo/images/category_images/' + str(a) + '.' + 'jpg'
    mongo_db_path1 = '/owo/images/category_images/' + str(a) + '.' + 'jpg'
    with open(category_image_path, 'wb') as pl:
        pl.write(base64.decodebytes(category_image))
    info = db.find()
    for j in info:
        p_id = j['category_id']
        if str(p_id) == str(category_id):
            db.update({'category_id': int(category_id)}, {'$set': {'category_image': mongo_db_path1,
                                                                   'modified_on': modified_on}})
            output.append({'category_id': int(category_id), 'category_image': mongo_db_path1,
                           'modified_on': modified_on})
            return jsonify({'status': True, 'message': 'Category image updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Something went wrong', 'result': output})


# --------------------------------------------------- Get Category by ID ----------------------------------------------
@app.route('/owo/get_category/<category_id>', methods=['GET'])
def getCategory(category_id):
    data = mongo.db.OWO
    db = data.category
    output = []
    info = db.find()
    for i in info:
        id = i['category_id']
        if int(id) == int(category_id):
            output.append({'category_id': i['category_id'], 'available_city': i['available_city'],
                           'package_type': i['package_type'], 'order': i['order'],
                           'unit_type': i['unit_type'], 'category_type': i['category_type'],
                           'category_image': i['category_image'], 'active_category': i['active_category']})
            return jsonify({'status': True, 'message': 'Category data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid category_id', 'result': output})


# --------------------------------------------------- Delete Category -------------------------------------------------
@app.route('/owo/delete_category/<category_id>', methods=['POST'])
def deleteCategory(category_id):
    data = mongo.db.OWO
    db = data.category
    for i in db.find():
        id = i['category_id']
        if int(id) == int(category_id):
            db.remove({'category_id': int(category_id)})
            return jsonify({'status': True, 'message': 'Category deleted successfully'})
    return jsonify({'status': False, 'message': 'Category_id not found'})


# --------------------------------------------------- Get All Package Type --------------------------------------------
@app.route('/owo/get_package_type', methods=['GET'])
def getCategoryPackageType():
    data = mongo.db.OWO
    db = data.category
    output = []
    for i in db.find({'active_category': True}):
        output.append({'category_type': i['category_type']})
    return jsonify({'status': True, 'message': 'List of package_type ', 'result': output})


# --------------------------------------------------- Get All Category ------------------------------------------------
@app.route('/owo/get_all_categories', methods=['GET'])
def getAllCategories():
    data = mongo.db.OWO
    db = data.category
    output = []
    for i in db.find(sort=[('order', pymongo.ASCENDING)]):
        temp = {}
        temp['category_id'] = i['category_id']
        temp['category_image'] = i['category_image']
        temp['available_city'] = i['available_city']
        temp['package_type'] = i['package_type']
        temp['unit_type'] = i['unit_type']
        temp['category_type'] = i['category_type']
        temp['date_of_creation'] = i['date_of_creation']
        temp['active_category'] = i['active_category']
        temp['order'] = i['order']
        if 'modified_on' not in i.keys():
            temp['modified_on'] = ''
        else:
            temp['modified_on'] = i['modified_on']
        output.append(temp)
    return jsonify({'status': True, 'message': 'List of  category data get successfully', 'result': output})


# ------------------------------------- Get all categories export admin side ------------------------------------------
@app.route('/owo/get_all_categories_export_admin', methods=['GET'])
def getAllCategoriesforexport():
    data = mongo.db.OWO
    db = data.category
    output = []
    for i in db.find(sort=[('order', pymongo.ASCENDING)]):
        temp = {}
        temp['category_id'] = i['category_id']
        temp['category_image'] = i['category_image']
        temp['unit_type'] = i['package_type']
        temp['units'] = i['unit_type']
        temp['package_type'] = i['category_type']
        temp['available_city'] = i['available_city']
        temp['date_of_creation'] = i['date_of_creation']
        temp['active_category'] = i['active_category']
        temp['order'] = i['order']
        if 'modified_on' not in i.keys():
            temp['modified_on'] = ''
        else:
            temp['modified_on'] = i['modified_on']
        output.append(temp)
    return jsonify({'status': True, 'message': 'Category data get export successfully', 'result': output})


# ----------------------------------- Get package type based on city name ---------------------------------------------
@app.route('/owo/basedOnCityNameGetPackageType', methods=['POST'])
@jwt_required
def getPackageType():
    data = mongo.db.OWO
    db = data.category
    output = []
    available_city = request.json['available_city']
    for i in db.find():
        a_city = i['available_city']
        if str(a_city) == str(available_city):
            if i['active_category'] == True:
                output.append({'category_type': i['category_type'], 'available_city': i['available_city']})
    return jsonify({'status': True, 'message': 'Package_type data get successfully', 'result': output})


# ---------------------------------------------- Add new products ------------------------------------------------------
@app.route('/owo/add_new_product', methods=['POST'])
@jwt_required
def addNewProducts():
    data = mongo.db.OWO
    dbs_a = data.Super_Admin
    db_p = data.products
    db_r = data.rating
    output = []
    company_name = request.json['company_name']
    company_id = request.json['company_id']
    brand_name = request.json['brand_name']
    brand_id = request.json['brand_id']
    plant_name = request.json['plant_name']
    plant_id = request.json['plant_id']
    city_name = request.json['city_name']
    product_name = request.json['product_name']
    # -------------------------------- System Generates Unique ID ------------------------------------------------------
    product_id_list = [i['product_id'] for i in db_p.find()]
    # print('ok1')
    if len(product_id_list) is 0:
        product_id = 1
    else:
        product_id = int(product_id_list[-1]) + 1
    # ------------------------------------------------------------------------------------------------------------------

    product_logo = request.json['product_logo']
    product_logo = product_logo.encode()
    product_logo_path = '/var/www/html/owo/images/product_images/' + str(product_id) + '.' + 'jpg'
    mongo.db.path1 = '/owo/images/product_images/' + str(product_id) + '.' + 'jpg'
    with open(product_logo_path, 'wb') as pl:
        pl.write(base64.decodebytes(product_logo))
    description = request.json['description']
    specification = request.json['specification']
    unit_price = request.json['unit_price']
    discount_in_percentage = request.json['discount_in_percentage']
    purchase_price = request.json['purchase_price']
    return_policy = request.json['return_policy']
    package_type = request.json['package_type']
    expiry_date = request.json['expiry_date']
    technical = request.json['technical']
    gst = request.json['gst']
    mrp = request.json['mrp']
    added_by = request.json['added_by']
    date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
    try:
        you_may_also_like = request.json['you_may_also_like']
        new_arrival = request.json['new_arrival']
    except KeyError or ValueError:
        you_may_also_like = False
        new_arrival = False
    package_id = int()

    # ------------------------------------------ Super Admin Adding The Data -----------------------------------------
    for o in db_p.find():
        pro_name = o['product_name']
        # print(pro_name)

        # ---------------------------------------- Finds the product name which user entered --------------------------
        if str(product_name) == str(pro_name):
            return jsonify({'status': False, 'message': 'Product name already exists'})

    # ---------------------------------- Insert the data into collection ----------------------------------------------
    db_p.insert(
        {'company_name': company_name, 'company_id': company_id,
         'brand_name': brand_name, 'brand_id': brand_id, 'plant_name': plant_name, 'plant_id': plant_id,
         'product_name': product_name, 'product_id': str(product_id), 'product_quantity': 0,
         'description': description, 'specification': specification, 'technical': technical, 'city_name': city_name,
         'product_logo': mongo.db.path1, 'active_status': True, 'you_may_also_like': you_may_also_like,
         'new_arrival': new_arrival,
         'date_of_creation': date_of_creation,
         'package_type': [{'package_type': package_type,
                           'package_id': package_id,
                           'purchase_price': str(purchase_price),
                           'unit_price': str(unit_price), 'gst': gst, 'mrp': mrp,
                           'discount_in_percentage': str(discount_in_percentage),
                           'return_policy': str(return_policy), 'expiry_date': expiry_date,
                           'added_by': added_by
                           }]})
    db_r.insert({'product_id': str(product_id), 'product_name': product_name, 'current_rating': float(5),
                 'rating_history': []})
    output.append(
        {'company_name': company_name, 'brand_name': brand_name, 'product_name': product_name,
         'product_id': product_id, 'plant_name': plant_name, 'plant_id': plant_id,
         'package_type': package_type, 'purchase_price': purchase_price,
         'description': description, 'specification': specification, 'date_of_creation': date_of_creation,
         'product_logo': mongo.db.path1,
         'unit_price': unit_price, 'discount_in_percentage': discount_in_percentage,
         'package_id': package_id, 'you_may_also_like': you_may_also_like, 'new_arrival': new_arrival,
         'added_by': added_by, 'gst': gst, 'mrp': mrp,
         'technical': technical, 'active_status': True,
         'return_policy': return_policy, 'expiry_date': expiry_date,
         'city_name': city_name})

    return jsonify({'status': True, 'message': 'Product inserted', 'result': output})


# ----------------------------------------- Edit New Product ----------------------------------------------------------
@app.route('/owo/edit_new_product', methods=['POST'])
@jwt_required
def editNewProduct():
    data = mongo.db.OWO
    db_a = data.Super_Admin
    db_p = data.products
    output = []
    # roles_id = request.json['roles_id']
    package_id = request.json['package_id']
    city_name = request.json['city_name']
    product_id = request.json['product_id']
    description = request.json['description']
    specification = request.json['specification']
    unit_price = request.json['unit_price']
    gst = request.json['gst']
    mrp = request.json['mrp']
    discount_in_percentage = request.json['discount_in_percentage']
    purchase_price = request.json['purchase_price']
    return_policy = request.json['return_policy']
    package_type = request.json['package_type']
    expiry_date = request.json['expiry_date']
    technical = request.json['technical']
    modified_by = request.json['modified_by']
    date_of_modification = strftime("%d/%m/%Y %H:%M:%S")
    try:
        you_may_also_like = request.json['you_may_also_like']
        new_arrival = request.json['new_arrival']
    except KeyError or ValueError:
        you_may_also_like = False
        new_arrival = False
    # for i in db_a.find():
    #     a_id = i['roles_id']
    #     a_name = i['email_id']
    #     if int(a_id) == int(roles_id):
    #         print("ok1")
    #         print(a_id)
    for k in db_p.find():
        pro_id = k['product_id']
        # print(pro_id)
        # print("ok2")
        if str(product_id) == str(pro_id):
            # print("ok3")
            db_p.update_one({'product_id': str(product_id), 'package_type.package_id': int(package_id)},
                            {'$set': {'package_type.$[].unit_price': str(unit_price),
                                      'package_type.$[].purchase_price': str(purchase_price),
                                      'package_type.$[].package_type': package_type,
                                      'package_type.$[].discount_in_percentage': str(discount_in_percentage),
                                      'package_type.$[].return_policy': str(return_policy),
                                      'package_type.$[].expiry_date': expiry_date,
                                      'package_type.$[].gst': gst,
                                      'package_type.$[].mrp': mrp,
                                      'technical': technical,
                                      'city_name': city_name,
                                      'specification': specification,
                                      'description': description,
                                      'you_may_also_like': you_may_also_like,
                                      'new_arrival': new_arrival,
                                      'modified_by': modified_by,
                                      'date_of_modification': date_of_modification}})
            output.append({'package_id': package_id, 'package_type': package_type,
                           'purchase_price': purchase_price, 'description': description,
                           'specification': specification, 'unit_price': unit_price,
                           'discount_in_percentage': discount_in_percentage, 'mrp': mrp,
                           'return_policy': return_policy, 'expiry_date': expiry_date,
                           'date_of_modification': date_of_modification, 'you_may_also_like': you_may_also_like,
                           'new_arrival': new_arrival, 'modified_by': modified_by, 'technical': technical, 'gst': gst,
                           'city_name': city_name})
            return jsonify({'status': True, 'message': 'Product edited successfully', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Admin not found', 'result': output})


# --------------------------------------- Get All Products ------------------------------------------------------------
@app.route('/owo/get_products', methods=['GET'])
def getProducts():
    data = mongo.db.OWO
    db = data.products
    output = []

    for i in db.find(sort=[('date_of_modification' or 'date_of_creation', pymongo.DESCENDING)]):
        company_name = i['company_name']
        brand_name = i['brand_name']
        product_name = i['product_name']
        product_id = i['product_id']
        plant_name = i['plant_name']
        product_logo = i['product_logo']
        city_name = i['city_name']
        if 'product_image' not in i.keys():
            product_image = '',
        else:
            product_image = i['product_image']
        description = i['description']
        specification = i['specification']
        new_arrival = i['new_arrival']
        you_may_also_like = i['you_may_also_like']
        active_status = i['active_status']
        try:
            p_type = i['package_type']
            for j in p_type:
                package_type = j['package_type']
                package_id = j['package_id']
                purchase_price = j['purchase_price']
                unit_price = j['unit_price']
                discount_in_percentage = j['discount_in_percentage']
                return_policy = j['return_policy']
                expiry_date = j['expiry_date']
                roles_id = j['added_by']
                gst = j['gst']
                mrp = j['mrp']
                date_of_creation = i['date_of_creation']
                if 'date_of_modification' not in i.keys():
                    date_of_modification = '',
                else:
                    date_of_modification = i['date_of_modification']
                if 'technical' not in i.keys():
                    technical = '',
                else:
                    technical = i['technical']
                output.append({'company_name': company_name, 'brand_name': brand_name, 'product_name': product_name,
                               'specification': specification, 'plant_name': plant_name,
                               'product_id': product_id, 'product_logo': product_logo,
                               'product_status': i['active_status'], 'product_image': product_image,
                               'description': description, 'package_type': package_type, 'package_id': package_id,
                               'purchase_price': purchase_price, 'unit_price': unit_price,
                               'active_status': active_status, 'new_arrival': new_arrival,
                               'you_may_also_like': you_may_also_like,
                               'discount_in_percentage': discount_in_percentage, 'gst': gst, 'mrp': mrp,
                               'return_policy': return_policy, 'expiry_date': expiry_date, 'roles_id': roles_id,
                               'city_name': city_name, 'technical': technical,
                               'date_of_modification': date_of_modification, 'date_of_creation': date_of_creation})
        except KeyError or ValueError:
            p_type = " "
    return jsonify({"status": True, 'message': 'Get all products success', 'result': output})


# --------------------------------------- Get Product by Product ID ----------------------------------------------------
@app.route('/owo/get_product_by_id/<product_id>', methods=['GET'])
def getProductByID(product_id):
    data = mongo.db.OWO
    db = data.products
    output = []
    details = db.find()
    for i in details:
        p_id = i['product_id']
        # print(product_id)
        # print(p_id)
        if str(product_id) == str(p_id):
            # print("ok")
            p_type = i['package_type']
            # print(p_type)
            for j in p_type:
                temp = {}
                temp['city_name'] = i['city_name']
                temp['company_name'] = i['company_name']
                temp['brand_name'] = i['brand_name']
                temp['product_id'] = i['product_id']
                temp['product_name'] = i['product_name']
                temp['product_logo'] = i['product_logo']
                temp['plant_name'] = i['plant_name']
                temp['new_arrival'] = i['new_arrival']
                temp['you_may_also_like'] = i['you_may_also_like']
                if 'product_image' not in i.keys():
                    temp['product_image'] = '',
                else:
                    temp['product_image'] = i['product_image']
                temp['unit_price'] = j['unit_price']
                temp['discount_in_percentage'] = j['discount_in_percentage']
                temp['purchase_price'] = j['purchase_price']
                temp['return_policy'] = j['return_policy']
                temp['package_type'] = j['package_type']
                temp['expiry_date'] = j['expiry_date']
                temp['gst'] = j['gst']
                temp['mrp'] = j['mrp']
                temp['specification'] = i['specification']
                temp['roles_id'] = j['added_by']
                temp['package_id'] = j['package_id']
                if 'technical' not in i.keys():
                    temp['technical'] = '',
                else:
                    temp['technical'] = i['technical']

                temp['description'] = i['description']
                output.append(temp)
    return jsonify({"status": True, 'message': "Product by id details get success", 'result': output})


# --------------------------------- Get product you may also like ------------------------------------------------------
@app.route('/owo/get_products_you_may_also_like', methods=['GET'])
def getProductyoumayalsolike():
    data = mongo.db.OWO
    db = data.products
    output = []
    details = db.find({'you_may_also_like': True, 'active_status': True})
    for i in details:
        p_type = i['package_type']
        for j in p_type:
            temp = {}
            temp['city_name'] = i['city_name']
            temp['company_name'] = i['company_name']
            temp['brand_name'] = i['brand_name']
            temp['product_id'] = i['product_id']
            temp['product_name'] = i['product_name']
            temp['product_logo'] = i['product_logo']
            temp['plant_name'] = i['plant_name']
            temp['new_arrival'] = i['new_arrival']
            temp['active_status'] = i['active_status']
            temp['you_may_also_like'] = i['you_may_also_like']
            if 'product_image' not in i.keys():
                temp['product_image'] = '',
            else:
                temp['product_image'] = i['product_image']
            temp['unit_price'] = j['unit_price']
            temp['discount_in_percentage'] = j['discount_in_percentage']
            temp['purchase_price'] = j['purchase_price']
            temp['return_policy'] = j['return_policy']
            temp['package_type'] = j['package_type']
            temp['expiry_date'] = j['expiry_date']
            temp['gst'] = j['gst']
            temp['mrp'] = j['mrp']
            temp['specification'] = i['specification']
            temp['roles_id'] = j['added_by']
            temp['package_id'] = j['package_id']

            if 'technical' not in i.keys():
                temp['technical'] = '',
            else:
                temp['technical'] = i['technical']

            temp['description'] = i['description']
            output.append(temp)
    return jsonify({"status": True, 'message': "Product by id details get success", 'result': output})


# ------------------------------------- Get product new arrival ------------------------------------------------------
@app.route('/owo/get_products_new_arrival', methods=['GET'])
def getProductnewarrival():
    data = mongo.db.OWO
    db = data.products
    output = []
    details = db.find({'new_arrival': True, 'active_status': True})
    for i in details:
        p_type = i['package_type']
        for j in p_type:
            temp = {}
            temp['city_name'] = i['city_name']
            temp['company_name'] = i['company_name']
            temp['brand_name'] = i['brand_name']
            temp['product_id'] = i['product_id']
            temp['product_name'] = i['product_name']
            temp['product_logo'] = i['product_logo']
            temp['plant_name'] = i['plant_name']
            temp['active_status'] = i['active_status']
            temp['new_arrival'] = i['new_arrival']
            temp['you_may_also_like'] = i['you_may_also_like']
            if 'product_image' not in i.keys():
                temp['product_image'] = '',
            else:
                temp['product_image'] = i['product_image']
            temp['unit_price'] = j['unit_price']
            temp['discount_in_percentage'] = j['discount_in_percentage']
            temp['purchase_price'] = j['purchase_price']
            temp['return_policy'] = j['return_policy']
            temp['package_type'] = j['package_type']
            temp['expiry_date'] = j['expiry_date']
            temp['gst'] = j['gst']
            temp['mrp'] = j['mrp']
            temp['specification'] = i['specification']
            temp['roles_id'] = j['added_by']
            temp['package_id'] = j['package_id']

            if 'technical' not in i.keys():
                temp['technical'] = '',
            else:
                temp['technical'] = i['technical']

            temp['description'] = i['description']
            output.append(temp)
    return jsonify({"status": True, 'message': "Product by id details get success", 'result': output})


# ------------------------------------- Get product new arrival ------------------------------------------------------
@app.route('/owo/get_products_new_arrival_admin', methods=['GET'])
def getProductnewarrivaladmin():
    data = mongo.db.OWO
    db = data.products
    output = []
    details = db.find({'new_arrival': True})
    for i in details:
        p_type = i['package_type']
        for j in p_type:
            temp = {}
            temp['city_name'] = i['city_name']
            temp['product_status'] = i['active_status']
            temp['product_id'] = i['product_id']
            temp['product_name'] = i['product_name']
            temp['date_of_creation'] = i['date_of_creation']
            output.append(temp)
    return jsonify({"status": True, 'message': "Product by id details get success", 'result': output})


# ------------------------------------- get_products_you_may_also_like_admin-------------------------------------------
@app.route('/owo/get_products_you_may_also_like_admin', methods=['GET'])
def getProductyoumayalsolikeadmin():
    data = mongo.db.OWO
    db = data.products
    output = []
    details = db.find({'you_may_also_like': True})
    for i in details:
        p_type = i['package_type']
        for j in p_type:
            temp = {}
            temp['city_name'] = i['city_name']
            temp['product_id'] = i['product_id']
            temp['product_status'] = i['active_status']
            temp['product_name'] = i['product_name']
            temp['date_of_creation'] = i['date_of_creation']
            output.append(temp)
    return jsonify({"status": True, 'message': "Product by id details get success", 'result': output})


# --------------------------------------------- Add Config Loyalty ----------------------------------------------
@app.route('/owo/add_config_loyalty', methods=['POST'])
@jwt_required
def add_subscription_loyalty():
    data = mongo.db.OWO
    db = data.config_loyalty
    output = []
    loyalty_type = request.json['loyalty_type']
    loyalty_points = request.json['loyalty_points']

    id_list = [i['id'] for i in db.find()]
    if len(id_list) is 0:
        id = 1
    else:
        id = int(id_list[-1]) + 1
    try:
        for i in db.find():
            l_type = i['loyalty_type']
            if str(l_type) == str(loyalty_type):
                return jsonify({'status': False, 'message': 'loyalty type already exist', 'result': output})
        db.insert({'id': int(id), 'loyalty_type': loyalty_type, 'loyalty_points': int(loyalty_points)})
        output.append({'id': int(id), 'loyalty_type': loyalty_type,
                       'loyalty_points': int(loyalty_points)})
        return jsonify({'status': True, 'message': 'Loyalty type added successfully', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e), 'return': output})


# ------------------------------------------ Edit Subscription Loyalty ------------------------------------------------
@app.route('/owo/edit_config_loyalty', methods=['POST'])
@jwt_required
def edit_config_loyalty():
    data = mongo.db.OWO
    db = data.config_loyalty
    output = []
    loyalty_type = request.json['loyalty_type']
    loyalty_points = request.json['loyalty_points']
    try:
        for i in db.find():
            m_type = i['loyalty_type']
            if str(m_type) == str(loyalty_type):
                db.find_one_and_update({'loyalty_type': str(loyalty_type)},
                                       {'$set': {'loyalty_points': int(loyalty_points)}})
                output.append({'loyalty_type': loyalty_type, 'loyalty_points': int(loyalty_points)})
                return jsonify({'status': True, 'message': 'loyalty points updated successfully', 'result': output})
        return jsonify({'status': False, 'message': 'Invalid loyalty type', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e), 'return': output})


# ------------------------------------------------ Get All Loyalty ------------------------------------------
@app.route('/owo/get_config_loyalty', methods=['GET'])
def getConfigLoyalty():
    data = mongo.db.OWO
    db = data.config_loyalty
    output = []
    for i in db.find():
        temp = {}
        temp['id'] = i['id']
        temp['loyalty_type'] = i['loyalty_type']
        temp['loyalty_points'] = i['loyalty_points']
        output.append(temp)
    return jsonify({'status': True, 'message': 'All data get successfully', 'result': output})


# ---------------------------------------- Get loyalty by id ---------------------------------------------
@app.route('/owo/get_config_loyalty/<id>', methods=['GET'])
def getConfigLoyaltyByID(id):
    data = mongo.db.OWO
    db = data.config_loyalty
    output = []
    for i in db.find():
        l_id = i['id']
        if int(l_id) == int(id):
            output.append({'id': i['id'], 'loyalty_type': i['loyalty_type'],
                           'loyalty_points': i['loyalty_points']})
            return jsonify({'status': True, 'message': 'Loyalty data get successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid id', 'result': output})


# ------------------------------------------- OWO membership Get api ------------------------------------------------
@app.route('/owo/admin_membership_get', methods=['GET'])
def getMembership():
    data = mongo.db.OWO
    db = data.membership
    db_sub = data.product_subscription_test
    output = []

    for i in db_sub.find():
        subscription_status = i['subscription_status']
    for j in db.find():
        user_id = j['user_id']
        email_id = j['email_id']
        mobile_number = j['mobile_number']
        signin_type = j['signin_type']
        subscription_id = j['subscription_id']
        membership = j['membership']
        output.append({'user_id': user_id, 'email_id': email_id, 'mobile_number': mobile_number,
                       'signin_type': signin_type, 'subscription_id': subscription_id, 'membership': membership,
                       'subscription_status': subscription_status})
    return jsonify({'status': True, 'message': 'Membership details', 'result': output})


# ---------------------------------------------- Get loyalty point list ----------------------------------------------
@app.route('/owo/loyalty_point_table', methods=['GET'])
def getLoyaltyPointsList():
    data = mongo.db.OWO
    db = data.loyalty
    db_m = data.membership
    output = []
    for i in db.find():
        temp = {}
        temp['user_id'] = i['user_id']
        temp['mobile_number'] = i['mobile_number']
        temp['email_id'] = i['email_id']
        temp['signin_type'] = i['signin_type']
        temp['loyalty_balance'] = i['loyalty_balance']
        output.append(temp)
    return jsonify({'status': True, 'message': 'Loyalty point data get successfully', 'result': output})


# ----------------------------------------------- Earned by subscription --------------------------------------------------
@app.route('/owo/earned_by_subscription/<user_id>/<signin_type>', methods=['GET'])
def earnedBySubscription(user_id, signin_type):
    data = mongo.db.OWO
    db_sh = data.subscription_history
    db_m = data.membership
    db_c = data.config_loyalty
    db = data.loyalty
    # db1 = data.owo_users_wallet
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        r_earning = i['recent_earnings']
        if int(u_id) == int(user_id) and str(s_type) == str(signin_type):
            for j in r_earning:
                e_type = j['earn_type']
                if str(e_type) == 'subscribed':
                    o_id = j['order_id']
                    for k in db_m.find():
                        id = k['user_id']
                        stype = k['signin_type']
                        if int(id) == int(u_id) and str(stype) == str(s_type):
                            print('ok1')
                            temp = {}
                            temp['order_id'] = j['order_id']
                            temp['order_value'] = j['order_value']
                            temp['membership_type'] = k['membership']
                            temp['transaction_date'] = j['earn_date']
                            temp['current_balance'] = j['current_balance']
                            temp['loyalty_earned'] = j['earn_points']
                            temp['closing_balance'] = j['closing_balance']
                            output.append(temp)
    return jsonify({'status': True, 'message': 'Loyalty points earned by subscription', 'result': output})


# ---------------------------------------------- Earned by referral ----------------------------------------------------
@app.route('/owo/earned_by_referral/<user_id>/<signin_type>', methods=['GET'])
def earnedByReferral1(user_id, signin_type):
    data = mongo.db.OWO
    db = data.loyalty
    output = []
    output1 = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        r_earning = i['recent_earnings']
        if int(user_id) == int(u_id) and str(s_type) == str(signin_type):
            for j in r_earning:
                e_type = j['earn_type']
                if str(e_type) == 'referral_code':
                    temp = {}
                    temp['referred_user_id'] = j['referred_user_id']
                    temp['referred_signin_type'] = j['signin_type']
                    temp['date_of_registration'] = j['earn_date']
                    if 'current_balance' not in j.keys():
                        temp['current_balance'] = ""
                    else:
                        temp['current_balance'] = j['current_balance']
                    temp['loyalty_earned'] = j['earn_points']
                    if 'closing_balance' not in j.keys():
                        temp['closing_balance'] = " "
                    else:
                        temp['closing_balance'] = j['closing_balance']
                    output.append(temp)
    return jsonify({'status': True, 'message': 'Loyalty point earned by referral', 'result': output + output1})


# ------------------------------------------------ loyalty_redeemed --------------------------------------------------
@app.route('/owo/loyalty_redeemed/<user_id>/<signin_type>', methods=['GET'])
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
                    temp['current_balance'] = j['current_balance']
                    temp['redeemed_points'] = j['order_value']
                    temp['closing_balance'] = j['closing_balance']
                    output.append(temp)
    return jsonify({'status': True, 'message': 'Redeemed loyalty points', 'result': output})


# ----------------------------------------- Rating management ---------------------------------------------------------
@app.route('/owo/rating_management', methods=['GET'])
def ratingManagement():
    data = mongo.db.OWO
    db_p = data.products
    db = data.rating
    output = []
    for i in db.find():
        r_history = i['rating_history']
        for j in r_history:
            user_id = j['user_id']
            user_mobile_number = j['mobile_number']
            user_email_id = j['email_id']
            order_id = j['order_id']
            product_id = i['product_id']
            product_name = i['product_name']
            date_and_time_of_rating = j['rating_date_time']
            rating_given_by_user_in_1_to_5_range = j['rating']
            overall_product_rating = i['current_rating']
            output.append({'user_id': user_id,
                           'user_mobile_number': user_mobile_number,
                           'user_email_id': user_email_id,
                           'order_id': order_id,
                           'product_id': product_id, 'product_name': product_name,
                           'date_and_time_of_rating': date_and_time_of_rating,
                           'rating': rating_given_by_user_in_1_to_5_range,
                           'overall_product_rating': overall_product_rating})
    return jsonify({'status': True, 'message': 'List of ratings', 'result': output})


# ----------------------------------------------- Banner Mangemenent --------------------------------------------------
# -----------------------------------------------Add New Banner  -------------------------------------------------------
@app.route('/owo/add_banner', methods=['POST'])
def add_banner():
    try:
        data = mongo.db.OWO
        db = data.banners
        # dbs_a = data.Super_Admin
        output = []
        # ts = calendar.timegm(gmtime())
        # ts = calendar.timegm(time.gmtime())
        ts = calendar.timegm(time.gmtime())
        date_of_creation = strftime("%d/%m/%Y %H:%M:%S")
        admin_id = request.json['admin_id']
        admin_userName = request.json['admin_userName']
        screen_name = request.json['screen_name']
        order = request.json['order']
        city_name = request.json['city_name']
        banner_id_list = [i['banner_id'] for i in db.find()]
        if len(banner_id_list) is 0:
            banner_id = 1
        else:
            banner_id = int(banner_id_list[-1]) + 1
        banner_image = request.json['banner_image']
        banner_image = banner_image.encode()
        b = str(banner_id) + str(ts)
        banner_path = '/var/www/html/owo/images/banner_images/' + str(b) + '.' + 'jpg'
        mongo_db_path = '/owo/images/banner_images/' + str(b) + '.' + 'jpg'
        with open(banner_path, "wb") as fh:
            fh.write(base64.decodebytes(banner_image))
        db.insert({'admin_id': int(admin_id), 'admin_userName': admin_userName, 'screen_name': screen_name,
                   'date_of_creation': date_of_creation, 'order': int(order), 'city_name': city_name,
                   'banner_image': mongo_db_path,
                   'banner_id': int(banner_id)})
        output.append({'admin_id': admin_id, 'admin_userName': admin_userName, 'screen_name': screen_name,
                       'banner_image': mongo_db_path, 'order': order, 'city_name': city_name,
                       'date_of_creation': date_of_creation, 'banner_id': int(banner_id)})
        return jsonify({'status': True, 'message': 'Banner added', 'result': output})
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)})


# ----------------------------------------------------- Edit Banner  --------------------------------------------------
@app.route('/owo/edit_banner', methods=['POST'])
def edit_banner():
    data = mongo.db.OWO
    db = data.banners
    output = []
    banner_id = request.json['banner_id']
    admin_id = request.json['admin_id']
    admin_userName = request.json['admin_userName']
    order = request.json['order']
    screen_name = request.json['screen_name']
    city_name = request.json['city_name']
    modified_on = strftime("%d/%m/%Y %H:%M:%S")
    info = db.find()
    for i in info:
        b_id = i['banner_id']
        if int(b_id) == int(banner_id):
            db.find_one_and_update({'banner_id': int(banner_id)},
                                   {'$set': {'admin_id': admin_id, 'admin_userName': admin_userName,
                                             'modified_on': modified_on, 'order': int(order), 'city_name': city_name,
                                             'screen_name': screen_name}})
            output.append({'banner_id': banner_id, 'screen_name': screen_name, 'admin_id': admin_id,
                           'modified_on': modified_on, 'order': order, 'city_name': city_name,
                           'admin_userName': admin_userName})
            return jsonify({'status': True, 'message': 'Updated successfully', 'result': output})
    else:
        return jsonify({'status': False, 'message': 'Invalid Banner Id'})


# ------------------------------------------------- Edit banner images -------------------------------------------------
@app.route('/owo/edit_banner_image', methods=['POST'])
def editbannerimage():
    data = mongo.db.OWO
    db = data.banners
    output = []
    # ts = calendar.timegm(time.gmtime())
    banner_id = request.json['banner_id']
    modified_on = strftime("%d/%m/%Y %H:%M:%S")
    # ts1 = calendar.timegm(strftime("%H:%M:%S"))
    banner_image = request.json['banner_image']
    banner_image = banner_image.encode()
    ts = calendar.timegm(time.gmtime())
    b = str(banner_id) + str(ts)
    # a = str(banner_id) + str(ts1)
    banner_path = '/var/www/html/owo/images/banner_images/' + str(b) + '.' + 'jpg'
    mongo_db_path = '/owo/images/banner_images/' + str(b) + '.' + 'jpg'

    with open(banner_path, "wb") as fh:
        fh.write(base64.decodebytes(banner_image))
    info = db.find()
    for i in info:
        b_id = i['banner_id']
        if int(b_id) == int(banner_id):
            db.find_one_and_update({'banner_id': int(banner_id)},
                                   {'$set': {'banner_image': mongo_db_path,
                                             }
                                    })
            output.append({'banner_id': banner_id, 'modified_on': modified_on})
            return jsonify({'status': True, 'message': 'Updated successfully', 'result': output})
    return jsonify({'status': False, 'message': 'Invalid Banner Id'})


# ----------------------------------------------- Delete Banner  ------------------------------------------------------
@app.route('/owo/delete_banner', methods=['POST'])
def delete_banner():
    data = mongo.db.OWO
    db = data.banners
    banner_id = request.json['banner_id']
    for q in db.find():
        id = q['banner_id']
        if int(banner_id) == int(id):
            db.remove({'banner_id': int(banner_id)})
            return jsonify({'status': True, 'message': 'Delete  successfully'})
    return jsonify({"status": False, 'message': "Banner_id invalid"})


# ----------------------------------------------- Get Banner  ---------------------------------------------------------
@app.route('/owo/get_banner_management', methods=['GET'])
def get_banner_managemet():
    data = mongo.db.OWO
    db = data.banners
    output = []
    for q in db.find():
        try:
            modified_on = q['modified_on']

        except KeyError or ValueError:
            modified_on = ''
        output.append({'screen_name': q['screen_name'], 'banner_image': q['banner_image'], 'admin_id': q['admin_id'],
                       'admin_userName': q['admin_userName'], 'city_name': q['city_name'],
                       'date_of_creation': q['date_of_creation'], 'order': q['order'], 'banner_id': q['banner_id'],
                       'modified_on': modified_on})
    return jsonify({'status': True, 'message': 'Banner Management data get successfully', 'result': output})


# ------------------------------------------------- Get Banner by ID  --------------------------------------------------
@app.route('/owo/get_banner/<banner_id>', methods=['GET'])
def get_banner(banner_id):
    data = mongo.db.OWO
    db = data.banners
    output = []
    info = db.find()
    for i in info:
        try:
            modified_on = i['modified_on']

        except KeyError or ValueError:
            modified_on = ''

        id = i['banner_id']
        if int(id) == int(banner_id):
            output.append(
                {'screen_name': i['screen_name'], 'banner_image': i['banner_image'], 'admin_id': i['admin_id'],
                 'admin_userName': i['admin_userName'], 'city_name': i['city_name'],
                 'date_of_creation': i['date_of_creation'], 'order': i['order'], 'banner_id': banner_id,
                 'modified_on': modified_on})
    return jsonify({'status': True, 'message': 'Banner data get successfully', 'result': output})


# -------------------------------------------------- Get app banner ----------------------------------------------------
@app.route("/owo/get_app_banner", methods=['POST'])
def getappbanners():
    data = mongo.db.OWO
    db = data.banners
    hstb = []
    hsbb = []
    hstc20 = []
    hstc10 = []
    tb = []
    hsumla = []
    city_name = request.json['city_name']
    for i in db.find():
        if str(i['city_name']) == str(city_name):
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
    return jsonify({'status': True, 'message': 'Get banners success', 'Home_screen_top_banner': hstb,
                    'Home_screen_brand_banner': hsbb, 'Home_screen_top_categories_20_ltrs': hstc20,
                    'Home_screen_top_categories_10_ltrs': hstc10, 'Trending_brands': tb,
                    'Home_screen_you_may_also_like': hsumla})


# -------------------------------------------------- Get all subscription  ------------------------------------------
@app.route('/owo/get_allsubscription', methods=['GET'])
# @jwt_required
def getAllSubscription():
    data = mongo.db.OWO
    db = data.product_subscription_test
    output = []
    # date = request.json['date']
    for i in db.find(
            {'products.cart_status': "deactive", 'subscription_status': "active", 'payment_status': 'success'}):
        try:
            prd = i['products']
            try:
                total_price = i['total_price']
            except KeyError or ValueError:
                pass
            for k in prd:
                try:
                    r_id = i['order_id']
                    amount = i['total_price']
                except KeyError or ValueError:
                    pass
                try:
                    t_id = i['transaction_id']
                except KeyError or ValueError:
                    pass
                try:
                    delivery_charges = i['delivery_charges']
                except KeyError or ValueError:
                    delivery_charges = ''
                try:
                    transaction_date = i['transaction_date']
                except KeyError or ValueError:
                    transaction_date = ''
                s_total = int(total_price) - int(delivery_charges)
                output.append({'subscription_id': i['subscription_id'], 'buy_plan': i['buy_plan'],
                               'customer_id': i['user_id'], 'transaction_date': transaction_date,
                               'start_day': i['start_day'], 'sub_total': s_total,
                               'starting_date': i['starting_date'], 'order_id': r_id,
                               'delivery_charges': delivery_charges,
                               'subscription_status': i['subscription_status'],
                               'plan_expiry_date': i['plan_expiry_date'],
                               'customer_type': i['signin_type'], 'product_count': len(prd),
                               'mobile_number': i['mobile_number'], 'email': i['email_id'], 'transaction_id': t_id,
                               'total_price': total_price})
        except KeyError or ValueError:
            pass
    res_list = {frozenset(item.items()): item for item in output}.values()
    return jsonify({'status': True, 'message': 'Get subscription plans success', 'result': list(res_list)})


# ------------------------------------------ Get user id and signin type for view loyalty details ----------------------
@app.route('/owo/get_userIdSigninType/<user_id>/<signin_type>', methods=['GET'])
def getUserIdSigninType(user_id, signin_type):
    data = mongo.db.OWO
    db = data.loyalty
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        if str(s_type) == str(signin_type) and int(user_id) == int(u_id):
            output.append({'user_id': i['user_id'], 'signin_type': i['signin_type']})
    return jsonify({'status': True, 'message': 'Data get successfully', 'result': output})


# ------------------------------------- Get App Notifications ---------------------------------------------------------
@app.route('/owo/get_app_notification', methods=['GET'])
def getAppNotification():
    data = mongo.db.OWO
    db = data.app_notifications
    db_ind = data.individual_users
    db_corp = data.corporate_users
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        notification_type = i['title']
        notification_title = i['title']
        notification_text_description = i['notifications']
        date_time = i['date_time']
        for j in db_ind.find():
            ui_id = j['user_id']
            si_type = j['signin_type']
            m_number = j['mobile_number']
            e_id = j['email_id']
            if 'device_token' not in j.keys():
                device_token = ''
            else:
                device_token = j['device_token']
            if str(si_type) == str(s_type) and int(u_id) == int(ui_id):
                output.append({'user_id': u_id, 'signin_type': s_type, 'mobile_number': m_number, 'email_id': e_id,
                               'device_id': device_token, 'notification_type': notification_type,
                               'notification_title': notification_title,
                               'notification_text_description': notification_text_description,
                               'sent_time_stamp': date_time})
        for k in db_corp.find():
            ui_id = k['user_id']
            si_type = k['signin_type']
            m_number = k['mobile_number']
            e_id = k['email_id']
            if 'device_token' not in k.keys():
                device_token = ''
            else:
                device_token = k['device_token']
            if str(si_type) == str(s_type) and int(u_id) == int(ui_id):
                output.append({'user_id': u_id, 'signin_type': s_type, 'mobile_number': m_number, 'email_id': e_id,
                               'device_id': device_token, 'notification_type': notification_type,
                               'notification_title': notification_title,
                               'notification_text_description': notification_text_description,
                               'sent_time_stamp': date_time})
    return jsonify({'status': True, 'message': 'Get all SMS notification text', 'result': output})


# --------------------------------- ------------ Get plans ----------------------------------------
@app.route("/owo/get_plans", methods=['POST'])
def getPlanBySubscriptionIdPlans():
    data = mongo.db.OWO
    db2 = data.subscription_history
    db = data.product_subscription_test
    db1 = data.products
    output = []
    res = []
    delivery_status = str()
    subscription_id = request.json['subscription_id']
    date = request.json['date']
    check_date = parse(date)
    day = findDay(date)
    for i in db.find():
        sub_id = i['subscription_id']
        if int(subscription_id) == int(sub_id) and i['is_subscribed'] == True:
            print("ok")
            try:
                for j in i['products']:
                    print("status ok")
                    if j['cart_status'] == "deactive" and j['product_status'] == "enabled":
                        print("cartdeactive")
                        set_quantity = j['set_quantity']
                        plan_start_date = i['starting_date']
                        plan_expiry_date = i['plan_expiry_date']
                        plan_sd = parse(plan_start_date)
                        plan_ed = parse(plan_expiry_date)
                        if plan_sd <= check_date <= plan_ed:
                            print("okdates")
                            for qua in set_quantity:
                                mydict = qua
                                for key in mydict:
                                    if key == day:
                                        quantity = mydict[key]
                                        print(quantity)
                                        p_i = j['purchase_price']
                                        total_price = p_i * quantity
                                        for k in db1.find():
                                            p_type = k['package_type']
                                            if str(j['product_id']) == str(k['product_id']):
                                                # print(p_id)
                                                print("product_found")
                                                # if 'product_image' not in k.keys():
                                                #     product_image = '',
                                                # else:
                                                #     product_image = k['product_image']
                                                for l in p_type:
                                                    # u_price = l['unit_price']
                                                    if 'package_type' not in l.keys():
                                                        package_type = '',
                                                    else:
                                                        package_type = l['package_type']
                                                    # print(product_image)
                                                    # s_id = i['subscription_id']
                                                    # print(s_id)
                                                    print("statusdone")
                                                    output.append(
                                                        {'product_id': j['product_id'],
                                                         'product_name': k['product_name'],
                                                         'subscription_id': i['subscription_id'],
                                                         'package_type': package_type, 'product_quantity': quantity,
                                                         'product_total_price': total_price,
                                                         'purchase_price': j['purchase_price']})
                                                    print("done")
                                                    # res = [i for i in output if not (i['product_quantity'] == 0)]
                                                    # print(res)
                                            # resp = {k: v for d in res for k, v in d.items()}
            except KeyError or ValueError:
                pass
    return jsonify({'status': True, 'message': 'Plans get successfully', 'result': output})


# --------------------------------- ------------ notification variables ----------------------------------------
@app.route("/owo/notification_variables", methods=['POST'])
def notificationvariables():
    data = mongo.db.OWO
    db = data.notification_variables
    output = []
    type = request.json['type']
    for i in db.find({}, {'_id': False}):
        if str(type) == str(i['type']):
            print(type)
            if 'first_name' not in i.keys():
                first_name = str(),
            else:
                first_name = i['first_name']
            if 'last_name' not in i.keys():
                last_name = str(),
            else:
                last_name = i['last_name']
            print(len(first_name))
            if 'amount' not in i.keys():
                amount = 0,
            else:
                amount = i['amount']
            print(amount)
            if 'order_id' not in i.keys():
                order_id = 0,
            else:
                order_id = i['order_id']
            print(order_id)
            if len(first_name) > 1:
                output.append({'first_name': first_name})
                return jsonify({'status': True, 'message': 'Details', 'first_name': first_name})
            if len(amount) > 1:
                output.append({'amount': amount})
                return jsonify({'status': True, 'message': 'Details', 'amount': amount})
            if len(order_id) > 1:
                output.append({'order_id': order_id})
                return jsonify({'status': True, 'message': 'Details', 'order_id': order_id})
            if len(last_name) > 1:
                output.append({'last_name': last_name})
                return jsonify({'status': True, 'message': 'Details', 'last_name': last_name})
    return jsonify({'status': False, 'message': 'Something went wrong', 'result': output})


# --------------------------------- ------------ Get all cancelled subscriptions ---------------------------------------
@app.route('/owo/get_allcancelsubscription', methods=['GET'])
# @jwt_required
def getAllCancelSubscription():
    data = mongo.db.OWO
    db = data.product_subscription_test
    output = []
    for i in db.find({'$or': [{'subscription_status': "cancelled"}, {'subscription_status': "expired"}, ]}):
        try:
            prd = i['products']
            try:
                total_price = i['total_price']
            except KeyError or ValueError:
                pass
            for k in prd:
                try:
                    r_id = i['order_id']
                    amount = i['total_price']
                    # print(amount)
                except KeyError or ValueError:
                    pass
                try:
                    t_id = i['transaction_id']
                except KeyError or ValueError:
                    pass
                try:
                    delivery_charges = i['delivery_charges']
                except KeyError or ValueError:
                    delivery_charges = ''
                try:
                    transaction_date = i['transaction_date']
                except KeyError or ValueError:
                    transaction_date = ''
                s_total = int(total_price) - int(delivery_charges)
                output.append({'subscription_id': i['subscription_id'], 'buy_plan': i['buy_plan'],
                               'customer_id': i['user_id'], 'transaction_date': transaction_date,
                               'start_day': i['start_day'], 'sub_total': s_total,
                               'starting_date': i['starting_date'], 'order_id': r_id,
                               'delivery_charges': delivery_charges,
                               'subscription_status': i['subscription_status'],
                               'plan_expiry_date': i['plan_expiry_date'],
                               'customer_type': i['signin_type'], 'product_count': len(prd),
                               'mobile_number': i['mobile_number'], 'email': i['email_id'], 'transaction_id': t_id,
                               'total_price': total_price})
        except KeyError or ValueError:
            pass
    res_list = {frozenset(item.items()): item for item in output}.values()
    return jsonify({'status': True, 'message': 'Get subscription plans success', 'result': list(res_list)})


# ------------------------------------------ Get SMS Notifications ----------------------------------
@app.route('/owo/get_SMS_notification', methods=['GET'])
def getSMSNotification():
    data = mongo.db.OWO
    db = data.sms_notification
    db_ind = data.individual_users
    db_corp = data.corporate_users
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        notification_type = i['title']
        notification_title = i['title']
        notification_text_description = i['notifications']
        date_time = i['date_time']
        for j in db_ind.find():
            ui_id = j['user_id']
            si_type = j['signin_type']
            m_number = j['mobile_number']
            e_id = j['email_id']
            if 'device_token' not in j.keys():
                device_token = ''
            else:
                device_token = j['device_token']
            if str(si_type) == str(s_type) and int(u_id) == int(ui_id):
                output.append({'user_id': u_id, 'signin_type': s_type, 'mobile_number': m_number, 'email_id': e_id,
                               'device_id': device_token, 'notification_type': notification_type,
                               'notification_title': notification_title,
                               'notification_text_description': notification_text_description,
                               'sent_time_stamp': date_time})
        for k in db_corp.find():
            ui_id = k['user_id']
            si_type = k['signin_type']
            m_number = k['mobile_number']
            e_id = k['email_id']
            if 'device_token' not in k.keys():
                device_token = ''
            else:
                device_token = k['device_token']
            if str(si_type) == str(s_type) and int(u_id) == int(ui_id):
                output.append({'user_id': u_id, 'signin_type': s_type, 'mobile_number': m_number, 'email_id': e_id,
                               'device_id': device_token, 'notification_type': notification_type,
                               'notification_title': notification_title,
                               'notification_text_description': notification_text_description,
                               'sent_time_stamp': date_time})
    return jsonify({'status': True, 'message': 'Get all SMS notification text', 'result': output})


# ------------------------------------- Get Email Notifications ----------------------------------
@app.route('/owo/get_Email_notification', methods=['GET'])
def getEmailNotification():
    data = mongo.db.OWO
    db = data.email_notifications
    db_ind = data.individual_users
    db_corp = data.corporate_users
    output = []
    for i in db.find():
        u_id = i['user_id']
        s_type = i['signin_type']
        notification_type = i['title']
        notification_title = i['title']
        notification_text_description = i['notifications']
        date_time = i['date_time']
        for j in db_ind.find():
            ui_id = j['user_id']
            si_type = j['signin_type']
            m_number = j['mobile_number']
            e_id = j['email_id']
            if 'device_token' not in j.keys():
                device_token = ''
            else:
                device_token = j['device_token']
            if str(si_type) == str(s_type) and int(u_id) == int(ui_id):
                output.append({'user_id': u_id, 'signin_type': s_type, 'mobile_number': m_number, 'email_id': e_id,
                               'device_id': device_token, 'notification_type': notification_type,
                               'notification_title': notification_title,
                               'notification_text_description': notification_text_description,
                               'sent_time_stamp': date_time})
        for k in db_corp.find():
            ui_id = k['user_id']
            si_type = k['signin_type']
            m_number = k['mobile_number']
            e_id = k['email_id']
            if 'device_token' not in k.keys():
                device_token = ''
            else:
                device_token = k['device_token']
            if str(si_type) == str(s_type) and int(u_id) == int(ui_id):
                output.append({'user_id': u_id, 'signin_type': s_type, 'mobile_number': m_number, 'email_id': e_id,
                               'device_id': device_token, 'notification_type': notification_type,
                               'notification_title': notification_title,
                               'notification_text_description': notification_text_description,
                               'sent_time_stamp': date_time})
    return jsonify({'status': True, 'message': 'Get all SMS notification text', 'result': output})



if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=6001, debug=True, threaded=True)