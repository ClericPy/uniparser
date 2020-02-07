# -*- coding: utf-8 -*-

from .webui import app
from sys import argv

if __name__ == "__main__":
    try:
        port = int(argv[-1])
    except ValueError:
        port = 8080
    app.run(port=port)
