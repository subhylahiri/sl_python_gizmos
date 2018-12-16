# -*- coding: utf-8 -*-
"""Test lnarray class
"""
import unittest
import numpy as np
import unittest_numpy as utn
import sl_py_tools.numpy_tricks.linalg as la
import sl_py_tools.numpy_tricks.linalg.gufuncs as gf

# =============================================================================
# %% Test python classes
# =============================================================================


class TestNewClasses(utn.TestCaseNumpy):
    """Testing lnarray, pinvarray, etc"""

    def setUp(self):
        super().setUp()
        self.u = {}
        self.v = {}
        self.w = {}
        self.x = {}
        self.y = {}
        self.z = {}
        for sctype in self.sctype:
            self.u[sctype] = utn.randn_asa((7, 5), sctype).view(la.lnarray)
            self.v[sctype] = utn.randn_asa((5, 2), sctype)
            self.w[sctype] = utn.randn_asa((3, 3), sctype).view(la.lnarray)
            self.x[sctype] = utn.randn_asa((2, 5, 3), sctype).view(la.lnarray)
            self.y[sctype] = utn.randn_asa((3, 5), sctype)
            self.z[sctype] = utn.randn_asa((3,), sctype)


class TestArray(TestNewClasses):
    """Testing lnarray"""

    def setUp(self):
        super().setUp()
        self.sctype.append('i')
        super().setUp()

    def test_array_type(self):
        """Check that functions & operators return the correct type
        """
        v, w, x, y = self.v['d'], self.w['d'], self.x['d'], self.y['d']
        self.assertIsInstance(x @ y, la.lnarray)
        self.assertIsInstance(y @ x, la.lnarray)
        self.assertIsInstance(np.matmul(x, y), np.ndarray)
        self.assertIsInstance(la.solve(w, y), la.lnarray)
        self.assertIsInstance(np.linalg.solve(w, y), np.ndarray)
        self.assertIsInstance(la.lstsq(x, v), la.lnarray)
        self.assertIsInstance(np.linalg.lstsq(x[0], v, rcond=None)[0],
                              np.ndarray)
        self.assertIsInstance(la.lu(w)[0], la.lnarray)
        self.assertIsInstance(la.lu(v)[0], np.ndarray)
        self.assertIsInstance(la.qr(w)[0], la.lnarray)
        self.assertIsInstance(la.qr(v)[0], np.ndarray)
        self.assertIsInstance(np.linalg.qr(w)[0], np.ndarray)

    def test_array_shape(self):
        """Check that shape manipulation properties & methods work
        """
        w, x = self.w['D'], self.x['D']
        self.assertEqual(x.t.shape, (2, 3, 5))
        self.assertEqual(x.h.shape, (2, 3, 5))
        self.assertArrayNotAllClose(x.t, x.h)
        self.assertEqual(w.c.shape, (3, 3, 1))
        self.assertEqual(x.c.uc.shape, (2, 5, 3))
        self.assertEqual(w.r.shape, (3, 1, 3))
        self.assertEqual(x.r.ur.shape, (2, 5, 3))
        self.assertEqual(w.s.shape, (3, 3, 1, 1))
        self.assertEqual(x.s.us.shape, (2, 5, 3))
        self.assertEqual(w.expand_dims(1, 3).shape, (3, 1, 3, 1))
        self.assertEqual((x.s * w).flattish(1, 4).shape, (2, 45, 3))
        with self.assertRaisesRegex(ValueError, "repeated axes"):
            x.expand_dims(2, -3)
        with self.assertRaises(ValueError):
            (x.s * w).flattish(3, -3)

    @utn.loop_test(attr_inds=slice(4))
    def test_array_value(self, sctype):
        """Check that operator returns the correct value
        """
        w, x, z = self.w[sctype], self.x[sctype], self.z[sctype]
        self.assertArrayAllClose(x @ w, np.matmul(x, w))
        self.assertArrayAllClose(x @ z, np.matmul(x, z))
        self.assertArrayAllClose(gf.solve(w, z), np.linalg.solve(w, z))
        self.assertArrayAllClose(gf.lstsq(x.t[0], z),
                                 np.linalg.lstsq(x[0].t, z, rcond=None)[0])
        self.assertArrayAllClose(gf.rmatmul(w, x), np.matmul(x, w))


