# -*- coding: utf-8 -*-
"""Tricks for manipulating integers
"""
import math
from math import floor, ceil, trunc
from operator import floordiv
from typing import Optional
from numbers import Number, Real, Integral
import gmpy2
from . import number_like as _nl
from .arg_tricks import Export
Export[floor, floordiv]


def ceil_divide(numerator: Number, denominator: Number) -> int:
    """Ceiling division
    """
    return ceil(numerator / denominator)


def trunc_divide(numerator: Number, denominator: Number) -> int:
    """Truncated division
    """
    return trunc(numerator / denominator)


def round_divide(numerator: Number,
                 denominator: Number,
                 ndigits: Optional[int] = None) -> Number:
    """Rounded division
    """
    return round(numerator / denominator, ndigits)


# =============================================================================
# %%* Modulo for extended integers
# =============================================================================


def mod(dividend: Number, divisor: Number) -> Number:
    """Modulo for extended integers.

    Extended integers include `nan` and `+/-inf`. We act as if:
    - `inf` is the product of all positive numbers, so `inf % anything == 0`.
    - `inf * 0 == 0 (mod inf)`, so that `anything % inf == anything`.
    """
    if math.isnan(dividend) or math.isnan(divisor):
        return math.nan
    if math.isfinite(dividend) and math.isfinite(divisor):
        return dividend % divisor
    if math.isinf(dividend):
        return 0
    return dividend


def divmod_(dividend: Number, divisor: Number) -> Number:
    """Quotient and remainder for extended integers.

    Roughly the same as `(dividend // divisor, mod(dividend, divisor))`.

    Extended integers include `nan` and `+/-inf`. We act as if:
    - `inf` is the product of all positive numbers, so `inf % anything == 0`.
    - `inf * 0 == 0 (mod inf)`, so that `anything % inf == anything`.
    - `anything // inf == 0`.
    """
    if math.isnan(dividend) or math.isnan(divisor):
        return (math.nan, math.nan)
    if math.isfinite(dividend) and math.isfinite(divisor):
        return divmod(dividend, divisor)
    if math.isinf(dividend):
        return (math.inf, 0) if (divisor > 0) else (-math.inf, 0)
    return (0, dividend)


# =============================================================================
# %%* ExtendedInt method wrappers
# =============================================================================


def _eint_conv(args):
    """Convert to Number
    """
    def _conv(arg):
        if isinstance(arg, ExtendedInt):
            return arg.value
        if isinstance(arg, Number):
            return arg
        raise TypeError("Other argument must be a number or eint")
    return [_conv(x) for x in args]


_eint_method_in, _, _eint_ops = _nl.make_method_wrappers(_eint_conv, 'value')
_Mixin = _nl.number_like_mixin(_eint_conv, 'value')

# =============================================================================
# %%* Extended integers
# =============================================================================


class ExtendedIntegral(Real):
    """ABC for extended Integral, including +/-inf and nan."""


ExtendedIntegral.register(Integral)


class ExtendedInt(ExtendedIntegral, _Mixin):
    """Extended integers to include +/-inf and nan.
    """
    value: Real

    __str__ = _eint_method_in(str)
    __hash__ = _eint_method_in(hash)
    __mod__, __rmod__, __imod__ = _eint_ops(mod)
    __divmod__, __rdivmod__ = _eint_ops(divmod_)[:2]

    def __init__(self, value):
        try:
            self.value = int(value)
        except (ValueError, OverflowError):
            self.value = float(value)

    def __repr__(self):
        return f"eint({self})"

    def __getattr__(self, name):
        return getattr(self.value, name)


# =============================================================================
# %%* ExtendedInt function wrappers
# =============================================================================

_nl.set_objclasses(ExtendedInt)
eint_in, eint_out = _nl.make_fn_wrappers(_eint_conv, ExtendedInt)


# =============================================================================
# %%* Convenience
# =============================================================================

eint = ExtendedInt

nan = eint('nan')
inf = eint('inf')

isinf = eint_in(math.isinf)
isnan = eint_in(math.isnan)
isfinite = eint_in(math.isfinite)

# =============================================================================
# %%* More modulo for Extended Integers
# =============================================================================


@eint_out
def gcd(a: Integral, b: Integral) -> Integral:
    """Greatest common divisor for extended integers.

    Extended integers include `nan` and `+/-inf`. We act as if:
    - `inf` is the product of all positive numbers, so `inf % anything == 0`.
    """
    if math.isnan(a) or math.isnan(b):
        return math.nan
    if math.isfinite(a) and math.isfinite(b):
        return math.gcd(a, b)
    if math.isinf(a):
        return b
    return a


@eint_out
def invert(x: Integral, m: Integral) -> Integral:
    """Multiplicative inverse (modulo m) for extended integers.

    Return `y` such that `x * y == 1 (mod m)`.

    Extended integers include `nan` and `+/-inf`. We act as if:
    - `inf` is the product of all positive numbers, so `inf % anything == 0`.
    - `inf * 0 == 0 (mod inf)`, so that `anything % inf == anything`.
    """
    if math.isnan(x) or math.isnan(m):
        return math.nan
    if m in {1, -1}:
        # everything is an inverse
        return 0
    if math.isfinite(x) and math.isfinite(m):
        return gmpy2.invert(x, m)
    if x in {1, -1}:
        return x
    raise ZeroDivisionError('not invertible')


@eint_out
def divm(a: Number, b: Number, m: Number) -> Integral:
    """Division (modulo m) for extended integers.

    Return `x` such that `x * b == a (mod m)`.

    Extended integers include `nan` and `+/-inf`. We act as if:
    - `inf` is the product of all positive numbers, so `inf % anything == 0`.
    - `inf * 0 == 0 (mod inf)`, so that `anything % inf == anything`.
    """
    if math.isnan(a) or math.isnan(b) or math.isnan(m):
        return math.nan
    if math.isfinite(a) and math.isfinite(b) and math.isfinite(m):
        if a == 0 and m in {1, -1}:
            return 0
        return gmpy2.divm(a, b, m)
    return mod(a * invert(b, m), m)
