import pymongo

myclient = pymongo.MongoClient("mongodb://root:root_password@localhost:27017/")

mydb = myclient["books"]


def insert_one(doc, collection):
    ret = collection.insert_one(doc)
    return ret.inserted_id


def insert_many(docs, collection):
    collection.insert_many(docs)
    return x.inserted_ids

def find_one(id = None, fields = None):
    


if __name__ == "__main__":
    print(myclient.list_database_names())
    mycol = mydb["test"]
    print(mydb.list_collection_names())
    mydict = {"name": "Peter", "address": "Lowstreet 27"}

    x = mycol.insert_one(mydict)

    print(x.inserted_id)
