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


def run_bf_case(problem, solver):
    x = problem["x"]
    p = problem["p"]
    con_list = problem["cons"]
    obj = problem["obj"]

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

    SolverFactory(solver).solve(m_upper)
    x_opt = value(m_upper.x_v[:])

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
            try:
                SolverFactory(solver).solve(m_lower)
                p_opt = value(m_lower.p_v[:])
                p_list.append(p_opt)
                print("Constraint violation: ", value(m_lower.obj))
                for k in range(len(p_opt)):
                    if p_opt[k] is None:
                        p_opt[k] = p_nominal[k]
                if value(m_lower.obj) > epsilon:
                    robust = False
                    m_upper.cons.add(expr=con(x_vars, p_opt) <= 0)
            except ValueError:
                continue
        if robust is True:
            print("\nRobust solution: ", x_opt)
            break
        SolverFactory(solver).solve(m_upper)
        x_opt = value(m_upper.x_v[:])
        x_list.append(x_opt)
    return
