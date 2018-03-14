import os
import datetime
import time

import flask

import utils
import db
import images

app = flask.Flask("ureports")

utils.init_app(app)
db.init_app(app)
images.init_app(app)

with app.app_context():
	app.config.update(dict(
		DATA=os.path.join(app.root_path, "data", flask.current_app.name),
		DEBUG=True,
		SECRET="password",
		IMG_TYPE="png",
		IMG_AGENT_XY=(500, 500),
		IMG_REPORT_XY=(2000, 2000)
	))

	# For convenience:
	app.config["DATABASE"] = os.path.join(app.config["DATA"], flask.current_app.name + ".db")
	app.config["IMG_REPORT"] = os.path.join(app.config["DATA"], "images", "reports/")
	app.config["IMG_AGENT"] = os.path.join(app.config["DATA"], "images", "agent/")

@app.cli.command("init")
def init_command():
	db.init()

@app.teardown_appcontext
def close_app(e):
	db.close_connection()

@app.route("/")
def index():
	return flask.render_template("index.html")

@app.route("/reports/")
def reports():
	return flask.render_template("reports.html", reports=db.get_reports())

@app.route("/reports/<report_id>")
def report(report_id):
	db_report = db.get_report(report_id)

	if db_report is None:
		flask.abort(404)

	return flask.render_template("report.html", report=db_report)

@app.route("/agents/", methods=["GET"])
def agents():
	return flask.render_template("agents.html", agents=db.get_agents())

@app.route("/agents/<agent_id>", methods=["GET"])
def agent(agent_id):
	db_agent = db.get_agent(agent_id)

	if db_agent is None:
		flask.abort(404)

	return flask.render_template("agent.html", agent=db_agent)

@app.route("/agents/<agent_id>/image", methods=["GET"])
def get_agent_image(agent_id: str):
	db_agent = db.get_agent(agent_id.strip())

	if db_agent is None:
		flask.abort(404)

	if db_agent["picture"] is None:
		return flask.send_from_directory(app.static_folder, "images/agent-img-404.png")

	return flask.send_from_directory(app.config["DATA"], db_agent["picture"])

@app.route("/manual/")
def manual():
	return flask.render_template("manual.html")

@app.errorhandler(404)
def page_not_found(e):
	return flask.render_template("404.html"), 404

# API endpoints
@app.route("/api/agents", methods=["POST"])
def api_add_agent():
	if not utils.verify_digest(flask.request.data, flask.request.headers["Authorization"]):
		app.logger.warning("Failed HMAC Auth")
		flask.abort(401)

	payload = flask.request.get_json()

	if utils.is_dict_empty(["id", "name", "location", "secret"], payload):
		app.logger.warning("Mandatory fields empty")
		flask.abort(404)

	if len(payload["id"]) > 50:
		app.logger.warning("ID too long (> 50)")
		flask.abort(404)

	if len(payload["secret"]) > 256:
		app.logger.warning("Secret too long (> 256)")
		flask.abort(404)

	if db.get_agent(payload["id"].strip()) is not None:
		#TODO: replace with API error instead
		app.logger.warning("Attempted to add agent with existing id")
		flask.abort(404)

	db.add_agent(payload["id"].strip(), payload["name"], payload["location"], payload["secret"], int(time.time()), 
				payload["description"])

	return "", 200

@app.route("/api/agents/image", methods=["POST"])
def add_agent_image():
	if not utils.verify_digest(flask.request.data, flask.request.headers["Authorization"]):
		app.logger.warning("Failed HMAC Auth")
		flask.abort(401)

	payload = flask.request.get_json()
	agent_id = payload["id"].strip()

	if utils.is_dict_empty(["id", "image"], payload):
		app.logger.warning("Mandatory fields empty")
		flask.abort(404)

	if db.get_agent(agent_id) is None:
		#TODO: replace with API error instead
		app.logger.warning("Attempted to upload picture for nonexistent agent")
		flask.abort(404)

	try:
		image_path = images.save_agent_image(agent_id, payload["image"])
		image_rel_path = os.path.relpath(image_path, start=app.config["DATA"])
		db.update_agent(agent_id, picture=image_rel_path)
	except (KeyError, IOError):
		flask.abort(500)

	return "", 200

#filters for jinga2 (http://flask.pocoo.org/docs/0.12/templating/#registering-filters)
@app.template_filter("datetime")
def filter_datetime(time_stamp: str) -> str:
	return datetime.datetime.fromtimestamp(time_stamp)
