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
from functools import total_ordering

import requests
from persistent import Persistent
from zeo_connector import transaction_manager
from backports.functools_lru_cache import lru_cache

from .. import analyzers
from worker import worker


# Functions & classes =========================================================
class PropertyInfo(namedtuple("PropertyInfo", ["name",
                                               "filler_func",
                                               "filler_params"])):
    """
    This class is used to join one function (:attr:`filler_func`) from
    :mod:`.analyzers` with its parameters (:attr:`filler_params`) and to say,
    where it should be stored (:attr:`name`).

    Example::

        PropertyInfo(
            name="title_tags",
            filler_func=analyzers.get_title_tags,
            filler_params=lambda self: self.index,
        )

    Attributes:
        name (str): Name of the property, where the data should be stored.
        filler_func (fn ref): Reference to function, which will be called.
        filler_params (lambda self:): Lambda function, which returns the
            parameters for :attr:`filler_func`. Function takes one parameter,
            which contains the reference to :class:`.PropertyInfo` object in
            which the result is stored.
    """


@lru_cache()
def _get_req_mapping():
    """
    This function serves as joiner for functions from :mod:`analyzers`, to map
    them to properties, which will be stored in :class:`.RequestInfo` database
    object.

    I've decided to do it this way, because it will allow paralel processing
    of the properties/functions and also all configuration is at one place,
    instead of multiple places in object properties / methods and so on.

    Returns:
        OrderedDict: with :class:`.PropertyInfo` objects.
    """
    REQ_MAPPING = [
        PropertyInfo(
            name="title_tags",
            filler_func=analyzers.get_title_tags,
            filler_params=lambda self: [self.index],
        ),
        PropertyInfo(
            name="place_tags",
            filler_func=analyzers.get_place_tags,
            filler_params=lambda self: [self.domain],
        ),
        PropertyInfo(
            name="lang_tags",
            filler_func=analyzers.get_lang_tags,
            filler_params=lambda self: [self.index],
        ),
        PropertyInfo(
            name="keyword_tags",
            filler_func=analyzers.get_keyword_tags,
            filler_params=lambda self: [self.index],
        ),
        PropertyInfo(
            name="author_tags",
            filler_func=analyzers.get_author_tags,
            filler_params=lambda self: [self.index],
        ),
        PropertyInfo(
            name="annotation_tags",
            filler_func=analyzers.get_annotation_tags,
            filler_params=lambda self: [self.index],
        ),
        PropertyInfo(
            name="creation_dates",
            filler_func=analyzers.get_creation_date_tags,
            filler_params=lambda self: (self.url, self.domain),
        ),
    ]

    # construct the OrderedDict - I want the order preserved
    return OrderedDict(
        (req.name, req)
        for req in REQ_MAPPING
    )


@total_ordering
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
                    for tag in getattr(self, property_name) or []
                ]
                for property_name in _get_req_mapping().keys()
            }
        }

    def __eq__(self, obj):
        if not isinstance(obj, RequestInfo):
            return False

        return self.url == obj.url

    def __lt__(self, obj):
        return float(self.creation_ts).__lt__(obj.creation_ts)
