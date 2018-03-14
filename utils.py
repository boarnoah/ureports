import hmac

app = None

def init_app(_app):
	global app
	app = _app

def verify_digest(input_data: str, input_hash: str) -> bool:
	key = str.encode(app.config["SECRET"])
	computed_hash = hmac.new(key, msg=input_data, digestmod="sha256")
	return hmac.compare_digest(computed_hash.hexdigest(), input_hash)

def is_dict_empty(keys_to_check: list, dict_to_check: dict) -> bool:
	for key in keys_to_check:
		data = dict_to_check.get(key)

		# Check if attr missing or empty str
		if data is None or not data.strip():
			app.logger.warning("Attribute: %s was not found or was empty", key)
			return True

	return False
