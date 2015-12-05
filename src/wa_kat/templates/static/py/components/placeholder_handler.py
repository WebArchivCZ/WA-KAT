#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================


# Functions & classes =========================================================
class PlaceholderHandler(object):
    _dropdown_text = " Klikněte pro výběr."

    @staticmethod
    def set_placeholder_text(input_el, text):
        input_el.placeholder = text

    @staticmethod
    def get_placeholder_text(input_el):
        return input_el.placeholder

    @classmethod
    def set_placeholder_dropdown(cls, input_el):
        text = cls.get_placeholder_text(input_el)
        cls.set_placeholder_text(
            input_el=input_el,
            text=text + cls._dropdown_text
        )

    @classmethod
    def reset_placeholder_dropdown(cls, input_el):
        text = cls.get_placeholder_text(input_el)
        cls.set_placeholder_text(
            input_el=input_el,
            text=text.replace(cls._dropdown_text, "")
        )
