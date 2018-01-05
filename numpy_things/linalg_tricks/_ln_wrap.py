# -*- coding: utf-8 -*-
# =============================================================================
# Created on Tue Dec  5 02:46:29 2017
# @author: subhy
# module: _ln_wrap
# =============================================================================
"""
Functions that change the return type of functions from `ndarray` to `lnarray`.
To use some other array class, change the first import statement and the
docstrings.
"""

from ._lnarray import lnarray as _array
from functools import wraps as _wraps
import numpy as _np


# =============================================================================
# Wrapping functionals
# =============================================================================


def wrap_one(np_func):
    """Create version of numpy function with single lnarray output.

    Does not pass through subclasses of `lnarray`

    Parameters
    ----------
    np_func : function
        A function that returns a single `ndarray`.

    Returns
    -------
    my_func : function
        A function that returns a single `lnarray`.
    """
    @_wraps(np_func)
    def wrapped(*args, **kwargs):
        return _converter(np_func(*args, **kwargs))
    return wrapped


def wrap_several(np_func):
    """Create version of numpy function with many lnarray outputs.

    Does not pass through subclasses of `lnarray`

    Parameters
    ----------
    np_func : function
        A function that returns a tuple of `ndarray`s.

    Returns
    -------
    my_func : function
        A function that returns a tuple of `lnarray`s.
    """
    @_wraps(np_func)
    def wrapped(*args, **kwargs):
        output = np_func(*args, **kwargs)
        return (_converter(x) for x in output)
    return wrapped


def wrap_some(np_func):
    """Create version of numpy function with some lnarray outputs, some
    non-array outputs.

    Does not pass through subclasses of `lnarray`

    Parameters
    ----------
    np_func : function
        A function that returns a mixed tuple of `ndarray`s and others.

    Returns
    -------
    my_func : function
        A function that returns a mixed tuple of `lnarray`s and others.
    """
    @_wraps(np_func)
    def wrapped(*args, **kwargs):
        output = np_func(*args, **kwargs)
        return (_converter_check(x) for x in output)
    return wrapped


def wrap_sub(np_func):
    """Create version of numpy function with single lnarray output.

    Does pass through subclasses of `lnarray`

    Parameters
    ----------
    np_func : function
        A function that returns a single `ndarray`.

    Returns
    -------
    my_func : function
        A function that returns a single `lnarray`.
    """
    @_wraps(np_func)
    def wrapped(*args, **kwargs):
        return _converter_sub(np_func(*args, **kwargs))
    return wrapped


def wrap_subseveral(np_func):
    """Create version of numpy function with many lnarray outputs.

    Does pass through subclasses of `lnarray`

    Parameters
    ----------
    np_func : function
        A function that returns a tuple of `ndarray`s.

    Returns
    -------
    my_func : function
        A function that returns a tuple of `lnarray`s.
    """
    @_wraps(np_func)
    def wrapped(*args, **kwargs):
        output = np_func(*args, **kwargs)
        return (_converter_sub(x) for x in output)
    return wrapped


def wrap_subsome(np_func):
    """Create version of numpy function with some lnarray outputs, some
    non-array outputs.

    Does pass through subclasses of `lnarray`

    Parameters
    ----------
    np_func : function
        A function that returns a mixed tuple of `ndarray`s and others.

    Returns
    -------
    my_func : function
        A function that returns a mixed tuple of `lnarray`s and others.
    """
    @_wraps(np_func)
    def wrapped(*args, **kwargs):
        output = np_func(*args, **kwargs)
        return (_converter_subcheck(x) for x in output)
    return wrapped


# =============================================================================
# Private stuff
# =============================================================================


def _converter(a: _np.ndarray) -> _array:
    return a.view(_array)


def _converter_check(a):
    if isinstance(a, _np.ndarray):
        return _converter(a)
    else:
        return a


def _converter_sub(a):
    if isinstance(a, _array):
        return a
    else:
        return _converter(a)


def _converter_subcheck(a):
    if isinstance(a, _array):
        return a
    elif isinstance(a, _np.ndarray):
        return _converter(a)
    else:
        return a
