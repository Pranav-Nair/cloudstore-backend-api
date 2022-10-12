from flask import Flask
from config import *
from mongoengine import connect
from flask_jwt_extended import JWTManager
from users import user_blueprint
from buckets import bucket_blueprint
from guests import guest_blueprint
import os
app = Flask(__name__)
app.config["SECRET_KEY"]=SECRET_KEY
app.config["MOGODB_DB"]=MONGO_DB
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
connect(MONGO_DB,host=HOST+":27017/osmiumdb",port=PORT)
app.register_blueprint(user_blueprint)
app.register_blueprint(bucket_blueprint)
app.register_blueprint(guest_blueprint)
JWTManager(app)
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
if __name__ == "__main__":
    app.run(debug=True)