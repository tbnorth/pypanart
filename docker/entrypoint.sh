echo $UID $GID
groupadd --gid $GID puser
# adduser --shell /bin/bash --uid $UID --gid $GID puser
useradd --create-home --shell /bin/bash --uid $UID --gid $GID puser

cat >>/home/puser/.bashrc << EOT
export PATH=/miniconda/bin:$PATH
export PYTHONPATH=/repo/pypanart
source activate pypanart
cd /data/src || cd /data || cd
echo
echo python make.py list
EOT

su puser -c bash

