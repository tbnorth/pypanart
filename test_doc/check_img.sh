# had to apply https://stackoverflow.com/a/52661288

mkdir -p test_images

# could do this in one step but results more consistent via PNG
convert -density 200 build/pdf/pypanart_test_doc.pdf \
  test_images/pypanart_test_doc.%02d.png
mogrify -flatten t/*
for i in t/pypanart_test_doc.??.png; do convert $i -compress none $i.pnm; done
sha1sum test_images/*pnm >test_images_hashes.txt
git diff test_images_hashes.txt

