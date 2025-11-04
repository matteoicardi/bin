#!/usr/bin/env bash
# pdfreduce.sh
# Compress PDFs (scanned or not) with Ghostscript
#
# Usage:
#   ./pdfreduce.sh input.pdf output.pdf [mode] [dpi]
#
# mode : bw | gray | color
# dpi  : target resolution for images (e.g. 72, 150, 300, 600)
#
# Examples:
#   ./pdfreduce.sh scan.pdf out_bw.pdf bw 300
#   ./pdfreduce.sh notes.pdf out_gray.pdf gray 150
#   ./pdfreduce.sh book.pdf out_color.pdf color 200
#
# Notes:
# - bw   = 1-bit (bilevel) via ImageMagick then CCITT Fax in PDF
# - gray = try grayscale conversion; falls back to colour if device props fail
# - color = RGB/colour kept; images downsampled & re-encoded
# - You can set PDFSETTINGS=/screen or /ebook for fallback; JPEGQ=50–75 to tune quality

INPUT="$1"
OUTPUT="$2"
MODE=${3:-gray}
DPI=${4:-150}
GS=$(which gs)
GSCMD="env -u GS_OPTIONS $GS"

show_help() {
  sed -n '2,30p' "$0"
}

if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
  show_help
  exit 1
fi

case "$MODE" in
  bw)
    echo ">>> Converting input PDF to 1-bit monochrome temporary PDF..."
    TMPFILE=$(mktemp --suffix=.pdf)
    magick -density "$DPI" "$INPUT" -threshold 50% -colors 2 -type bilevel -monochrome "$TMPFILE"
    echo ">>> Compressing as B/W (1-bit) at ${DPI} dpi..."
    $GSCMD -o "$OUTPUT" -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.4 \
        -dDetectDuplicateImages=true \
        -dDownsampleMonoImages=true \
        -dMonoImageDownsampleType=/Bicubic -dMonoImageResolution=$DPI \
        -dMonoImageDownsampleThreshold=1.0 \
        -sMonoImageFilter=/CCITTFaxEncode \
        "$TMPFILE" \
      || $GSCMD -o "$OUTPUT" -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.4 -dPDFSETTINGS=${PDFSETTINGS:-/ebook} \
        -dDetectDuplicateImages=true -dAutoRotatePages=/None \
        "$TMPFILE"
    rm -f "$TMPFILE"
    ;;
  gray)
    echo ">>> Compressing as Grayscale at ${DPI} dpi..."
    $GSCMD -o "$OUTPUT" -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.4 \
        -dDetectDuplicateImages=true \
        -sColorConversionStrategy=Gray \
        -dDownsampleColorImages=true -dColorImageDownsampleType=/Bicubic -dColorImageResolution=$DPI -dColorImageDownsampleThreshold=1.0 \
        -dDownsampleGrayImages=true  -dGrayImageDownsampleType=/Bicubic  -dGrayImageResolution=$DPI  -dGrayImageDownsampleThreshold=1.0 \
        -dEncodeColorImages=true -dEncodeGrayImages=true -dJPEGQ=${JPEGQ:-60} \
        "$INPUT" \
      || $GSCMD -o "$OUTPUT" -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.4 -dPDFSETTINGS=${PDFSETTINGS:-/ebook} \
        -dDetectDuplicateImages=true -dAutoRotatePages=/None \
        "$INPUT"
    ;;
  color)
    echo ">>> Compressing as Colour at ${DPI} dpi..."
    $GSCMD -o "$OUTPUT" -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.4 \
        -dDetectDuplicateImages=true \
        -dDownsampleColorImages=true -dColorImageDownsampleType=/Bicubic -dColorImageResolution=$DPI -dColorImageDownsampleThreshold=1.0 \
        -dDownsampleGrayImages=true  -dGrayImageDownsampleType=/Bicubic  -dGrayImageResolution=$DPI  -dGrayImageDownsampleThreshold=1.0 \
        -dEncodeColorImages=true -dEncodeGrayImages=true -dJPEGQ=${JPEGQ:-60} \
        "$INPUT" \
      || $GSCMD -o "$OUTPUT" -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.4 -dPDFSETTINGS=${PDFSETTINGS:-/ebook} \
        -dDetectDuplicateImages=true -dAutoRotatePages=/None \
        "$INPUT"
    ;;
  *)
    echo "Invalid mode: $MODE"
    echo "Must be one of: bw | gray | color"
    exit 1
    ;;
esac

# gs	-q -dNOPAUSE -dBATCH -dSAFER \
# 	-sPAPERSIZE=a4 \
#   -sDEVICE=pdfwrite \
# 	-dCompatibilityLevel=1.3 \
# 	-dPDFSETTINGS=/screen \
# 	-dEmbedAllFonts=true \
# 	-dSubsetFonts=true \
# 	-dColorImageDownsampleType=/Bicubic \
# 	-dColorImageResolution=120 \
# 	-dGrayImageDownsampleType=/Bicubic \
# 	-dGrayImageResolution=120 \
# 	-dMonoImageDownsampleType=/Bicubic \
# 	-dMonoImageResolution=120 \
# 	-sOutputFile=out.pdf \
# 	 $1
