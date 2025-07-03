FROM ghcr.io/kivy/buildozer:latest

USER root
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y libc6:i386 libncurses5:i386 libstdc++6:i386 zlib1g:i386
USER docker

WORKDIR /src