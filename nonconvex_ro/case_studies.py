import pprint
import pandas as pd
import signal
from reactor import create_reactor_problem
from heat_exchange import create_heat_exchange_problem
from supply_chain import create_supply_chain_problem
from toy import create_toy_problem
from run_bf import run_bf_case, bf_data
from run_ms import run_ms_case, ms_data
from run_it import run_it_case, it_data
from run_it_rs import run_it_rs_case, it_rs_data
from run_it_slsqp import run_it_slsqp_case, it_slsqp_data

import json

cases = {}
x, p, con_list, obj = create_toy_problem()
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["toy"] = problem
x, p, con_list, obj = create_reactor_problem(5)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["reactor_5"] = problem
x, p, con_list, obj = create_reactor_problem(3)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["reactor_3"] = problem
x, p, con_list, obj = create_reactor_problem(2)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["reactor_2"] = problem
x, p, con_list, obj = create_supply_chain_problem(5, 2, 1)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["supply_5"] = problem
x, p, con_list, obj = create_supply_chain_problem(10, 3, 2)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["supply_10"] = problem
x, p, con_list, obj = create_supply_chain_problem(20, 5, 2)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["supply_20"] = problem
x, p, con_list, obj = create_supply_chain_problem(50, 10, 5)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["supply_50"] = problem
x, p, con_list, obj = create_heat_exchange_problem()
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["heat_exchange"] = problem

problem_res = pd.DataFrame(columns=["case", "variables", "constraints"])
for n, p in cases.items():
    vars = len(p["x"].values())
    cons = len(p["cons"])
    params = int(len(p["p"].values()))

    problem_res = problem_res.append(
        {"case": n, "variables": vars, "constraints": cons, "parameters": params},
        ignore_index=True,
    )
print(problem_res.to_latex(index=False))

# res = run_it_case(cases['supply_5'],'mindtpy',1e-4,2)
# print(res)

methods = {
    "MINLP IE 1": {"fun": run_it_case, "n": 1, "data": it_data},
    "Blankenship-Faulk All": {"fun": run_bf_case, "cut": "All", "data": bf_data},
    "Blankenship-Faulk Single": {"fun": run_bf_case, "cut": "Single", "data": bf_data},
    "Blankenship-Faulk Five": {"fun": run_bf_case, "cut": "Five", "data": bf_data},
    "Restriction of RHS": {"fun": run_ms_case, "data": ms_data},
    "Nonsmooth IE 1, RS": {
        "fun": run_it_rs_case,
        "data": it_rs_data,
        "n": 1,
        "p": 10000,
    },
    "Nonsmooth IE 1, SLSQP": {
        "fun": run_it_slsqp_case,
        "data": it_slsqp_data,
        "n": 1,
        "p": 10000,
    },
    "MINLP IE 2": {"fun": run_it_case, "n": 2, "data": it_data},
    "Nonsmooth IE 2, RS": {
        "fun": run_it_rs_case,
        "data": it_rs_data,
        "n": 2,
        "p": 10000,
    },
    "Nonsmooth IE 2, SLSQP": {
        "fun": run_it_slsqp_case,
        "data": it_slsqp_data,
        "n": 2,
        "p": 10000,
    },
    "MINLP IE 10": {"fun": run_it_case, "n": 10},
    "Nonsmooth IE 10, RS": {
        "fun": run_it_rs_case,
        "data": it_rs_data,
        "n": 10,
        "p": 10000,
    },
    "Nonsmooth IE 10, SLSQP": {
        "fun": run_it_slsqp_case,
        "data": it_slsqp_data,
        "n": 10,
        "p": 10000,
    },
}


class TimeoutException(Exception):  # Custom exception class
    pass


def timeout_handler(signum, frame):  # Custom signal handler
    raise TimeoutException


# Change the behavior of SIGALRM
signal.signal(signal.SIGALRM, timeout_handler)


def run(key, value, m):

    e = 1e-4
    if key.split(" ")[0] == "MINLP":
        n = value["n"]
        res = m(cases[k], "mindtpy", e, n)
    elif key.split(" ")[0] == "Nonsmooth":
        if key.split(" ")[-1] == "search":
            n = value["n"]
            p = value["p"]
            res = m(cases[k], n, p)
        else:
            n = value["n"]
            p = value["p"]
            res = m(cases[k], n, p, e)

    elif key.split(" ")[0] == "Blankenship-Faulk":
        cut = value["cut"]
        res = m(cases[k], "ipopt", e, cut)
    else:
        res = m(cases[k], "ipopt", e)
    return res


timeout = 900
res_overall = {}
for key, value in methods.items():
    m = value["fun"]
    d = value["data"]
    res_cases = {}
    for k in list(cases.keys()):
        print("SOLVING ", k, " USING ", key)
        signal.alarm(int(timeout))

        try:
            res = run(key, value, m)
            res_cases[k] = res
        except TimeoutException:
            res = run(key, value, d)
            res_cases[k] = res
            continue  # continue the for loop if function takes more than 5 second
        except ValueError:
            res = {"ERROR": "FAIL"}
            res_cases[k] = res
            continue

        else:
            signal.alarm(0)
    res_overall[key] = res_cases

pprint.pprint(res_overall)
with open("results.json", "w") as fp:
    json.dump(res_overall, fp)
