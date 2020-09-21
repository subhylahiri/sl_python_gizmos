"""Tools for working with dictionaries.
"""
from __future__ import annotations

import collections as cn
import contextlib as _cx
import functools as _ft
import typing as _ty

import sl_py_tools.arg_tricks as _ag

# =============================================================================
# Dictionaries
# =============================================================================


def update_new(to_update: _ty.MutableMapping[Key, Val],
               update_from: Dictable[Key, Val] = (), **kwds) -> None:
    """Update new keys only

    If `key` in `update_from` but not `to_update`, set `to_update[key] =
    update_from[key]`. Further keywords overrule items in `update_from`.
    """
    if isinstance(update_from, cn.abc.Mapping):
        for k in update_from:
            to_update.setdefault(k, update_from[k])
    else:
        for k, val in update_from:
            if k not in to_update:
                to_update[k] = val
    for k, val in kwds.items():
        to_update.setdefault(k, val)


def update_existing(to_update: _ty.MutableMapping[Key, Val],
                    update_from: Dictable[Key, Val] = (), **kwds) -> None:
    """Update existing keys only

    If `key` in `update_from` and `to_update`, set `to_update[key] =
    update_from[key]`. Further keywords overrule items in `update_from`.
    """
    if isinstance(update_from, cn.abc.Mapping):
        for k in to_update:
            to_update[k] = update_from.get(k, to_update[k])
    else:
        for k, val in update_from:
            if k in to_update:
                to_update[k] = val
    for k in to_update:
        to_update[k] = kwds.get(k, to_update[k])


def pop_existing(to_update: _ty.MutableMapping[Key, Val],
                 pop_from: _ty.MutableMapping[Key, Val]) -> None:
    """Pop to update existing keys only

    If `k` in `pop_from` and `to_update`, set `to_update[k] = pop_from[k]`
    and `del pop_from[k]`.
    """
    for k in to_update:
        to_update[k] = pop_from.pop(k, to_update[k])


def pop_new(to_update: _ty.MutableMapping[Key, Val],
            pop_from: _ty.MutableMapping[Key, Val]) -> None:
    """Pop to update new keys only

    If `k` in `pop_from` but not `to_update`, set `to_update[k] = pop_from[k]`
    and `del pop_from[k]`.
    """
    for k in pop_from:
        if k not in to_update:
            to_update[k] = pop_from.pop(k)


@_cx.contextmanager
def updated(base: _ty.Dict[Key, Val], extra: Dictable[Key, Val], **kwds
            ) ->  _ty.Dict[Key, Val]:
    """Update a dictionary in a context, then restore

    Parameters
    ----------
    base : Dict[Var, Val]
        Orgiginal dictionary
    extra : Dict[Var, Val]
        Dictionary to update `base` with.
    Further keywords are included in the update.

    Returns
    -------
    modified : Dict[Var, Val]
        `base` updated with `extra`.
    """
    original = base.copy()
    try:
        base.update(extra, **kwds)
        yield base
    finally:
        base.clear()
        base.update(original)


def _inv_dict_iter(to_invert: _ty.Mapping[Key, Val]
                   ) -> _ty.Iterator[_ty.Tuple[Val, Key]]:
    """Swap keys and values.

    Can be used to build/update another dict or other container.
    Can only be used once - best not to store in a variable.
    """
    return ((v, k) for k, v in to_invert.items())


def invert_dict(to_invert: _ty.Mapping[Key, Val],
                check: bool = True) -> _ty.Dict[Val, Key]:
    """Swap keys and values.

    Assumes values are distinct and hashable.

    Raises
    ------
    TypeError
        If any of `to_invert.values()` are not hashable.
    ValueError
        If `check` is `True` and any of `to_invert.values()` are repeated.
    """
    inverted = dict(_inv_dict_iter(to_invert))
    if check and len(inverted) < len(to_invert):
        raise ValueError(f'Repeated values in {to_invert}?')
    return inverted


def is_inverse_dict(map1: _ty.Mapping[Key, Val], map2: _ty.Mapping[Val, Key]
                    ) -> bool:
    """Test if two dicts are each others inverses.

    Checks `map2[map1[key]] == key` for every `key` in `map1.keys()` and every
    `key` in `map2.values()`. Does not check order of entries.
    """
    if len(map1) != len(map2):
        return False
    return all(map2[v] == k for k, v in map1.items())


