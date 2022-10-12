from flask import Blueprint,request,jsonify,send_file,send_from_directory
import os
import config
from flask_jwt_extended import jwt_required,get_jwt_identity
from database import Bucket,Guest
import shutil

bucket_blueprint = Blueprint("bucket",__name__,url_prefix="/bucket")

@bucket_blueprint.post("/")
@jwt_required()
def mk_bucket():
    name = request.json.get("name","")
    if not name:
        return jsonify({
            "error": "missing fields",
            "fields_required": ["name"]
        }),400
    cur_uer = get_jwt_identity()
    if Bucket.objects(name=name,uid=cur_uer):
        return jsonify({"error":"duplicate bucket name"}),400
    bucket = Bucket(uid=cur_uer,name=name)
    bucket.save()
    os.mkdir(config.UPLOAD_FOLDER + "/" + str(cur_uer) + "/" + name)
    return jsonify({"message":"bucket created"}),200

@bucket_blueprint.delete("/")
@jwt_required()
def rm_bucket():
    name = request.json.get("name","")
    if not name:
        return jsonify({
            "error": "missing fields",
            "fields_required": ["name"]
        }),400
    cur_user = get_jwt_identity()
    bucket = Bucket.objects(uid=cur_user,name=name)
    if bucket:
        guests = Guest.objects(bid=str(bucket._id))
        shutil.rmtree(config.UPLOAD_FOLDER + "/" + str(cur_user) + "/" + name)
        if guests:
            guests.delete()
        bucket.delete()
        return jsonify({"message":"bucket deleted"})
    else:
        return jsonify({"error":"bucket not found"}),404

@bucket_blueprint.get("/")
@jwt_required()
def list_buckets():
    curr_user = get_jwt_identity()
    buckets =[]
    bucks = Bucket.objects(uid=curr_user)
    if bucks:
        for buck in bucks:
            buckets.append(buck.name)
    else:
        return jsonify({"error":"no buckets"}),404
    return jsonify({"buckets":buckets}),200

@bucket_blueprint.patch("/")
@jwt_required()
def rename_bucket():
    curr_user = get_jwt_identity()
    name = request.json.get("name","")
    newname = request.json.get("newname","")
    if not name or not newname:
        return jsonify({
            "error": "missing fields",
            "fields_required": ["name","newname"]
        }),400
    if Bucket.objects(name=newname,uid=curr_user).first():
        return jsonify({"error":"bucket name taken"}),400
    bucket = Bucket.objects(uid=curr_user,name=name).first()
    if bucket:
        bucket.name=newname
        bucket.save()
        os.rename(config.UPLOAD_FOLDER + "/" + str(curr_user) + "/" + name,
                  config.UPLOAD_FOLDER + "/" + str(curr_user) + "/" + newname)
        return jsonify({"message":"bucket name changed"}),200
    else:
        return jsonify({"error":"bucket not found"}),404


@bucket_blueprint.route("/dir",methods=["GET","POST","PATCH","PUT","DELETE"])
@jwt_required()
def manage_folders():
    cur_user = get_jwt_identity()
    cur_bucket = request.json.get("bucket","")
    bucket_root = config.UPLOAD_FOLDER + "/" + str(cur_user) + "/" + cur_bucket
    # os.chdir(bucket_root)
    if not cur_bucket:
        return jsonify({"error":"mssing field bucket"}),400
    if request.method == "GET":
        loc = request.json.get("loc","")
        if not loc:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["loc","bucket"]
            }),400
        pth = bucket_root+loc
        if os.path.isdir(pth):
            files = os.listdir(pth)
            if not files:
                return jsonify({"path":pth,"dirs":[],"msg":"no files"}),200
            dirs =[]
            for file in files:
                if not os.path.isfile(file):
                    dirs.append(file)
            return jsonify({"path":pth,"dirs":dirs}),200
        else:
            return jsonify({"error":"path is not folder"}),400
    elif request.method == "POST":
        loc = request.json.get("loc", "")
        if not loc:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["loc","bucket"]
            }),400
        pth = bucket_root + loc
        if os.path.dirname(bucket_root) == os.path.dirname(pth):
            return jsonify({"error":"cannot create folder outside bucket"}),400
        if not os.path.exists(os.path.dirname(pth)):
            return jsonify({"error":"parent folder does not exist"}),404
        if os.path.isdir(pth):
            return jsonify({"mesg":"path already exists"}),400
        else:
            os.mkdir(pth)
            return jsonify({"msg":"path created","path":pth}),200
    elif request.method == "PATCH":
        loc = request.json.get("loc", "")
        newname = request.json.get("newname","")
        if not loc or not newname:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["newname","loc"]
            }), 400
        pth = bucket_root+loc
        newpath = bucket_root+newname
        if os.path.dirname(pth) == os.path.dirname(bucket_root) or os.path.dirname(newpath) == os.path.dirname(bucket_root):
            return jsonify({"error":"cannot perform operation outside bucket"}),400
        if os.path.exists(newpath):
            return jsonify({"error":"path already exists"}),400
        if os.path.isdir(pth):
            try:
                os.rename(pth,newpath)
            except Exception as e:
                return jsonify({"error":str(e)}),400
            return jsonify({
                "old_ath":pth,
                "new_path":newpath
            }),200
        else:
            return jsonify({"error":"path not valid directory","path":pth}),400
    elif request.method == "DELETE":
        loc = request.json.get("loc", "")
        newname = request.json.get("newname","")
        if not loc or not newname:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["loc"]
            }), 400
        pth = bucket_root+loc
        if os.path.dirname(bucket_root) == os.path.dirname(pth):
            return jsonify({"error":"cannot create folder outside bucket"}),400
        if os.path.isdir(pth):
            shutil.rmtree(pth)
            return jsonify({"msg":"directory removed"})
        else:
            return jsonify({"error":"path is not a valid directory"}),400
    else:
        return jsonify({"error":"invalid requet"}),400


