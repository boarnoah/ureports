import os
import sqlite3

import flask

#import simplereports.views
#import db

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

@app.route('/')
def index():
	return flask.render_template('index.html')

@app.route('/reports/')
def reports():
	return flask.render_template('reports.html')

@app.route('/report/<reportId>')
def report(reportId):
	return flask.render_template('report.html', reportId=reportId)

@app.route('/agents/')
def agents():
	return flask.render_template('agents.html')

@app.route('/agent/<agentId>')
def agent(agentId):
	return flask.render_template('agent.html', agentId=agentId)

@app.route('/manual/')
def manual():
	return flask.render_template('manual.html')

@app.errorhandler(404)
def page_not_found(e):
	return flask.render_template('404.html'), 404