import pymysql

def get_db_connection():
    connection = pymysql.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="3rDqFvQeWzvQ3TV.root",
        password="0vU9cQIaIL8kezMI",
        database="inventory_management",
        ssl={"ssl": {}},
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection