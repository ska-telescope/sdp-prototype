#/usr/bin/python

from __future__ import print_function
import argparse
import logging
import os
import spead2.recv
import spead2

# pylint: disable=C0116,W1202,R0201

# A module to receive data over UDP using the spead2 data exchange protocol
#
# Author: Benjamin Shaw
# Email : benjamin.shaw@manchester.ac.uk


class UdpReceive():

    """
    **************************************************************************

                            Pulsar search data receiver

    **************************************************************************

    :param debug:       Flag to determine what is done with the received data.
                        If True, data will be printed to console, else it will
                        be written to a file on the disk
                        (type=bool).

    :return:            None

    **Description:**

    The module that listens on a port for incoming
    streams of data on UDP, reads
    metadata and constructs a file on disk
    comprising the data

    Data is received as "heaps"

    A heap contains all of the "item groups" and is received over the network
    using whatever transport mechanism we decide - in this case UDP.
    In time a decision will be made on the exact transport mechanism we will
    eventually use (e.g., RDMA). I'm not sure yet if RDMA is supported by
    spead2.

    The buffer size is configurable in the class "spead2.send.UdpStream".
    This is currently set to 10000 (MB?)

    The receive method below receives heaps and each heap is
    deconstructed into item groups. Item groups may comprise a piece
    of metadata or a line from the file that was sent by SEND.
    The module reads the metadata itemgroups from which it learns the
    unique ID of the file that was sent, its name, size and the
    number of line in contained.

    If debug mode is off then the receive will create a file with the filename
    extracted from the metadata and then read the itemgroups that correspond
    to lines in the file. It will then write these lines to the file.
    The hope is that the written file will be identical to the file
    that was sent!

    If debug mode is off then the data received will simply be written
    to the console. This is the best method if the container is running
    as part of a K8s ensemble as logs can be extracted using docker logs
    rather than trying to write a log file somewhere.

    ************************************************************************
    Author: Benjamin Shaw

    Email : benjamin.shaw@manchester.ac.uk

    Web   : http://www.benjaminshaw.me.uk

    ************************************************************************

    **Running the code:**

    The constructor of the module looks to see if we're in
    debug mode and sets up the parameters of
    the stream. The "receive" then gets the heap(s)
    from the incoming stream, unpacks them into
    itemgroups, extracts the metadata and does what
    it will with the data - either write it to a
    file or to the console. At the moment this is
    set up to receive a spccl file as a single heap.

    Import the code by running

      ``from receive import udp_receive``

    if running within other modules or run

      ``python receive.py``

    if running as a standalone package.

    The code broadly does the following


       * Receives a heap
       * Creates an empty itemgroup into which the contents of the the
         heap willbe unpacked
       * Checks for metadata in the heap - looking for specific identifiers
         that tell it what each itemgroup contains (metadata)
       * Checks one of these identifiers is a filename. If not the stream will
         be ignored
       * Goes through the item groups looking for the
         contents of the file and writes them to a new file

    *************************************************************************
"""

    def __init__(self, debug=False):

        self.thread_pool = spead2.ThreadPool()
        self.stream = spead2.recv.Stream(self.thread_pool)
        self.pool = spead2.MemoryPool(16384, 26214400, 12, 8)
        self.debug = debug
        self.metadata = None

        self.stream.set_memory_allocator(self.pool)
        self.stream.add_udp_reader(9021, max_size=10000, buffer_size=10000)

        if self.debug:
            logging.basicConfig(level=logging.DEBUG,
                                format='%(levelname)s %(asctime)s %(message)s')
        else:
            logging.basicConfig(filename='receive.log',
                                level=logging.DEBUG,
                                format='%(levelname)s %(asctime)s %(message)s')

    def is_file(self, values):
        metadata = {}
        for item in values:
            line = bytearray(item.value).decode("utf-8").strip()
            if "identifier" in item.name:
                metadata['identifier'] = line
            if "filename" in item.name:
                metadata['filename'] = line
            if "nbytes" in item.name:
                metadata['nbytes'] = line
            if "nlines" in item.name:
                metadata['nlines'] = line
        return metadata

    def do_log(self):
        '''
        Parameterless function that writes the
        metadata that we are receiving to a log
        file. This probably doesn't conform
        to standard logging procedure but we
        can modify this at a later stage

        :params: None
        :return: None
        '''

        ident = self.metadata['identifier']
        name = self.metadata['filename']
        nbytes = self.metadata['nbytes']
        nlines = self.metadata['nlines']

        logging.info("Received stream with id={}, name={}".format(ident, name))
        logging.info("Received stream with id={}, nbytes={}".format(ident, nbytes))
        logging.info("Received stream with id={}, nlines={}".format(ident, nlines))

    def receive(self):
        print("Listening on port 9021..")
        for heap in self.stream:

            outdir = "output"
            if not os.path.exists(outdir):
                os.mkdir(outdir)

            # Create empty item group to receive from heap
            item_group = spead2.ItemGroup()

            # Update item group with contents of new heap
            item_group.update(heap)

            # Check for a filename + metadata
            self.metadata = self.is_file(item_group.values())

            # Check we have a filename, ignore the stream (for now) if not
            try:
                self.metadata['filename']
            except KeyError:
                logging.warning("No filename for stream with id={}".format(self.metadata['identifier']))
                continue

            # Log stream metadata
            self.do_log()

            # Unpack file contents from item group
            output_filename = "output/" + self.metadata['filename']
            # with open(self.metadata['filename'], 'a') as outfile:
            with open(output_filename, 'a') as outfile:

                for item in item_group.values():
                    line = bytearray(item.value).decode("utf-8").strip()
                    if "dataline" in item.name:
                        outfile.write(line + "\n")
                        print(item.name, line)


def main():
    parser = argparse.ArgumentParser(description='Receives files over UDP')
    parser.add_argument('-d', '--debug',
                        help='Enable debug mode',
                        required=False,
                        action='store_true')
    args = parser.parse_args()

    receiver = UdpReceive(args.debug)
    receiver.receive()

if __name__ == '__main__':
    main()
