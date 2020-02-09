# -*- coding: utf-8 -*-

from .webui import app
from sys import argv


def main():
    try:
        port = int(argv[-1])
    except ValueError:
        port = 8080
    app.run(port=port)


if __name__ == "__main__":
    main()
