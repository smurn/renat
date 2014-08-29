'''
Created on Aug 29, 2014

@author: stefan
'''
import unittest
from renatserver import ddlist

class Item(object):
    def __init__(self, name="item"):
        self.name =  name
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name

class TestLinkedList(unittest.TestCase):
    
    def setUp(self):
        self.target = ddlist.LinkedList()

    def test_len_empty(self):
        self.assertEqual(0, len(self.target))

    def test_iter_empty(self):
        self.assertEqual([], list(self.target))

    def test_reversed_empty(self):
        self.assertEqual([], list(reversed(self.target)))

    def test_equalhash_empty(self):
        self.assertTrue(hash(self.target) == hash(ddlist.LinkedList()))
        
    def test_init_empty(self):
        self.target = ddlist.LinkedList([])
        self.assertEqual(0, len(self.target))

        
    def test_init_one(self):
        item = Item()
        self.target = ddlist.LinkedList([item])
        self.assertEqual(1, len(self.target))
        self.assertEqual([item], list(self.target))
        
    def test_init_two(self):
        item1 = Item("1")
        item2 = Item("2")
        self.target = ddlist.LinkedList([item1, item2])
        self.assertEqual(2, len(self.target))
        self.assertEqual([item1, item2], list(self.target))
        
    def test_equal_empty(self):
        self.assertTrue(self.target == ddlist.LinkedList())
        
    def test_equal_true(self):
        item1 = Item("1")
        item2 = Item("2")
        self.assertTrue(ddlist.LinkedList([item1, item2]) == ddlist.LinkedList([item1, item2]))
        
    def test_equal_order(self):
        item1 = Item("1")
        item2 = Item("2")
        self.assertFalse(ddlist.LinkedList([item2, item1]) == ddlist.LinkedList([item1, item2]))
     
    def test_equal_count(self):
        item1 = Item("1")
        item2 = Item("2")
        self.assertFalse(ddlist.LinkedList([item2]) == ddlist.LinkedList([item1, item2])) 
            
    def test_append_left_first(self):
        item = Item()
        self.target.append_left(item)
        self.assertEqual(ddlist.LinkedList([item]), self.target)
        
    def test_append_right_first(self):
        item = Item()
        self.target.append_right(item)
        self.assertEqual(ddlist.LinkedList([item]), self.target)
        
    def test_append_left_second(self):
        item1 = Item("1")
        item2 = Item("2")
        self.target.append_left(item1)
        self.target.append_left(item2)
        self.assertEqual(ddlist.LinkedList([item2, item1]), self.target)
        
    def test_append_right_second(self):
        item1 = Item("1")
        item2 = Item("2")
        self.target.append_right(item1)
        self.target.append_right(item2)
        self.assertEqual(ddlist.LinkedList([item1, item2]), self.target)
        
    def test_len(self):
        item1 = Item("1")
        item2 = Item("2")
        self.target.append_right(item1)
        self.target.append_right(item2)
        self.assertEqual(2, len(self.target))
        
    def test_len_remove(self):
        item1 = Item("1")
        item2 = Item("2")
        self.target.append_right(item1)
        self.target.append_right(item2)
        self.target.remove(item2)
        self.assertEqual(1, len(self.target))
        
    def test_remove_middle(self):
        item1 = Item("1")
        item2 = Item("2")
        item3 = Item("3")
        self.target = ddlist.LinkedList([item1, item2, item3])
        self.target.remove(item2)
        self.assertEqual(ddlist.LinkedList([item1, item3]), self.target)
        
    def test_remove_left(self):
        item1 = Item("1")
        item2 = Item("2")
        item3 = Item("3")
        self.target = ddlist.LinkedList([item1, item2, item3])
        self.target.remove(item1)
        self.assertEqual(ddlist.LinkedList([item2, item3]), self.target)
    
    def test_remove_right(self):
        item1 = Item("1")
        item2 = Item("2")
        item3 = Item("3")
        self.target = ddlist.LinkedList([item1, item2, item3])
        self.target.remove(item3)
        self.assertEqual(ddlist.LinkedList([item1, item2]), self.target)
        
    def test_remove_last(self):
        item1 = Item("1")
        self.target = ddlist.LinkedList([item1])
        self.target.remove(item1)
        self.assertEqual(ddlist.LinkedList([]), self.target)
        
    def test_remove_insert(self):
        item1 = Item("1")
        item2 = Item("2")
        item3 = Item("3")
        self.target = ddlist.LinkedList([item1, item2, item3])
        self.target.remove(item2)
        self.target.append_right(item2)
        self.assertEqual(ddlist.LinkedList([item1, item3, item2]), self.target)
        
    def test_concurrent_append(self):
        item1 = Item("1")
        item2 = Item("2")
        item3 = Item("3")
        self.target = ddlist.LinkedList([item1, item2])
        it = iter(self.target)
        self.target.append_right(item3)
        self.assertRaises(ValueError, next, it)
        
    def test_concurrent_remove(self):
        item1 = Item("1")
        item2 = Item("2")
        item3 = Item("3")
        self.target = ddlist.LinkedList([item1, item2, item3])
        it = iter(self.target)
        self.target.remove(item3)
        self.assertRaises(ValueError, next, it)
        