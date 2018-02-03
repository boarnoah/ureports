import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
	return flask.render_template('index.html')

@app.route('/reports/')
def reports():
	return flask.render_template('reports.html')

@app.route('/reports/<reportId>')
def report(reportId):
	return flask.render_template('report.html')

@app.route('/agents/')
def agents():
	return flask.render_template('agents.html')

@app.route('/manual/')
def manual():
	return flask.render_template('manual.html')

@app.errorhandler(404)
def page_not_found(e):
	return flask.render_template('404.html'), 404