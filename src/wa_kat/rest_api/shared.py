#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import os
import gzip
import time
import os.path
import StringIO

from bottle import request
from bottle import response
from bottle import parse_date
from bottle import HTTPResponse


# Variables ===================================================================
API_PATH = "/api_v1/"
RESPONSE_TYPE = "application/json; charset=utf-8"


# Functions ===================================================================
def gzipped(fn):
    def gzipped_wrapper(*args, **kwargs):
        accepted_encoding = request.get_header("Accept-Encoding")

        if not accepted_encoding or "gzip" not in accepted_encoding:
            return fn(*args, **kwargs)

        response.set_header("Content-Encoding", "gzip")

        out = StringIO.StringIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(
                fn(*args, **kwargs)
            )

        out.seek(0)
        return out

    return gzipped_wrapper


def gzip_cache(path):
    accept_enc = request.get_header("Accept-Encoding")

    if accept_enc and "gzip" in accept_enc and os.path.exists(path + ".gz"):
        path = path + ".gz"
        response.set_header("Content-Encoding", "gzip")

    headers = dict()
    stats = os.stat(path)
    headers['Content-Length'] = stats.st_size
    headers['Last-Modified'] = time.strftime(
        "%a, %d %b %Y %H:%M:%S GMT",
        time.gmtime(stats.st_mtime)
    )

    modified_since = request.environ.get('HTTP_IF_MODIFIED_SINCE')
    if modified_since:
        modified_since = parse_date(modified_since.split(";")[0].strip())

    if modified_since is not None and modified_since >= int(stats.st_mtime):
        headers['Date'] = time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT",
            time.gmtime()
        )
        return HTTPResponse(status=304, **headers)

    return open(path)
