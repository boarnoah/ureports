#Deploy

Please note, the below is last min rush job, didn't have time to figure out wsgi or docker or anything for that matter

1. install nginx:
apt-get install nginx

2. install pip & pipenv:
apt-get install python-pip
pip install pipenv

3. dl and run ureports:
git clone https://github.com/boarnoah/ureports.git
pipenv install --three
export FLASK_APP=ureports.py
pipenv run flask init
pipenv run flask run &

4. add nginx config:
// Copy config from etc/ in this /deploy folder to nginx's config location
sudo cp etc/nginx/sites-available/ureports.vhost /etc/nginx/sites-available/ureports.vhost
sudo ln -s /etc/nginx/sites-available/ureports.vhost sites-enabled/ureports.vhost
// remove the default config
sudo rm sites-enabled/default