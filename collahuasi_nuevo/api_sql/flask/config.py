DB_USERNAME     = 'admin'
DB_PASSWORD     = 'audio2023'
DB_HOST         = 'localhost'
DB_PORT         = 3306
DB_NAME         = 'smartlinkDB'

SQLALCHEMY_DATABASE_URI         = f'mariadb+mariadbconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
SQLALCHEMY_TRACK_MODIFICATIONS  = False
