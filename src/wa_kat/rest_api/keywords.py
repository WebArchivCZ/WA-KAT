#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import bz2
import json
import os.path
from os.path import join

from bottle import get
from bottle import response

from shared import API_PATH
from shared import gzip_cache
from shared import RESPONSE_TYPE
from shared import to_gzipped_file


# Loaders =====================================================================
def read_kw_file():
    kw_list_path = join(
        os.path.dirname(__file__),
        "../templates/keyword_list.json.bz2"
    )

    with bz2.BZ2File(kw_list_path) as f:
        kw_list = f.read()

    return json.loads(kw_list)


# Variables ===================================================================
_INITIALIZED = False
KW_DICT = None
KEYWORDS = None
KW_CACHE_PATH = None


def init():
    global _INITIALIZED

    if _INITIALIZED:
        return

    global KW_DICT
    global KEYWORDS
    global KW_CACHE_PATH

    KW_LIST = read_kw_file()
    KW_DICT = {
        keyword_dict["zahlavi"].encode("utf-8"): keyword_dict
        for keyword_dict in KW_LIST
        if "zahlavi" in keyword_dict
    }
    KEYWORDS = [k.decode("utf-8") for k in sorted(KW_DICT.keys())]
    KEYWORDS_JSON = json.dumps(KEYWORDS)
    KW_CACHE_PATH = "/tmp/wa_kat_cache_keywords.json"

    # create cached files
    with open(KW_CACHE_PATH, "w") as f:
        f.write(KEYWORDS_JSON)
    with open(KW_CACHE_PATH + ".gz", "w") as f:
        to_gzipped_file(KEYWORDS_JSON, out=f)

    _INITIALIZED = True


init()


# Functions ===================================================================
def keyword_to_info(keyword):
    return KW_DICT.get(keyword)


# API =========================================================================
@get(join(API_PATH, "kw_list.json"))
def get_kw_list():
    response.content_type = RESPONSE_TYPE

    return gzip_cache(KW_CACHE_PATH)
