if [ "$UID" -a "$UID" -ne 0 ]; then
    echo $UID $GID
    groupadd --gid $GID puser
    # adduser --shell /bin/bash --uid $UID --gid $GID puser
    useradd --create-home --shell /bin/bash --uid $UID --gid $GID puser
    PHOME=/home/puser
else
    PHOME=/root
fi

cat >>$PHOME/.bashrc << EOT
export PATH=/miniconda/bin:$PATH
export PYTHONPATH=/repo/pypanart
source activate pypanart
cd /data/src || cd /data || cd
echo
echo python make.py list
EOT

if [ "$UID" -a "$UID" -ne 0 ]; then
    su puser -c bash
else
    bash
fi

