from reactor import create_reactor_problem
from heat_exchange import create_heat_exchange_problem
from supply_chain import create_supply_chain_problem
from toy import create_toy_problem
from run_bf import run_bf_case
from run_ms import run_ms_case
from tqdm import tqdm


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


methods = {"Blankenship-Faulk": run_bf_case, "Restriction of RHS": run_ms_case}
methods = {"Restriction of RHS": run_ms_case}
e = 1e-4

res_overall = {}
for key, value in methods.items():
    res_cases = {}
    for k in tqdm(list(cases.keys())):
        res = value(cases[k], "ipopt", e)
        res_cases[k] = res
    res_overall[key] = res_cases

print(res_overall)
