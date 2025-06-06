"""A StableSet is a mutable set that remembers its insertion order.
Featuring: Fast O(1) insertion, deletion, iteration and membership testing.
But slow O(N) Index Lookup.

An OrderedSet is a mutable data structure that is a hybrid of a list and a set.
It remembers its insertion order so that every entry has an index that can be looked up.
Featuring: O(1) Index lookup, insertion, iteration and membership testing.
But slow O(N) Deletion.

Both have similar interfaces but differ in respect of their implementation and performance.

OrderedSet Based on a recipe originally posted to ActiveState Recipes by Raymond Hettiger,
and released under the MIT license."""

__description__ = (
    "StableSet and OrderedSet are sets that remembers their order, "
    "and allows looking up its items by their index in that order."
)
__long_description__ = __doc__
__author__ = "Elia Robyn Lake, Idan Miara"
__author_email__ = "gh@arborelia.net, idan@miara.com"
__url__ = "https://github.com/idanmiara/ordered-set"
__python_requires__ = ">=3.8"

import itertools
import itertools as it
from typing import (
    AbstractSet,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    MutableSet,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
    overload,
)

SLICE_ALL = slice(None)
__version__ = "5.2.2"


T = TypeVar("T", covariant=True)

# SetLike[T] is either a set of elements of type T, or a sequence, which
# we will convert to a StableSet or to an OrderedSet by adding its elements in order.
SetLike = Union[AbstractSet[T], Sequence[T]]
StableSetLike = Union["StableSet[T]", Sequence[T]]
SetInitializer = Union[AbstractSet[T], Sequence[T], Iterable[T]]


def _is_atomic(obj: object) -> bool:
    """
    Returns True for objects which are iterable but should not be iterated in
    the context of indexing a StableSet or an OrderedSet.

    When we index by an iterable, usually that means we're being asked to look
    up a list of things.

    However, in the case of the .index() method, we shouldn't handle strings
    and tuples like other iterables. They're not sequences of things to look
    up, they're the single, atomic thing we're trying to find.

    As an example, oset.index('hello') should give the index of 'hello' in an
    StableSet of strings. It shouldn't give the indexes of each individual
    character.
    """
    return isinstance(obj, (str, tuple))


