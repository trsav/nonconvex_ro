import pprint
import signal
from reactor import create_reactor_problem
from heat_exchange import create_heat_exchange_problem
from supply_chain import create_supply_chain_problem
from toy import create_toy_problem
from run_bf import run_bf_case
from run_ms import run_ms_case

# from run_it import run_it_case
# from run_it_rs import run_it_rs_case
# from run_it_slsqp import run_it_slsqp_case
# from tqdm import tqdm
import json

cases = {}
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
x, p, con_list, obj = create_toy_problem()
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["toy"] = problem


# res = run_it_case(cases['reactor_3'],'bonmin',1e-4,2)
# print(res)

methods = {
    "Blankenship-Faulk All": {"fun": run_bf_case, "cut": "All"},
    "Blankenship-Faulk Single": {"fun": run_bf_case, "cut": "Single"},
    "Blankenship-Faulk Five": {"fun": run_bf_case, "cut": "Five"},
    "Restriction of RHS": {"fun": run_ms_case},
    #     "MINLP 1 interval extensions": {"fun": run_it_case, "n": 1},
    #     "Nonsmooth 1 interval extensions, random search": {
    #         "fun": run_it_rs_case,
    #         "n": 1,
    #         "p": 1000,
    #     },
    #     "Nonsmooth 1 interval extensions, SLSQP": {
    #         "fun": run_it_slsqp_case,
    #         "n": 1,
    #         "p": 1000,
    #     },
    #     "MINLP 10 interval extensions": {"fun": run_it_case, "n": 10},
    #     "Nonsmooth 10 interval extensions, random search": {
    #         "fun": run_it_rs_case,
    #         "n": 10,
    #         "p": 1000,
    #     },
    #     "Nonsmooth 10 interval extensions, SLSQP": {
    #         "fun": run_it_slsqp_case,
    #         "n": 10,
    #         "p": 1000,
    #     },
    #     "MINLP 100 interval extensions": {"fun": run_it_case, "n": 100},
    #     "Nonsmooth 100 interval extensions, random search": {
    #         "fun": run_it_rs_case,
    #         "n": 100,
    #         "p": 1000,
    #     },
    #     "Nonsmooth 100 interval extensions, SLSQP": {
    #         "fun": run_it_slsqp_case,
    #         "n": 100,
    #         "p": 1000,
    #     },
}


class TimeoutException(Exception):  # Custom exception class
    pass


def timeout_handler(signum, frame):  # Custom signal handler
    raise TimeoutException


# Change the behavior of SIGALRM
signal.signal(signal.SIGALRM, timeout_handler)


def run(key, value, m):
    if key.split(" ")[0] == "MINLP":
        n = value["n"]
        res = m(cases[k], "bonmin", e, n)
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


e = 1e-5
timeout = 1000
res_overall = {}
for key, value in methods.items():
    m = value["fun"]
    res_cases = {}
    for k in list(cases.keys()):
        print("SOLVING ", k, " USING ", key)
        signal.alarm(int(timeout))

        try:
            res = run(key, value, m)
            res_cases[k] = res
        except TimeoutException:
            res = {"ERROR":'TIMEOUT'}
            res_cases[k] = res
            continue  # continue the for loop if function takes more than 5 second
        except ValueError:
            res = {'ERROR':'FAIL'}
            res_cases[k] = res
            continue

        else:
            signal.alarm(0)
    res_overall[key] = res_cases

pprint.pprint(res_overall)
with open("results.json", "w") as fp:
    json.dump(res_overall, fp)
