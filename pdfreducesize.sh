#!/bin/sh

gs	-q -dNOPAUSE -dBATCH -dSAFER \
	-sPAPERSIZE=a4 \
  -sDEVICE=pdfwrite \
	-dCompatibilityLevel=1.3 \
	-dPDFSETTINGS=/screen \
	-dEmbedAllFonts=true \
	-dSubsetFonts=true \
	-dColorImageDownsampleType=/Bicubic \
	-dColorImageResolution=120 \
	-dGrayImageDownsampleType=/Bicubic \
	-dGrayImageResolution=120 \
	-dMonoImageDownsampleType=/Bicubic \
	-dMonoImageResolution=120 \
	-sOutputFile=out.pdf \
	 $1
