import os
import sqlite3
import datetime

import flask

app = flask.Flask('ureports')

app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'data/ureports.db'),
	DEBUG=True,
	# Credentials to create new Agents, not suitable for a production app
	USERNAME='',
	PASSWORD=''
))

def get_db():
	db = getattr(flask.g, '_database', None)
	if db is None:
		db = flask.g._database = sqlite3.connect(app.config.get('DATABASE'))
		db.row_factory = sqlite3.Row
	return db

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()
		
@app.teardown_appcontext
def close_connection(exception):
	db = getattr(flask.g, '_database', None)
	if db is not None:
		db.close()

@app.cli.command('initdb')
def initdb_command():
	init_db()
	print('Initialized the database.')

def add_agent(agentId: str, name: str, location: str, secret: str, online: int = None, description: str = None, picture: str = None):
	get_db.execute("INSERT INTO agents (id, name, location, secret, online, description, picture) VALUES (?, ?, ?, ?, ?, ?, ?)", 
					agentId, name, location, secret, online, description, picture)
	raise NotImplementedError

def get_agents() -> list:
	#TODO: See todo for get_reports
	return get_db().execute("SELECT * FROM agents").fetchall()

def get_agent(agentId: str) -> sqlite3.Row:
	return get_db().execute("SELECT * FROM agents where id = ?", (agentId, )).fetchone()

def add_report(reportId: str, time: int, location: str, agent: str):
	get_db().execute("INSERT INTO reports (id, time, location, agent)", reportId, time, location, agent)
	raise NotImplementedError

def get_reports(numReports: int = 20, startIndex: int = 0) -> list:
	#TODO: Better to lazily iterate cursor's return obj than to fetchall rows as a list () if data is big (which its not)
	return get_db().execute("SELECT * FROM reports ORDER BY time DESC LIMIT ? OFFSET ?", (numReports, startIndex)).fetchall()

def get_report(reportId: str) -> sqlite3.Row:
	return get_db().execute("SELECT * FROM reports WHERE id = ?", (reportId, )).fetchone()

@app.route('/')
def index():
	return flask.render_template('index.html')

@app.route('/reports/')
def reports():
	return flask.render_template('reports.html', reports=get_reports())

@app.route('/report/<reportId>')
def report(reportId):
	report = get_report(reportId)

	if report is None:
		flask.abort(404)

	return flask.render_template('report.html', report=report)

@app.route('/agents/')
def agents():
	return flask.render_template('agents.html', agents=get_agents())

@app.route('/agent/<agentId>')
def agent(agentId):
	agent = get_agent(agentId)

	if agent is None:
		flask.abort(404)

	return flask.render_template('agent.html', agent=agent)

@app.route('/manual/')
def manual():
	return flask.render_template('manual.html')

@app.errorhandler(404)
def page_not_found(e):
	return flask.render_template('404.html'), 404


#filters for jinga2 (http://flask.pocoo.org/docs/0.12/templating/#registering-filters)
@app.template_filter('datetime')
def filter_datetime(timestamp:str) -> str:
	return datetime.datetime.fromtimestamp(timestamp)