from os.path import abspath, dirname
import numpy as np
import pytest

from firedrake import *

cwd = abspath(dirname(__file__))


def make_c_evaluator(f):
    from ctypes import POINTER, c_double

    p_cf = cFunction(f)
    c_evaluate = make_c_evaluate(f)

    def evaluate(x):
        value_shape = f.function_space().ufl_element().value_shape() or 1
        result = np.zeros(value_shape, dtype=float)
        err = c_evaluate(p_cf,
                         x.ctypes.data_as(POINTER(c_double)),
                         result.ctypes.data_as(POINTER(c_double)))
        if err == -1:
            raise RuntimeError("Point %s is not in the domain!" % x)
        return result

    return evaluate


@pytest.mark.xfail
def test_1d():
    mesh = UnitIntervalMesh(2)
    V = FunctionSpace(mesh, "P", 3)
    f = Function(V).interpolate(Expression("x[0]*x[0]*(1.0 - x[0])"))

    evaluate = make_c_evaluator(f)

    x = np.array([0.2, 0.65], dtype=float)
    actual = evaluate(x)

    expected = np.array([eval("x[0]*x[0]*(1.0 - x[0])")])
    assert np.allclose(expected, actual)


def test_2d():
    mesh = UnitSquareMesh(2, 2, quadrilateral=False)
    V = FunctionSpace(mesh, "P", 2)
    f = Function(V).interpolate(Expression("x[0]*(1.0 - x[0]) + 0.5*x[1]"))

    evaluate = make_c_evaluator(f)

    x = np.array([0.2, 0.65], dtype=float)
    actual = evaluate(x)

    expected = np.array([x[0]*(1.0 - x[0]) + 0.5*x[1]])
    assert np.allclose(expected, actual)


def test_2d_quad():
    mesh = UnitSquareMesh(2, 2, quadrilateral=True)
    V = FunctionSpace(mesh, "Q", 2)
    f = Function(V).interpolate(Expression("x[0]*(1.0 - x[0]) + 0.5*x[1]"))

    evaluate = make_c_evaluator(f)

    x = np.array([0.12, 0.12], dtype=float)
    actual = evaluate(x)

    expected = np.array([x[0]*(1.0 - x[0]) + 0.5*x[1]])
    assert np.allclose(expected, actual)


def test_2d_nonaffine_quad():
    mesh = Mesh("/home/mh1714/git/firedrake/vedat/quad.msh")
    V = FunctionSpace(mesh, "Q", 2)
    f = Function(V).interpolate(Expression("x[0]*(1.0 - x[0]) + 0.5*x[1]"))

    evaluate = make_c_evaluator(f)

    Lx = 1.0
    Ly = 1.0
    nx = 64
    ny = 64
    dx = float(Lx) / nx
    dy = float(Ly) / ny
    xcoords = np.arange(0.0, Lx + 0.01 * dx, dx)
    ycoords = np.arange(0.0, Ly + 0.01 * dy, dy)
    coords = np.asarray(np.meshgrid(xcoords, ycoords)).swapaxes(0, 2).reshape(-1, 2)

    for x in coords:
        actual = evaluate(x)
        expected = np.array([x[0]*(1.0 - x[0]) + 0.5*x[1]])
        assert np.allclose(expected, actual)


def test_2d_to_2d():
    mesh = UnitSquareMesh(2, 2, quadrilateral=False)
    V = VectorFunctionSpace(mesh, "P", 2)
    f = Function(V).interpolate(Expression(("x[0]*(1.0 - x[1])", "x[0] + 0.5*x[1]")))

    evaluate = make_c_evaluator(f)

    x = np.array([0.2, 0.65], dtype=float)
    actual = evaluate(x)

    expected = np.array([x[0]*(1.0 - x[1]), x[0] + 0.5*x[1]])
    assert np.allclose(expected, actual)


def test_3d():
    mesh = UnitCubeMesh(2, 2, 2)
    V = FunctionSpace(mesh, "P", 2)
    f = Function(V).interpolate(Expression("x[0]*(1.0 - x[2]) + 0.5*x[1]"))

    evaluate = make_c_evaluator(f)

    x = np.array([0.2, 0.65, 0.1], dtype=float)
    actual = evaluate(x)

    expected = np.array([x[0]*(1.0 - x[2]) + 0.5*x[1]])
    assert np.allclose(expected, actual)

if __name__ == '__main__':
    import os
    pytest.main(os.path.abspath(__file__))

    # Lx = 1.0
    # Ly = 1.0
    # nx = 64
    # ny = 64
    # dx = float(Lx) / nx
    # dy = float(Ly) / ny
    # xcoords = np.arange(0.0, Lx + 0.01 * dx, dx)
    # ycoords = np.arange(0.0, Ly + 0.01 * dy, dy)
    # coords = np.asarray(np.meshgrid(xcoords, ycoords)).swapaxes(0, 2).reshape(-1, 2)

    # for p in coords:
    #     assert np.allclose(evaluate(p), analytic(p))
