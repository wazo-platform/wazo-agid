Dockerfile for XiVO agid

## Install Docker

To install docker on Linux :

    curl -sL https://get.docker.io/ | sh
 
 or
 
     wget -qO- https://get.docker.io/ | sh

## Build

To build the image, simply invoke

    docker build -t xivo-agid github.com/xivo-pbx/xivo-agid

Or directly in the sources in contribs/docker

    docker build -t xivo-agid .
  
## Usage

To run the container, do the following:

    docker run -d -v /conf/agid:/etc/xivo/agid/conf.d -p 4573:4573 xivo-agid

On interactive mode :

    docker run -v /conf/agid:/etc/xivo/agid/conf.d -p 4573:4573 -it xivo-agid bash

After launch xivo-agid.

    xivo-agid -f -d

## Infos

- Using docker version 1.5.0 (from get.docker.io) on ubuntu 14.04.
- If you want to using a simple webi to administrate docker use : https://github.com/crosbymichael/dockerui

To get the IP of your container use :

    docker ps -a
    docker inspect <container_id> | grep IPAddress | awk -F\" '{print $4}'
