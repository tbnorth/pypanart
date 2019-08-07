## Build

```shell
docker build --build-arg PYVER=2 -t pypanart2 .
# and / or
docker build --build-arg PYVER=3 -t pypanart3 .
```
   
## Run

```shell
docker run --rm -it -e UID=`id -u` -e GID=`id -g` \
    -v /data/repo:/repo \
    -v /data/repo/pypanart/template:/data \
    pypanart2
```    

`/repo` should contain the `pypanart` repo. checked out to the
appropriate Python version (2 or 3).

