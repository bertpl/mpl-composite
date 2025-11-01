#! /bin/sh
# ---------------------------------------------
# Input:  ./images/splash/*
# Output: ./images/splash_with_version.webp
# ---------------------------------------------

# --- check imagemagick version ---
echo "------ ImageMagick version info --------------------------------------------"
magick identify -version
echo "----------------------------------------------------------------------------"

# --- create splash ---
echo "Adding text & version info..."
magick -pointsize 36 -font "./images/splash/google_fonts_montserrat_italic.ttf" "./images/splash/splash_grey.png" -gravity SouthWest -fill "#dddddd" -annotate +10+5 "DiffusionBee 2.5.3 (FLUX.1-dev + Real-ESRGAN)" "./images/temp.mpc"
magick -pointsize 64 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/temp.mpc" -gravity South -fill "#000000" -annotate +3+22 "Matplotlib wrapper for composite figure building." "./images/temp.mpc"
magick -pointsize 64 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/temp.mpc" -gravity South -fill "#eeeeee" -annotate +0+25 "Matplotlib wrapper for composite figure building." "./images/temp.mpc"
magick -pointsize 128 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/temp.mpc" -gravity East -fill "black" -annotate +997+303 "v$(uv version --short)" "./images/temp.mpc"
magick -pointsize 128 -font "./images/splash/google_fonts_montserrat_bold.ttf" "./images/temp.mpc" -gravity East -fill "white" -annotate +1000+300 "v$(uv version --short)" -quality 95 -define webp:lossless=false "./images/splash_with_version.webp"

# --- clean up ---
echo "Cleaning up..."
rm ./images/*.mpc
rm ./images/*.cache
