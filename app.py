import os

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from helpers import login_required, error


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///bookme.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    return render_template('index.html', uid = session['user_id'])

@app.route("/login", methods = ["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return error()

        if not request.form.get("password"):
            return error()

        row = db.execute("SELECT userid FROM user where username = ? and password = ?", request.form.get("username"), request.form.get("password"))

        if len(row) != 1:
            return "Incorrect Username or Password"

        session['user_id'] = row[0]['userid']

        return redirect("/")

    else:
        return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    return redirect("/login")


@app.route('/service')
@login_required
def service():
    row = db.execute("SELECT * FROM service")
    return render_template("service.html", rows = row)

#adding a service
@app.route('/add', methods = ["POST"])
@login_required
def add():
    if request.form.get("name"):
        db.execute("INSERT INTO service (name) VALUES (?)", request.form.get("name"))
        return redirect('/service')

#Deleting a service
@app.route('/del-service', methods = ['POST'])
@login_required
def delete():
    #Continue
    serviceid = request.form.get("id")
    db.execute("DELETE FROM service WHERE serviceid = ?", serviceid)
    return redirect('/service')


#User booking an appointment
@app.route('/book', methods = ["GET", "POST"])
def book():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        number = request.form.get("phone")
        date = request.form.get("date")
        serviceid = request.form.get("service")

        if not name or not email or not number or not date or not serviceid:
            return error()

        db.execute("INSERT INTO appointment (serviceid, name, email, phone, timedate) VALUES (?, ?, ?, ?, ?)", serviceid, name, email, number, date)

        return "Success! You will be contacted once your appointment approves"

    else:
        row = db.execute("SELECT * FROM service")
        return render_template("bookme.html", services = row)

#Admin view appointments
@app.route("/appoint", methods = ["GET", "POST"])
@login_required
def appoint():
    if request.method == "POST":
        if request.form.get("accept"):
            appid = request.form.get("accept")
            db.execute("UPDATE appointment SET status = 1 WHERE appid = ?", appid)
            return redirect("/appoint")

        #appointment rejected
        appid = request.form.get("reject")
        db.execute("UPDATE appointment SET status = 2 WHERE appid = ?", appid)
        return redirect("/appoint")

    row = db.execute("SELECT appid, service.name as service, appointment.name as name, email, phone, timedate FROM appointment JOIN service ON appointment.serviceid = service.serviceid  WHERE status = 0;")
    row2 = db.execute("SELECT appid, service.name as service, appointment.name as name, email, phone, timedate, status FROM appointment JOIN service ON appointment.serviceid = service.serviceid;")

    return render_template("/appointment.html", appointments = row, app2 = row2)


@app.route("/view", methods = ["POST"])
@login_required
def view():
    status = request.form.get("select")

    if status == "*":
        row = db.execute("SELECT appid, service.name as service, appointment.name as name, email, phone, timedate, status FROM appointment JOIN service ON appointment.serviceid = service.serviceid;")
    else:
        row = db.execute("SELECT appid, service.name as service, appointment.name as name, email, phone, timedate, status FROM appointment JOIN service ON appointment.serviceid = service.serviceid WHERE status = ?;", status)

    return jsonify(row)