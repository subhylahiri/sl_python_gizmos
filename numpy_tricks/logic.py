# -*- coding: utf-8 -*-
"""
Functions for testing array values.
"""
import numpy as np


def allfinite(*arrays) -> bool:
    """Check if all array elements are finite

    Returns `True` if no element of any array is `nan` or `inf`.
    """
    return all(np.isfinite(arr).all() for arr in arrays)


def anyclose(first, second, *args, **kwds) -> bool:
    """Are any elements close?

    Like numpy.allclose but with any instead of all.
    """
    return np.isclose(first, second, *args, **kwds).any()


def tri_low_rank(array, *args, **kwds):
    """Check for low rank triangular matrix

    Returns `True` if any diagonal element is close to 0.
    Does not check if the array is triangular. It can be used on the 'raw'
    forms of lu/qr factors.
    """
    return anyclose(np.diagonal(array), 0., *args, **kwds)


def indarg(array, argfn):
    """Unravelled index of argmax, etc

    Parameters
    ----------
    array
        array being searched
    argfn
        callable that returns ravel index of an element

    Returns
    -------
    ind
        tuple of ints indexing the element
    """
    return np.unravel_index(argfn(array), array.shape)


def indmax(array, ignore_nan=True):
    """Unravelled index of argmax

    Parameters
    ----------
    array
        array being searched
    ignore_nan
        do we ignore nans?

    Returns
    -------
    ind
        tuple of ints indexing the max
    """
    if ignore_nan:
        return indarg(array, np.nanargmax)
    return indarg(array, np.argmax)


def indmin(array, ignore_nan=True):
    """Unravelled index of argmin

    Parameters
    ----------
    array
        array being searched
    ignore_nan
        do we ignore nans?

    Returns
    -------
    ind
        tuple of ints indexing the min
    """
    if ignore_nan:
        return indarg(array, np.nanargmin)
    return indarg(array, np.argmin)


def unique_unsorted(sequence: np.ndarray, get_inv: bool = False) -> np.ndarray:
    """Remove repetitions without changing the order

    Parameters
    ----------
    sequence : array_like, (N,)
        The array whose unique elements we want.
    return_inverse : bool, optional
        If `True`, also return an array of assignments. By default `False`.

    Returns
    -------
    unique : np.ndarray, (V,)
        Array containing the unique elements of `sequence` in the order they
        first apppear.
    inv : np.ndarray[int] (N,)
        Array of assignments, i.e. the index array, `inds`, such that
        `sequence = unique[inds]`.
    """
    sequence = np.asanyarray(sequence)
    if not get_inv:
        _, inds = np.unique(sequence, return_index=True)
        inds.sort()
        return sequence[inds]
    unq_srt, inds, inv = np.unique(sequence, True, True)
    order = np.argsort(inds)
    iorder = np.argsort(order)
    # iorder[order] = np.arange(len(order))
    return unq_srt[order], iorder[inv]
