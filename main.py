from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/reports/')
def reports():
	return render_template('reports.html')

@app.route('/reports/<reportId>')
def report(reportId):
	return render_template('report.html')

@app.route('/agents/')
def agents():
	return render_template('agents.html')

@app.route('/manual/')
def manual():
	return render_template('manual.html')

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404