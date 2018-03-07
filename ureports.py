import os
import sqlite3
import datetime
import time
import hmac
import tempfile
import json 
import base64

import flask
import PIL
import werkzeug

app = flask.Flask('ureports')

IMG_TYPE = "PNG"
IMG_SIZE = 2 * (10 ** 6)
IMG_OTHER_X = 500
IMG_OTHER_Y = 500
IMG_REPORT_X = 2000
IMG_REPORT_Y = 2000

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

def verify_digest_json(inputData: str, inputHash: str) -> bool:
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

def valid_image_type(fileName:str) -> bool:
	secureFilename = werkzeug.utils.secure_filename(fileName)
	fileExtension = secureFilename.rsplit('.', 1)[1].lower()
	return '.' in secureFilename and fileExtension == IMG_TYPE

def temp_image(image:bytes):
	tempFile = SpooledTemporaryFile()
	PIL.Image.save(tempFile, format=IMG_TYPE)
	return PIL.Image.open(tempFile)

# dimensions + file size
def valid_image_size(image:bytes, x:int, y:int, size:int) -> bool:
	#tempImg = tempfile.SpooledTemporaryFile()

	#TODO: Checks
	return True

def save_square_image(fileName:str, image:str, location:str) -> str:
	image = base64.b64decode(image)
	tempImage = temp_image(image)

	print("Saved temp copy of image")

	# #TODO: Replace with exceptions
	# if not valid_image_type(image):
	# 	app.logger.warn("Uploaded image, not valid type")
	# 	return False
	
	# #if not valid_image_size():
	# secureFileName = os.path.join(location, werkzeug.utils.secure_filename(fileName) + ".jpg")
	# image.save(secureFileName)

	return secureFileName

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

@app.route('/reports/<reportId>')
def report(reportId):
	report = get_report(reportId)

	if report is None:
		flask.abort(404)

	return flask.render_template('report.html', report=report)

@app.route('/agents/', methods=['GET'])
def agents():
	return flask.render_template('agents.html', agents=get_agents())

@app.route('/agents/<agentId>', methods=['GET'])
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
@app.route('/api/agents', methods=['POST'])
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

@app.route('/api/agents/image', methods=['POST'])
def add_agent_image():
	#if not verify_digest(flask.request.form, flask.request.headers['Authorization']):
	#	app.logger.warn("Failed HMAC Authorization")
	#	return ""
	payload = flask.request.get_json()

	if is_dict_empty(['id', 'image'], payload):
		app.logger.warn("Mandatory fields empty")
		flask.abort(404)

	if get_agent(payload['id'].strip()) is None:
		#TODO: replace with API error instead
		app.logger.warn("Attempted to upload picture for nonexistent agent")
		flask.abort(404)

	save_square_image(payload['id'].strip(), payload['image'], app.config['IMG_OTHER'])

	return "", 200

#filters for jinga2 (http://flask.pocoo.org/docs/0.12/templating/#registering-filters)
@app.template_filter('datetime')
def filter_datetime(timestamp:str) -> str:
	return datetime.datetime.fromtimestamp(timestamp)