from pyomo.environ import (
    ConcreteModel,
    Var,
    Reals,
    value,
    Set,
    ConstraintList,
    Objective,
    minimize,
)
from pyomo.opt import SolverFactory
import numpy as np
from interval_definitions import Interval


def subdivide(x, N):
    A = np.zeros(N + 1, dtype="object")
    A[0] = x.l
    w_x = x.u - x.l
    for j in range(1, N + 1):
        A[j] = A[j - 1] + (w_x / N)
    return A


def subdivide_vector(int_list, N):
    l = len(int_list)
    d = [subdivide(int_list[i], N) for i in range(l)]
    G = np.meshgrid(*d)
    I = len(G[0][:, 0, 0]) - 1
    J = len(G[0][0, :, 0]) - 1
    K = len(G[0][0, 0, :]) - 1
    for i in range(I):
        for j in range(J):
            for k in range(K):
                if i == 0 and j == 0 and k == 0:
                    res = np.array(
                        [
                            [
                                Interval(G[m][i, j, k], G[m][i + 1, j + 1, k + 1])
                                for m in range(len(G[:]))
                            ]
                        ]
                    )
                else:
                    res = np.append(
                        res,
                        [
                            [
                                Interval(G[m][i, j, k], G[m][i + 1, j + 1, k + 1])
                                for m in range(len(G[:]))
                            ]
                        ],
                        axis=0,
                    )
    return res


def run_it_case(problem, solver, e, n_int):
    x = problem["x"]
    p = problem["p"]
    con_list = problem["cons"]
    obj = problem["obj"]

    def var_bounds(m, i):
        return (x[i][0], x[i][1])

    def uncertain_bounds(m, i):
        return (p[i]["val"] - p[i]["unc"], p[i]["val"] + p[i]["unc"])

    m_upper = ConcreteModel()
    m_upper.x = Set(initialize=x.keys())
    m_upper.x_v = Var(m_upper.x, domain=Reals, bounds=var_bounds)
    p_l = [p[key]["val"] - p[key]["unc"] for key in p.keys()]
    p_u = [p[key]["val"] + p[key]["unc"] for key in p.keys()]
    p_full = [Interval(p_l[i], p_u[i]) for i in range(len(p_l))]

    x_vars = [m_upper.x_v[i] for i in x.keys()]
    m_upper.cons = ConstraintList()

    p_list = subdivide_vector(p_full, n_int)
    print("Interval Extensions: ", len(p_list))
    for i in range(len(p_list)):
        for con in con_list:
            m_upper.cons.add(expr=con(x_vars, p_list[i]) <= 0)
    m_upper.obj = Objective(expr=obj(x_vars), sense=minimize)
    SolverFactory(solver).solve(m_upper)

    return value(m_upper.x_vars[:])
