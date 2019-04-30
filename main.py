from __future__ import unicode_literals
import logging
import json
from alice_sdk import AliceRequest, AliceResponse
from handler import handle_dialog
from flask import Flask, request
app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)

session_storage = {}

with open("sessions.json", "w", encoding="utf8") as file:
    json.dump(session_storage, fp=file)


@app.route("/", methods=["POST"])
def main():
    with open("sessions.json", encoding="utf8") as file:
        session_storage = json.loads(file.read())

    alice_request = AliceRequest(request.json)
    # logging.info("Request: {}".format(alice_request))

    alice_response = AliceResponse(alice_request)

    user_id = alice_request.user_id

    alice_response, session_storage[user_id] = handle_dialog(
        alice_request, alice_response, session_storage.get(user_id)
    )

    with open("sessions.json", "w", encoding="utf8") as file:
        json.dump(session_storage, fp=file)

    logging.info("Response: {}".format(alice_response))

    return alice_response.dumps()


if __name__ == '__main__':
    app.run()
