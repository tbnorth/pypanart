FROM thomasweise/docker-texlive-full
# 1.5 Gb, big download

COPY requirements.conda.txt requirements.pip.txt ./

SHELL ["/bin/bash", "-c"]

RUN apt-get update &&\
    apt-get install -y gcc inkscape git &&\
    # gcc needed by pip
    # git and inkscape needed by pypanart
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O ~/miniconda.sh &&\
    bash ~/miniconda.sh -b -p ~/miniconda &&\
    rm ~/miniconda.sh &&\
    echo 'export PATH=~/miniconda/bin:$PATH' >>~/.bashrc &&\
    PATH=~/miniconda/bin:$PATH &&\
    conda update conda &&\
    conda create --yes --name pypanart -c conda-forge 'python<3' &&\
    PATH=~/miniconda/bin:$PATH &&\
    source activate pypanart &&\
    grep -v '#' requirements.conda.txt | xargs conda install -c conda-forge &&\
    pip install -r requirements.pip.txt

# USER root
# COPY entrypoint.sh /root/
# RUN chmod +x /root/entrypoint.sh
# ENTRYPOINT ["/root/entrypoint.sh"]

# ARG USER_ID
# ARG GROUP_ID

# RUN apt-get update \
#  && apt-get install -y inkscape texlive-xetex texlive-luatex \
#                        texlive-math-extra 
#  && useradd -ms /bin/bash n3muser \
#  && ln -sTf /bin/bash /bin/sh

# screen nano git gcc wget bzip2

# USER n3muser
# USER root
# # build image for specific USER/GROUP_ID to avoid slow usermod later
# RUN usermod -u $USER_ID n3muser \
#  && groupmod -g $GROUP_ID n3muser
# USER n3muser
# WORKDIR /home/n3muser
# RUN chown -R $USER_ID:$GROUP_ID /home/n3muser
# USER $USER_ID:$GROUP_ID
# ENV HOME=/home/n3muser
# RUN conda create --name n3m python=2.7

# COPY requirements.conda.txt requirements.pip.txt ./

# RUN conda update conda \
#  && source activate n3m \
#  && xargs conda install -c conda-forge < requirements.conda.txt \
#  && pip install -r requirements.pip.txt

# USER root
# COPY entrypoint.sh /root/
# RUN chmod +x /root/entrypoint.sh
# ENTRYPOINT ["/root/entrypoint.sh"]

