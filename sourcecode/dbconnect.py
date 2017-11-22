import MySQLdb

def connection():
    conn = MySQLdb.connect(host="localhost",
                            user = "root",
                            passwd = "beatsOne3a",
                            db = "movieusers")
    c = conn.cursor()

    return c, conn
