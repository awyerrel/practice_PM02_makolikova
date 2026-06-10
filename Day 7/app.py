from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
from functools import wraps
import random

app = Flask(__name__)
app.secret_key = "fitness_secret_key_2026"

# НАСТРОЙКИ MYSQL


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'mydb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# ДЕКОРАТОРЫ


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Сначала войдите в систему")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if session.get('role') != 'admin':
            flash("Доступ запрещен")
            return redirect(url_for('worker_dashboard'))

        return f(*args, **kwargs)
    return decorated_function



# ГЛАВНАЯ

@app.route('/')
def index():

    if 'user_id' in session:

        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))

        return redirect(url_for('worker_dashboard'))

    return redirect(url_for('login'))



# ВХОД


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        login_user = request.form['login']
        password = request.form['password']
        captcha = request.form['captcha']

        try:
            if int(captcha) != session.get('captcha_result'):
                flash("Неверная капча")
                return redirect(url_for('login'))
        except:
            flash("Неверная капча")
            return redirect(url_for('login'))

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM Пользователи WHERE логин=%s",
            (login_user,)
        )

        user = cur.fetchone()

        cur.close()

        if user:

            if bcrypt.checkpw(
                password.encode('utf-8'),
                user['пароль_hash'].encode('utf-8')
            ):

                session['user_id'] = user['id_пользователя']
                session['login'] = user['логин']
                session['role'] = user['роль']

                flash("Успешный вход")

                if user['роль'] == 'admin':
                    return redirect(url_for('admin_dashboard'))

                return redirect(url_for('worker_dashboard'))

        flash("Неверный логин или пароль")

    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)

    session['captcha_result'] = num1 + num2

    return render_template(
        'login.html',
        num1=num1,
        num2=num2
    )



# ВЫХОД


@app.route('/logout')
def logout():

    session.clear()

    flash("Вы вышли из системы")

    return redirect(url_for('login'))


# АДМИН

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')


@app.route('/admin/users')
@admin_required
def admin_users():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
        id_пользователя,
        логин,
        роль,
        created_at
        FROM Пользователи
    """)

    users = cur.fetchall()

    cur.close()

    return render_template(
        'admin/users.html',
        users=users
    )


@app.route('/admin/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():

    if request.method == 'POST':

        login = request.form['login']
        password = request.form['password']
        role = request.form['role']

        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        )

        cur = mysql.connection.cursor()

        try:

            cur.execute(
                """
                INSERT INTO Пользователи
                (логин, пароль_hash, роль)
                VALUES (%s,%s,%s)
                """,
                (
                    login,
                    password_hash.decode('utf-8'),
                    role
                )
            )

            mysql.connection.commit()

            flash("Пользователь добавлен")

        except Exception as e:
            flash(f"Ошибка: {e}")

        finally:
            cur.close()

        return redirect(url_for('admin_users'))

    return render_template('admin/add_user.html')


@app.route('/admin/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):

    if user_id == session['user_id']:
        flash("Нельзя удалить самого себя")
        return redirect(url_for('admin_users'))

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM Пользователи WHERE id_пользователя=%s",
        (user_id,)
    )

    mysql.connection.commit()

    cur.close()

    flash("Пользователь удален")

    return redirect(url_for('admin_users'))



# РАБОТНИК

@app.route('/worker/dashboard')
@login_required
def worker_dashboard():
    return render_template('worker/dashboard.html')



# СПИСОК КЛИЕНТОВ


@app.route('/clients')
@login_required
def clients():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM Клиенты
    """)

    clients = cur.fetchall()

    cur.close()

    return render_template(
        'clients.html',
        clients=clients
    )


# ЗАПУСК


if __name__ == '__main__':
    app.run(debug=True)