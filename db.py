import sqlite3
import os

import flask

app = None

def init_app(_app):
	global app
	app = _app

def get_db():
	db = getattr(flask.g, "_database", None)
	if db is None:
		db = flask.g._database = sqlite3.connect(app.config["DATABASE"])
		db.row_factory = sqlite3.Row
	return db

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource("schema.sql", mode="r") as f:
			db.cursor().executescript(f.read())
		db.commit()

def init_folder() -> bool:
	folder_existed = True

	if not os.path.exists(app.config["DATA"]):
		folder_existed = False
		os.makedirs(app.config["DATA"])
		os.makedirs(app.config["IMG_REPORT"])
		os.makedirs(app.config["IMG_AGENT"])

	return folder_existed

def init():
	if init_folder():
		print("okay")
		#app.logger.info("Folder tree (" %s ") already exists. Using it as is", app.config["DATA"])
	else:
		app.logger.info("Created folder tree at %s", app.config["DATA"])

	init_db()
	app.logger.info("Initialized the database.")

def close_connection():
	db = getattr(flask.g, "_database", None)
	if db is not None:
		db.close()

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
	get_db().execute("INSERT INTO reports (id, time, location, agent) VALUES (?, ?, ?, ?)", (report_id, report_time, location, agent_id))
	get_db().commit()

def get_reports(num_reports: int = 20, start_index: int = 0) -> list:
	#TODO: Better to lazily iterate cursor's return obj than to fetchall rows as a list () if data is big (which its not)
	return get_db().execute("SELECT * FROM reports ORDER BY time DESC LIMIT ? OFFSET ?", (num_reports, start_index)).fetchall()

def get_report(report_id: str) -> sqlite3.Row:
	return get_db().execute("SELECT * FROM reports WHERE id = ?", (report_id, )).fetchone()

def add_report_image(image_id:str, image_path:str, location: str, image_confirmed: int, report_id:str):
	get_db().execute("INSERT INTO images (id, path, location, confirmed, report) VALUES (?, ?, ?, ?, ?)", (image_id, image_path, location, image_confirmed, report_id))
	get_db().commit()
