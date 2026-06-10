import bcrypt
from flask_mysqldb import MySQL
import MySQLdb

conn = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="root",
    db="mydb"
)

cursor = conn.cursor()

users = [
    ("admin", "admin123", "admin"),
    ("worker", "worker123", "worker")
]

for login, password, role in users:

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    try:

        cursor.execute(
            """
            INSERT INTO Пользователи
            (логин, пароль_hash, роль)
            VALUES (%s,%s,%s)
            """,
            (
                login,
                password_hash.decode("utf-8"),
                role
            )
        )

        print(f"{login} создан")

    except:
        print(f"{login} уже существует")

conn.commit()

cursor.close()
conn.close()