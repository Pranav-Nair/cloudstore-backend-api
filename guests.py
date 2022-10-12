from flask import Blueprint,request,jsonify,send_file
from flask_jwt_extended import jwt_required,get_jwt_identity,create_access_token,create_refresh_token
from database import User,Bucket,Guest
import os,config

guest_blueprint = Blueprint("guest",__name__,url_prefix="/guest")

@guest_blueprint.get("/")
@jwt_required()
def list_guests():
    bucketname = request.json.get("bucket","")
    curr_user = get_jwt_identity()
    if not bucketname:
        return jsonify({
            "error":"missing fields",
            "fields_required":["bucket"]
        })
    user = User.objects(_id=curr_user).first()
    if not user:
        return jsonify({"error":"user does not exist"}),404
    bucket = Bucket.objects(uid=curr_user,name=bucketname).first()
    if not bucket:
        return jsonify({"error":"bucket not found"}),404
    guest = Guest.objects(bid=bucket._id)
    guests = []
    if guest:
        for g in guest:
            guests.append({
                "guestname":g.name,
                "guest_folder":g.folder
            })
    return jsonify({"guests":guests}),200

@guest_blueprint.post("/")
@jwt_required()
def make_guest():
    curr_user = get_jwt_identity()
    bucketame = request.json.get("bucket","")
    guestname = request.json.get("name","")
    folder = request.json.get("folder","")

    if not guestname or not folder or not bucketame:
        return jsonify({"error":"mising fileds","fields_required":["name","folder","bucket"]}),400
    user = User.objects(_id=curr_user).first()
    if not user:
        return jsonify({"error":"user not found"}),404
    bucket = Bucket.objects(uid=curr_user,name=bucketame).first()
    if not bucket:
        return jsonify({"error":"bucket not found"}),404
    bucket_root = config.UPLOAD_FOLDER + "/" + str(curr_user) + "/" + bucket.name
    folder_path = bucket_root + folder
    if os.path.dirname(bucket_root) == os.path.dirname(folder_path):
        return jsonify({"error":"cannot create folder outside buckket"}),400
    if not os.path.exists(folder_path):
        return jsonify({"error":"folder does not exist","path":folder_path}),400
    if Guest.objects(name=guestname,bid=bucket._id):
        return jsonify({"error":"guest with same name exists"}),400
    guest = Guest(name=guestname,bid=str(bucket._id),folder=folder)
    guest.save()
    return jsonify({"msg":"guest was created"}),200

@guest_blueprint.delete("/")
@jwt_required()
def delete_guest():
    curr_user = get_jwt_identity()
    bucketname = request.json.get('bucket',"")
    guestname = request.json.get("guest","")
    if not bucketname or not guestname:
        return jsonify({"error":"missing fields","fields_required":["bucket","guest"]}),400
    bucket = Bucket.objects(uid=curr_user,name=bucketname).first()
    if not bucket:
        return jsonify({"error":"bucket not dound"}),404
    guest = Guest.objects(bid=bucket._id).first()
    if not guest:
        return jsonify({"error":"guest not found"}),404
    guest.delete()
    return jsonify({"msg":"guest was deleted"}),200

@guest_blueprint.get("/access")
@jwt_required()
def get_guest_access():
    curr_user = get_jwt_identity()
    guestname = request.json.get("guest","")
    bucketname = request.json.get("bucket","")
    if not guestname or not bucketname:
        return jsonify({"error":"missing fields","fields_required":["guest","bucket"]}),400
    bucket = Bucket.objects(uid=curr_user,name=bucketname).first()
    if not bucket:
        return jsonify({"error":"bucket not found","bucket":bucketname,"uid":curr_user}),404
    guest = Guest.objects(bid=str(bucket._id),name=guestname).first()
    if not guest:
        return jsonify({"error":"guest not found"}),404
    access = create_access_token(identity=str(guest._id))
    refresh = create_refresh_token(identity=str(guest._id))
    return jsonify({"guest":guest.name,"access":access,"refresh":refresh}),200

@guest_blueprint.get("/refresh/access")
@jwt_required(refresh=True)
def refresh_access():
    curr_guest = get_jwt_identity()
    access = create_access_token(identity=curr_guest)
    return jsonify({"access":access}),200


