import requests
import base64
import json
def cipher(text):
    url = "<stub>"
    b = text.encode("UTF-8")
    e = base64.b64encode(b)
    body = {
        "versionId": "<stub>",
        "plaintext": e.decode()
    }
    headers = {"Authorization": "<stub>"}

    x = requests.post(url, json=body, headers=headers)
    return x.json()['ciphertext']

def decrypt(text):
    url = "<stub>"
    body = {
        "ciphertext": text
    }
    headers = {"Authorization": "<stub>"}
    x = requests.post(url, json=body, headers=headers)
    return x.json()['plaintext']

