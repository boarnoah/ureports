import hmac
import json
import os
import base64
import time 

import requests

SECRET = "password"
HOST = "http://localhost:5000"

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
		"agent": "mr-whiskers-jr",
		"time": int(time.time()),
		"images": [
			{
				"image": "sacks.jpg",
				"location": "WP-1"
			},
			{
				"image": "sacks.jpg",
				"location": "WP-2"
			}
		]
	},
	{
		"agent": "golden-boy",
		"time": int(time.time()) + (60*60*24),
		"images": [
			{
				"image": "sacks.jpg",
				"location": "WP-1"
			},
			{
				"image": "mouse.jpg",
				"location": "WP-2"
			}
		]
	}
]

def calc_hmac(payload: bytes) -> str:
	digest = hmac.new(str.encode(SECRET), msg=payload, digestmod="sha256")
	return digest.hexdigest()


def add_agent() -> None:
	url = HOST + "/api/agents"

	for agent in AGENTS:
		json_payload = json.dumps(agent)

		headers = {
			"Authorization": calc_hmac(str.encode(json_payload))
		}

		try:
			requests.post(url, json=agent, headers=headers)
		except requests.exceptions.RequestException as req_exception:
			print(req_exception)
			print("Failed to ", url, " for agent: ", agent["id"])
			continue

		print("Sending ", url, " for agent: ", agent["id"])

def add_agent_images():
	url = HOST + "/api/agents/image"

	for agent in AGENTS:
		image = open(os.path.join(os.getcwd(), "images", agent["image"]), mode="rb")

		payload = {
			"id": agent["id"],
			"image": bytes.decode(base64.b64encode(image.read()))
		}

		json_payload = json.dumps(payload)

		headers = {
			"Authorization": calc_hmac(str.encode(json_payload))
		}

		try:
			requests.post(url, json=payload, headers=headers)
		except requests.exceptions.RequestException as req_exception:
			print(req_exception)
			print("Failed to ", url, "for agent: ", agent["id"])
			continue

		print("Sending ", url, "for agent: ", agent["id"])

def add_report():
	url = HOST + "/api/reports"
	for report in REPORTS:

		payload = {
			"agent": report["agent"],
			"time": report["time"],
			"images": []
		}

		for image in report["images"]:
			iamge_file = open(os.path.join(os.getcwd(), "images", image["image"]), mode="rb")
			image_payload = {
				"image": bytes.decode(base64.b64encode(iamge_file.read())),
				"location": image["location"]
			}

			payload["images"].append(image_payload)

		json_payload = json.dumps(payload)

		headers = {
			"Authorization": calc_hmac(str.encode(json_payload))
		}

		try:
			requests.post(url, json=payload, headers=headers)
		except requests.exceptions.RequestException as req_exception:
			print(req_exception)
			print("Failed to ", url, " for report with agent id: : ", report["agent"])
			continue

		print("Sending", url, " for report with agent id: ", report["agent"])

add_agent()
add_agent_images()
add_report()
