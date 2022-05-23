from pyomo.environ import (
    ConcreteModel,
    Var,
    Reals,
    Set,
    ConstraintList,
    Objective,
    minimize,
    SolverFactory,
    value,
)
import time
from interval_definitions import Interval, subdivide_vector


def run_it_case(problem, solver, e, n_int):
    s = time.time()
    x = problem["x"]
    p = problem["p"]
    con_list = problem["cons"]
    obj = problem["obj"]

    def var_bounds(m, i):
        return (x[i][0], x[i][1])

    m_upper = ConcreteModel()
    m_upper.x = Set(initialize=x.keys())
    m_upper.x_v = Var(m_upper.x, domain=Reals, bounds=var_bounds)
    p_l = [p[key]["val"] - p[key]["unc"] for key in p.keys()]
    p_u = [p[key]["val"] + p[key]["unc"] for key in p.keys()]
    p_full = [Interval(p_l[i], p_u[i]) for i in range(len(p_l))]

    x_vars = [m_upper.x_v[i] for i in x.keys()]
    m_upper.cons = ConstraintList()

    p_list = subdivide_vector(p_full, n_int)

    def con_u(x, p, con):
        return con(x, p).u

    # print("Interval Extensions: ", len(p_list))
    for i in range(len(p_list)):
        for con in con_list:
            m_upper.cons.add(expr=con_u(x_vars, p_list[i], con) <= 0)
    m_upper.obj = Objective(expr=obj(x_vars), sense=minimize)
    print("Starting to solve...")

    bin_vars = int(((len(m_upper._decl) - 5) / 2) * 4)
    res = {}
    res["vars"] = len(x_vars)
    res["cons"] = len(m_upper.cons)
    res["bin_vars"] = bin_vars

    SolverFactory(solver).solve(m_upper)
    res["solution"] = value(m_upper.x_v[:])
    res["objective"] = value(m_upper.obj)

    e = time.time()
    wct = e - s
    res["wallclock_time"] = wct
    res["problems_solved"] = 1
    res["average_constraints_in_any_problem"] = int(len(p_list) * len(con_list))

    return res


def it_data(problem, solver, e, n_int):
    x = problem["x"]
    p = problem["p"]
    con_list = problem["cons"]
    obj = problem["obj"]

    def var_bounds(m, i):
        return (x[i][0], x[i][1])

    m_upper = ConcreteModel()
    m_upper.x = Set(initialize=x.keys())
    m_upper.x_v = Var(m_upper.x, domain=Reals, bounds=var_bounds)
    p_l = [p[key]["val"] - p[key]["unc"] for key in p.keys()]
    p_u = [p[key]["val"] + p[key]["unc"] for key in p.keys()]
    p_full = [Interval(p_l[i], p_u[i]) for i in range(len(p_l))]

    x_vars = [m_upper.x_v[i] for i in x.keys()]
    m_upper.cons = ConstraintList()

    p_list = subdivide_vector(p_full, n_int)

    def con_u(x, p, con):
        return con(x, p).u

    # print("Interval Extensions: ", len(p_list))
    for i in range(len(p_list)):
        for con in con_list:
            m_upper.cons.add(expr=con_u(x_vars, p_list[i], con) <= 0)
    m_upper.obj = Objective(expr=obj(x_vars), sense=minimize)
    print("Starting to solve...")

    res = {}
    res["wallclock_time"] = "N/A"
    res["problems_solved"] = 0
    res["average_constraints_in_any_problem"] = len(m_upper.cons)

    return res
