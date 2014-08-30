
_NO_DEFAULT = object()

class LinkedList(object):
    
    _next_name = 0
    
    def __init__(self, iterable=None):
        self.name = str(LinkedList._next_name)
        LinkedList._next_name += 1
   
        self._generation = 0
        self._len = 0
        self._sentinel = self._Sentinel()
        self._setleft(self._sentinel, self._sentinel)
        self._setright(self._sentinel, self._sentinel)
        
        if iterable:
            for item in iterable:
                self.append_right(item)
        
    def append_left(self, item):
        if self._hasattr(item):
            raise ValueError("already in the list")
        
        self._generation += 1
        neighbor = self._getright(self._sentinel)
        self._setleft(item, self._sentinel)
        self._setright(item, neighbor)
        self._setright(self._sentinel, item)
        self._setleft(neighbor, item)
        self._len += 1
    
    def append_right(self, item):
        if self._hasattr(item):
            raise ValueError("already in the list")
        
        self._generation += 1
        neighbor = self._getleft(self._sentinel)
        self._setleft(item, neighbor)
        self._setright(item, self._sentinel)
        self._setleft(self._sentinel, item)
        self._setright(neighbor, item)
        self._len += 1
        
    def remove(self, item):
        if not self._hasattr(item):
            raise ValueError("item not in the list")
    
        self._generation += 1
        leftitem = self._getleft(item)
        rightitem = self._getright(item)
        self._setright(leftitem, rightitem)
        self._setleft(rightitem, leftitem)
        self._len -= 1
        self._removeattr(item)
        
    def get_leftmost(self, default=_NO_DEFAULT):
        item = self._getright(self._sentinel)
        if item is self._sentinel:
            if default == _NO_DEFAULT:
                raise ValueError("empty list")
            else:
                return default
        return item
    
    def get_rightmost(self, default=_NO_DEFAULT):
        item = self._getleft(self._sentinel)
        if item is self._sentinel:
            if default == _NO_DEFAULT:
                raise ValueError("empty list")
            else:
                return default
        return item
    
    def __iter__(self):
        return self._iter(self._generation)
    
    def _iter(self, generation):
        item = self._getright(self._sentinel)
        while item is not self._sentinel:
            if generation != self._generation:
                raise ValueError("concurrent modification")
            yield item
            item = self._getright(item)
    
    def __reversed__(self):
        return self._reversed(self._generation)
    
    def _reversed(self, generation):
        item = self._getleft(self._sentinel)
        while item is not self._sentinel:
            if generation != self._generation:
                raise ValueError("concurrent modification")
            yield item
            item = self._getleft(item)
    
    def __len__(self):
        return self._len
    
    def __nonzero__(self):
        return self._len > 0
    
    def __eq__(self, other):
        if not isinstance(other, LinkedList):
            raise NotImplementedError()
        return list(self) == list(other)

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        s = 0
        for i, item in enumerate(self):
            s =+ i * hash(item)
        return s
    
    def __repr__(self):
        return repr(list(self))
    
    def __str__(self):
        return str(list(self))
    
    def _next(self, item):
        pass
    
    def _hasattr(self, item):
        return hasattr(item, "_%s_left" % self.name) and hasattr(item, "_%s_right" % self.name)
    
    def _removeattr(self, item):
        delattr(item, "_%s_left" % self.name)
        delattr(item, "_%s_right" % self.name)
    
    def _getleft(self, item):
        return getattr(item, "_%s_left" % self.name)
    
    def _setleft(self, item, value):
        setattr(item, "_%s_left" % self.name, value)
        
    def _getright(self, item):
        return getattr(item, "_%s_right" % self.name)
    
    def _setright(self, item, value):
        setattr(item, "_%s_right" % self.name, value)
    
    class _Sentinel(object):
        pass
    
