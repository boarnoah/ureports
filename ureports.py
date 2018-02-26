import os
import sqlite3
import datetime
import time
import hmac

import flask

app = flask.Flask('ureports')

with app.app_context():
	app.config.update(dict(
		DATA= os.path.join(app.root_path, 'data', flask.current_app.name),
		DEBUG=True,
		# Credentials to create new Agents, not suitable for a production app
		USERNAME='',
		PASSWORD=''
	))

	# For convenience:
	app.config['DATABASE'] = os.path.join(app.config['DATA'], flask.current_app.name + '.db')
	app.config['IMG_REPORT'] = os.path.join(app.config['DATA'], 'images', 'reports/')
	app.config['IMG_OTHER'] = os.path.join(app.config['DATA'], 'images', 'other/')

def get_db():
	db = getattr(flask.g, '_database', None)
	if db is None:
		db = flask.g._database = sqlite3.connect(app.config['DATABASE'])
		db.row_factory = sqlite3.Row
	return db

def init_folder() -> bool:
	folderExsisted = True

	if not os.path.exists(app.config['DATA']):
		folderExsisted = False
		os.makedirs(app.config['DATA'])
		os.makedirs(app.config['IMG_REPORT'])
		os.makedirs(app.config['IMG_OTHER'])

	return folderExsisted

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()
		
def verify_digest(inputData: bytes, inputHash: str) -> bool:
	key = str.encode(app.config['SECRET'])
	computedHash = hmac.new(key, msg = inputData, digestmod = 'sha256')
	return hmac.compare_digest(computedHash.hexdigest(), inputHash)

def is_dict_empty(keysToCheck: list, dictToCheck: dict) -> bool:
	for key in keysToCheck:
		data = dictToCheck.get(key)

		# Check if attr missing or empty str
		if data is None or not data.strip():
			app.logger.warn("Attribute: " + key + " was not found or was empty")
			return True
	
	return False

@app.teardown_appcontext
def close_connection(exception):
	db = getattr(flask.g, '_database', None)
	if db is not None:
		db.close()

@app.cli.command('init')
def init_command():
	if init_folder():
		print('Folder tree (', app.config['DATA'], ') already exists. Using it as is', )
	else:
		print('Created folder tree at', app.config['DATA'])

	init_db()
	print('Initialized the database.')

def add_agent(agentId: str, name: str, location: str, secret: str, online: int, description: str = None, picture: str = None):
	get_db().execute("INSERT INTO agents (id, name, location, secret, online, description, picture) VALUES (?, ?, ?, ?, ?, ?, ?)", 
					(agentId, name, location, secret, online, description, picture))
	get_db().commit()

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

# API endpoints
@app.route('/api/add-agent', methods=['POST'])
def api_add_agent():
	if not verify_digest(flask.request.data, flask.request.headers['Authorization']):
		app.logger.warn("Failed HMAC Auth")
		flask.abort(401)

	payload = flask.request.get_json()

	if is_dict_empty(['id', 'name', 'location', 'secret'], payload):
		app.logger.warn("Mandatory fields empty")
		flask.abort(404)

	if len(payload['id']) > 50:
		app.logger.warn("ID too long (> 50)")
		flask.abort(404)

	if len(payload['secret']) > 256:
		app.logger.warn("Secret too long (> 256)")
		flask.abort(404)

	if get_agent(payload['id'].strip()) is not None:
		#TODO: replace with API error instead
		app.logger.warn("Attempted to add agent with existing id")
		flask.abort(404)

	add_agent(payload['id'].strip(), payload['name'], payload['location'], payload['secret'], int(time.time()), 
				payload['description'])
	
	return "", 200

#filters for jinga2 (http://flask.pocoo.org/docs/0.12/templating/#registering-filters)
@app.template_filter('datetime')
def filter_datetime(timestamp:str) -> str:
	return datetime.datetime.fromtimestamp(timestamp)