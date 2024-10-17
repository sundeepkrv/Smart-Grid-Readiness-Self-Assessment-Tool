# ========== LIBRARIES ==========

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
import json
import pandas as pd
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename
import sqlite3 as sql
from hashlib import sha256
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import string
import random
import ast

# ========== APP PARAMETERS ==========

app = Flask(__name__)
app.config["SECRET_KEY"] = "R3adyn3ssS3!fAss3ssm3ntToo!"
app.config["SESSION_TYPE"] = "filesystem"
DATABASE = "sgrsat.sqlite3.db"

with open("static/defdata/defdata.json", encoding="utf-8") as file:
	defdata = json.load(file)
	levels = list(defdata["lscores"].keys())
	subdomains = list(defdata["sdscores"].keys())
	domains = list(defdata["dscores"].keys())

def genCaptcha():
	captchatext = str(uuid4())[:6]
	img = Image.new('RGBA',(130,50),color=(0,0,0,0))
	font = ImageFont.truetype('static/fonts/TimesNewRoman.ttf',40)
	draw = ImageDraw.Draw(img)
	draw.text((5,5),captchatext,(142,68,173),font)
	buffered = BytesIO()
	img.save(buffered, format="PNG")
	return captchatext, base64.b64encode(buffered.getvalue()).decode('utf-8')

Session(app)

# ========== SESSION MANAGEMENT ==========

@app.before_request
def before_request():
	session.permanent = False
	app.permanent_session_lifetime = timedelta(minutes=10)

# ========== UTILITY USER ==========

@app.route("/login")
def login():
	ctext, cimg = genCaptcha()
	cimg = "data:image/png;base64," + cimg
	session["captcha"] = ctext
	return render_template("login.html", cimg = cimg)

@app.route("/logout")
def logout():
	session.clear()
	flash('Logged out successfully.', 'info')
	return redirect(url_for("login"))

@app.route("/login", methods = ["POST"])
def post_login():
	username = request.form.get("username")
	password = str(request.form.get("password"))+app.config['SECRET_KEY']
	password = sha256(password.encode('utf-8')).hexdigest()
	# remember = True if request.form.get("remember") else False
	conn = sql.connect(DATABASE)
	cur = conn.cursor()
	cur.execute("SELECT * FROM users WHERE username = ? AND password = ? AND usertype = ?", (username, password, 'utility'))
	if not cur.fetchall():
		flash('Wrong Username/Password. Try Again !!!', 'danger')
		return redirect(url_for("login"))
	if request.form.get("captcha") == session["captcha"]:
		session['logged_in'] = True
		session['username'] = username
		session['usertype'] = 'utility'
		return redirect(url_for("projects"))
	flash('Captcha did not match. Try Again !!!', 'danger')
	return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def home():
	if ('logged_in' in session) and (session['logged_in'] == True):
		return redirect(url_for("projects"))
	return render_template("index.html")

@app.route("/profile", methods = ["GET", "POST"])
def profile():
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	username = session['username']
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	user = cur.execute("SELECT * FROM users WHERE username = ? AND usertype = ? ", (username,'utility')).fetchone()
	with open("static/defdata/states.json", encoding="utf-8") as file:
		states = json.load(file)
	if request.method == "POST":
		update = request.form.to_dict()
		if update['password']:
			password = str(update['password'])+app.config['SECRET_KEY']
			cur.execute("UPDATE users SET password = ?, utility = ?, state = ?, nodalname = ?, nodaldesig = ?, nodaltel = ?, nodalemail = ? WHERE username = ?", (password, update['utility'], update['state'], update['nodalname'], update['nodaldesig'], update['nodaltel'], update['nodalemail'], update['username']))
		else:
			cur.execute("UPDATE users SET utility = ?, state = ?, nodalname = ?, nodaldesig = ?, nodaltel = ?, nodalemail = ? WHERE username = ?", (update['utility'], update['state'], update['nodalname'], update['nodaldesig'], update['nodaltel'], update['nodalemail'], update['username']))
		conn.commit()
		return redirect("profile")
	return render_template("profile.html", user = user, states = states)

# ========== ADMIN USER ==========

@app.route("/adminlogin")
def adminlogin():
	ctext, cimg = genCaptcha()
	cimg = "data:image/png;base64," + cimg
	session["captcha"] = ctext
	return render_template("adminlogin.html", cimg = cimg)

@app.route("/adminlogout")
def adminlogout():
	session.clear()
	flash('Logged out successfully.', 'info')
	return redirect(url_for("adminlogin"))

