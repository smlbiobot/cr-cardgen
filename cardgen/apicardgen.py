#!/usr/bin/env python3
"""
Read card images from API and save as PNGs
"""
import requests
import os

token = os.environ.get('TOKEN')

r = requests.get('http://api.royaleapi.com/player/C0G20PR2', headers={'auth': token})
player = r.json()
print(player)

path = './card-api-png'
os.makedirs(path, exist_ok=True)

for card in player['cards']:
    card_path = os.path.join(path, card['key'] + '.png')
    print('Writing {}'.format(card_path))
    r = requests.get(card['icon'], stream=True)
    if r.status_code == 200:
        with open(card_path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    print('done')

