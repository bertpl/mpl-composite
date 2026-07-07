#! /bin/sh
# ---------------------------------------------
# Input:  ./images/splash/*
# Output: ./images/splash_with_version.webp
#
# Two-stage: the version-independent base (tagline + attribution) is built once
# and committed (./images/splash/_splash_without_version.png); each invocation
# only stamps the version onto that base. Run locally at release time — CI has
# no ImageMagick dependency.
# ---------------------------------------------

# --- check imagemagick version ---
echo "------ ImageMagick version info --------------------------------------------"
magick identify -version
echo "----------------------------------------------------------------------------"

# --- argument handling ---
DISPLAY_VERSION="$1"  # e.g. "v0.1.10" or "v0.1.11-dev"

# --- create splash without version info (cached: committed once, reused) ---
if [ ! -f ./images/splash/_splash_without_version.png ]; then
  echo "Building version-independent splash base..."
  magick -pointsize 36 -font "./images/splash/google_fonts_montserrat_italic.ttf" "./images/splash/splash_grey.png" -gravity SouthWest -fill "#dddddd" -annotate +10+5 "DiffusionBee 2.5.3 (FLUX.1-dev + Real-ESRGAN)" "./images/temp.mpc"
  magick -pointsize 64 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/temp.mpc" -gravity South -fill "#000000" -annotate +3+22 "Matplotlib wrapper for composite figure building." "./images/temp.mpc"
  magick -pointsize 64 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/temp.mpc" -gravity South -fill "#eeeeee" -annotate +0+25 "Matplotlib wrapper for composite figure building." "./images/splash/_splash_without_version.png"
fi

# --- add version info ---
echo "Adding version info..."
magick -pointsize 128 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/splash/_splash_without_version.png" -gravity East -fill "black" -annotate +997+303 "${DISPLAY_VERSION}" "./images/temp.mpc"
magick -pointsize 128 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/temp.mpc" -gravity East -fill "white" -annotate +1000+300 "${DISPLAY_VERSION}" -quality 95 -define webp:lossless=false "./images/splash_with_version.webp"

# --- clean up ---
echo "Cleaning up..."
rm -f ./images/*.mpc
rm -f ./images/*.cache
