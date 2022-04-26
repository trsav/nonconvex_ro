import time
import numpy as np
from interval_definitions import Interval, subdivide_vector


def con_u(x, p, con):
    return con(x, p).u


def random_search(obj, con_list, p, bounds, n_int, it):
    p_l = [p[key]["val"] - p[key]["unc"] for key in p.keys()]
    p_u = [p[key]["val"] + p[key]["unc"] for key in p.keys()]
    p_full = [Interval(p_l[i], p_u[i]) for i in range(len(p_l))]
    p_list = subdivide_vector(p_full, n_int)
    sample = np.random.uniform(bounds[:, 0], bounds[:, 1], (it, 2))
    func_evals = 0
    con_vals = []
    valid_points = [0 for i in range(it)]
    j = 0
    while j < it:
        # each random point
        for i in range(len(p_list)):
            # each interval
            for con in con_list:
                # each constraint
                con_eval = con_u(sample[j, :], p_list[i], con)
                con_vals.append(con_eval)
                func_evals += 1
                if con_eval > 0:
                    valid_points[j] = 1
                    break
            if valid_points[j] == 1:
                break
        j += 1

    valid_indices = []
    for i in range(len(valid_points)):
        if valid_points[i] == 0:
            valid_indices += [i]

    f_min = 1e20
    for i in valid_indices:
        f = obj(sample[i])
        if f < f_min:
            f_min = f
            best_index = i

    return sample[best_index], f_min


def run_it_rs_case(problem, n_int, it):
    s = time.time()
    x = problem["x"]
    p = problem["p"]
    con_list = problem["cons"]
    obj = problem["obj"]
    bounds = np.array([[i[0], i[1]] for i in x.values()])
    sol, val = random_search(obj, con_list, p, bounds, n_int, it)
    e = time.time()
    wct = e - s
    res = {}
    res["wallclock_time"] = wct
    res["solution"] = sol
    res["objective"] = val

    return res
