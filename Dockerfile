FROM ubuntu:22.04

RUN apt update && apt -y upgrade && apt install -y curl && apt clean

RUN curl -fsSL https://pixi.sh/install.sh | bash && mv /root/.pixi/bin/pixi /bin/pixi
RUN curl -fsSL https://gitlab.com/bits-n-bites/buildcache/-/releases/v0.28.7/downloads/buildcache-linux.tar.gz --output buildcache-linux.tar.gz \
 && tar xvzf buildcache-linux.tar.gz \
 && mv buildcache/bin/buildcache /usr/bin/

ADD pixi.toml pixi.toml
RUN pixi install

ADD .github .github
ADD ros.toml ros.toml
ADD helper.py helper.py

CMD ["/bin/bash"]
