# -*- coding: utf-8 -*-
# pip install fastapi uvicorn aiofiles jinja2

from uniparser.fastapi_ui import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
