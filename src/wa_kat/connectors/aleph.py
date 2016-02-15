#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
from collections import namedtuple

from remove_hairs import remove_hairs
from marcxml_parser import MARCXMLRecord
from edeposit.amqp.aleph import aleph

from ..data_model import Model
from ..analyzers.source_string import SourceString


# Functions & classes =========================================================
def _first_or_none(array):
    """
    Pick first item from `array`, or return `None`, if there is none.
    """
    if not array:
        return None

    return array[0]


def _add_source(model):
    """
    Go over all attributes in `model` and add :class:`SourceString` to them.

    Args:
        model (obj): :class:`Model` instance.

    Returns:
        obj: :class:`Model` instance with :class:`SourceString` descriptors.
    """
    # convert all values to source strings
    source = "Aleph"
    for key, val in model.get_mapping().iteritems():
        if type(val) in [list, tuple]:
            ss_val = [
                SourceString(item, source).to_dict()
                for item in val
            ]
        else:
            ss_val = [SourceString(val, source).to_dict()]

        setattr(model, key, ss_val)

    return model


def by_issn(issn):
    """
    Query aleph for records with given `issn`.

    Args:
        issn (str): ISSN of the periodical.

    Returns:
        obj: :class:`Model` instances for each record.
    """
    for record in aleph.getISSNsXML(issn):
        marc = MARCXMLRecord(record)

        model = Model(
            url=_first_or_none(
                marc.get("856u")
            ),
            conspect=_first_or_none(
                marc.get("072a")
            ),
            annotation_tags=_first_or_none(
                marc.get("520a")
            ),
            periodicity=_first_or_none(
                marc.get("310a")
            ),
            title_tags=_first_or_none(
                marc.get("222a")
            ),
            place_tags=remove_hairs(
                _first_or_none(marc.get("260a")) or ""
            ),
            author_tags=remove_hairs(
                (
                    _first_or_none(marc.get("260b")) or
                    _first_or_none(marc.get("264b")) or
                    "",
                ),
                ", "
            ),
            # publisher_tags=,
            creation_dates=_first_or_none(
                marc.get("260c")
            ),
            lang_tags=_first_or_none(
                marc.get("040b")
            ),
            keyword_tags=marc.get("650a07"),
            source_info=_first_or_none(
                marc.get("500a")
            ),
        )

        yield _add_source(model)


class Author(namedtuple("Author", "name code linked_forms")):
    @classmethod
    def search_by_name(cls, name):
        records = aleph.downloadRecords(
            aleph.searchInAleph("aut", name, False, "wau")
        )

        for record in records:
            marc = MARCXMLRecord(record)

            yield cls(
                name=_first_or_none(marc["110a"]),
                code=_first_or_none(marc["1107"]),
                linked_forms=marc["410a2 "],
            )
