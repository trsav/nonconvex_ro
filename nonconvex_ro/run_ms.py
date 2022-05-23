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
import logging

logging.getLogger("pyomo.core").setLevel(logging.ERROR)


def run_ms_case(problem, solver, e):
    x = problem["x"]
    p = problem["p"]
    con_list = problem["cons"]
    obj = problem["obj"]

    def var_bounds(m, i):
        return (x[i][0], x[i][1])

    # con = con_list[0]

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
    for con in con_list:
        LBD.cons.add(expr=con(x_vars, p_nominal) <= 0)
    LBD.obj = Objective(expr=obj(x_vars), sense=minimize)

    UBD = ConcreteModel()
    UBD.x = Set(initialize=x.keys())
    UBD.x_v = Var(UBD.x, domain=Reals, bounds=var_bounds)

    p_nominal = [p[key]["val"] for key in p.keys()]
    x_vars = [UBD.x_v[i] for i in x.keys()]
    UBD.cons = ConstraintList()
    e_g = {}
    c_list = Set(initialize=range(len(con_list)))
    for i in range(len(con_list)):
        e_g[i] = 0.001
    UBD.e_g = Param(c_list, initialize=e_g, mutable=True, within=Any)
    for i in range(len(con_list)):
        UBD.cons.add(expr=con_list[i](x_vars, p_nominal) <= -UBD.e_g[i])
    UBD.obj = Objective(expr=obj(x_vars), sense=minimize)

    def build_LLP(x_opt, con):
        LLP = ConcreteModel()
        LLP.p = Set(initialize=p.keys())
        LLP.p_v = Var(LLP.p, domain=Reals, bounds=uncertain_bounds)
        param_vars = [LLP.p_v[str(i)] for i in p.keys()]
        LLP.obj = Objective(expr=con(x_opt, param_vars), sense=maximize)
        return LLP

    sip_upper_bound = [0]
    sip_lower_bound = [0]
    lb_store = []
    ub_store = []

    x_list = []

    while f_ubd - f_lbd > e_f:
        sip_upper_bound.append(f_ubd)
        sip_lower_bound.append(f_lbd)

        try:
            SolverFactory(solver).solve(LBD)
        except ValueError:
            print("Problem is infeasible?... cannot find a lower bound")
            return {}
        cons_count += len(LBD.cons)
        problem_count += 1
        f_lbd = value(LBD.obj)
        lb_store.append(f_lbd)
        ub_store.append(f_ubd)
        x_opt = value(LBD.x_v[:])
        x_list.append(x_opt)

        LLP_vals = []
        for con in con_list:
            LLP = build_LLP(x_opt, con)
            try:
                SolverFactory(solver).solve(LLP)
            except ValueError:
                pass
            problem_count += 1
            p_opt = value(LLP.p_v[:])
            for i_p in range(len(p_opt)):
                if p_opt[i_p] is None:
                    p_opt[i_p] = p_nominal[i_p]
            LLP_vals.append(value(LLP.obj))
            LBD.cons.add(expr=con([LBD.x_v[i] for i in x.keys()], p_opt) <= 0)
            cut_count += 1

        if max(LLP_vals) < 0:
            f_ubd = obj(x_opt)
            res = {}
            end = time.time()
            wct = end - start
            res["wallclock_time"] = wct
            res["problems_solved"] = problem_count
            res["average_constraints_in_any_problem"] = cons_count / problem_count
            res["constraints_added"] = cut_count
            res["SIP_lower_bound"] = sip_lower_bound[1:]
            res["SIP_upper_bound"] = sip_upper_bound[1:]
            res["solution"] = x_opt
            return res

        res = SolverFactory(solver).solve(UBD)
        cons_count += len(UBD.cons)

        problem_count += 1
        term_con = res.solver.termination_condition
        if term_con != TerminationCondition.infeasible:
            x_opt = value(UBD.x_v[:])

            for i in range(len(con_list)):
                LLP = build_LLP(x_opt, con_list[i])
                SolverFactory(solver).solve(LLP)
                problem_count += 1
                v = value(LLP.obj)

                if v < 0:
                    f_x = obj(x_opt)
                    if f_x <= f_ubd:
                        f_ubd = f_x

                    UBD.e_g[i] = value(UBD.e_g[:])[i] / r
                else:
                    p_opt = value(LLP.p_v[:])
                    for i_p in range(len(p_opt)):
                        if p_opt[i_p] is None:
                            p_opt[i_p] = p_nominal[i_p]

                    UBD.cons.add(
                        expr=con_list[i]([UBD.x_v[i] for i in x.keys()], p_opt)
                        <= -UBD.e_g[i]
                    )
                    cut_count += 1
            else:
                UBD.e_g[i] = value(UBD.e_g[:])[i] / r

    end = time.time()
    wct = end - start

    res = {}
    res["wallclock_time"] = wct
    res["problems_solved"] = problem_count
    res["average_constraints_in_any_problem"] = cons_count / problem_count
    res["constraints_added"] = cut_count
    res["SIP_lower_bound"] = sip_lower_bound[1:]
    res["SIP_upper_bound"] = sip_upper_bound[1:]
    res["solution"] = x_opt

    return res


def ms_data(problem, solver, e):
    res = {}
    res["wallclock_time"] = "N/A"
    res["problems_solved"] = "N/A"
    res["average_constraints_in_any_problem"] = "N/A"
    return res
