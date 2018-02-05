# Micro Reports
Generate reports with times + images based on data sent as POSTs using Flask and sqlite3

Populated with sample data for "CatCatCat", a fictional Feline Assassins as a Service company

## Dependencies
Installation:
python 3 & pipenv

Project (handled by pipenv):
Flask

## Build Instructions

To install dependencies on a fresh clone:

	pipenv install 

To run app (set instead of export for windows)

	export FLASK_APP=ureports.py

Then, for a fresh db

	pipenv run flask initdb

Finally

	pipenv run flask run
