#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import json
import base64
import traceback
from os.path import join

import requests  # for requests.exceptions.Timeout
from bottle import get
from bottle import post
from bottle import response
from bottle import HTTPError
from bottle_rest import form_to_params

from .. import settings
from ..zeo import RequestDatabase
from ..zeo import ConspectDatabase
from ..connectors import aleph

from shared import API_PATH
from shared import RESPONSE_TYPE

from to_marc import to_marc
from keywords import get_kw_list


# Functions & classes =========================================================
@post(join(API_PATH, "analyze"))
@form_to_params
def get_result(url):
    rd = RequestDatabase()
    response.content_type = RESPONSE_TYPE

    # handle cacheing
    try:
        ri = rd.get_request(url)

        if ri.is_old():
            print "Running the analysis"  #: TODO: to log

            # forget the old one and create new request info - this prevents
            # conflict errors
            ri = rd.get_request(url, new=True)

            # run the processing
            ri.paralel_processing()

    except (requests.exceptions.Timeout, requests.ConnectionError):
        error_msg = """
            Požadovanou stránku {url} nebylo možné stáhnout během {timeout}
            vteřin. Zkuste URL zadat s `www.`, či zkontrolovat funkčnost
            stránek.
        """
        error_msg = error_msg.format(url=url, timeout=settings.REQUEST_TIMEOUT)

        return {
            "status": False,
            "log": ri.get_log(),
            "error": error_msg,
        }
    except Exception as e:
        return {
            "status": False,
            "log": ri.get_log(),
            "error": str(e.message) + "\n" + traceback.format_exc().strip()
        }

    return {
        "status": True,
        "body": ri.to_dict(),
        "log": ri.get_log(),
        "conspect_dict": ConspectDatabase().data,
    }


@get(join(API_PATH, "conspect"))
def get_conspect():
    cd = ConspectDatabase()
    response.content_type = RESPONSE_TYPE

    return json.dumps(cd.data)


@post(join(API_PATH, "aleph"))
@form_to_params
def get_aleph_info(issn):
    results = list(aleph.by_issn(issn))

    return [
        result.get_mapping()
        for result in results
    ]


@post(join(API_PATH, "as_file/<fn:path>"))
@form_to_params
def download_as_file(fn, data=None):
    if data is None:
        raise HTTPError(
            500,
            "This service require base64 encoded POST `data` parameter."
        )

    dec_data = base64.b64decode(data)

    response.set_header("Content-Type", "application/octet-stream")
    response.set_header(
        "Content-Disposition",
        'attachment; filename="%s"' % fn
    )

    return dec_data
