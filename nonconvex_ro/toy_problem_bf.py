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
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors


# uncertain variables
p = {}
p["p"] = {"val": 1, "unc": 1}


def con(x, p_v):
    x1, x2 = x
    p = p_v[0]
    return 2 * x1 ** 2 * p ** 2 - p ** 4 + x1 ** 2 - x2 - 0.5 * x1


def obj(x):
    x1, x2 = x
    return x2 - 2 * x1 ** 2


con_list = [con]

x = {"x1": [-2, 2], "x2": [-2, 2]}


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


SolverFactory("baron").solve(m_upper)
x_opt = value(m_upper.x_v[:])


def plot_upper(x_list, p_list):
    fig, axs = plt.subplots(1, len(x_list), figsize=(16, 3))
    plt.subplots_adjust(left=0.025, right=0.975)
    n = 500
    levels = 20
    x1 = np.linspace(x["x1"][0], x["x1"][1], n)
    x2 = np.linspace(x["x2"][0], x["x2"][1], n)
    X1, X2 = np.meshgrid(x1, x2)
    Z = np.zeros((n, n))
    Z_con = np.zeros_like(Z)
    for i in range(n):
        for j in range(n):
            x_eval = [X1[i, j], X2[i, j]]
            Z[i, j] = obj(x_eval)
    for i in range(len(x_list)):
        axs[i].contourf(X1, X2, Z, levels)
        axs[i].set_xticks([], [])
        axs[i].set_yticks([], [])

    Z_feas = np.zeros((n, n))
    for k in range(len(x_list)):
        for p in p_list[: k + 1]:
            Z_con_line = np.zeros_like(Z)
            Z_con = np.zeros_like(Z)
            for i in range(n):
                for j in range(n):
                    x_eval = [X1[i, j], X2[i, j]]
                    Z_con[i, j] = con(x_eval, p)
                    if Z_con[i, j] <= 0:
                        Z_con[i, j] = np.NaN
                        Z_con_line[i, j] = 0
                    else:
                        Z_con[i, j] = 1
                        Z_con_line[i, j] = 1
            axs[k].contourf(
                X1, X2, Z_con, cmap=colors.ListedColormap(["black"]), alpha=0.25
            )
            axs[k].contour(
                X1,
                X2,
                Z_con_line,
                [0],
                cmap=colors.ListedColormap(["black"]),
                linestyles="dashed",
            )

            if k == len(x_list) - 1:
                Z_feas += Z_con_line

        x_opt = x_list[k]
        axs[k].scatter(x_opt[0], x_opt[1], c="red", edgecolors="black", s=50)
        if k != 0:
            x_prev = x_list[k - 1]
            axs[k].scatter(x_prev[0], x_prev[1], c="blue", edgecolors="black", s=50)

    for i in range(n):
        for j in range(n):
            if Z_feas[i, j] <= 0:
                Z_feas[i, j] = 0
            else:
                Z_feas[i, j] = 1
    for k in range(len(x_list)):
        axs[k].contour(
            X1,
            X2,
            Z_feas,
            [0],
            cmap=colors.ListedColormap(["white"]),
            linestyles="dashed",
        )

    plt.savefig("output_images/toy_bf_results.pdf")
    return


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
        SolverFactory("baron").solve(m_lower)

        p_opt = value(m_lower.p_v[:])
        p_list.append(p_opt)
        print("Constraint violation: ", value(m_lower.obj))
        if value(m_lower.obj) > epsilon:
            robust = False
            m_upper.cons.add(expr=con(x_vars, p_opt) <= 0)
    # plot_upper(x_opt,p_list)
    if robust is True:

        plot_upper(x_list, p_list)
        print("\nRobust solution: ", x_opt)
        break

    SolverFactory("baron").solve(m_upper)

    x_opt = value(m_upper.x_v[:])
    x_list.append(x_opt)
