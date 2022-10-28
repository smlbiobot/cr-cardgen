#!/bin/sh


# Resize images with ImageMagick and put in the card source folders

echo "$1"

convert "$1" -resize 104x132 "/Users/sml/git/cr-cardgen/cardgen/card-src-104x132/$1"
convert "$1" -resize 118x150 "/Users/sml/git/cr-cardgen/cardgen/card-src-118x150/$1"
convert "$1" -resize 236x300 "/Users/sml/git/cr-cardgen/cardgen/card-src-236x300/$1"