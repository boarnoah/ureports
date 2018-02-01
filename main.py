from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/reports/')
def reports():
	return render_template('reports.html')

@app.route('/agents/')
def agents():
	return render_template('agents.html')

@app.route('/manual/')
def manual():
	return render_template('manual.html')