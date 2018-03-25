import hmac
import json

import requests

SECRET = "password"
HOST = "https://localhost:5000"

AGENTS = [
	{
		"id": "mr-whiskers-jr",
		"name": "Mr Whiskers",
		"location": "New York",
		"secret": "123456",
		"image": "cat.jpg"
	},
	{
		"id": "golden-boy",
		"name": "Sir Golden Boy",
		"location": "London",
		"secret": "123456",
		"image": "dog.jpg"
	}
]

REPORTS = [
	{
		""
	}
]

def calc_hmac(payload: bytes) -> str:
	digest = hmac.new(str.encode(SECRET), msg=payload, digestmod="sha256")
	return digest.hexdigest()


def add_agent() -> None:
	url = HOST + "/api/AGENTS"

	for agent in AGENTS:
		json_payload = json.dumps(agent)

		headers = {
			"Authorization": calc_hmac(str.encode(json_payload))
		}

		try:
			requests.post(url, json=json_payload, headers=headers)
		except requests.exceptions.RequestException as req_exception:
			print(req_exception)
			print("Failed to /api/AGENTS for agent: ", agent["id"])
			continue

		print("Sending /api/AGENTS for agent: ", agent["id"])

def add_agent_images():
	url = HOST + "/api/AGENTS/image"
	raise NotImplementedError

add_agent()
#add_agent_images()
