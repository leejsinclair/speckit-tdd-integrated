import unittest

from shop import cart


class ItemCountTests(unittest.TestCase):
    def test_empty_cart_has_no_items(self):
        self.assertEqual(cart.item_count([]), 0)

    def test_counts_items(self):
        self.assertEqual(cart.item_count([1.5, 2.0]), 2)
