"""Base test case for chart tests: every chart test class derives from ChartTestCase."""

import unittest



class ChartTestCase(unittest.TestCase):
    """Test case of one chart; the subclass sets the chart folder and the repository root."""

    chart_dir = None
    repository = None
