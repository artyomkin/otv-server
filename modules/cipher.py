import requests
import base64
import json
def decrypt(text):
    url = "https://kms.yandex/kms/v1/keys/abjgdckdsih3iv7hoe9t:decrypt"
    body = {
        "ciphertext": text
    }
    headers = {"Authorization":
    return base64.b64decode(x.json()['plaintext']).decode()

def cipher(text):
    url = "https://kms.yandex/kms/v1/keys/abjgdckdsih3iv7hoe9t:encrypt"
    b = text.encode("UTF-8")
    e = base64.b64encode(b)
    body = {
        "versionId": "abjq12ovk0njiep8qgkb",
        "plaintext": e.decode()
    }
    headers = {"Authorization": "Bearer 

    x = requests.post(url, json=body, headers=headers)
    return x.json()['ciphertext']

