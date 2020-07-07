# -*- coding: utf-8 -*-

from sys import argv


def main():
    try:
        port = int(argv[-1])
    except ValueError:
        port = 8080
    try:
        from .fastapi_ui import app
        from uvicorn import run
        run(app, port=port)
    except ImportError:
        from .webui import app
        app.run(port=port)


if __name__ == "__main__":
    main()
