#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import time
from urlparse import urlparse
from collections import namedtuple
from collections import OrderedDict
from multiprocessing import Process

import requests
from persistent import Persistent
from zeo_connector import transaction_manager
from backports.functools_lru_cache import lru_cache

from .. import analyzers
from worker import worker


# Functions & classes =========================================================
@lru_cache()
def _get_req_mapping():
    REQ_MAPPING = [
        PropertyInfo(
            name="title_tags",
            filler_func=analyzers.get_title_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="place_tags",
            filler_func=analyzers.get_place_tags,
            filler_params=lambda self: self.domain,
        ),
        PropertyInfo(
            name="lang_tags",
            filler_func=analyzers.get_lang_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="keyword_tags",
            filler_func=analyzers.get_keyword_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="author_tags",
            filler_func=analyzers.get_author_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="annotation_tags",
            filler_func=analyzers.get_annotation_tags,
            filler_params=lambda self: self.index,
        ),
        PropertyInfo(
            name="creation_dates",
            filler_func=analyzers.get_creation_date_tags,
            filler_params=lambda self: (self.url, self.domain),
        ),
    ]

    return OrderedDict(
        (req.name, req)
        for req in REQ_MAPPING
    )


class PropertyInfo(namedtuple("PropertyInfo", ["name",
                                               "filler_func",
                                               "filler_params"])):
    """
    TODO: docstrings
    """


class RequestInfo(Persistent):
    def __init__(self, url):
        self.url = url
        self.domain = urlparse(url).netloc
        self.index = None

        # time trackers
        self.creation_ts = time.time()
        self.downloaded_ts = None
        self.processing_started_ts = None
        self.processing_ended_ts = None

        for req in _get_req_mapping().values():
            setattr(self, req.name, None)

    def _download(self, url):
        resp = requests.get(url)  # TODO: custom headers

        return resp.text.encode("utf-8")

    @transaction_manager
    def paralel_processing(self):
        self.index = self._download(self.url)
        self.downloaded_ts = time.time()
        self.processing_started_ts = time.time()

        # launch all workers as paralel processes
        for pi in _get_req_mapping().values():
            p = Process(
                target=worker,
                args=[self.url, pi, pi.filler_params(self)]
            )
            p.start()

    def _set_properties(self):
        mapping_set = set(_get_req_mapping().keys())

        return set(
            property_name
            for property_name in mapping_set
            if getattr(self, property_name) is not None
        )

    def progress(self):
        return len(self._set_properties()), len(_get_req_mapping())

    def is_all_set(self):
        return self._set_properties() == set(_get_req_mapping().keys())

    def to_dict(self):
        return {
            "all_set": self.is_all_set(),
            "progress": self.progress(),
            "values": {
                property_name: [
                    tag.to_dict()
                    for tag in getattr(self, property_name)
                ]
                for property_name in _get_req_mapping().keys()
            }
        }
