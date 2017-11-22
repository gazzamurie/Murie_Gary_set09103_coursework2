from flask import Flask, render_template, flash, request, url_for, redirect, session, json, jsonify
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from MySQLdb import escape_string as thwart
from dbconnect import connection
import gc
import os
import json

app = Flask(__name__)

@app.route('/')
def homepage():
    PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(PROJECT_ROOT, 'static/movies.json')
    data = json.load(open(json_url))
    return render_template("main.html", data=data)

@app.route('/tv/')
def tvpage():
    return render_template("tv.html")

@app.route('/about/')
def aboutpage():
    return render_template("about.html")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
    return wrap

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('homepage'))


@app.route("/display/", methods=["GET","POST"])
@login_required
def display():
    with open('static/movies.json', 'w') as f:
        json.dump(request.form, f)
        return json.dump(request.form, f)
    # flash("Thanks For Your Submisson")
    # return render_template("main.html")

@app.route("/upload/", methods=["GET","POST"])
@login_required
def upload():
    return render_template("upload.html")

@app.route('/login/', methods=["GET","POST"])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":
            data = c.execute("SELECT * FROM users WHERE username = (%s)",
                             [thwart(request.form['username'])])
            data = c.fetchone()[2]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash("You are now logged in")
                return redirect(url_for("homepage"))
            else:
                error = "Invalid Username or Password, try again."

        gc.collect()
        return render_template("login.html", error=error)
    except Exception as e:
        error = "Invalid credentials, try again."
        return render_template("login.html", error = error)

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.Required()])

@app.route('/signup/', methods=["GET","POST"])
def signup_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username  = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            x = c.execute("SELECT * FROM users WHERE username = (%s)", (username,))

            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template('signup.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                          (thwart(username), thwart(password), thwart(email)))

                conn.commit()
                flash("Thanks for registering!")
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('homepage'))

        return render_template("signup.html", form=form)

    except Exception as e:
        return(str(e))

# @app.route('/<d>/')
# def film(d=None):
#     PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
#     json_url = os.path.join(PROJECT_ROOT, 'static/movies.json')
#     data = json.load(open(json_url))
#     {% for d in data %}
# 	data = db.getRecord(d)
# 	data(d) = d
#     {% endfor &}
# 	return render_template("filmtemp.html", d=d)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

if __name__ == "__main__":
    app.run()
