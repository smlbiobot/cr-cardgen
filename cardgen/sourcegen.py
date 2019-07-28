#!/usr/bin/env python3

import json
import logging
import os
import shutil
import sys

import requests
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CONFIG = os.path.join("config.yaml")


def load_json(filename):
    """Load json by filename."""
    with open(filename, encoding='utf-8', mode='r') as f:
        data = json.load(f)
    return data


def get_cards_data(config, local=False):
    if local:
        cards_data = load_json(config["cards_data"])
    else:
        r = requests.get(config["cards_data_url"])
        cards_data = r.json()

    return cards_data


def main(arguments):
    """
    Naming source images
    :param arguments:
    :return:
    """

    with open(CONFIG) as f:
        config = yaml.full_load(f)

    spells_path = config["spells_dir"]

    output_path = config["raw_dir"]
    os.makedirs(output_path, exist_ok=True)

    filenames = dict((v, k) for k, v in config["cards"].items())

    cards_data = get_cards_data(config, local=True)

    for card_data in cards_data:
        name = card_data['key']
        filename = filenames.get(name)
        src_path = os.path.join(spells_path, "{}.png".format(filename))
        dst_path = os.path.join(output_path, "{}.png".format(name))

        shutil.copy(src_path, dst_path)
        logger.info(dst_path)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
