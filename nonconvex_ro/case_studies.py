from reactor import create_reactor_problem
from heat_exchange import create_heat_exchange_problem
from supply_chain import create_supply_chain_problem
from toy import create_toy_problem
from run_bf import run_bf_case

cases = {}
x, p, con_list, obj = create_reactor_problem(5)
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["reactor"] = problem
x, p, con_list, obj = create_supply_chain_problem(5, 2, 2)
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
print(problem)
cases["heat_exchange"] = problem
x, p, con_list, obj = create_toy_problem()
problem = {"x": x, "p": p, "cons": con_list, "obj": obj}
cases["toy"] = problem


run_bf_case(cases["heat_exchange"], "ipopt")