class StableSet(MutableSet[T], Sequence[T]):
    """
    A StableSet is a custom MutableSet that remembers its insertion order.
    Featuring: Fast O(1) insertion, deletion, iteration and membership testing.
    But slow O(N) Index Lookup.

    StableSet is meant to be a drop-in replacement for `set` when iteration in insertion order
    is the only additional requirement over the built-in `set`.

    Equality: StableSet, like `set` and `dict_keys` [dict.keys()], and unlike OrderedSet,
    disregards the items order when checking equality.
    Like `set` it may be equal only to other instances of AbstractSet
    (like `set`, `dict_keys` or StableSet).

    This implementation of StableSet is based on the built-in dict type.
    In Python 3.6 and later, the built-in dict type is inherently ordered.
    If you ignore the dictionary values, that also gives you a simple ordered set,
    with fast O(1) insertion, deletion, iteration and membership testing.
    However, dict does not provide the list-like random access features of StableSet.
    So we have to convert it to a list in O(N) to look up the index of an entry
    or look up an entry by its index.

    Example:
        >>> StableSet([1, 1, 2, 3, 2])
        StableSet([1, 2, 3])
    """

    __slots__ = ("_map",)

    _map: Dict[T, Any]

    def __init__(self, initial: Optional[SetInitializer[T]] = None):
        self._map = dict.fromkeys(initial) if initial else {}

    def __len__(self) -> int:
        """
        Returns the number of unique elements in the ordered set

        Example:
            >>> len(StableSet([]))
            0
            >>> len(StableSet([1, 2]))
            2
        """
        # return len(self._map)
        return self._map.__len__()

    @overload
    def __getitem__(self, index: slice) -> "StableSet[T]":
        ...

    @overload
    def __getitem__(self, index: Sequence[int]) -> List[T]:
        ...

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    # concrete implementation
    def __getitem__(self, index):
        """
        Get the item at a given index.

        If `index` is a slice, you will get back that slice of items, as a
        new StableSet.

        If `index` is a list or a similar iterable, you'll get a list of
        items corresponding to those indices. This is similar to NumPy's
        "fancy indexing". The result is not a StableSet because you may ask
        for duplicate indices, and the number of elements returned should be
        the number of elements asked for.

        Example:
            >>> oset = StableSet([1, 2, 3])
            >>> oset[1]
            2
        """
        if isinstance(index, int):
            try:
                return next(itertools.islice(self._map.keys(), index, index + 1))
            except StopIteration:
                raise IndexError(f"index {index} out of range")
        elif isinstance(index, slice) and index == SLICE_ALL:
            return self.copy()
        items = list(self._map.keys())
        if isinstance(index, Iterable):
            return [items[i] for i in index]
        elif isinstance(index, slice) or hasattr(index, "__index__"):
            result = items[index]
            if isinstance(result, list):
                return self.__class__(result)
            else:
                return result
        else:
            raise TypeError(f"Don't know how to index a StableSet by {index}")

    # Define the gritty details of how a StableSet is serialized as a pickle.
    # We leave off type annotations, because the only code that should interact
    # with this is a generalized tool such as pickle.
    def __getstate__(self):
        if len(self) == 0:
            # In pickle, the state can't be an empty list.
            # We need to return a truthy value, or else __setstate__ won't be run.
            #
            # This could have been done more gracefully by always putting the state
            # in a tuple, but this way is backwards- and forwards- compatible with
            # previous versions of StableSet.
            return (None,)
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key: Any) -> bool:
        """
        Test if the item is in this ordered set.

        Example:
            >>> 1 in StableSet([1, 3, 2])
            True
            >>> 5 in StableSet([1, 3, 2])
            False
        """
        # return key in self._map
        return self._map.__contains__(key)

    def __iter__(self) -> Iterator[T]:
        """
        Example:
            >>> list(iter(StableSet([1, 2, 3])))
            [1, 2, 3]
        """
        # return iter(self._map.keys())
        return self._map.keys().__iter__()

    def __reversed__(self) -> Iterator[T]:
        """
        Supported from Python >= 3.8
        Example:
            >>> list(reversed(StableSet([1, 2, 3])))
            [3, 2, 1]
        """
        return reversed(self._map.keys())

    def __repr__(self) -> str:
        if not self:
            return f"{self.__class__.__name__}()"
        return f"{self.__class__.__name__}({list(self)!r})"

    def __and__(self, other: SetLike[T]) -> "StableSet[T]":
        # the parent implementation of this is backwards
        return self.intersection(other)

    # sub, or, xor that support ordering
    # (left hand and right hand - as the operands order does matter)
    # based on the implementations of the super class (Set(Collection)),
    # see _collections_abc.py
    def __sub__(self, other):
        cls = type(
            self
            if isinstance(self, StableSet)
            else other
            if isinstance(other, StableSet)
            else StableSet
        )
        if not isinstance(other, Set):
            if not isinstance(other, Iterable):
                return NotImplemented
            other = cls(other)
        return cls(value for value in self if value not in other)

    def __rsub__(self, other):
        cls = type(
            self
            if isinstance(self, StableSet)
            else other
            if isinstance(other, StableSet)
            else StableSet
        )
        if not isinstance(other, Set):
            if not isinstance(other, Iterable):
                return NotImplemented
            other = cls(other)
        return cls(value for value in other if value not in self)

    def __or__(self, other):
        cls = type(
            self
            if isinstance(self, StableSet)
            else other
            if isinstance(other, StableSet)
            else StableSet
        )
        if not isinstance(other, Iterable):
            return NotImplemented
        chain = (e for s in (self, other) for e in s)
        return cls(chain)

    def __ror__(self, other):
        cls = type(
            self
            if isinstance(self, StableSet)
            else other
            if isinstance(other, StableSet)
            else StableSet
        )
        if not isinstance(other, Iterable):
            return NotImplemented
        chain = (e for s in (other, self) for e in s)
        return cls(chain)

    def __xor__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        return (self - other) | (other - self)

    def __rxor__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        return (other - self) | (self - other)

    def clear(self) -> None:
        """
        Remove all items from this StableSet.
        """
        self._map.clear()

    def copy(self) -> "StableSet[T]":
        """
        Return a shallow copy of this object.

        Example:
            >>> this = StableSet([1, 2, 3])
            >>> other = this.copy()
            >>> this == other
            True
            >>> this is other
            False
        """
        return self.__class__(self)

    # Technically type-incompatible with MutableSet, because we return an
    # int instead of nothing. This is also one of the things that makes
    # StableSet convenient to use.
    def add(self, key: T) -> int:
        """
        Add `key` as an item to this StableSet, then return its index.

        If `key` is already in the StableSet, return the index it already
        had.

        Example:
            >>> oset = StableSet()
            >>> oset.append(3)
            0
            >>> print(oset)
            StableSet([3])
        """
        self._map[key] = None
        return len(self._map) - 1

    append = add

    def update(self, sequence: SetLike[T]) -> int:
        """
        Update the set with the given iterable sequence, then return the index
        of the last element inserted.

        Example:
            >>> oset = StableSet([1, 2, 3])
            >>> oset.update([3, 1, 5, 1, 4])
            4
            >>> print(oset)
            StableSet([1, 2, 3, 5, 4])
        """
        try:
            other_map = dict.fromkeys(sequence)
            self._map.update(other_map)
        except TypeError:
            raise ValueError(f"Argument needs to be an iterable, got {type(sequence)}")
        return len(self._map) - 1

    @overload
    def index(self, key: Sequence[T]) -> List[int]:  # NOQA
        ...

    @overload
    def index(self, key: T) -> int:  # NOQA
        ...

    # concrete implementation
    def index(self, key):  # NOQA
        """
        Get the index of a given entry, raising an IndexError if it's not present

        `key` can be an iterable of entries that is not a string, in which case
        this returns a list of indices.

        Example:
            >>> oset = StableSet([1, 2, 3])
            >>> oset.index(2)
            1
        """
        try:
            if isinstance(key, Iterable) and not _is_atomic(key):
                return [self.index(subkey) for subkey in key]
            for index, item in enumerate(self._map.keys()):
                if item == key:
                    return index
            raise KeyError(key)
            # return list(self._map.keys()).index(key)
        except ValueError:
            raise KeyError(key)

    # Provide some compatibility with pd.Index
    get_loc = index
    get_indexer = index

    def pop(self, index: int = -1) -> T:
        """
        Remove and return item at index (default last).

        Raises KeyError if the set is empty.
        Raises IndexError if index is out of range.

        Example:
            >>> oset = StableSet([1, 2, 3])
            >>> oset.pop()
            3
        """
        if not self._map:
            raise KeyError("Set is empty")
        if index == -1:
            elem, _ = self._map.popitem()
            return elem
        elif index == 0:
            elem = next(iter(self._map.keys()))
        else:
            elem = next(itertools.islice(self._map.keys(), index, index + 1))
        self._map.pop(elem)
        return elem

    def popitem(self, last: bool = True):
        """Remove and return an item from the set.
        Items are returned in LIFO order if last is true or FIFO order if false.
        """
        if not self._map:
            raise KeyError("Set is empty")
        if last:
            elem, _ = self._map.popitem()
            return elem
        elem = next(iter(self._map.keys()))
        self._map.pop(elem)
        return elem

    def move_to_end(self, key) -> None:
        """Move an existing element to the end.
        Raise KeyError if the element does not exist.
        """
        self._map.pop(key)
        self._map[key] = None

    def discard(self, key: T) -> None:
        """
        Remove an element.  Do not raise an exception if absent.

        The MutableSet mixin uses this to implement the .remove() method, which
        *does* raise an error when asked to remove a non-existent item.

        Example:
            >>> oset = StableSet([1, 2, 3])
            >>> oset.discard(2)
            >>> print(oset)
            StableSet([1, 3])
            >>> oset.discard(2)
            >>> print(oset)
            StableSet([1, 3])
        """
        # if key in self:
        #     del self._map[key]
        self._map.pop(key, None)

    def union(self, *sets: SetLike[T]) -> "StableSet[T]":
        """
        Combines all unique items.
        Each item order is defined by its first appearance.

        Example:
            >>> oset = StableSet.union(StableSet([3, 1, 4, 1, 5]), [1, 3], [2, 0])
            >>> print(oset)
            StableSet([3, 1, 4, 5, 2, 0])
            >>> oset.union([8, 9])
            StableSet([3, 1, 4, 5, 2, 0, 8, 9])
            >>> oset | {10}
            StableSet([3, 1, 4, 5, 2, 0, 10])
        """
        cls = type(self if isinstance(self, StableSet) else StableSet)
        containers = map(list, it.chain([self], sets))  # type: ignore
        items = it.chain.from_iterable(containers)
        return cls(items)  # type: ignore

    def intersection(self, *sets: SetLike[T]) -> "StableSet[T]":
        """
        Returns elements in common between all sets. Order is defined only
        by the first set.

        Example:
            >>> oset = StableSet.intersection(StableSet([0, 1, 2, 3]), [1, 2, 3])
            >>> print(oset)
            StableSet([1, 2, 3])
            >>> oset.intersection([2, 4, 5], [1, 2, 3, 4])
            StableSet([2])
            >>> oset.intersection()
            StableSet([1, 2, 3])
        """
        cls = type(self if isinstance(self, StableSet) else StableSet)
        items: SetInitializer[T] = self
        if sets:
            common = set.intersection(*map(set, sets))  # type: ignore
            items = (item for item in self if item in common)
        return cls(items)

    def difference(self, *sets: SetLike[T]) -> "StableSet[T]":
        """
        Returns all elements that are in this set but not the others.

        Example:
            >>> StableSet([1, 2, 3]).difference(StableSet([2]))
            StableSet([1, 3])
            >>> StableSet([1, 2, 3]).difference(StableSet([2]), StableSet([3]))
            StableSet([1])
            >>> StableSet([1, 2, 3]) - StableSet([2])
            StableSet([1, 3])
            >>> StableSet([1, 2, 3]).difference()
            StableSet([1, 2, 3])
        """
        cls = type(self if isinstance(self, StableSet) else StableSet)
        items: SetInitializer[T] = self
        if sets:
            other = set.union(*map(set, sets))  # type: ignore
            items = (item for item in self if item not in other)
        return cls(items)

    def symmetric_difference(self, other: SetLike[T]) -> "StableSet[T]":
        """
        Return the symmetric difference of two StableSets as a new set.
        That is, the new set will contain all elements that are in exactly
        one of the sets.

        Their order will be preserved, with elements from `self` preceding
        elements from `other`.

        Example:
            >>> this = StableSet([1, 4, 3, 5, 7])
            >>> other = StableSet([9, 7, 1, 3, 2])
            >>> this.symmetric_difference(other)
            StableSet([4, 5, 9, 2])
        """
        cls = type(
            self
            if isinstance(self, StableSet)
            else other
            if isinstance(other, StableSet)
            else StableSet
        )
        diff1 = cls(self).difference(other)
        diff2 = cls(other).difference(self)
        return diff1.union(diff2)

    def difference_update(self, *sets: SetLike[T]) -> None:
        """
        Update this StableSet to remove items from one or more other sets.

        Example:
            >>> this = StableSet([1, 2, 3])
            >>> this.difference_update(StableSet([2, 4]))
            >>> print(this)
            StableSet([1, 3])

            >>> this = StableSet([1, 2, 3, 4, 5])
            >>> this.difference_update(StableSet([2, 4]), StableSet([1, 4, 6]))
            >>> print(this)
            StableSet([3, 5])
        """
        items_to_remove = set()  # type: Set[T]
        for other in sets:
            items_as_set = set(other)  # type: Set[T]
            items_to_remove |= items_as_set
        self._map = dict.fromkeys(
            [item for item in self._map if item not in items_to_remove]
        )

    def intersection_update(self, other: SetLike[T]) -> None:
        """
        Update this StableSet to keep only items in another set, preserving
        their order in this set.

        Example:
            >>> this = StableSet([1, 4, 3, 5, 7])
            >>> other = StableSet([9, 7, 1, 3, 2])
            >>> this.intersection_update(other)
            >>> print(this)
            StableSet([1, 3, 7])
        """
        other = set(other)
        self._map = dict.fromkeys([item for item in self._map if item in other])

    def symmetric_difference_update(self, other: SetLike[T]) -> None:
        """
        Update this StableSet to remove items from another set, then
        add items from the other set that were not present in this set.

        Example:
            >>> this = StableSet([1, 4, 3, 5, 7])
            >>> other = StableSet([9, 7, 1, 3, 2])
            >>> this.symmetric_difference_update(other)
            >>> print(this)
            StableSet([4, 5, 9, 2])
        """
        items_to_add = [item for item in other if item not in self]
        items_to_remove = set(other)
        self._map = dict.fromkeys(
            [item for item in self._map if item not in items_to_remove] + items_to_add
        )

    def issubset(self: SetLike[T], other: SetLike[T]) -> bool:
        """
        Report whether another set contains this set.

        Example:
            >>> StableSet([1, 2, 3]).issubset({1, 2, 3, 4})
            True
            >>> StableSet([1, 2, 3]).issubset({1, 2})
            False
            >>> StableSet([1, 2, 3]).issubset({1, 4, 3, 5})
            False
        """
        if len(self) > len(other):  # Fast check for obvious cases
            return False
        return all(item in other for item in self)

    def issuperset(self: SetLike[T], other: SetLike[T]) -> bool:
        """
        Report whether this set contains another set.

        Example:
            >>> StableSet([1, 2, 3, 4]).issuperset({1, 2, 3})
            True
            >>> StableSet([1, 2]).issuperset([1, 2, 3])
            False
            >>> StableSet([1, 4, 3, 5]).issuperset({1, 2, 3})
            False
        """
        if len(self) < len(other):  # Fast check for obvious cases
            return False
        return all(item in self for item in other)

    def isorderedsubset(self: StableSetLike[T], other: StableSetLike[T]):
        """
        Report whether another set contains this set in the same order.

        Example:
            >>> StableSet([1, 2, 3]).isorderedsubset([7, 1, 2, 3, 4])
            True
            >>> StableSet([1, 2, 3]).isorderedsubset([7, 1, 3, 2, 4])
            False
            >>> StableSet([1, 2, 3]).isorderedsubset([1, 2])
            False
        """
        if len(self) > len(other):
            return False
        i = 0
        self_len = len(self)
        for other_item in other:
            if other_item == self[i]:
                i += 1
                if i == self_len:
                    return True
        return False

    def isorderedsuperset(self: StableSetLike[T], other: StableSetLike[T]):
        return StableSet.isorderedsubset(other, self)

    def isprefix(self: StableSetLike[T], other: StableSetLike[T]):
        """
        Report whether this set is a prefix of another set.

        Example:
            >>> StableSet([1, 2]).isprefix([1, 2, 3])
            True
            >>> StableSet([1, 2, 3]).isprefix([1, 2])
            False
            >>> StableSet([1, 2, 3]).isprefix([1, 2, 3])
            True
            >>> StableSet([1, 2]).isprefix([4, 1, 2, 3])
            False
        """
        if len(self) > len(other):
            return False
        for self_item, other_item in zip(self, other):
            if not self_item == other_item:
                return False
        return True

    def ispostfix(self: StableSetLike[T], other: StableSetLike[T]):
        return StableSet.isprefix(other, self)


