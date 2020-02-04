##############################################################################################
# Purpose   : Docker image of PSS to SDP SEND method
# Python    : 3.6
# Version   : 1.1
# Author    : Benjamin Shaw (benjamin.shaw@manchester.ac.uk)
##############################################################################################

# Import spead2 image
FROM pulsarben/pss2sdp-spead2:latest

# Set labels
LABEL maintainer="Benjamin Shaw"
LABEL description="This dockerfile implements the spead2 UDP data transfer library for SEND"

# Install inotify for the watcher.
# We may not need this in the end 
# but it's useful for demostrating 
# that this works
RUN pip3 install --no-cache-dir inotify

# Set the name of and create the directory
# in which the sender will live
WORKDIR /home/pss2sdp/send

# Add send and watch codes
# and test file to images
COPY send.py /home/pss2sdp/send
COPY test.spccl /home/pss2sdp/send

# Create dir to watch
RUN mkdir -p /home/pss2sdp/send/data

# Open the right port through which to 
# send UDP traffic
EXPOSE 9021/udp

# Set commands that will run when 
# the container starts
ENTRYPOINT ["/usr/bin/python3"]
CMD ["./send.py","-f", "test.spccl", "-d", "pss-receive"]


