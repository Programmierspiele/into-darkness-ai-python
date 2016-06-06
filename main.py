#!/bin/python

import sys
from ai.ai import AI
from renderer.ui import ui as ui
from ai.log import log as log
from threading import Thread
import time
import errno
from socket import error as socket_error
from renderer.renderer import Renderer

renderer = Renderer()

def main():
    amount_of_ais = int(sys.argv[1])
    host = sys.argv[2]
    port = int(sys.argv[3])
    while True:
        ais = []
        try:
            for i in range(amount_of_ais):
                ais.append(AI("The Machine Thread", i+1, renderer, host, port))

            for ai in ais:
                ai.join()
        except socket_error as serr:
            for ai in ais:
                ai.stop()
            log("Retry in 3s.")
            time.sleep(3)

if len(sys.argv) == 4:
    t = Thread(target=main)
    t.setDaemon(True)
    t.start()
    ui(renderer)
else:
    print("Usage: python main.py <ai_count> <host> <port>")