class StableSetEq(StableSet[T]):
    """
    StableSetEq is a StableSet with a modified equality operator.

    StableSetEq, like `set` and `dict_keys` [dict.keys()], and unlike OrderedSet,
    disregards the items order when checking equality.
    Unlike StableSet, `set`, or `dict_keys` - A StableSetEq can also equal be equal to a Sequence:
    `StableSetEq([1, 2]) == [1, 2]` and `StableSetEq([1, 2]) == [2, 1]`; but `set([1, 2]) != [1, 2]`
    """

    def __eq__(self, other: Any) -> bool:
        """
        Returns true if the containers have the same items.
        Items order is ignored.

        Example:
            >>> oset = StableSetEq([1, 3, 2])
            >>> oset == [1, 3, 2]
            True
            >>> oset == [1, 2, 3]
            True
            >>> oset == [2, 3]
            False
            >>> oset == StableSetEq([3, 2, 1])
            True
        """

        if not isinstance(other, AbstractSet):
            try:
                other = set(other)
            except TypeError:
                # If `other` can't be converted into a set, it's not equal.
                return False
        return self._map.keys() == other

    def __le__(self, other: SetLike[T]):
        return len(self) <= len(other) and (
            self._map.keys() <= other
            if isinstance(other, AbstractSet)
            else self._map.keys() <= set(other)
        )

    def __lt__(self, other: SetLike[T]):
        return len(self) < len(other) and (
            self._map.keys() < other
            if isinstance(other, AbstractSet)
            else self._map.keys() < set(other)
        )

    def __ge__(self, other: SetLike[T]):
        return len(self) >= len(other) and (
            self._map.keys() >= other
            if isinstance(other, AbstractSet)
            else self._map.keys() >= set(other)
        )

    def __gt__(self, other: SetLike[T]):
        return len(self) > len(other) and (
            self._map.keys() > other
            if isinstance(other, AbstractSet)
            else self._map.keys() > set(other)
        )