class TestPinvarray(TestNewClasses):
    """test pinvarray & invarray classes
    """

    def test_pinv_type(self):
        """test type attributes
        """
        w = self.w['D']
        self.assertIsInstance(w.pinv, la.pinvarray)
        self.assertIsInstance(w.inv, la.invarray)
        self.assertIs(w.pinv.dtype, np.dtype('D'))
        self.assertIsInstance(w.pinv.pinv, la.lnarray)
        self.assertIsInstance(w.inv.inv, la.lnarray)
        self.assertIsInstance(w.pinv(), la.lnarray)
        self.assertIsInstance(w.inv(), la.lnarray)
        p = la.pinvarray(self.v['d'])
        self.assertIsInstance(p, la.pinvarray)
        self.assertIsInstance(p.pinv, la.lnarray)
        self.assertIsInstance(2 * p, la.pinvarray)
        self.assertIsInstance((2 * p).pinv, la.lnarray)
        with self.assertRaises(AttributeError):
            p.inv
        with self.assertRaises(TypeError):
            w.inv.pinv

    def test_pinv_shape(self):
        """test shape attributes
        """
        xp = self.x['d'].pinv
        self.assertEqual(xp.ndim, 3)
        self.assertEqual(xp.shape, (2, 3, 5))
        self.assertEqual(xp.size, 30)
        self.assertEqual(xp().shape, (2, 3, 5))
        with self.assertRaises(ValueError):
            self.x['d'].inv
        xp = self.x['d'].c.pinv
        self.assertEqual(xp.swapaxes(0, 1).shape, (5, 2, 1, 3))
        self.assertEqual(xp.swapaxes(0, 2).shape, (1, 5, 2, 3))
        self.assertEqual(xp.swapaxes(-1, -2).shape, (2, 5, 3, 1))

    @utn.loop_test()
    def test_pinv_funcs(self, sctype):
        """test behaviour in gufuncs
        """
        u, v, x = self.u[sctype], self.v[sctype], self.x[sctype]
        self.assertArrayAllClose(gf.matmul(x.pinv, v), gf.lstsq(x, v))
        self.assertArrayAllClose(gf.matmul(u, x.pinv.t), gf.rlstsq(u, x.t))
        with self.assertRaises(TypeError):
            gf.matmul(x.pinv, u.pinv)
        self.assertArrayAllClose(gf.lstsq(u.pinv, v), gf.matmul(u, v))
        with self.assertRaises(TypeError):
            gf.lstsq(v, u.pinv)
        self.assertArrayAllClose(gf.rlstsq(v.T, u.t.pinv), gf.matmul(v.T, u.t))
        with self.assertRaises(TypeError):
            gf.rlstsq(u.t.pinv, v.T)
        self.assertArrayAllClose(gf.rmatmul(v, x.pinv), gf.lstsq(x, v))
        self.assertArrayAllClose(gf.rmatmul(x.pinv.t, u), gf.rlstsq(u, x.t))
        with self.assertRaises(TypeError):
            gf.rmatmul(u.pinv, x.pinv)

    @utn.loop_test()
    def test_inv_funcs(self, sctype):
        """test behaviour in gufuncs
        """
        w, x, y = self.w[sctype], self.x[sctype], self.y[sctype]
        xw = x[:, :3]
        self.assertArrayAllClose(gf.matmul(w.inv, y), gf.solve(w, y))
        self.assertArrayAllClose(gf.matmul(x, w.inv), gf.rsolve(x, w))
        self.assertArrayAllClose(gf.matmul(w.inv, xw.inv).inv, xw @ w)
        self.assertArrayAllClose(gf.solve(w.inv, y), gf.matmul(w, y))
        self.assertArrayAllClose(gf.solve(xw, w.inv).inv, gf.matmul(w, xw))
        self.assertArrayAllClose(gf.solve(xw.inv, w.inv), gf.rsolve(xw, w))
        self.assertArrayAllClose(gf.rsolve(w, xw.inv), gf.matmul(w, xw))
        self.assertArrayAllClose(gf.rsolve(xw.inv, w).inv, gf.matmul(w, xw))
        self.assertArrayAllClose(gf.rsolve(xw.inv, w.inv), gf.solve(xw, w))
        self.assertArrayAllClose(gf.rmatmul(w, xw.inv), gf.solve(xw, w))
        self.assertArrayAllClose(gf.rmatmul(xw.inv, w), gf.rsolve(w, xw))
        self.assertArrayAllClose(gf.rmatmul(xw.inv, w.inv).inv, xw @ w)


if __name__ == '__main__':
    unittest.main(verbosity=2)
