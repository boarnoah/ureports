# Micro Reports
Generate reports with times + images based on data sent as POSTs using Flask and sqlite3

Populated with sample data for "CatCatCat", a fictional Feline Assassins as a Service company

### Why?
To serve as a reference implemenation for a small customizable dashboard for any purpose.

## Dependencies
Installation:

python 3 

[pipenv](https://github.com/pypa/pipenv)

Project (handled by pipenv):

[Flask](http://flask.pocoo.org/)

[Pillow](https://github.com/python-pillow/Pillow) (for image manipulation)


## Build Instructions

To install dependencies on a fresh clone (add --dev to install dev deps ex: to test with client.py):

	pipenv install 

To run app (set instead of export for windows)

	export FLASK_APP=ureports.py

Then, for a fresh db + folder structure

	pipenv run flask init

Finally

	pipenv run flask run


## Client/client.py
Serves as a regression test + example of the client implementation. Client being the agent that generates reports.

note: install depdencies via "pipenv install --dev" as the client has dependencies not needed for the dashboard app.

In app root:

	pipenv shell
	cd Client/
	python client.py

## License
MIT