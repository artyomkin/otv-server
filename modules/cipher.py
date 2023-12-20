import requests
import base64
import json
def decrypt(text):
    url = "https://kms.yandex/kms/v1/keys/abjgdckdsih3iv7hoe9t:decrypt"
    body = {
        "ciphertext": text
    }
    headers = {"Authorization": "Bearer t1.9euelZrOipSezpyMyJCLnYmej8jMz-3rnpWayc2JlpmMmc2ekI2ck47PyM7l8_d7EHVT-e8GYHF1_N3z9zs_clP57wZgcXX8zef1656VmsielMmPi56WlZudy4zOl5WX7_zF656VmsielMmPi56WlZudy4zOl5WX.Z8AhORcT-4fVUh4k73X9-MxDZNjKk6ft6Y0XkwEZXncngLq7H_8prc8Xf9HTFKrLG7dcqdaSFbUv4_Ulmi5hCg"}
    x = requests.post(url, json=body, headers=headers)
    return base64.b64decode(x.json()['plaintext']).decode()

def cipher(text):
    url = "https://kms.yandex/kms/v1/keys/abjgdckdsih3iv7hoe9t:encrypt"
    b = text.encode("UTF-8")
    e = base64.b64encode(b)
    body = {
        "versionId": "abjq12ovk0njiep8qgkb",
        "plaintext": e.decode()
    }
    headers = {"Authorization": "Bearer t1.9euelZrOipSezpyMyJCLnYmej8jMz-3rnpWayc2JlpmMmc2ekI2ck47PyM7l8_d7EHVT-e8GYHF1_N3z9zs_clP57wZgcXX8zef1656VmsielMmPi56WlZudy4zOl5WX7_zF656VmsielMmPi56WlZudy4zOl5WX.Z8AhORcT-4fVUh4k73X9-MxDZNjKk6ft6Y0XkwEZXncngLq7H_8prc8Xf9HTFKrLG7dcqdaSFbUv4_Ulmi5hCg"}

    x = requests.post(url, json=body, headers=headers)
    return x.json()['ciphertext']

