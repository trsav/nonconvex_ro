from pyomo.environ import (
    ConcreteModel,
    Var,
    Reals,
    value,
    Set,
    ConstraintList,
    Objective,
    minimize,
    maximize,
)
from pyomo.opt import SolverFactory


p = {}
p["A"] = {"val": 1.4, "unc": 0.3}
p["B"] = {"val": 1.4, "unc": 0.3}

x = {}
x["z"] = [1, 10]
x["y"] = [1, 10]


def obj(x):
    x, y = x
    return x + y


def con1(x, p):
    z, y = x
    A, B = p
    return z + A + y + B


con_list = [con1]


def var_bounds(m, i):
    return (x[i][0], x[i][1])


def uncertain_bounds(m, i):
    return (p[i]["val"] - p[i]["unc"], p[i]["val"] + p[i]["unc"])


epsilon = 1e-4

m_upper = ConcreteModel()
m_upper.x = Set(initialize=x.keys())
m_upper.x_v = Var(m_upper.x, domain=Reals, bounds=var_bounds)
p_nominal = [p[key]["val"] for key in p.keys()]
x_vars = [m_upper.x_v[i] for i in x.keys()]
m_upper.cons = ConstraintList()
for con in con_list:
    m_upper.cons.add(expr=con(x_vars, p_nominal) <= 0)
m_upper.obj = Objective(expr=obj(x_vars), sense=minimize)


SolverFactory("ipopt").solve(m_upper)
x_opt = value(m_upper.x_v[:])
print("\nNominal solution: ", x_opt, "\n")

p_list = [p_nominal]
x_list = [x_opt]

robust = True
while True:
    robust = True

    for con in con_list:

        m_lower = ConcreteModel()
        m_lower.p = Set(initialize=p.keys())
        m_lower.p_v = Var(m_lower.p, domain=Reals, bounds=uncertain_bounds)
        param_vars = [m_lower.p_v[str(i)] for i in p.keys()]
        m_lower.obj = Objective(expr=con(x_opt, param_vars), sense=maximize)
        SolverFactory("ipopt").solve(m_lower)

        p_opt = value(m_lower.p_v[:])
        p_list.append(p_opt)
        print("Constraint violation: ", value(m_lower.obj))
        if value(m_lower.obj) > epsilon:
            robust = False
            m_upper.cons.add(expr=con(x_vars, p_opt) <= 0)
    # plot_upper(x_opt,p_list)
    if robust is True:

        print("\nRobust solution: ", x_opt)
        break

    SolverFactory("ipopt").solve(m_upper)

    x_opt = value(m_upper.x_v[:])
    x_list.append(x_opt)
