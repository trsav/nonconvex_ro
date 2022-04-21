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
    exp,
)
from pyomo.opt import SolverFactory

n = 5

p = {}
p["A"] = {"val": 1.4, "unc": 0.3}
p["R"] = {"val": 8.314, "unc": 0}
p["E"] = {"val": 3200, "unc": 200}
p["v"] = {"val": 2, "unc": 0.2}
for i in range(n):
    p["T" + str(i + 1)] = {"val": 400, "unc": 10 + 10 * i}

x = {}
for i in range(n):
    x["V" + str(i + 1)] = [1, 100]


def obj(x):
    V = x
    return sum(V)


def con1(x, p):
    V = x
    A, R, E, v = p[:4]
    T = p[4:]
    X = 0
    for i in range(len(V)):
        tau = V[i] / v
        k = A * exp(-E / (R * T[i]))
        Da = tau * k
        X = (X + Da) / (1 + Da)
    return 0.9 - X


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
