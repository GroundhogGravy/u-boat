#! /usr/bin/env python3

import os
import sys
import random

interface = sys.argv[1]

mac_addr = "02:00:00:%02x:%02x:%02x" % (random.randint(0, 255),
                                        random.randint(0, 255),
                                        random.randint(0, 255))

os.system("ifconfig %s lladdr %s" % (interface, mac_addr))
