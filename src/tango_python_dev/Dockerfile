FROM ubuntu:18.04
LABEL maintainer="Benjmain Mort <ben.mort@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install tango development packages
RUN apt-get update && apt-get install -y \
        python3 \
        python3-pytango \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Create unprivaliged ska user
RUN useradd -ms /bin/bash orca
USER orca
WORKDIR /home/orca

ENTRYPOINT ["/bin/bash"]
CMD []
