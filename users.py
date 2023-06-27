from flask import Blueprint,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
import validators
from database import User,Bucket,Guest
import custom_validators
import os
import config
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt_identity
import shutil
user_blueprint = Blueprint("user",__name__,url_prefix="/user")

@user_blueprint.post("/register")
def register():
    name = request.json.get("username","")
    email = request.json.get("email","")
    npass = request.json.get("new_passwd","")
    cpass = request.json.get("confirm_passwd","")

    if not name or not email or not npass or not cpass:
        return jsonify(({
            "error":"missing fields",
            "fields_required":[
                "email","username","new_passwd","confirm_passwd"
            ]
        })),400
    if not validators.email(email):
        return jsonify({"error":"email not valid"}),400
    if User.objects(email=email):
        return jsonify({"error":"email already taken"}),400
    if npass !=cpass:
        return jsonify({"eror":"passwords dont match"}),400
    if not custom_validators.isvalidpasswd(npass):
        return jsonify({"error":"password must be 8 charecters and must ot have spaces"}),400
    user = User(email=email,passwd=generate_password_hash(npass),username=name)
    user.save()
    nu = User.objects(email=email).first()
    os.mkdir(config.UPLOAD_FOLDER + "/" + str(nu._id))
    return jsonify({"message":"user created"})

@user_blueprint.get("/login")
def login():
    email = request.json.get("email","")
    passwd = request.json.get("passwd","")
    if not email or not passwd:
        return jsonify({
            "error":"missing fields",
            "fields_required":[
                "email","passwd"
            ]
        }),400
    user = User.objects(email=email).first()
    if user:
        if check_password_hash(user.passwd,passwd):
            acess = create_access_token(identity=str(user._id))
            refresh = create_refresh_token(identity=str(user._id))
            return jsonify({
                "email":user.email,
                "access":acess,
                "refresh":refresh
            }),200
        else:
            return jsonify({"error":"invalid credentialls"}),400
    else:
        return jsonify({"error":"account not found"}),404


@user_blueprint.get("/refresh/access")
@jwt_required(refresh=True)
def refreh_access():
    cur_user = get_jwt_identity()
    user = User.objects(_id=cur_user)
    if user:
        acess = create_access_token(identity=cur_user)
        return jsonify({
            "access":acess
        }),200
    else:
        return jsonify({"error":"user not found"}),404

@user_blueprint.patch("/modify/credentials/<string:choice>")
@jwt_required()
def change_cred(choice):
    cur_user = get_jwt_identity()
    mods = ["username","email","passwd"]
    user = User.objects(_id=cur_user).first()
    if not user:
        return jsonify({"error":"user not found"}),404
    if choice in mods:
        if choice == "username":
            userame = request.json.get("username","")
            if userame:
                user.username=userame
                user.save()
                return jsonify({"message":"username changed"}),200
            else:
                return jsonify({
                    "error":"missing fields",
                    "fields_required":["username"]
                }),400
        elif choice == "email":
            email = request.json.get("email","")
            if email:
                if not validators.email(email):
                    return jsonify({"error":"email not valid"}),400
                if User.objects(email=email):
                    return jsonify({"error":"email already taken"}),400
                user.email=email
                user.save()
                return jsonify({"message":"email changed"}),200
            else:
                return jsonify({
                    "error": "missing fields",
                    "fields_required": ["email"]
                }),400
        elif choice=="passwd":
            opass=request.json.get("passwd","")
            npass = request.json.get("new_passwd","")
            cpass= request.json.get("confirm_passwd","")
            if not opass or not npass or not cpass:
                return jsonify({
                    "error": "missing fields",
                    "fields_required": ["passwd","new_passwd","confirm_passwd"]
                }),400
            if npass !=cpass:
                return jsonify({"error":"passwords must match"}),400
            if check_password_hash(user.passwd,opass):
                user.passwd = generate_password_hash(npass)
                user.save()
                return jsonify({"message":"password changed"}),200
            else:
                return jsonify({"error":"old password is wrong"}),400
    else:
        return jsonify({"error":"invalid choice"}),400


@user_blueprint.get("/me")
@jwt_required()
def userinfo():
    cur_user = get_jwt_identity()
    user = User.objects(_id=cur_user).first()
    if user:
        return jsonify({
            "email":user.email,
            "username":user.username
        })
    else:
        return jsonify({"error":"uer not found"}),404

@user_blueprint.delete("/delete")
@jwt_required()
def delete_user():
    curr_user = get_jwt_identity()
    user = User.objects.get(_id=curr_user)
    if not user:
        return jsonify({"error":"user not found"}),404
    elif user:
        uid = user._id
        buckets=Bucket.objects(uid=str(uid))
        if buckets:
            for bucket in list(buckets):
                guests = Guest.objects(bid=str(bucket._id))
                guests.delete()
        buckets.delete()
        user.delete()
        try:
            shutil.rmtree(config.UPLOAD_FOLDER + "/" + str(curr_user))
        except Exception as e:
            pass
        return jsonify({"msg":"user was deleted","uid":str(user._id)}),200
    else:
        return jsonify({"error":"user not found"}),400
    # else:









