import time
import numpy as np
from interval_definitions import Interval, subdivide_vector
from scipy.optimize import minimize


def con_u(x, p, con):
    return con(x, p).u


def con_u_ineq(x, p, con):
    return -con_u(x, p, con)


def run_it_slsqp_case(problem, n_int, it, e):
    s = time.time()
    x = problem["x"]
    p = problem["p"]
    p_l = [p[key]["val"] - p[key]["unc"] for key in p.keys()]
    p_u = [p[key]["val"] + p[key]["unc"] for key in p.keys()]
    p_full = [Interval(p_l[i], p_u[i]) for i in range(len(p_l))]
    p_list = subdivide_vector(p_full, n_int)
    con_list = problem["cons"]
    obj = problem["obj"]
    bounds = np.array([[i[0], i[1]] for i in x.values()])
    cons = []
    for p_val in p_list:
        for con in con_list:
            con_dict = {}
            con_dict["type"] = "ineq"
            con_dict["fun"] = con_u_ineq
            con_dict["args"] = [p_val, con]
            cons.append(con_dict)

    r = minimize(
        obj,
        x0=np.mean(bounds, axis=0),
        method="SLSQP",
        constraints=cons,
        bounds=bounds,
        options={"maxiter": it, "ftol": e},
    )

    e = time.time()
    wct = e - s
    res = {}
    res["wallclock_time"] = wct
    res["solution"] = r.x
    res["objective"] = r.fun
    res["constraints"] = len(cons)

    return res
