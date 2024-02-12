#!/usr/bin/env bash

gs -q -dNOPAUSE -dBATCH -dSAFER -sPAPERSIZE=a4 -sDEVICE=pdfwrite -dCompatibilityLevel=1.3 -dPDFSETTINGS=/screen -dEmbedAllFonts=true -dSubsetFonts=true -sDEVICE=pdfwrite -sColorConversionStrategy=Gray -dProcessColorModel=/DeviceGray -dGrayImageDownsampleType=/Bicubic -dGrayImageResolution=300 -dMonoImageDownsampleType=/Bicubic -dMonoImageResolution=300 -sOutputFile=compressed$1.pdf $1

