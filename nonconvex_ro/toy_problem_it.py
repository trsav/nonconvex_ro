from pyomo.environ import (
    ConcreteModel,
    Var,
    Reals,
    Set,
    ConstraintList,
    Objective,
    minimize,
    SolverFactory,
    value,
)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from interval_definitions import Interval


# uncertain variables
p = {}
p["p"] = {"val": 1, "unc": 1}


def con_int(x, p_int):
    x1, x2 = x
    p = p_int
    return 2 * x1 ** 2 * (p ** 2).u + (-(p ** 4)).u + x1 ** 2 - x2 - 0.5 * x1


def con_norm(x, p_v):
    x1, x2 = x
    p = p_v[0]
    return 2 * x1 ** 2 * (p ** 2) - (p ** 4) + x1 ** 2 - x2 - 0.5 * x1


def obj(x):
    x1, x2 = x
    return x2 - 2 * x1 ** 2


con_list = [con_int]


x = {"x1": [-2, 2], "x2": [-2, 2]}


def var_bounds(m, i):
    return (x[i][0], x[i][1])


def uncertain_bounds(m, i):
    return (p[i]["val"] - p[i]["unc"], p[i]["val"] + p[i]["unc"])


epsilon = 1e-4

n_list = [2, 3, 4, 5, 6, 7, 8, 9]
x_list = []
for n_int in n_list:
    m_upper = ConcreteModel()
    m_upper.x = Set(initialize=x.keys())
    m_upper.x_v = Var(m_upper.x, domain=Reals, bounds=var_bounds)
    p_nominal = [p[key]["val"] for key in p.keys()]
    p_l = [p[key]["val"] - p[key]["unc"] for key in p.keys()]
    p_u = [p[key]["val"] + p[key]["unc"] for key in p.keys()]

    x_vars = [m_upper.x_v[i] for i in x.keys()]
    m_upper.cons = ConstraintList()
    p_list = np.linspace(p_l, p_u, n_int)
    for i in range(len(p_list) - 1):
        for con in con_list:
            m_upper.cons.add(expr=con(x_vars, Interval(p_list[i], p_list[i + 1])) <= 0)
    m_upper.obj = Objective(expr=obj(x_vars), sense=minimize)

    SolverFactory("baron").solve(m_upper)
    x_opt = value(m_upper.x_v[:])
    x_list.append(x_opt)


def plot_upper(x_list, n_list):
    fig, axs = plt.subplots(1, len(x_list), figsize=(16, 3))
    plt.subplots_adjust(left=0.025, right=0.975)
    n = 500
    levels = 40
    x1 = np.linspace(x["x1"][0], x["x1"][1], n)
    x2 = np.linspace(x["x2"][0], x["x2"][1], n)
    X1, X2 = np.meshgrid(x1, x2)
    Z = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            x_eval = [X1[i, j], X2[i, j]]
            Z[i, j] = obj(x_eval)
    for ax in axs:
        ax.contourf(X1, X2, Z, levels, cmap="plasma")
        ax.set_xticks([], [])
        ax.set_yticks([], [])

    for k in range(len(x_list)):
        p_list = np.linspace(p_l, p_u, n_list[k])
        for p_i in range(len(p_list) - 1):
            Z_con_line = np.zeros_like(Z)
            Z_con = np.zeros_like(Z)
            for i in range(n):
                for j in range(n):
                    x_eval = [X1[i, j], X2[i, j]]
                    Z_con[i, j] = con_int(
                        x_eval, Interval(p_list[p_i], p_list[p_i + 1])
                    )
                    if Z_con[i, j] <= 0:
                        Z_con[i, j] = np.NaN
                        Z_con_line[i, j] = 0
                    else:
                        Z_con[i, j] = 1
                        Z_con_line[i, j] = 1
            axs[k].contourf(
                X1, X2, Z_con, cmap=colors.ListedColormap(["black"]), alpha=0.35
            )
            axs[k].contour(
                X1,
                X2,
                Z_con_line,
                [0],
                cmap=colors.ListedColormap(["black"]),
                linestyles="dashed",
            )

    p_robust_feas = np.linspace(0, 2, 20)
    Z_feas = np.zeros((n, n))
    print("plotting robust feasible region...")
    for p in p_robust_feas:
        Z_con = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                x_eval = [X1[i, j], X2[i, j]]
                Z_con[i, j] = con_norm(x_eval, [p])
                if Z_con[i, j] <= 0:
                    Z_con[i, j] = 0
                else:
                    Z_con[i, j] = 1
        Z_feas += Z_con

    for i in range(n):
        for j in range(n):
            if Z_feas[i, j] <= 0:
                Z_feas[i, j] = 0
            else:
                Z_feas[i, j] = 1

    for k in range(len(x_list)):
        x_opt = x_list[k]
        axs[k].contour(
            X1,
            X2,
            Z_feas,
            [0],
            cmap=colors.ListedColormap(["white"]),
            linestyles="dashed",
        )
        axs[k].scatter(x_opt[0], x_opt[1], c="r")
        if n_list[k] - 1 == 1:
            axs[k].set_title(str(n_list[k] - 1) + " interval")
        else:
            axs[k].set_title(str(n_list[k] - 1) + " intervals")

    plt.savefig("output_images/toy_it_results.pdf")
    return


plot_upper(x_list, n_list)
