#!/usr/bin/env python3

import logging
import argparse
import random
import string
import os
import numpy as np
import spead2
import spead2.send

# pylint: disable=C0116,W1202

# A module to send a file over UDP using the spead2 data exchange protocol
#
# Author: Benjamin Shaw
# Email : benjamin.shaw@manchester.ac.uk


class UdpSend():

    """
    **************************************************************************

                            Pulsar search data sender

    **************************************************************************

    :param this_file:   Path to file we wish to send
                        (type=str).

    :return:            None

    **Description:**

    The module reads a file into memory and decomposes the contents into
    numpy arrays.

    These arrays are then packaged into "item groups".

    A "heap" containing all of the item groups is sent over the network using
    whatever transport mechanism we decide - in this case UDP. In time a
    decision will be made on the exact transport mechanism we will
    eventually use (e.g., RDMA). I'm not sure yet if RDMA is
    supported by spead2.

    The buffer size is configurable in the class "spead2.send.UdpStream".
    This is currently set to 2000 (MB?)

    The send method below also grabs some metadata that can be sent as
    separate item groups to the contents of the file that we are sending.
    At the moment I assign a unique file identifier to the stream so
    that the file is traceable when received. I also extract the file size,
    the number of lines and the file name so that it can be rebuilt at the
    other end. These data are logged using the "logging" package.

    Each peice of metadata (e.g., the file ID, file name etc) is packaged
    as one item group. Each line in the file we are sending* is also
    packaged as one item group. The whole lot is then compiled into
    a heap and the heap is sent

    * The file we are sending at the moment is a pulsar search candidate file
    which is simply a text file containing the details of each single pulse
    candidate associated with a particular filterbank file.


    ************************************************************************
    Author: Benjamin Shaw

    Email : benjamin.shaw@manchester.ac.uk

    ************************************************************************

    **Running the code:**

    The constructor of the module takes in file and sets up the parameters of
    the stream. The "send method" then checks the file exists, extracts the
    metadata, packages up the item groups as described above and then sends
    the lot as a single heap.

    Import the code by running

      ``from send import udp_send``

    if running within other modules or run

      ``python send.py -f <file to send>

    if running as a standalone package.

    The code broadly does the following


       * Checks the file we want to send exists. Exits if not
       * Generates a 16 character random string to identify the stream
         and casts this as an item group
       * Get the filename and casts this as an item group
       * Gets the size of the file and casts this as an item group
       * Gets the number of lines in the file and casts this as an item group
       * Goes through the file and casts each individual line as an item group
       * Forms the itemgroups into a single heap
       * Sends the heap over UDP on port 9012 (randomly chosen - we could have
         this as an argument of the module)

    Logging it set to debug mode. It will print the logs to the console (for
    better compatibility with K8s)

    *************************************************************************
"""

    def __init__(self, this_file, destination='127.0.0.1'):

        self.this_file = this_file
        self.destination = destination
        self.this_id = None

        # Construct a thread pool and start the threads.
        self.thread_pool = spead2.ThreadPool()
        # Configure the stream
        self.stream_config = spead2.send.StreamConfig()
        # Set up UDP stream (Port 9021, max buffer size=2000 MB?)
        self.stream = spead2.send.UdpStream(self.thread_pool,
                                            self.destination,
                                            9021,
                                            self.stream_config,
                                            2000)

        # Enable logging to console (rather than a file)
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s %(asctime)s %(message)s')

    @staticmethod
    def check_file_exists(cfile):
        """
        Takes in the path to a file and
        checks that the file exists on the file
        system

        :param cfile:   Name of the file we are checking exists
                        (type=str)

        :return:        Outcome. True is file exists
                        Else false
                        (type=bool)

        """
        outcome = True
        if not os.path.isfile(cfile):
            outcome = False
        return outcome

    @staticmethod
    def id_gen():
        """
        Generates a random 16 character string comprising letters and numbers

        :return:    16 character string
                    (type=str)
        """
        idstring = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)])
        return idstring

    @staticmethod
    def get_filesize(cfile):
        """
        Gets size of file (in bytes)

        :param cfile: Filename
                      (type=str)

        :return:      Size of file (in bytes)
                      (type=str)
        """
        nbytes = str(os.path.getsize(cfile))
        return nbytes

    def send(self):
        if self.check_file_exists(self.this_file):
            pass
        else:
            raise OSError("No such file as {}".format(self.this_file))

        # Create item group to hold all our items
        item_group = spead2.send.ItemGroup()

        # Get a unique identifier for the file we are sending
        self.this_id = self.id_gen()
        item_group.add_item(None, name='identifier',
                            description='Unique tranfer ID',
                            shape=(len(self.this_id),),
                            dtype=np.byte,
                            value=bytearray(self.this_id, 'UTF8'))

        # Add the file name as an item
        filename = os.path.basename(self.this_file)
        item_group.add_item(None, name='filename', description="Filename",
                            shape=(len(filename),),
                            dtype=np.byte,
                            value=bytearray(filename, 'UTF8'))

        # Add the filesize as an item
        nbytes = self.get_filesize(self.this_file)
        item_group.add_item(None, name='nbytes',
                            description="File size (bytes)",
                            shape=(len(nbytes),),
                            dtype=np.byte,
                            value=bytearray(nbytes, 'UTF8'))

        # Open file we're going to send
        with open(self.this_file) as infile:
            lines = infile.readlines()

        # Add the number of lines we're sending as an itemgroup
        length = str(len(lines))
        item_group.add_item(None, name='nlines', description="Number of lines",
                            shape=(len(length),), dtype=np.byte,
                            value=bytearray(length, 'UTF8'))

        # Each line in the file is an item
        # Add each item to the item group
        line_number = 1
        for line in lines:
            item_group.add_item(None, "dataline {}".format(line_number),
                                "line",
                                shape=(len(line),),
                                dtype=np.byte,
                                value=bytearray(line, 'UTF8'))
            line_number = line_number + 1

        # For item group into a heap
        heap = item_group.get_heap()

        # Send heap
        self.stream.send_heap(heap)
        logging.info("Start of stream")
        logging.info("Sending stream with id={}, name={}".format(self.this_id, filename))
        logging.info("Sending stream with id={}, nbytes={}".format(self.this_id, nbytes))
        logging.info("Sending stream with id={}, nlines={}".format(self.this_id, length))
        logging.info("End of stream")

        # Send "I've finished"
        self.stream.send_heap(item_group.get_end())

        print("File {} sent".format(self.this_file))

def main():
    parser = argparse.ArgumentParser(description='Sends files over UDP')
    parser.add_argument('-f', '--file', help='File to send', required=True)
    parser.add_argument('-d', '--destination',
                        help='Hostname of receiver (default=127.0.0.1)',
                        required=False,
                        default='127.0.0.1')
    args = parser.parse_args()

    sender = UdpSend(args.file, args.destination)
    sender.send()

if __name__ == '__main__':
    main()
