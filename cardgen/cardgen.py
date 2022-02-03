#!/usr/bin/env python3

import json
import logging
import os
import shutil
import sys

import pngquant
import requests
import yaml
from PIL import Image
from PIL import ImageCms
from PIL import ImageChops

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CONFIG = os.path.join("config.yaml")

pngquant.config('/usr/local/bin/pngquant')


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


def makedirs(dirs):
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)


def generate_cards(is_gold=False, with_elixir=False):
    """Generate Clash Royale cards."""
    with open(CONFIG) as f:
        config = yaml.full_load(f)

    cards_data = get_cards_data(config, local=True)

    src_path = config["src_dir"]
    spells_path = config["spells_dir"]
    if is_gold:
        output_png24_dir = config["output_png24_gold_dir"]
        output_png8_dir = config["output_png8_gold_dir"]
    else:
        if with_elixir:
            output_png24_dir = config["output_png24_elixir_dir"]
            output_png8_dir = config["output_png8_elixir_dir"]
        else:
            output_png24_dir = config["output_png24_dir"]
            output_png8_dir = config["output_png8_dir"]

    makedirs([output_png8_dir, output_png24_dir])

    filenames = dict((v, k) for k, v in config["cards"].items())

    if is_gold:
        card_frame = Image.open(os.path.join(src_path, "frame-card-gold.png"))
        leggie_frame = Image.open(os.path.join(src_path, "frame-legendary-gold.png"))
        champion_frame = Image.open(os.path.join(src_path, "frame-champion.png"))
    else:
        card_frame = Image.open(os.path.join(src_path, "frame-card.png"))
        leggie_frame = Image.open(os.path.join(src_path, "frame-legendary.png"))
        champion_frame = Image.open(os.path.join(src_path, "frame-champion.png"))

    card_mask = Image.open(
        os.path.join(src_path, "mask-card.png")).convert("RGBA")
    leggie_mask = Image.open(
        os.path.join(src_path, "mask-legendary.png")).convert("RGBA")
    champion_mask = Image.open(
        os.path.join(src_path, "mask-champion.png")).convert("RGBA")

    commons_bg = Image.open(os.path.join(src_path, "bg-commons.png"))
    rare_bg = Image.open(os.path.join(src_path, "bg-rare.png"))
    epic_bg = Image.open(os.path.join(src_path, "bg-epic.png"))
    leggie_bg = Image.open(os.path.join(src_path, "bg-legendary.png"))
    leggie_gold_bg = Image.open(os.path.join(src_path, "bg-legendary-gold.png"))
    gold_bg = Image.open(os.path.join(src_path, "bg-gold.png"))
    champion_bg = Image.open(os.path.join(src_path, "bg-champion.png"))

    size = card_frame.size

    for card_data in cards_data:
        name = card_data['key']
        rarity = card_data['rarity']
        elixir = card_data['elixir']

        # debug: skip everything but champion
        # if rarity != "Champion":
        #     continue

        filename = filenames.get(name)

        if filename is None:
            logger.warning(f"{name} does not have a corresponding file, continuing…")
            continue

        card_src = os.path.join(spells_path, "{}.png".format(filename))
        card_dst_png24 = os.path.join(output_png24_dir, "{}.png".format(name))
        card_dst_png8 = os.path.join(output_png8_dir, "{}.png".format(name))
        card_image = Image.open(card_src)

        # scale card to fit frame
        scale = 1
        card_image = card_image.resize(
            [int(dim * scale) for dim in card_image.size])

        # pad card with transparent pixels to be same size as output
        card_size = card_image.size
        card_x = int((size[0] - card_size[0]) / 2)
        card_y = int((size[1] - card_size[1]) / 2)
        card_x1 = card_x + card_size[0]
        card_y1 = card_y + card_size[1]

        im = Image.new("RGBA", size)
        im.paste(
            card_image, (card_x, card_y, card_x1, card_y1))
        card_image = im

        im = Image.new("RGBA", size)

        if rarity == "Legendary":
            im.paste(card_image, mask=leggie_mask)
        elif rarity == "Champion":
            # scale up image slightly and then crop to same dimension
            c_image = card_image
            orig_size = c_image.size
            old_w = orig_size[0]
            old_h = orig_size[1]
            scale = 1.1
            new_w = int(old_w * scale)
            new_h = int(old_h * scale)
            c_image = c_image.resize(
                (new_w, new_h)
            )
            crop_x = int((new_w - old_w) / 2)
            crop_y = int((new_h - old_w) / 2)
            crop_right = crop_x + old_w
            crop_bottom = crop_y + old_h

            c_image = c_image.crop(
                (crop_x, crop_y, crop_right, crop_bottom)
            )
            c_image = ImageChops.offset(c_image, 0, 50)
            im.paste(c_image, mask=champion_mask)
        else:
            im.paste(card_image, mask=card_mask)

        card_image = im

        im = Image.new("RGBA", size)
        im = Image.alpha_composite(im, card_image)

        # use background image for regular cards
        bg = None
        if rarity == "Champion":
            bg = champion_bg
        elif is_gold:
            if rarity == 'Legendary':
                bg = leggie_gold_bg
            else:
                bg = gold_bg
        elif rarity == "Commons":
            bg = commons_bg
        elif rarity == "Rare":
            bg = rare_bg
        elif rarity == "Epic":
            bg = epic_bg
        elif rarity == "Legendary":
            bg = leggie_bg
        else:
            bg = Image.new("RGBA", size)

        # add frame
        im = Image.alpha_composite(bg, im)
        if rarity == "Legendary":
            im = Image.alpha_composite(im, leggie_frame)
        elif rarity == "Champion":
            im = Image.alpha_composite(im, champion_frame)
        else:
            im = Image.alpha_composite(im, card_frame)

        # add elixir
        if with_elixir:
            im_elixir = Image.open(os.path.join(src_path, f"elixir-{elixir}.png"))
            im = Image.alpha_composite(im, im_elixir)

        # save and output path to std out

        converted_im = ImageCms.profileToProfile(im, './AdobeRGB1998.icc', 'sRGB.icc')
        converted_im.save(card_dst_png24)
        logger.info(card_dst_png24)


