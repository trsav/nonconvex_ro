from pyomo.environ import (
    ConcreteModel,
    Var,
    Reals,
    value,
    Set,
    ConstraintList,
    Objective,
    Param,
    Any,
    minimize,
    maximize,
    TerminationCondition,
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


x = {"x1": [-2, 2], "x2": [-2, 2]}


def var_bounds(m, i):
    return (x[i][0], x[i][1])


def uncertain_bounds(m, i):
    return (p[i]["val"] - p[i]["unc"], p[i]["val"] + p[i]["unc"])


e_f = 1e-4
r = 2

p_nominal = [p[key]["val"] for key in p.keys()]
p_list = [p_nominal]

f_ubd = np.Infinity
f_lbd = -np.Infinity

LBD = ConcreteModel()
LBD.x = Set(initialize=x.keys())
LBD.x_v = Var(LBD.x, domain=Reals, bounds=var_bounds)
p_nominal = [p[key]["val"] for key in p.keys()]
x_vars = [LBD.x_v[i] for i in x.keys()]
LBD.cons = ConstraintList()
LBD.cons.add(expr=con(x_vars, p_nominal) <= 0)
LBD.obj = Objective(expr=obj(x_vars), sense=minimize)

UBD = ConcreteModel()
UBD.x = Set(initialize=x.keys())
UBD.x_v = Var(UBD.x, domain=Reals, bounds=var_bounds)
p_nominal = [p[key]["val"] for key in p.keys()]
x_vars = [UBD.x_v[i] for i in x.keys()]
UBD.cons = ConstraintList()
UBD.e_g = Param(initialize=2, mutable=True, within=Any)
UBD.cons.add(expr=con(x_vars, p_nominal) <= -UBD.e_g)
UBD.obj = Objective(expr=obj(x_vars), sense=minimize)


def build_LLP(x_opt):
    LLP = ConcreteModel()
    LLP.p = Set(initialize=p.keys())
    LLP.p_v = Var(LLP.p, domain=Reals, bounds=uncertain_bounds)
    param_vars = [LLP.p_v[str(i)] for i in p.keys()]
    LLP.obj = Objective(expr=con(x_opt, param_vars), sense=maximize)
    SolverFactory("baron").solve(LLP)
    return LLP


def plot_problem(x_list, LBD_list, UBD_list, e_g_list):
    x_list = x_list[:8]
    LBD_list = LBD_list[:8]
    UBD_list = UBD_list[:8]
    fig, axs = plt.subplots(2, len(x_list), figsize=(16, 6))
    plt.subplots_adjust(left=0.025, right=0.975)
    n = 200
    levels = 20
    x1 = np.linspace(x["x1"][0], x["x1"][1], n)
    x2 = np.linspace(x["x2"][0], x["x2"][1], n)
    X1, X2 = np.meshgrid(x1, x2)
    Z = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            x_eval = [X1[i, j], X2[i, j]]
            Z[i, j] = obj(x_eval)
    for i in range(len(x_list)):
        for j in range(2):
            axs[j, i].contourf(X1, X2, Z, levels)
            axs[j, i].set_xticks([], [])
            axs[j, i].set_yticks([], [])

    Z_feas = np.zeros((n, n))
    for k in range(len(x_list)):
        for p in LBD_list[: k + 1]:
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

            axs[0, k].contourf(
                X1, X2, Z_con, cmap=colors.ListedColormap(["black"]), alpha=0.25
            )
            axs[0, k].contour(
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
        axs[0, k].scatter(x_opt[0], x_opt[1], c="red", edgecolors="black", s=50)
        if k != 0:
            x_prev = x_list[k - 1]
            axs[0, k].scatter(x_prev[0], x_prev[1], c="blue", edgecolors="black", s=50)

        for m in range(len(UBD_list[: k + 1])):
            if UBD_list[m] is not None:
                Z_con_line = np.zeros_like(Z)
                Z_con = np.zeros_like(Z)
                for i in range(n):
                    for j in range(n):
                        x_eval = [X1[i, j], X2[i, j]]
                        Z_con[i, j] = con(x_eval, UBD_list[m])
                        if Z_con[i, j] <= -e_g_list[k]:
                            Z_con[i, j] = np.NaN
                            Z_con_line[i, j] = 0
                        else:
                            Z_con[i, j] = 1
                            Z_con_line[i, j] = 1

                axs[1, k].contourf(
                    X1, X2, Z_con, cmap=colors.ListedColormap(["red"]), alpha=0.25
                )
                axs[1, k].contour(
                    X1,
                    X2,
                    Z_con_line,
                    [0],
                    cmap=colors.ListedColormap(["red"]),
                    linestyles="dashed",
                )
    for i in range(n):
        for j in range(n):
            if Z_feas[i, j] <= 0:
                Z_feas[i, j] = 0
            else:
                Z_feas[i, j] = 1
    for k in range(len(x_list)):
        axs[0, k].contour(
            X1,
            X2,
            Z_feas,
            [0],
            cmap=colors.ListedColormap(["white"]),
            linestyles="dashed",
        )
        axs[1, k].contour(
            X1,
            X2,
            Z_feas,
            [0],
            cmap=colors.ListedColormap(["white"]),
            linestyles="dashed",
        )

    plt.savefig("output_images/toy_ms_results.pdf")
    return


LBD_list = [p_nominal]
UBD_list = [p_nominal]

lb_store = []
ub_store = []

x_list = []
e_g_list = []
while f_ubd - f_lbd > e_f:
    print("SIP Upper Bound: ", f_ubd, "\nSIP Lower Bound: ", f_lbd, "\n")
    SolverFactory("baron").solve(LBD)
    f_lbd = value(LBD.obj)
    lb_store.append(f_lbd)
    ub_store.append(f_ubd)
    x_opt = value(LBD.x_v[:])
    x_list.append(x_opt)
    e_g_list.append(value(UBD.e_g))

    # plot_ubd_lbd(x_opt,LBD_list,UBD_list,UBD)

    LLP = build_LLP(x_opt)
    SolverFactory("baron").solve(LLP)

    if value(LLP.obj) < 0:
        f_ubd = obj(x_opt)
        print("Robust solution: ", x_opt)
        break

    p_opt = value(LLP.p_v[:])
    LBD_list.append(p_opt)
    # plot_ubd_lbd(x_opt,LBD_list,UBD_list,UBD)
    LBD.cons.add(expr=con([LBD.x_v[i] for i in x.keys()], p_opt) <= 0)

    res = SolverFactory("baron").solve(UBD)

    if res.solver.termination_condition != TerminationCondition.infeasible:
        x_opt = value(UBD.x_v[:])
        #

        LLP = build_LLP(x_opt)
        SolverFactory("baron").solve(LLP)
        v = value(LLP.obj)

        if v < 0:
            f_x = obj(x_opt)
            if f_x <= f_ubd:
                f_ubd = f_x

            UBD_list.append(None)
            UBD.e_g = value(UBD.e_g) / r
        else:
            p_opt = value(LLP.p_v[:])
            UBD_list.append(p_opt)
            UBD.cons.add(expr=con([UBD.x_v[i] for i in x.keys()], p_opt) <= -UBD.e_g)
    else:
        UBD.e_g = value(UBD.e_g) / r

plot_problem(x_list, LBD_list, UBD_list, e_g_list)

plt.figure(figsize=(6, 4))
plt.grid(alpha=0.3)
plt.plot(
    np.arange(len(lb_store)),
    lb_store,
    c="k",
    linewidth=1,
    label="SIP Lower Bound",
    linestyle="dashed",
)
plt.plot(
    np.arange(len(ub_store)), ub_store, c="k", linewidth=1, label="SIP Upper Bound"
)
plt.xlabel("Iterations")
ticks = [int(i) for i in range(len(lb_store)) if i % 2 == 0]
plt.xticks(ticks, ticks)
plt.ylabel("$f(x)$")
plt.legend()
plt.savefig("output_images/toy_ms_plot.pdf")
