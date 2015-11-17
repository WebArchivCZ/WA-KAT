#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
from zeo_connector import transaction_manager
from zeo_connector.examples import DatabaseHandler

from ..settings import PROJECT_KEY
from ..settings import ZEO_CLIENT_PATH

from request_info import RequestInfo


# Variables ===================================================================
DAY = 60 * 60 * 24
YEAR = DAY * 356


# Functions & classes =========================================================
class RequestDatabase(DatabaseHandler):
    def __init__(self, conf_path=ZEO_CLIENT_PATH, project_key=PROJECT_KEY):
        super(self.__class__, self).__init__(
            conf_path=conf_path,
            project_key=project_key
        )

        self.request_key = "requests"
        self.requests = self._get_key_or_create(self.request_key)

    @transaction_manager
    def get_request(self, url):
        req = self.requests.get(url, None)

        # return already stored requests
        if url:
            return req

        # if not found, create new
        req = RequestInfo(url=url)
        self.requests[url] = req

        return req

    def garbage_collection(self, time_limit=YEAR/2.0):
        pass