@bucket_blueprint.route("/file/<string:bucket>/<path:loc>",methods=["GET","POST","DELETE","PATCH"])
@jwt_required()
def manage_files(bucket,loc):
    loc = loc.replace("home","/",1)
    cur_user = get_jwt_identity()
    bucket = bucket
    if not bucket:
        return jsonify({"error":"bucket field required"})
    if not Bucket.objects(uid=cur_user,name=bucket):
        return jsonify({"error":"bucket not found"}),404
    bucket_root = config.UPLOAD_FOLDER + "/" + str(cur_user) + "/" + bucket
    if request.method == "GET":
        if not loc:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["loc","bucket"]
            }),400
        path = bucket_root+loc
        if os.path.dirname(path) == os.path.dirname(bucket_root):
            return jsonify({"error":"cannot perform operation outside bucket start path with /"})
        if not os.path.isdir(path):
            return jsonify({"error":"path does not exist"}),404
        data =[]
        files = os.listdir(path)
        for file in files:
            if not os.path.isdir(file):
                data.append(file)
        return jsonify({"files":data,"path":path}),200
    elif request.method=="POST":
        file = request.files.get("file","")
        if not loc or not file:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["loc", "bucket","file"]
            }),400
        fname = file.filename
        fname = fname.replace(" ","-")
        path = bucket_root+loc
        if os.path.dirname(path) == os.path.dirname(bucket_root):
            return jsonify({"error":"cannot perform operation outside bucket"}),400
        if not os.path.isdir(path):
            return jsonify({"error":"loc is not valid directory"}),400
        fpath = path+"/"+fname
        if os.path.isfile(fpath):
            return jsonify({"error":"file with same name exists in path"}),400
        try:
            file.save(fpath)
            return jsonify({"msg":"file uploaded","path":fpath})
        except Exception as e:
            return jsonify({"error":str(e),"path":fpath}),400
    elif request.method == "DELETE":
        filename = request.json.get("filename","")
        if not loc or not filename:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["loc", "bucket","filename"]
            }),400
        path = bucket_root+loc+"/"+filename
        if os.path.dirname(path) == os.path.dirname(bucket_root):
            return jsonify({"error":"cannot perform operation outside bucket"}),400
        if os.path.isdir(path):
            return jsonify({"error":"loc is not valid file"}),400
        if not os.path.exists(path):
            return jsonify({"error":"file does not exist"}),404
        os.remove(path)
        return jsonify({"msg":"file deleted"}),200
    elif request.method == "PATCH":
        filename = request.json.get("filename","")
        rename = request.json.get("newname","")
        if not filename or not rename:
            return jsonify({
                "error": "missing fields",
                "fields_required": ["newname", "bucket", "filename"]
            }),400
        path = bucket_root + loc + "/" + filename
        newpath = bucket_root+ loc + "/"+rename
        if os.path.dirname(path) == os.path.dirname(bucket_root) or os.path.dirname(newpath) == os.path.dirname(bucket_root):
            return jsonify({"error": "cannot perform operation outside bucket"}), 400
        if os.path.isdir(path):
            return jsonify({"error": "path is directory"}), 400
        if not os.path.exists(path):
            return jsonify({"error": "file does not exist"}), 404
        if os.path.exists(newpath):
            return jsonify({"error":"file with new name already exists"}),400
        try:
            os.rename(path,newpath)
            return jsonify({"msg":"file renamed","old_name":path,"newname":newpath}),200
        except Exception as e:
            return jsonify({"error":str(e)}),400


@bucket_blueprint.get("/download")
@jwt_required()
def download_file():
    curr_user = get_jwt_identity()
    bucket = request.json.get("bucket","")
    loc = request.json.get("loc","")
    if not bucket or not loc:
        return jsonify({
            "error": "missing fields",
            "fields_required": ["loc","bucket"]
        }),400
    if not Bucket.objects(uid=curr_user,name=bucket).first():
        return jsonify({"error":"bucket not found"}),404
    buckt_root = config.UPLOAD_FOLDER + "/" + str(curr_user) + "/" + bucket
    fpath = buckt_root+loc
    if os.path.dirname(buckt_root) == os.path.dirname(fpath):
        return jsonify({"error":"cannot perform operation outside bucket"}),400
    if not os.path.exists(fpath) or os.path.isdir(fpath):
        return jsonify({"error":"path is not valid file ot may not exist","path":fpath}),404
    return send_file(fpath)







