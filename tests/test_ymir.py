#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
main code test
see LICENSE.TXT
"""

from io import BytesIO
import os
import unittest

import pytest

from ymir.ymir import last_posts

FIXTURE_DIR = './tests/fixtures/'

class TestYmir(unittest.TestCase):
    """Test the main code."""

    def read_fixture(self, fixture_file):
        """Read the fixture for tests."""
        fixture_path = os.path.abspath(os.path.join(FIXTURE_DIR, fixture_file))
        return parsing.parse_html_post(fixture_path)

    def make_xml(self, text):
        """Convert a string as an etree Element."""
        parser = etree.XMLParser(remove_blank_text=True)
        xml_fragment = etree.parse(BytesIO(text), parser)
        return xml_fragment.getroot()

    def setUp(self):
        """Set up the tests."""
        self.maxDiff = None
        pass

    def tearDown(self):
        """Tear down the tests."""
        pass

    def test_last_posts(self):
        """test the feed parsing"""
        feed_path = os.path.abspath(os.path.join(FIXTURE_DIR, 'feed.atom'))
        actual = last_posts(feed_path)
        expected = [{
            'published': '2020-04-21T23:59:59+09:00',
            'title': 'absences',
            'updated': '2020-04-21T14:59:59Z',
            'url': 'http://www.la-grange.net/2020/04/21/absence'}, ]
        assert actual == expected
        assert type(actual) is list
        assert type(actual[0]) is dict
