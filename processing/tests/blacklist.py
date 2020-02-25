import unittest
from process import GuilyBlacklist

guilties = [('fa', 'mb'), ('fc', 'md')]


class BlacklistTest(unittest.TestCase):

    def setUp(self):
        self.bl = GuilyBlacklist(guilties)

    def test_blacklisted_item(self):
        existing = guilties[1]
        self.assertEqual(self.bl.contains(existing), True)

    def test_non_blacklisted_item(self):
        non_existing = ('fx', 'mx')
        self.assertEqual(self.bl.contains(non_existing), False)


if __name__ == '__main__':
    unittest.main()
