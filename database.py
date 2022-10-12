import mongoengine as db
from mongoengine import CASCADE
from bson.objectid import ObjectId
import config,os


class User(db.Document):
    _id = db.ObjectIdField(primary_key=True,default=ObjectId)
    email = db.StringField(null=False,unique=True)
    passwd = db.StringField(null=False)
    username = db.StringField(null=False)
    meta = {"allow_inheritance":True,"strict":False}


class Bucket(db.Document):
    _id = db.ObjectIdField(primary_key=True,default=ObjectId)
    uid = db.StringField(null=False)
    name = db.StringField(null=False)
    # meta = {"allow_inheritance":True,"strict":False}



class Guest(db.Document):
    _id = db.ObjectIdField(primary_key=True,default=ObjectId)
    name = db.StringField(null=False)
    folder = db.StringField(null=False)
    bid = db.StringField(null=False)




