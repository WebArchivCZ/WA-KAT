#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
from browser import document


# Functions & classes =========================================================
class ErrorBox(object):
    def __init__(self, tag_id, whole_tag_id):
        self.tag = document[tag_id]
        self.whole_tag = document[whole_tag_id]

    def show(self, msg):
        self.tag.innerHTML = msg
        self.whole_tag.style.display = "block"

    def hide(self):
        self.whole_tag.style.display = "none"

    def reset(self):
        self.hide()
        self.tag.innerHTML = ""


UrlBoxError = ErrorBox("urlbox_error", "whole_urlbox_error")
ISSNBoxError = ErrorBox("issnbox_error", "whole_issnbox_error")
