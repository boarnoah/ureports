import os
import datetime
import time
import random

import flask
import werkzeug

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
		DEBUG=False,
		SECRET="",
		IMG_TYPE="png",
		IMG_AGENT_XY=(500, 500),
		IMG_REPORT_XY=(2000, 2000),
		IMG_REPORT_THUMB_XY=(500, 500)
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
	#TODO: Change this to only get first 10 reports/agents etc... if necessary
	return flask.render_template("index.html", agents=db.get_agents(), reports=db.get_reports())

@app.route("/reports/")
def reports():
	return flask.render_template("reports.html", reports=db.get_reports())

@app.route("/reports/<report_id>")
def report(report_id):
	db_report = db.get_report(report_id)
	db_report_images = db.get_report_images(report_id)

	if db_report is None:
		flask.abort(404)

	return flask.render_template("report.html", report=db_report, report_images=db_report_images)

@app.route("/agents/", methods=["GET"])
def agents():
	return flask.render_template("agents.html", agents=db.get_agents())

@app.route("/agents/<agent_id>", methods=["GET"])
def agent(agent_id):
	db_agent = db.get_agent(agent_id)
	db_agent_reports = db.get_reports_by_agent(agent_id)

	if db_agent is None:
		flask.abort(404)

	return flask.render_template("agent.html", agent=db_agent, agent_reports=db_agent_reports)

#TODO: refactor to get rid duplicate code
@app.route("/agents/<agent_id>/image", methods=["GET"])
def get_agent_image(agent_id: str):
	db_agent = db.get_agent(agent_id.strip())

	if db_agent is None:
		flask.abort(404)

	file_name = werkzeug.utils.secure_filename(db_agent["id"]) + "." + app.config["IMG_TYPE"]

	if os.path.isfile(os.path.join(app.config["IMG_AGENT"], file_name)):
		return flask.send_from_directory(app.config["IMG_AGENT"], file_name)
	else:
		return flask.send_from_directory(app.static_folder, "images/agent-img-404.png")

@app.route("/reports/<report_id>/image/<image_id>", methods=["GET"])
def get_report_image(report_id: str, image_id: str):
	db_report_image = db.get_report_image(image_id.strip())

	file_name = werkzeug.utils.secure_filename(db_report_image["id"]) + "." + app.config["IMG_TYPE"]

	if os.path.isfile(os.path.join(app.config["IMG_REPORT"], file_name)):
		return flask.send_from_directory(app.config["IMG_REPORT"], file_name)
	else:
		return flask.send_from_directory(app.static_folder, "images/agent-img-404.png")

@app.route("/reports/<report_id>/image/<image_id>/thumb", methods=["GET"])
def get_report_image_thumb(report_id: str, image_id: str):
	db_report_image = db.get_report_image(image_id.strip())

	file_name = werkzeug.utils.secure_filename(db_report_image["id"]) + ".thumb." + app.config["IMG_TYPE"]

	if os.path.isfile(os.path.join(app.config["IMG_REPORT"], file_name)):
		return flask.send_from_directory(app.config["IMG_REPORT"], file_name)
	else:
		return flask.send_from_directory(app.static_folder, "images/agent-img-404.png")

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
				payload.get("description"))

	return "", 200

@app.route("/api/agents/image", methods=["POST"])
def api_add_agent_image():
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
		images.save_image(agent_id, payload["image"], images.ImageType.AGENT)
	except (KeyError, IOError):
		flask.abort(500)

	return "", 200

@app.route("/api/reports", methods=["post"])
def api_add_report():
	if not utils.verify_digest(flask.request.data, flask.request.headers["Authorization"]):
		app.logger.warning("Failed HMAC Auth")
		flask.abort(401)

	payload = flask.request.get_json()
	agent_id = payload["agent"].strip()

	if utils.is_dict_empty(["agent"], payload):
		app.logger.warning("Mandatory fields empty")
		flask.abort(404)

	db_agent = db.get_agent(agent_id)
	if agent is None:
		#TODO: replace with API error instead
		app.logger.warning("Attempted to upload report for nonexistent agent")
		flask.abort(404)

	#TODO: replace with proper short unique id generation
	report_id = utils.generate_short_uuid(str(random.random() * 1000) + str(payload["time"]) + agent_id, 8)

	db.add_report(report_id, payload["time"], db_agent["location"], agent_id)

	for report_image in payload["images"]:
		image_id = report_id + "_" + report_image["location"]

		try:
			images.save_image(image_id, report_image["image"], images.ImageType.REPORT)
			db.add_report_image(image_id, report_image["location"], 0, report_id)

			#thumbnail image for smaller version for dashboard
			images.save_image(image_id + ".thumb", report_image["image"], images.ImageType.REPORT_THUMB)
		except (KeyError, IOError):
			flask.abort(500)

	return "", 200

#filters for jinga2 (http://flask.pocoo.org/docs/0.12/templating/#registering-filters)
@app.template_filter("datetime")
def filter_datetime(time_stamp: str) -> str:
	return datetime.datetime.fromtimestamp(time_stamp)