# pylint: disable=too-many-ancestors
class PairedDict(cn.UserDict):
    """One direction of bidirectional mapping

    Instances Store a reference to their inverse mapping in `self.inverse`.
    Both keys and values must be unique and hashable.

    Deleting an item also deletes the reversed item from `self.inverse`.
    Setting an item with `self[key1] = key2`, deletes `key1` from `self` as
    above, deletes `key2` from `self.inverse`, adds item `(key1, key2)` to
    `self`, and adds item `(key2, key1)` to `self.inverse`.

    Ideally, the instances should be built using the class-method
    `PairedDict.make_pairs`. This will raise a `ValueError` for repeated values

    If you do use the constructor directly: when `inverse` is not provided in
    the constructor, `self.inverse` will be created with `invert_dict(self)`
    without checking for repeated values. When `inverse` is provided in the
    constructor, it will be copied and updated with `invert_dict(self)` and
    `self` will be updated with `invert_dict(self.inverse)`, both without
    checking for repeated values. We recommend running `self.fix_inverse()`
    after construction, which will raise a `ValueError` if there were any
    repeated values, or at least calling `self.check_inverse()`.

    Under normal circumstances `self.inverse.inverse is self` should hold. This
    can break if `self.inverse` is replaced or private machinery is used.
    There is no guarantee that `self.inverse == invert_dict(self)` due to the
    possibility of repeated values, but if it holds after construction it
    should remain True thereafter.

    Parameters
    ----------
    Positional arguments
        Passed to the `UserDict` constructor.
    inverse
        The inverse dictionary. Can only be given as a keyword argument.
    Other keword arguments
        Passed to the `UserDict` constructor.

    Raises
    ------
    ValueError
        If any keys/values are not unique.
    TypeError
        If any keys/values are not hashable.

    See Also
    --------
    dict
    collections.UserDict
    BijectiveMap
    """
    inverse: _ty.Optional[PairedDict] = None
    _formed: bool = False

    def __init__(self, *args, inverse=None, **kwds):
        # ensure we only use super().__setitem__ to prevent infinite recursion
        self._formed = False
        # were we called by another object's __init__?
        secret = kwds.pop('__secret', False)
        # use this to construct self.inverse if inverse is not already ok
        init_fn = _ft.partial(type(self), inverse=self, __secret=True)
        super().__init__(*args, **kwds)

        # self.inverse.__init__ will not be callled if secret is True and
        # inverse is not None.
        if secret:
            self.inverse = _ag.default_eval(inverse, init_fn)
        else:
            self.inverse = _ag.non_default_eval(inverse, init_fn, init_fn)
        # In all calls of self.inverse.__init__ above, __secret is True and
        # inverse is self => no infinite recursion (at most one more call).

        # First object constructed is last to be updated by its inverse
        if secret or inverse is not None:
            self.update(_inv_dict_iter(self.inverse))
        # we can use our own __setitem__ now that self.update is done
        self._formed = True
        # if not (secret or self.check_inverse()):
        #     raise ValueError("Unable to form inverse. Repeated keys/values?")

    def __delitem__(self, key):
        """Delete inverse map as well as forward map"""
        if self._formed:
            # not in constructor/fix_inverse, assume self.inverse is good
            # use super().__delitem__ to avoid infinite recursion
            super(PairedDict, self.inverse).__delitem__(self[key])
        # maybe in constructor/fix_inverse, make no assumptions
        super().__delitem__(key)

    def __setitem__(self, key, value):
        """Delete inverse & forward maps, then create new foward & inverse map
        """
        if self._formed:
            # not in constructor/fix_inverse, assume self.inverse is good
            if key in self.keys():
                del self[key]
            if value in self.inverse.keys():
                del self.inverse[value]
            # use super().__setitem__ to avoid infinite recursion
            super(PairedDict, self.inverse).__setitem__(value, key)
        # maybe in constructor/fix_inverse, make no assumptions
        super().__setitem__(key, value)

    def check_inverse(self) -> bool:
        """Check that inverse has the correct value."""
        if self.inverse is None:
            return False
        if self.inverse.inverse != self:
            return False
        return is_inverse_dict(self, self.inverse)

    def check_inverse_strict(self) -> bool:
        """Check that inverse is correct and properly linked to self."""
        return self.check_inverse() and (self.inverse.inverse is self)

    @_cx.contextmanager
    def _unformed(self):
        try:
            self._formed = False
            yield
        finally:
            self._formed = True

    def fix_me(self):
        """Set self using inverse

        Updates `self` with inverse of `self.inverse`, if needed.
        If `self.inverse` has not been set, it does nothing.
        It does not modify `self.inverse`.
        """
        if self.inverse is not None:
            if not self.check_inverse():
                with self._unformed():
                    self.update(_inv_dict_iter(self.inverse))

    def fix_inverse(self):
        """Set inverse using self

        If `self.inverse` has not been set, it is created by inverting `self`.
        If they are not inverses of each other, first we try updating
        `self.inverse` with the inverse of `self`. Then we try updating `self`
        with the inverse of `self.inverse`. If they are still not inverses, we
        raise a `ValueError`.
        """
        if self.inverse is None:
            self.inverse = type(self)(inverse=self)
        self.inverse.inverse = self
        if not self.check_inverse():
            self.inverse.fix_me()
        if not self.check_inverse():
            self.fix_me()
        if not self.check_inverse():
            raise ValueError("Unable to fix inverse. Repeated keys/values?")

    @classmethod
    def make_pairs(cls, *args, **kwds) -> _ty.Tuple[PairedDict, PairedDict]:
        """Create a pair of dicts that are inverses of each other

        Parameters
        ----------
        All used to construct `fwd`.

        Returns
        -------
        fwd : PairedDict
            Dictionary built with parameters.
        bwd : PairedDict
            Inverse of `fwd`

        Raises
        ------
        ValueError
            If values are not unique or if 'inverse' is used as a key.
        TypeError
            If any values are not hashable.
        """
        if 'inverse' in kwds.keys():
            raise ValueError("Cannot use 'inverse' as a key here")
        fwd = cls(*args, **kwds)
        fwd.fix_inverse()
        bwd = fwd.inverse
        if not fwd.check_inverse_strict():
            raise ValueError("Repeated keys/values?")
        return fwd, bwd