@app.route("/adminlogin", methods = ["POST"])
def post_admin_login():
	username = request.form.get("username")
	password = str(request.form.get("password"))+app.config['SECRET_KEY']
	password = sha256(password.encode('utf-8')).hexdigest()
	# remember = True if request.form.get("remember") else False
	conn = sql.connect(DATABASE)
	cur = conn.cursor()
	cur.execute("SELECT * FROM users WHERE username = ? AND password = ? AND usertype = ?", (username, password, 'admin'))
	if not cur.fetchall():
		flash('Wrong Admin Username/Password. Try Again !!!', 'danger')
		return redirect(url_for("adminlogin"))
	if request.form.get("captcha") == session["captcha"]:
		session['logged_in'] = True
		session['username'] = username
		session['usertype'] = 'admin'
		return redirect(url_for("users"))
	flash('Captcha did not match. Try Again !!!', 'danger')
	return redirect(url_for("adminlogin"))

@app.route("/users", methods = ["GET", "POST"])
def users():
	if ('logged_in' not in session) or (session['logged_in'] != True) or ('usertype' not in session) or (session['usertype'] != 'admin'):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("adminlogin"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	users = cur.execute("SELECT * FROM users WHERE usertype = ?", ('utility',)).fetchall()
	return render_template("users.html", users = users)

@app.route("/adduser", methods = ["GET", "POST"])
def adduser():
	if ('logged_in' not in session) or (session['logged_in'] != True) or ('usertype' not in session) or (session['usertype'] != 'admin'):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("adminlogin"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	with open("static/defdata/states.json", encoding="utf-8") as file:
		states = json.load(file)
	if request.method == "POST":
		content = request.form.to_dict()
		content['password'] = sha256(str(content['password']+app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
		content['usertype'] = 'utility'
		cur.execute("INSERT INTO users ({}) VALUES ({})".format(','.join(content.keys()), ', '.join(['?']*len(content))), tuple(content.values()))
		conn.commit()
		return redirect(url_for("users"))
	return render_template("adduser.html", states = states)

@app.route("/user/<string:uid>", methods = ["GET", "POST"])
def user(uid):
	if ('logged_in' not in session) or (session['logged_in'] != True) or ('usertype' not in session) or (session['usertype'] != 'admin'):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("adminlogin"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	userdata = cur.execute("SELECT * FROM users WHERE username = ? AND usertype = ?", (uid,'utility')).fetchone()
	with open("static/defdata/states.json", encoding="utf-8") as file:
		states = json.load(file)
	if request.method == "POST":
		update = request.form.to_dict()
		if update['password']:
			password = str(update['password'])+app.config['SECRET_KEY']
			cur.execute("UPDATE users SET password = ?, utility = ?, state = ?, nodalname = ?, nodaldesig = ?, nodaltel = ?, nodalemail = ? WHERE username = ? AND usertype = ?", (password, update['utility'], update['state'], update['nodalname'], update['nodaldesig'], update['nodaltel'], update['nodalemail'], update['username'], 'utility'))
		else:
			cur.execute("UPDATE users SET utility = ?, state = ?, nodalname = ?, nodaldesig = ?, nodaltel = ?, nodalemail = ? WHERE username = ? AND usertype = ?", (update['utility'], update['state'], update['nodalname'], update['nodaldesig'], update['nodaltel'], update['nodalemail'], update['username'], 'utility'))
		conn.commit()
	return render_template("user.html", states = states, userdata = userdata)

# ========== PROJECTS ==========

@app.route("/projects", methods = ["GET", "POST"])
def projects():
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	projects = cur.execute("SELECT * FROM projects WHERE user = ?", (session['username'],)).fetchall()
	return render_template("projects.html", projects = projects)

@app.route("/addproject", methods = ["GET", "POST"])
def addproject():
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	with open("static/defdata/states.json", encoding="utf-8") as file:
		states = json.load(file)
	with open("static/defdata/defdata.json", encoding="utf-8") as file:
		jdata = json.load(file)
		adata, bdata, tdata = [jdata['data']]*3
		alscores, blscores, tlscores = [jdata['lscores']]*3
		asdscores, bsdscores, tsdscores = [jdata['sdscores']]*3
		adscores, bdscores, tdscores = [jdata['dscores']]*3
	if request.method == "POST":
		content = request.form.to_dict()
		projectcode = ''.join(random.choice(string.ascii_lowercase) for i in range(8))
		content['projectcode'] = projectcode
		content['user'] = session['username']
		cur.execute("INSERT INTO projects ({}) VALUES ({})".format(','.join(content.keys()), ', '.join(['?']*len(content))), tuple(content.values()))
		cur.execute("INSERT INTO assessment (projectcode, adata, alscores, asdscores, adscores, bdata, blscores, bsdscores, bdscores, tdata, tlscores, tsdscores, tdscores) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(projectcode), str(adata), str(alscores), str(asdscores), str(adscores), str(bdata), str(blscores), str(bsdscores), str(bdscores), str(tdata), str(tlscores), str(tsdscores), str(tdscores)))
		conn.commit()
		return redirect(url_for("projects"))
	return render_template("addproject.html", states = states)

@app.route("/editproject/<string:uid>", methods = ["GET", "POST"])
def editproject(uid):
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	pdata = cur.execute("SELECT * FROM projects WHERE projectcode = ?", (uid,)).fetchone()
	with open("static/defdata/states.json", encoding="utf-8") as file:
		states = json.load(file)
	if request.method == "POST":
		content = request.form.to_dict()
		keys = list(content.keys()).copy()
		vals = list(content.values()).copy()
		vals.append(uid)
		cur.execute("UPDATE projects SET {} = ? WHERE projectcode = ?".format(' = ?, '.join(keys)), tuple(vals))
		conn.commit()
		return redirect(url_for("projects"))
	return render_template("editproject.html", states = states, pdata = pdata)

# ========== ASSESSMENT ==========

@app.route("/assessment/<string:uid>", methods = ["GET", "POST"])
def assessment(uid):
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	if request.method == "POST":
		adata = request.form.to_dict()
		alscores, asdscores, adscores = {}, {}, {}
		for i in levels:
			alscores[i] = round(sum([float(adata[key]) for key in adata.keys() if key.startswith(i)]),2)
		for i in subdomains:
			x = [round(alscores[key],2) for key in alscores.keys() if key.startswith(i)]
			asdscores[i] = (4+x[4]) if x[4] else (3+x[3]) if x[3] else (2+x[2]) if x[2] else (1+x[1]) if x[1] else x[0]
		for i in domains:
			adscores[i] = [round(asdscores[key],2) for key in asdscores.keys() if key.startswith(i)]
		cur.execute("UPDATE assessment SET adata = ?, alscores = ?, asdscores = ?, adscores = ?, tdata = ? WHERE projectcode = ?", (str(adata), str(alscores), str(asdscores), str(adscores), str(adata), str(uid)))
		conn.commit()
		return redirect(url_for("projects"))
	return render_template("assessment.html")

# ========== RESULT ==========

@app.route("/result/<string:uid>", methods = ["GET", "POST"])
def result(uid):
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	results = cur.execute("SELECT * FROM assessment WHERE projectcode = ?", (uid,)).fetchone()
	pdata = cur.execute("SELECT * FROM projects WHERE projectcode = ?", (uid,)).fetchone()
	adscores = ast.literal_eval(results['adscores'])
	bdscores = ast.literal_eval(results['bdscores'])
	tdscores = ast.literal_eval(results['tdscores'])
	if request.method == "POST":
		bdscores = adscores
		cur.execute("UPDATE assessment SET bdscores = ? WHERE projectcode = ?", (str(bdscores), str(uid)))
		conn.commit()
	return render_template("result.html", scores = [adscores, bdscores, tdscores], pdata = pdata)

# ========== TARGET ==========

@app.route("/target/<string:uid>", methods = ["GET", "POST"])
def target(uid):
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	results = cur.execute("SELECT * FROM assessment WHERE projectcode = ?", (uid,)).fetchone()
	tdata = ast.literal_eval(results['tdata'])
	if request.method == "POST":
		tdata = request.form.to_dict()
		tlscores, tsdscores, tdscores = {}, {}, {}
		for i in levels:
			tlscores[i] = round(sum([float(tdata[key]) for key in tdata.keys() if key.startswith(i)]),2)
		for i in subdomains:
			x = [round(tlscores[key],2) for key in tlscores.keys() if key.startswith(i)]
			tsdscores[i] = (4+x[4]) if x[4] else (3+x[3]) if x[3] else (2+x[2]) if x[2] else (1+x[1]) if x[1] else x[0]
		for i in domains:
			tdscores[i] = [round(tsdscores[key],2) for key in tsdscores.keys() if key.startswith(i)]
		cur.execute("UPDATE assessment SET tdata = ?, tlscores = ?, tsdscores = ?, tdscores = ? WHERE projectcode = ?", (str(tdata), str(tlscores), str(tsdscores), str(tdscores), str(uid)))
		conn.commit()
		return redirect(url_for('result', uid=uid))
	return render_template("target.html", tdata = tdata)

# ========== PRINT RESULT ==========

@app.route("/printresult/<string:uid>", methods = ["GET", "POST"])
def printresult(uid):
	if ('logged_in' not in session) or (session['logged_in'] != True):
		flash('Session timeout. Please login again', 'info')
		return redirect(url_for("login"))
	conn = sql.connect(DATABASE)
	conn.row_factory = sql.Row
	cur = conn.cursor()
	results = cur.execute("SELECT * FROM assessment WHERE projectcode = ?", (uid,)).fetchone()
	pdata = cur.execute("SELECT * FROM projects WHERE projectcode = ?", (uid,)).fetchone()
	adscores = ast.literal_eval(results['adscores'])
	bdscores = ast.literal_eval(results['bdscores'])
	tdscores = ast.literal_eval(results['tdscores'])
	return render_template("printresult.html", scores = [adscores, bdscores, tdscores], pdata = pdata)

# ========== APP RUN ==========

if __name__ == '__main__':
	app.run(debug = True, host='0.0.0.0')