#!/bin/sh

convert -background white -type Grayscale -density 200x200 -quality 60 -compress zip $1 out.pdf

