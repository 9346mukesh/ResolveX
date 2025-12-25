class Config:
    SECRET_KEY = "secret123"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root@localhost/ticket_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False