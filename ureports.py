import os
import sqlite3
import datetime
import time
import hmac
import tempfile
import base64

import flask
from PIL import Image as pilImage
import werkzeug

app = flask.Flask("ureports")

IMG_TYPE = "png"
IMG_AGENT_XY = (500, 500)
IMG_REPORT_XY = (2000, 2000)

with app.app_context():
	app.config.update(dict(
		DATA=os.path.join(app.root_path, "data", flask.current_app.name),
		DEBUG=True,
		SECRET=""
	))

	# For convenience:
	app.config["DATABASE"] = os.path.join(app.config["DATA"], flask.current_app.name + ".db")
	app.config["IMG_REPORT"] = os.path.join(app.config["DATA"], "images", "reports/")
	app.config["IMG_AGENT"] = os.path.join(app.config["DATA"], "images", "agent/")

def get_db():
	db = getattr(flask.g, "_database", None)
	if db is None:
		db = flask.g._database = sqlite3.connect(app.config["DATABASE"])
		db.row_factory = sqlite3.Row
	return db

def init_folder() -> bool:
	folder_existed = True

	if not os.path.exists(app.config["DATA"]):
		folder_existed = False
		os.makedirs(app.config["DATA"])
		os.makedirs(app.config["IMG_REPORT"])
		os.makedirs(app.config["IMG_AGENT"])

	return folder_existed

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource("schema.sql", mode="r") as f:
			db.cursor().executescript(f.read())
		db.commit()

def verify_digest(input_data: str, input_hash: str) -> bool:
	key = str.encode(app.config["SECRET"])
	computed_hash = hmac.new(key, msg=input_data, digestmod="sha256")
	return hmac.compare_digest(computed_hash.hexdigest(), input_hash)

def is_dict_empty(keys_to_check: list, dict_to_check: dict) -> bool:
	for key in keys_to_check:
		data = dict_to_check.get(key)

		# Check if attr missing or empty str
		if data is None or not data.strip():
			app.logger.warn("Attribute: %s was not found or was empty", key)
			return True

	return False

def valid_image_type(file_name: str) -> bool:
	secure_file_name = werkzeug.utils.secure_filename(file_name)
	file_extension = secure_file_name.rsplit('.', 1)[1].lower()
	return '.' in secure_file_name and file_extension == IMG_TYPE

def save_agent_image(file_name: str, image: str) -> str:
	image = base64.b64decode(image)
	secure_file_path = os.path.join(app.config["IMG_AGENT"], werkzeug.utils.secure_filename(file_name) + '.' + IMG_TYPE)

	temp_file = tempfile.SpooledTemporaryFile()
	temp_file.write(image)

	try:
		image = pilImage.open(temp_file)
		image.thumbnail(IMG_AGENT_XY)
		image.save(secure_file_path, format=IMG_TYPE)
	except (KeyError, IOError):
		app.logger.warn("Failed save temp image! Broken file / unknown format ")
		raise

	return secure_file_path

@app.teardown_appcontext
def close_connection():
	db = getattr(flask.g, "_database", None)
	if db is not None:
		db.close()

@app.cli.command("init")
def init_command():
	if init_folder():
		print("Folder tree (", app.config["DATA"], ") already exists. Using it as is")
	else:
		print("Created folder tree at", app.config["DATA"])

	init_db()
	print("Initialized the database.")

def add_agent(agent_id: str, name: str, location: str, secret: str, online: int, description: str = None, picture: str = None):
	get_db().execute("INSERT INTO agents (id, name, location, secret, online, description, picture) VALUES (?, ?, ?, ?, ?, ?, ?)", 
					(agent_id, name, location, secret, online, description, picture))
	get_db().commit()

def update_agent(agent_id: str, name: str = None, location: str = None, secret: str = None, online: int = None, description: str = None, picture: str = None):
	db = get_db()

	if name is not None:
		db.execute("UPDATE agents SET name = ? WHERE id = ?", (name, agent_id))
	if location is not None:
		db.execute("UPDATE agents SET location = ? where id = ?", (location, agent_id))
	if secret is not None:
		db.execute("UPDATE agents SET secret = ? where id = ?", (secret, agent_id))
	if online is not None:
		db.execute("UPDATE agents SET online = ? where id = ?", (online, agent_id))
	if description is not None:
		db.execute("UPDATE agents SET description = ? where id = ?", (description, agent_id))
	if picture is not None:
		db.execute("UPDATE agents SET picture = ? where id = ?", (picture, agent_id))

	db.commit()

