import requests
import base64
import json
import os
from time import time
import vk_api


def auth_handler():
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device


vk_session = vk_api.VkApi('login', 'password', auth_handler=auth_handler)
vk_session.auth()
vk = vk_session.get_api()
path = '/'.join(os.path.realpath(__file__).split('/')[:-1])
with open(path + '/config.json', 'r') as fp:
    config = json.load(fp)

client_id = config['client_id']
client_secret = config['client_secret']
default = config['default_status']
refresh_token = config['refresh_token']


class SpotifyTokenError(Exception):
    pass


def get_token(cid, csec, refresh):
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh,
    }
    headers = {
        'Authorization': 'Basic {}'.format(base64.b64encode(f"{cid}:{csec}".encode()).decode()),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    token_expiration = int(time()) + 3599
    r = requests.post("https://accounts.spotify.com/api/token", data=payload, headers=headers)
    if r.status_code == 200:
        result = {
            'lifetime': token_expiration,
            'token': json.loads(r.text)['access_token']
        }
        return result
    else:
        raise Exception(f"Got {r.status_code} while getting access token")


def get_playing(api):
    lifetime = api['lifetime']
    token = api['token']
    if time() > lifetime:
        raise SpotifyTokenError
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 200:
        try:
            playing = json.loads(r.text)
        except json.decoder.JSONDecodeError:
            return default
        status = f"Listening \"{playing['item']['name']}\" by {playing['item']['artists'][0]['name']}"
        max_length = 70
        if len(status) > max_length:
            status = status[:max_length]
        return status
    elif r.status_code == 204:
        return default
    else:
        raise Exception(f"Got {r.status_code} while getting current song")


api = get_token(client_id, client_secret, refresh_token)
print(get_playing(api))
