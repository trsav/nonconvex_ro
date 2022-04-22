from pyomo.environ import (
    ConcreteModel,
    Var,
    Reals,
    value,
    Set,
    ConstraintList,
    Objective,
    Param,
    Any,
    minimize,
    maximize,
    TerminationCondition,
)
from pyomo.opt import SolverFactory
import numpy as np
import time


def run_ms_case(problem, solver, e):
    x = problem["x"]
    p = problem["p"]
    con_list = problem["cons"]
    obj = problem["obj"]

    def var_bounds(m, i):
        return (x[i][0], x[i][1])

    con = con_list[0]

    def uncertain_bounds(m, i):
        return (p[i]["val"] - p[i]["unc"], p[i]["val"] + p[i]["unc"])

    problem_count = 0
    e_f = e
    cut_count = 0
    r = 2
    cons_count = 0
    start = time.time()

    p_nominal = [p[key]["val"] for key in p.keys()]

    f_ubd = np.Infinity
    f_lbd = -np.Infinity

    LBD = ConcreteModel()
    LBD.x = Set(initialize=x.keys())
    LBD.x_v = Var(LBD.x, domain=Reals, bounds=var_bounds)
    p_nominal = [p[key]["val"] for key in p.keys()]
    x_vars = [LBD.x_v[i] for i in x.keys()]
    LBD.cons = ConstraintList()
    LBD.cons.add(expr=con(x_vars, p_nominal) <= 0)
    LBD.obj = Objective(expr=obj(x_vars), sense=minimize)

    UBD = ConcreteModel()
    UBD.x = Set(initialize=x.keys())
    UBD.x_v = Var(UBD.x, domain=Reals, bounds=var_bounds)
    p_nominal = [p[key]["val"] for key in p.keys()]
    x_vars = [UBD.x_v[i] for i in x.keys()]
    UBD.cons = ConstraintList()
    UBD.e_g = Param(initialize=2, mutable=True, within=Any)
    UBD.cons.add(expr=con(x_vars, p_nominal) <= -UBD.e_g)
    UBD.obj = Objective(expr=obj(x_vars), sense=minimize)

    def build_LLP(x_opt):
        LLP = ConcreteModel()
        LLP.p = Set(initialize=p.keys())
        LLP.p_v = Var(LLP.p, domain=Reals, bounds=uncertain_bounds)
        param_vars = [LLP.p_v[str(i)] for i in p.keys()]
        LLP.obj = Objective(expr=con(x_opt, param_vars), sense=maximize)
        return LLP

    LBD_list = [p_nominal]
    UBD_list = [p_nominal]
    sip_upper_bound = [0]
    sip_lower_bound = [0]
    lb_store = []
    ub_store = []

    x_list = []
    e_g_list = []
    while f_ubd - f_lbd > e_f:
        sip_upper_bound.append(f_ubd)
        sip_lower_bound.append(f_lbd)
        SolverFactory(solver).solve(LBD)
        cons_count += len(LBD.cons)
        problem_count += 1
        f_lbd = value(LBD.obj)
        lb_store.append(f_lbd)
        ub_store.append(f_ubd)
        x_opt = value(LBD.x_v[:])
        x_list.append(x_opt)
        e_g_list.append(value(UBD.e_g))

        LLP = build_LLP(x_opt)
        SolverFactory(solver).solve(LLP)

        problem_count += 1

        if value(LLP.obj) < 0:
            f_ubd = obj(x_opt)
            break

        p_opt = value(LLP.p_v[:])
        LBD_list.append(p_opt)
        LBD.cons.add(expr=con([LBD.x_v[i] for i in x.keys()], p_opt) <= 0)
        cut_count += 1

        res = SolverFactory(solver).solve(UBD)
        cons_count += len(UBD.cons)

        problem_count += 1

        if res.solver.termination_condition != TerminationCondition.infeasible:
            x_opt = value(UBD.x_v[:])

            LLP = build_LLP(x_opt)
            SolverFactory(solver).solve(LLP)

            problem_count += 1
            v = value(LLP.obj)

            if v < 0:
                f_x = obj(x_opt)
                if f_x <= f_ubd:
                    f_ubd = f_x

                UBD_list.append(None)
                UBD.e_g = value(UBD.e_g) / r
            else:
                p_opt = value(LLP.p_v[:])
                UBD_list.append(p_opt)
                UBD.cons.add(
                    expr=con([UBD.x_v[i] for i in x.keys()], p_opt) <= -UBD.e_g
                )
                cut_count += 1
        else:
            UBD.e_g = value(UBD.e_g) / r

    end = time.time()
    wct = end - start

    res = {}
    res["wallclock_time"] = wct
    res["problems_solved"] = problem_count
    res["average_constraints_in_any_problem"] = cons_count / problem_count
    res["constraints_added"] = cut_count
    res["SIP_lower_bound"] = sip_lower_bound[1:]
    res["SIP_upper_bound"] = sip_upper_bound[1:]

    return res