class OrderedSet(StableSet[T]):
    """
    An OrderedSet is a mutable data structure that is a hybrid of a list and a set.
    It remembers its insertion order so that every entry has an index that can be looked up.
    Featuring: O(1) Index lookup, insertion, iteration and membership testing.
    But slow O(N) Deletion.
    Using OrderedSet over StableSet is advised only if you require fast Index lookup -
    Otherwise using StableSet is advised as it is much faster and has a smaller memory footprint.

    In some aspects OrderedSet behaves like a `set` and in other aspects it behaves like a list.

    Equality: OrderedSet, like `list` and `odict_keys` [OrderdDict.keys()], and unlike OrderedSet,
    regards the items order when checking equality.
    Unlike `set`, An OrderedSet can also equal be equal to a Sequence:
    `StableSet([1, 2]) == [1, 2]` and `StableSet([1, 2]) != [2, 1]`; but `set([1, 2]) != [1, 2]`

    The original implementation of OrderedSet was a recipe posted by Raymond Hettiger,
    https://code.activestate.com/recipes/576694-orderedset/
    Released under the MIT license.
    Hettiger's implementation kept its content in a doubly-linked list referenced by a dict.
    As a result, looking up an item by its index was an O(N) operation, while deletion was O(1).
    This version makes different trade-offs for the sake of efficient lookups.
    Its content is a standard Python list instead of a doubly-linked list.
    This provides O(1) lookups by index at the expense of O(N) deletion,
    as well as slightly faster iteration.

    Example:
        >>> OrderedSet([1, 1, 2, 3, 2])
        OrderedSet([1, 2, 3])
    """

    __slots__ = ("_items",)

    _items: List[T]

    def __init__(self, initial: Optional[SetInitializer[T]] = None):
        self._items = []
        self._map = {}
        if initial is not None:
            # In terms of duck-typing, the default __ior__ is compatible with
            # the types we use, but it doesn't expect all the types we
            # support as values for `initial`.
            self |= initial  # type: ignore

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._items[index]
        elif isinstance(index, slice) and index == SLICE_ALL:
            return self.copy()
        elif isinstance(index, Iterable):
            return [self._items[i] for i in index]
        elif isinstance(index, slice) or hasattr(index, "__index__"):
            result = self._items[index]
            if isinstance(result, list):
                return self.__class__(result)
            else:
                return result
        else:
            raise TypeError("Don't know how to index an OrderedSet by %r" % index)

    def __eq__(self, other: Any) -> bool:
        """
        Returns true if the containers have the same items.
        If `other` is a Sequence, then order is checked, otherwise it is ignored.

        Example:
            >>> oset = OrderedSet([1, 3, 2])
            >>> oset == [1, 3, 2]
            True
            >>> oset == [1, 2, 3]
            False
            >>> oset == [2, 3]
            False
            >>> oset == OrderedSet([3, 2, 1])
            False
        """
        if isinstance(other, Sequence):
            # Check that this OrderedSet contains the same elements, in the
            # same order, as the other object.
            return len(self) == len(other) and self._items == list(other)
        try:
            other_as_set = set(other)
        except TypeError:
            # If `other` can't be converted into a set, it's not equal.
            return False
        else:
            return self._map.keys() == other_as_set

    def __le__(self, other: SetLike[T]):
        return len(self) <= len(other) and (
            self._map.keys() <= other
            if isinstance(other, AbstractSet)
            else self._items <= other
            if isinstance(other, list)
            else self._items <= list(other)
        )

    def __lt__(self, other: SetLike[T]):
        return len(self) < len(other) and (
            self._map.keys() < other
            if isinstance(other, AbstractSet)
            else self._items < other
            if isinstance(other, list)
            else self._items < list(other)
        )

    def __ge__(self, other: SetLike[T]):
        return len(self) >= len(other) and (
            self._map.keys() >= other
            if isinstance(other, AbstractSet)
            else self._items >= other
            if isinstance(other, list)
            else self._items >= list(other)
        )

    def __gt__(self, other: SetLike[T]):
        return len(self) > len(other) and (
            self._map.keys() > other
            if isinstance(other, AbstractSet)
            else self._items > other
            if isinstance(other, list)
            else self._items > list(other)
        )

    def clear(self) -> None:
        del self._items[:]
        self._map.clear()

    def add(self, key: T) -> int:
        if key not in self._map:
            self._map[key] = len(self._items)
            self._items.append(key)
        return self._map[key]

    def update(self, sequence: SetLike[T]) -> int:
        item_index = 0
        try:
            for item in sequence:
                item_index = self.add(item)
        except TypeError:
            raise ValueError(f"Argument needs to be an iterable, got {type(sequence)}")
        return item_index

    def index(self, key):
        if isinstance(key, Iterable) and not _is_atomic(key):
            return [self.index(subkey) for subkey in key]
        return self._map[key]

    def pop(self, index: int = -1) -> T:
        if not self._items:
            raise KeyError("Set is empty")
        elem = self._items[index]
        del self._items[index]
        del self._map[elem]
        return elem

    def popitem(self, last: bool = True):
        if not self._items:
            raise KeyError("Set is empty")
        index = -1 if last else 0
        elem = self._items[index]
        del self._items[index]
        del self._map[elem]
        return elem

    def move_to_end(self, key) -> None:
        if key in self:
            self.discard(key)
            self.add(key)
        else:
            raise KeyError(key)

    def discard(self, key: T) -> None:
        if key in self:
            i = self._map[key]
            del self._items[i]
            del self._map[key]
            for k, v in self._map.items():
                if v >= i:
                    self._map[k] = v - 1

    def _update_items(self, items: list) -> None:
        """
        Replace the 'items' list of this OrderedSet with a new one, updating
        self._map accordingly.
        """
        self._items = items
        self._map = {item: idx for (idx, item) in enumerate(items)}

    def difference_update(self, *sets: SetLike[T]) -> None:
        items_to_remove = set()  # type: Set[T]
        for other in sets:
            items_as_set = set(other)  # type: Set[T]
            items_to_remove |= items_as_set
        self._update_items(
            [item for item in self._items if item not in items_to_remove]
        )

    def intersection_update(self, other: SetLike[T]) -> None:
        other = set(other)
        self._update_items([item for item in self._items if item in other])

    def symmetric_difference_update(self, other: SetLike[T]) -> None:
        items_to_add = [item for item in other if item not in self]
        items_to_remove = set(other)
        self._update_items(
            [item for item in self._items if item not in items_to_remove] + items_to_add
        )