# pylint: disable=too-many-ancestors
class BijectiveMap(cn.ChainMap):
    """Bidirectional mapping

    Similar to a `dict`, except the statement `self.fwd[key1] == key2` is
    equivalent to `self.bwd[key2] == key1`. Both of these statements imply
    that `self[key1] == key2` and `self[key2] == key1`. Both keys must be
    unique and hashable.

    A symmetric bijective map arises when subscripting the object itself.
    An asymmetric bijective map arises when subscripting the `fwd` and `bwd`
    properties, which are both `PairedDict`s and inverses of each other.

    If an association is modified, in either direction, both the forward and
    backward mappings are deleted and a new association is created. (see
    documentation for `PairedDict`). Setting `self[key1] = key2` is always
    applied to `self.fwd`, with `self.bwd` modified appropriately. For more
    control, you can call `self.fwd[key1] = key2` or `self.bwd[key2] = key1`.

    See Also
    --------
    dict
    collections.UserDict
    collections.ChainMap
    PairedDict
    """
    maps: _ty.List[PairedDict]

    def __init__(self, *args, **kwds):
        super().__init__(*PairedDict.make_pairs(*args, **kwds))

    def __delitem__(self, key):
        if key in self.fwd.keys():
            del self.fwd[key]
        elif key in self.bwd.keys():
            del self.bwd[key]
        else:
            raise KeyError(f"Key '{key}' not found in either direction.")

    @property
    def fwd(self) -> PairedDict:
        """The forward mapping"""
        return self.maps[0]

    @property
    def bwd(self) -> PairedDict:
        """The reverse mapping"""
        return self.maps[1]


# =============================================================================
# Hints, aliases
# =============================================================================
Key = _ty.TypeVar('Key')
Val = _ty.TypeVar('Val')
Dictable = _ty.Union[_ty.Mapping[Key, Val], _ty.Iterable[_ty.Tuple[Key, Val]]]