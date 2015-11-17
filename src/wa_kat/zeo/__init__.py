#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
from urlparse import urlparse
from collections import namedtuple
from collections import OrderedDict
from multiprocessing import Process

import transaction
from persistent import Persistent
from persistent.list import PersistentList
# from BTrees.OOBTree import OOSet  TODO: remove if not used

import requests

from zeo_connector import transaction_manager
from zeo_connector.examples import DatabaseHandler

from .. import analyzers
from ..settings import PROJECT_KEY
from ..settings import ZEO_CLIENT_PATH


# Variables ===================================================================
class PropertyInfo(namedtuple("PropertyInfo", ["name",
                                               "attr_type",
                                               "filler_func",
                                               "filler_params"])):
    """
    TODO: docstrings
    """


def get_req_mapping():
    REQ_MAPPING = [
        PropertyInfo(
            name="title_tags",
            attr_type=PersistentList,
            filler_func=analyzers.get_title_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="place_tags",
            attr_type=PersistentList,
            filler_func=analyzers.get_place_tags,
            filler_params=lambda self: self.domain,
        ),
        PropertyInfo(
            name="lang_tags",
            attr_type=PersistentList,
            filler_func=analyzers.get_lang_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="keyword_tags",
            attr_type=PersistentList,
            filler_func=analyzers.get_keyword_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="author_tags",
            attr_type=PersistentList,
            filler_func=analyzers.get_author_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="annotation_tags",
            attr_type=PersistentList,
            filler_func=analyzers.get_annotation_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="creation_dates",
            attr_type=PersistentList,
            filler_func=analyzers.get_creation_date_tags,
            filler_params=lambda self: (self.url, self.domain),
        ),
    ]

    return OrderedDict(
        (req.name, req)
        for req in REQ_MAPPING
    )


# Functions & classes =========================================================
class Request(Persistent):
    def __init__(self, url):
        self.url = url
        self.domain = urlparse(url).netloc
        self.index = None

        self._mapping = get_req_mapping()

        for req in self._mapping.values():
            setattr(self, req.name, req.attr_type)

    def _download(self, url):
        resp = requests.get(url)  # TODO: custom headers

        return resp.text.encode("utf-8")

    def paralel_download(self):
        self.index = self._download(self.url)

        def worker(url, property_info, params):
            db = RequestDatabase()
            req = db.get_request(url)

            with transaction.manager:
                setattr(
                    req,
                    property_info.name,
                    property_info.filler_func(*params)
                )

        for pi in self._mapping:
            Process(worker, [self.url, pi, pi.filler_params(self)])


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
        req = Request(url=url)
        self.requests[url] = req

        return req
