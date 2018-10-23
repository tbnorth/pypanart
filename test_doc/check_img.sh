# this script relies on real ImageMagick, doesn't work
# with the graphicsmajick wrappers
# had to apply https://stackoverflow.com/a/52661288

mkdir -p {test,comp,reference}_images

# could do this in one step but results more consistent via PNG
convert -density 200 build/pdf/pypanart_test_doc.pdf \
  test_images/pypanart_test_doc.%02d.png
mogrify -flatten test_images/*.png
mogrify -compress none -format ppm test_images/*.png
sha1sum test_images/*ppm >test_images_hashes.txt
# make less avoid paging for less than a page
LESS="-F -X $LESS" git diff test_images_hashes.txt
cat << EOT

# To compare reference and current images:

ls reference_images/*png | sed 's%.*/%%; s/.png$//' \
  | xargs -IF compare reference_images/F.png test_images/F.ppm comp_images/comp_F.png
feh comp_images/comp_*png

EOT