def get_agents() -> list:
	#TODO: See todo for get_reports
	return get_db().execute("SELECT * FROM agents").fetchall()

def get_agent(agent_id: str) -> sqlite3.Row:
	return get_db().execute("SELECT * FROM agents where id = ?", (agent_id, )).fetchone()

def add_report(report_id: str, report_time: int, location: str, agent_id: str):
	get_db().execute("INSERT INTO reports (id, time, location, agent)", report_id, report_time, location, agent_id)
	raise NotImplementedError

def get_reports(num_reports: int = 20, start_index: int = 0) -> list:
	#TODO: Better to lazily iterate cursor's return obj than to fetchall rows as a list () if data is big (which its not)
	return get_db().execute("SELECT * FROM reports ORDER BY time DESC LIMIT ? OFFSET ?", (num_reports, start_index)).fetchall()

def get_report(report_id: str) -> sqlite3.Row:
	return get_db().execute("SELECT * FROM reports WHERE id = ?", (report_id, )).fetchone()

@app.route("/")
def index():
	return flask.render_template("index.html")

@app.route("/reports/")
def reports():
	return flask.render_template("reports.html", reports=get_reports())

@app.route("/reports/<report_id>")
def report(report_id):
	db_report = get_report(report_id)

	if db_report is None:
		flask.abort(404)

	return flask.render_template("report.html", report=db_report)

@app.route("/agents/", methods=["GET"])
def agents():
	return flask.render_template("agents.html", agents=get_agents())

@app.route("/agents/<agent_id>", methods=["GET"])
def agent(agent_id):
	db_agent = get_agent(agent_id)

	if db_agent is None:
		flask.abort(404)

	return flask.render_template("agent.html", agent=db_agent)

@app.route("/agents/<agent_id>/image", methods=["GET"])
def get_agent_image(agent_id: str):
	db_agent = get_agent(agent_id.strip())

	if db_agent is None:
		flask.abort(404)

	if db_agent["picture"] is None:
		return flask.send_from_directory(app.static_folder, "images/agent-img-404.png")

	return flask.send_from_directory(app.config["DATA"], db_agent["picture"])

@app.route("/manual/")
def manual():
	return flask.render_template("manual.html")

@app.errorhandler(404)
def page_not_found():
	return flask.render_template("404.html"), 404

# API endpoints
@app.route("/api/agents", methods=["POST"])
def api_add_agent():
	if not verify_digest(flask.request.data, flask.request.headers["Authorization"]):
		app.logger.warn("Failed HMAC Auth")
		flask.abort(401)

	payload = flask.request.get_json()

	if is_dict_empty(["id", "name", "location", "secret"], payload):
		app.logger.warn("Mandatory fields empty")
		flask.abort(404)

	if len(payload["id"]) > 50:
		app.logger.warn("ID too long (> 50)")
		flask.abort(404)

	if len(payload["secret"]) > 256:
		app.logger.warn("Secret too long (> 256)")
		flask.abort(404)

	if get_agent(payload["id"].strip()) is not None:
		#TODO: replace with API error instead
		app.logger.warn("Attempted to add agent with existing id")
		flask.abort(404)

	add_agent(payload["id"].strip(), payload["name"], payload["location"], payload["secret"], int(time.time()), 
				payload["description"])

	return "", 200

@app.route("/api/agents/image", methods=["POST"])
def add_agent_image():
	if not verify_digest(flask.request.data, flask.request.headers["Authorization"]):
		app.logger.warn("Failed HMAC Auth")
		flask.abort(401)

	payload = flask.request.get_json()
	agent_id = payload["id"].strip()

	if is_dict_empty(["id", "image"], payload):
		app.logger.warn("Mandatory fields empty")
		flask.abort(404)

	if get_agent(agent_id) is None:
		#TODO: replace with API error instead
		app.logger.warn("Attempted to upload picture for nonexistent agent")
		flask.abort(404)

	try:
		image_path = save_agent_image(agent_id, payload["image"])
		image_rel_path = os.path.relpath(image_path, start=app.config["DATA"])
		update_agent(agent_id, picture=image_rel_path)
	except (KeyError, IOError):
		flask.abort(500)

	return "", 200

#filters for jinga2 (http://flask.pocoo.org/docs/0.12/templating/#registering-filters)
@app.template_filter("datetime")
def filter_datetime(time_stamp: str) -> str:
	return datetime.datetime.fromtimestamp(time_stamp)
