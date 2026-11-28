import unittest
from pathlib import Path

from case import ID_PATTERN
from case import test_case



def collect_tests(suite):
    """Yield every test case in a suite, including tests nested in sub-suites."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from collect_tests(item)
        else:
            yield item


class TestRegistryTest(unittest.TestCase):
    """Behavioral tests for the tracking IDs of the test suite."""

    def setUp(self):
        self.tests = self.discovered_tests()

    def discovered_tests(self):
        """Return the (id, title, name) of every tracked test in the tests folder."""
        folder = str(Path(__file__).resolve().parent)
        suite = unittest.defaultTestLoader.discover(folder, pattern='test_*.py', top_level_dir=folder)
        found = []
        for test in collect_tests(suite):
            method = getattr(test, test._testMethodName)
            identifier = getattr(method, 'test_id', None)
            if identifier is not None:
                found.append((identifier, getattr(method, 'test_title', ''), test.id()))
        return found

    @test_case('TC-REG-001', 'Every tracking ID follows the TC-<AREA>-<NNN> pattern')
    def test_every_tracked_id_has_the_expected_format(self):
        """Test that every tracking ID follows the TC-<AREA>-<NNN> pattern."""
        for identifier, _, name in self.tests:
            with self.subTest(test=name):
                self.assertRegex(identifier, ID_PATTERN)

    @test_case('TC-REG-002', 'Each tracking ID belongs to exactly one test across the suite')
    def test_no_tracking_id_is_used_twice(self):
        """Test that each tracking ID belongs to exactly one test across the suite."""
        identifiers = [identifier for identifier, _, _ in self.tests]
        self.assertEqual(len(identifiers), len(set(identifiers)), f'duplicate ids: {identifiers}')

    @test_case('TC-REG-003', 'Each tracked test has a non-empty title for the registry')
    def test_every_tracked_test_has_a_title(self):
        """Test that each tracked test has a non-empty title for the registry."""
        for identifier, title, name in self.tests:
            with self.subTest(test=name):
                self.assertTrue(title.strip(), identifier)


if __name__ == '__main__':
    unittest.main()
