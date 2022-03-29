import json
import logging
import os

import yaml
from PIL import Image

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CardMastery:
    cards_json = '/Users/sml/git/cr-cardgen/cardgen/cards.json'
    config_yaml = '/Users/sml/git/cr-cardgen/cardgen/config.yaml'

    dst_folder = '/Users/sml/Dropbox/_projects/RoyaleAPI_dev/ui/mastery/dst'
    assets_folder = '/Users/sml/Dropbox/_projects/RoyaleAPI_dev/ui/mastery/mastery-assets'
    spells_folder = '/Users/sml/git/cr-cardgen/cardgen/card-src-104x132'

    def __init__(self):
        self._cards_data = None
        self._card_filenames = None
        self._config = None

    @property
    def cards_data(self):
        if self._cards_data is None:
            with open(self.cards_json, encoding='utf-8', mode='r') as f:
                self._cards_data = json.load(f)
        return self._cards_data

    @property
    def config(self):
        if self._config is None:
            with open(self.config_yaml) as f:
                self._config = yaml.full_load(f)
        return self._config

    @property
    def card_filenames(self):
        if self._card_filenames is None:
            self._card_filenames = dict((v, k) for k, v in self.config["cards"].items())
        return self._card_filenames

    def get_card_src_path(self, key):
        return os.path.join(
            self.spells_folder, self.card_filenames.get(key) + '.png'
        )

    def make_mastery_img(self, key, level):
        mask_im = Image.open(
            os.path.join(
                self.assets_folder, 'mask.png'
            )
        )

        card_im = Image.open(
            self.get_card_src_path(key)
        )

        lvl_img = Image.open(
            os.path.join(
                self.assets_folder, f"lvl{level}.png"
            )
        )

        size = mask_im.size

        # pad card with transparent pixels
        card_size = card_im.size
        card_x = int((size[0] - card_size[0]) / 2)
        card_y = int((size[1] - card_size[1]) / 2)
        card_x1 = card_x + card_size[0]
        card_y1 = card_y + card_size[1]

        im = Image.new("RGBA", size)
        im.paste(
            card_im, (
                76,
                64,
                76 + card_size[0],
                64 + card_size[1],
            )
        )
        card_im = im

        im = Image.new("RGBA", size)

        # paste card
        im.paste(card_im, mask=mask_im)

        # add frame
        im = Image.alpha_composite(
            im, lvl_img
        )

        # dst
        dst_path = os.path.join(
            self.dst_folder,
            f"{key}-lvl{level}.png"
        )

        im.save(dst_path)
        logger.info(dst_path)

    def run(self):
        for card in self.cards_data:
            key = card.get('key')
            for lvl in range(1, 11):
                self.make_mastery_img(key, lvl)


if __name__ == '__main__':
    job = CardMastery()
    job.run()
