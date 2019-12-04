import os
import sys
import pymongo
import time, datetime
import gridfs
def aggsum(lis, attri):
    cnt=0
    for ent in lis:
        cnt+=int(ent[attri])
    return cnt

def agglis(lis, attri):
    res_lis=[]
    for ent in lis:
        res_lis.append(ent[attri])
    return res_lis

def retri_lis(lis, attri):
    return [x[attri] for x in lis]


def insert_beread():
    client = pymongo.MongoClient("mongodb://101.6.31.11:27017/")

    mydb=client.topread
    article_cl = mydb.article
    user_cl=mydb.user
    read_cl=mydb.read

    be_read_lis=[]

    for article in article_cl.find():
        entry={}
        entry['id']="br"+article["aid"]
        entry['aid']=article["aid"]
        entry['timestamp']=article["timestamp"]

        read_this_art=read_cl.find({"aid":entry['aid']})

        entry["readNum"]=list(read_cl.aggregate([
            {"$match":{"aid":entry['aid'],"readOrNot":'1'}},
            {"$count":"cnt"}
        ]))[0]["cnt"]

        entry["readUidList"]=retri_lis(read_cl.find({"aid":entry['aid'],"readOrNot":'1'},{"_id":0,"uid":1}),"uid")

        entry["commentNum"]=list(read_cl.aggregate([
            {"$match":{"aid":entry['aid'],"commentOrNot":'1'}},
            {"$count":"cnt"}
        ]))[0]["cnt"]

        entry["commentUidList"]=retri_lis(read_cl.find({"aid":entry['aid'],"commentOrNot":'1'},{"_id":0,"uid":1}),"uid")

        entry["agreeNum"]=list(read_cl.aggregate([
            {"$match":{"aid":entry['aid'],"agreeOrNot":'1'}},
            {"$count":"cnt"}
        ]))[0]["cnt"]

        entry["agreeUidList"]=retri_lis(read_cl.find({"aid":entry['aid'],"agreeOrNot":'1'},{"_id":0,"uid":1}),"uid")

        entry["shareNum"]=list(read_cl.aggregate([
            {"$match":{"aid":entry['aid'],"shareOrNot":'1'}},
            {"$count":"cnt"}
        ]))[0]["cnt"]

        entry["shareUidList"]=retri_lis(read_cl.find({"aid":entry['aid'],"shareOrNot":'1'},{"_id":0,"uid":1}),"uid")    

        be_read_lis.append(entry)

    print("read_to_insert_num",len(be_read_lis))

    mydb.be_read.insert_many(be_read_lis)

def query_popular(mydb, timepoint, lim):
    timestamp=str(int(timepoint.timestamp()*1000))
    beread_cl=mydb.be_read
    pop=beread_cl.find({"timestamp":{"$gt":timestamp}},{"readNum":1,"aid":1}).sort("readNum",-1).limit(lim)
    aids=retri_lis(pop,"aid")
    return aids

def insert_popular(client=None, curr_time=None):
    if not client:
        client = pymongo.MongoClient("mongodb://101.6.31.11:27017/")

    if not curr_time:
        # curr_time=datetime.datetime.now()
        curr_time=datetime.datetime.fromtimestamp(1506000011.000)

    mydb=client.topread
    article_cl = mydb.article
    user_cl=mydb.user
    read_cl=mydb.read
    beread_cl=mydb.be_read

    timestamp=str(int(curr_time.timestamp()*1000))

    dla_time=datetime.timedelta(days=1)
    daily_aids=query_popular(mydb, curr_time-dla_time, 5)
    mydb.popular_rank.insert_one({
        "id":"p"+timestamp,
        "timestamp":timestamp,
        "temporalGranularity":"daily",
        "articleAidList":daily_aids
    })

    dla_time=datetime.timedelta(days=7)
    weekly_aids=query_popular(mydb, curr_time-dla_time, 5)
    mydb.popular_rank.insert_one({
        "id":"p"+timestamp,
        "timestamp":timestamp,
        "temporalGranularity":"weekly",
        "articleAidList":weekly_aids
    })

    dla_time=datetime.timedelta(days=30)
    monthly_aids=query_popular(mydb, curr_time-dla_time, 5)
    mydb.popular_rank.insert_one({
        "id":"p"+timestamp,
        "timestamp":timestamp,
        "temporalGranularity":"monthly",
        "articleAidList":monthly_aids
    })

def insert_a_file(mydb, filepath):
    fs = gridfs.GridFS(mydb)

    filename=os.path.split(filepath)[1]
    with open(filepath, "rb") as f:
        fid=fs.put(f, filename=filename)
    
    return fid

def retrive_a_file(mydb, filename):
    fs = gridfs.GridFS(mydb)
    f = fs.find_one({"filename": filename})
    
    return f

def store_file_article():
    client = pymongo.MongoClient("mongodb://101.6.31.11:27017/")
    mydb=client.topread
    article_cl = mydb.article

    prefix="./3-sized-db-generation/"
    all_art=article_cl.find()
    for art in all_art:
        fn=prefix+"articles/article"+art["aid"]+"/"+art["text"]
        insert_a_file(mydb, fn)

        img_lis=[x for x in art["image"].split(',') if x]
        for img in img_lis:
            fn=prefix+"articles/article"+art["aid"]+"/"+img
            if not os.path.exists(fn):continue
            insert_a_file(mydb, fn)

    fn=prefix+"video/"+"video1.flv"
    insert_a_file(mydb, fn)

    fn=prefix+"video/"+"video2.flv"
    insert_a_file(mydb, fn)


class Mongodbtool(object):
    def __init__(self, host=None):
        if not host:
            host="101.6.31.11"
        self.client = pymongo.MongoClient("mongodb://"+host+":27017/")
        self.mydb=client.topread
        self.article_cl = mydb.article
        self.user_cl=mydb.user
        self.read_cl=mydb.read
        self.beread_cl=mydb.be_read
        self.popularrank_cl=mydb.popular_rank
        self.fs = gridfs.GridFS(self.mydb)

    def insert_a_file(self, filepath):

        filename=os.path.split(filepath)[1]
        with open(filepath, "rb") as f:
            fid=self.fs.put(f, filename=filename)
        
        return fid

    def retrive_a_file(self, filename):
        f = self.fs.find_one({"filename": filename})
        
        return f

    def get_db(self):
        return self.mydb

    def get_secondarys(self):
        db1=pymongo.MongoClient("mongodb://"+"101.6.31.12"+":27017/").topread
        db2=pymongo.MongoClient("mongodb://"+"101.6.31.13"+":27017/").topread

        return [db1,db2]


if __name__=="__main__":
    pass
    # insert_beread()

    # curr_time=datetime.datetime.fromtimestamp(1506000011.000)
    # insert_popular(curr_time=curr_time)

    # store_file_article()

    client = pymongo.MongoClient("mongodb://101.6.31.11:27017/")
    mydb=client.topread
    f=retrive_a_file(mydb,"text_a40.txt")
    txt=f.read()
    print(txt)
