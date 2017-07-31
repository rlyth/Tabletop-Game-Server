# Tabletop Game Server

Include the following config.py in the project's root folder:


SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(

    username="YOUR_DB_USERNAME",
    
    password="YOUR_DB_PASSWORD",
    
    hostname="YOUR_DB_HOSTNAME",
    
    databasename="YOUR_DB_NAME",
    
)

SQLALCHEMY_POOL_RECYCLE = 299

SQLALCHEMY_TRACK_MODIFICATIONS = False


SECRET_KEY = 'YOUR_SECRET_KEY'