@guest_blueprint.patch("/<string:choice>")
@jwt_required()
def mod_guest(choice):
    curr_user= get_jwt_identity()
    bucketname = request.json.get("bucket","")
    guestname = request.json.get('guest',"")
    if choice not in ["name","folder"]:
        return jsonify({"error":"not valid operation"}),400
    if not bucketname or not guestname:
        return jsonify({
            "error":"missing fields",
            "fields_required":["guest","bucket"]
        })
    bucket = Bucket.objects(name=bucketname,uid=curr_user).first()
    if not bucket:
        return jsonify({"error":"bucket not found"}),404
    guest = Guest.objects(bid=bucket._id,name=guestname).first()
    if not guest:
        return jsonify({"error":"guest not found"}),404
    if choice == "name":
        newname = request.json.get("newname","")
        if not newname:
            return jsonify({
                "error":"missing fields",
                "fields_required":["guest","bucket","newname"]
            }),400
        if Guest.objects(bid=bucket._id,name=newname):
            return jsonify({"error":"guest with name exists"}),400
        guest.name=newname
        guest.save()
        return jsonify({"msg":"guest name changed"}),200
    elif choice == "folder":
        newfoldr = request.json.get("folder","")
        if not newfoldr:
            return jsonify({
                "error":"missing fields",
                "fields_required":["guest","bucket","folder"]
            }),400
        bucket_root = config.UPLOAD_FOLDER + "/" + str(curr_user) + "/" + bucket.name
        folder_path = bucket_root+newfoldr
        if os.path.dirname(bucket_root) == os.path.dirname(folder_path):
            return jsonify({"error":"cannot access folder outside bucket"}),400
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return jsonify({"error":"folder is not a valid folder","path":folder_path}),400
        guest.folder = newfoldr
        guest.save()
        return jsonify({"msg":"guest folder changed"}),200


@guest_blueprint.get("/list")
@jwt_required()
def list_folder():
    curr_guest = get_jwt_identity()
    fpath = request.json.get("loc", "")
    guest = Guest.objects(_id=curr_guest).first()
    if not guest:
        return jsonify({"error": "guest does not exist","id":curr_guest}), 404
    if not fpath:
        return jsonify({"error": "missing fields", "fields_required": ["loc"]}), 400
    bucket = Bucket.objects(_id=guest.bid).first()
    uid = bucket.uid
    guest_root = config.UPLOAD_FOLDER + "/" + str(uid) + "/" + bucket.name + "/" + guest.folder
    abs_path = guest_root + fpath
    if not os.path.exists(abs_path):
        return jsonify({"error":"path does not exist"})
    if os.path.dirname(abs_path) == os.path.dirname(guest_root):
        return jsonify({"error": "guest does not have permission to access the folder"}), 400
    if os.path.isfile(abs_path):
        return jsonify({"error": "path is not a valid folder"}), 400
    folders = []
    dirs = os.listdir(abs_path)
    for file in dirs:
        if os.path.isdir(file):
            folders.append({"name":file,"type":"folder"})
        else:
            folders.append({"name":file,"type":"file"})
    return jsonify({"dirs":folders}),200


@guest_blueprint.get("/download")
@jwt_required()
def download_file():
    curr_guest = get_jwt_identity()
    fpath = request.json.get("loc","")
    guest = Guest.objects(_id=curr_guest).first()
    if not guest:
        return jsonify({"error":"guest does not exist"}),404
    if not fpath:
        return jsonify({"error":"missing fields","fields_required":["loc"]}),400
    # bid = guest.bid
    bucket = Bucket.objects(_id=guest.bid).first()
    if not bucket:
        return jsonify({"error":"bucket not valid","bucket":str(guest.bid)})
    uid = bucket.uid
    guest_root = config.UPLOAD_FOLDER + "/" + str(uid) + "/" + bucket.name + guest.folder
    abs_path = guest_root + fpath
    if os.path.dirname(abs_path) == os.path.dirname(guest_root):
        return jsonify({"error":"guest does not have permission to access the folder"}),400
    if not os.path.isfile(abs_path):
        return jsonify({"error":"path is not a valid file"}),400
    return send_file(abs_path),200

