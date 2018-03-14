import base64
import tempfile
import os

from PIL import Image as pilImage
import werkzeug

app = None

def init_app(_app):
	global app
	app = _app

def save_agent_image(file_name: str, image: str) -> str:
	image = base64.b64decode(image)
	secure_file_path = os.path.join(app.config["IMG_AGENT"], werkzeug.utils.secure_filename(file_name) + '.' + app.config["IMG_TYPE"])

	temp_file = tempfile.SpooledTemporaryFile()
	temp_file.write(image)

	try:
		image = pilImage.open(temp_file)
		image.thumbnail(app.config["IMG_AGENT_XY"])
		image.save(secure_file_path, format=app.config["IMG_TYPE"])
	except (KeyError, IOError):
		app.logger.warning("Failed save temp image! Broken file / unknown format ")
		raise

	return secure_file_path
