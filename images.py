import base64
import tempfile
import os
import enum

from PIL import Image as pilImage
import werkzeug

app = None

def init_app(_app):
	global app
	app = _app

class ImageType(enum.Enum):
	AGENT = 0
	REPORT = 1
	REPORT_THUMB = 2

def save_image_disk(file_path: str, image: str, image_xy: tuple, image_format: str):
	image = base64.b64decode(image)

	temp_file = tempfile.SpooledTemporaryFile()
	temp_file.write(image)

	try:
		image = pilImage.open(temp_file)
		image.thumbnail(image_xy)
		image.save(file_path, format=image_format)
	except (KeyError, IOError):
		app.logger.warning("Failed save temp image! Broken file / unknown format ")
		raise

def save_image(file_name: str, image: str, image_type: ImageType) -> str:
	image_format = app.config["IMG_TYPE"]

	if image_type == ImageType.AGENT:
		img_location = app.config["IMG_AGENT"]
		image_xy = app.config["IMG_AGENT_XY"]
	elif image_type == ImageType.REPORT:
		img_location = app.config["IMG_REPORT"]
		image_xy = app.config["IMG_REPORT_XY"]
	elif image_type == ImageType.REPORT_THUMB:
		img_location = app.config["IMG_REPORT"]
		image_xy = app.config["IMG_REPORT_THUMB_XY"]

	secure_file_name = werkzeug.utils.secure_filename(file_name) + '.' + image_format
	secure_file_path = os.path.join(img_location, secure_file_name)

	save_image_disk(secure_file_path, image, image_xy, image_format)

	return secure_file_path