def create_size(w, h, folder_name, is_gold=False, with_elixir=False):
    with open(CONFIG) as f:
        config = yaml.full_load(f)

    root = config.get('working_dir')

    if is_gold:
        src_dir = config.get('output_png24_gold_dir')
    else:
        if with_elixir:
            src_dir = config["output_png24_elixir_dir"]
        else:
            src_dir = config["output_png24_dir"]

    dst_dir = os.path.join(root, folder_name)

    os.makedirs(dst_dir, exist_ok=True)

    cards_data = get_cards_data(config, local=True)

    for card_data in cards_data:
        key = card_data.get('key')
        card_src = os.path.join(src_dir, "{}.png".format(key))
        card_dst = os.path.join(dst_dir, "{}.png".format(key))

        try:
            im = Image.open(card_src)
            im.thumbnail((w, h), Image.ANTIALIAS)
            im.save(card_dst)
            logger.info(card_dst)
        except IOError:
            logger.error(f"Cannot create thumbnail for {key}")


def create_png8(folder_name, is_gold=False):
    with open(CONFIG) as f:
        config = yaml.full_load(f)

    root = config.get('working_dir')

    if is_gold:
        src_dir = config.get('output_png24_gold_dir')
    else:
        src_dir = config.get('output_png24_dir')

    dst_dir = os.path.join(root, folder_name)

    os.makedirs(dst_dir, exist_ok=True)

    cards_data = get_cards_data(config, local=True)

    for card_data in cards_data:
        key = card_data.get('key')
        card_src = os.path.join(src_dir, "{}.png".format(key))
        card_dst = os.path.join(dst_dir, "{}.png".format(key))

        if not os.path.exists(card_src):
            print(f"{card_src} does not exist!")
            continue

        try:
            pngquant.quant_image(
                image=card_src,
                dst=card_dst
            )
            logger.info(card_dst)
        except IOError:
            logger.error(f"Cannot create thumbnail for {key}")


def copyfiles(src_root='/Users/sml/git/cr-cardgen/cardgen',
              dst_root='/Users/sml/git/cr-api-web/public/static/img',
              include_png8=False):
    """Copy card images to cr-api-web."""
    with open(CONFIG) as f:
        config = yaml.full_load(f)

    folders = [
        dict(
            src='./cards',
            dst='./cards'
        ),
        dict(
            src='./cards-75',
            dst='./cards-75'
        ),
        dict(
            src='./cards-150',
            dst='./cards-150'
        ),
        dict(
            src='./cards-gold',
            dst='./cards-gold'
        ),
        dict(
            src='./cards-75-gold',
            dst='./cards-75-gold'
        ),
        dict(
            src='./cards-150-gold',
            dst='./cards-150-gold'
        ),

    ]

    if include_png8:
        folders.extend([
            dict(
                src='./cards-png8',
                dst='./cards-png8'
            ),
            dict(
                src='./cards-gold-png8',
                dst='./cards-gold-png8'
            ),
        ])

    for folder in folders:
        src = os.path.join(src_root, folder.get('src'))
        dst = os.path.join(dst_root, folder.get('dst'))
        for file in os.listdir(src):
            if not file.startswith('.'):
                src_path = os.path.join(src, file)
                dst_path = os.path.join(dst, file)
                shutil.copy(src_path, dst_path)
                logger.info(dst_path)


def copy_cards_json():
    # shutil.copy(
    #     '/Users/sml/git/cr-api-data/docs/json/cards.json',
    #     '/Users/sml/git/cr-cardgen/cardgen/cards.json'
    # )

    shutil.copy(
        '/Users/sml/git/cr-api-data-process/docs/json/cards.json',
        '/Users/sml/git/cr-cardgen/cardgen/cards.json'
    )


def main(arguments):
    """Main."""

    copy_cards_json()

    for with_elixir in [True, False]:
        generate_cards(is_gold=False, with_elixir=with_elixir)

    # return

    create_size(75, 90, "cards-elixir-75", is_gold=False, with_elixir=True)
    create_size(150, 180, "cards-elixir-150", is_gold=False, with_elixir=True)

    generate_cards(is_gold=False)
    create_size(75, 90, "cards-75", is_gold=False)
    create_size(150, 180, "cards-150", is_gold=False)
    create_png8("cards-png8", is_gold=False)

    generate_cards(is_gold=True)
    create_size(75, 90, "cards-75-gold", is_gold=True)
    create_size(150, 180, "cards-150-gold", is_gold=True)
    create_png8("card-gold-png8", is_gold=True)

    copyfiles(
        src_root='/Users/sml/git/cr-cardgen/cardgen',
        dst_root='/Users/sml/git/cr-api-web/public/static/img'
    )

    copyfiles(dst_root='/Users/sml/git/cr-api-assets', include_png8=True)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
