# -*- coding: utf-8 -*-
# pip install fastapi uvicorn

from uniparser.fastapi_ui import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
