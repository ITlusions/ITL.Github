"""Tracking-ID decorator for test methods: attaches an ID and a title that the test registry reads."""

import re


ID_PATTERN = re.compile(r'TC-[A-Z]+-\d{3}')


def test_case(identifier, title):
    """Attach a tracking ID and a title to a test method.

    Args:
        identifier: Tracking ID in the form TC-<AREA>-<NNN>, for example TC-REQ-001.
        title: Short description of the behaviour the test checks.

    Raises:
        ValueError: When the identifier does not match TC-<AREA>-<NNN> or the title is empty.
    """
    if not ID_PATTERN.fullmatch(identifier):
        raise ValueError(f'test id must match TC-<AREA>-<NNN>: {identifier}')
    if not title.strip():
        raise ValueError(f'test {identifier} needs a title')

    def mark(function):
        function.test_id = identifier
        function.test_title = title
        return function

    return mark
