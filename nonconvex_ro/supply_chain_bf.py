import matplotlib.pyplot as plt
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
import numpy as np

np.random.seed(100)

I = 12
J = 4
K = 3

p = {}
for i in range(I):
    p["grow_w_" + str(i + 1)] = {"val": 1, "unc": 0.2}
for j in range(J):
    p["proc_w_" + str(j + 1)] = {"val": 3, "unc": 0.2}

loc_I = np.random.uniform(0, 1, (I, 2))
loc_J = np.random.uniform(0, 1, (J, 2))
loc_K = np.random.uniform(0, 1, (K, 2))

for i in range(I):
    for j in range(J):
        D = np.linalg.norm(loc_I[i] - loc_J[j])
        p["grow_T_" + str(i + 1) + str(j + 1)] = {"val": D, "unc": D * 0.1}

for j in range(J):
    for k in range(K):
        D = np.linalg.norm(loc_J[j] - loc_K[k])
        p["proc_T_" + str(j + 1) + str(k + 1)] = {"val": D, "unc": D * 0.1}

for i in range(I):
    p["grow_max" + str(i + 1)] = {"val": 1, "unc": 0.2}
for j in range(J):
    p["proc_max" + str(j + 1)] = {"val": 1, "unc": 0.2}
for k in range(K):
    p["dem_min" + str(k + 1)] = {"val": 1, "unc": 0.02}


param_indices = [0, I, J, I * J, J * K, I, J, K]
s_p = np.cumsum(param_indices)

x_indices = [0, I * J, J * K, 1]
s_x = np.cumsum(x_indices)

x = {}
for i in range(I):
    for j in range(J):
        x["grow_S" + str(i + 1) + str(j + 1)] = [0, 10]
for j in range(J):
    for k in range(K):
        x["proc_S" + str(j + 1) + str(k + 1)] = [0, 10]
x["t"] = [-1e20, 1e20]


def unpack_params(p):
    grow_w = p[s_p[0] : s_p[1]]
    proc_w = p[s_p[1] : s_p[2]]
    grow_T = np.reshape(p[s_p[2] : s_p[3]], (I, J))
    proc_T = np.reshape(p[s_p[3] : s_p[4]], (J, K))
    grow_max = p[s_p[4] : s_p[5]]
    proc_max = p[s_p[5] : s_p[6]]
    dem_min = p[s_p[6] : s_p[7]]
    return grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min


def unpack_vars(x):
    grow_S = np.reshape(x[s_x[0] : s_x[1]], (I, J))
    proc_S = np.reshape(x[s_x[1] : s_x[2]], (J, K))
    t = x[s_x[2] : s_x[3]]
    return grow_S, proc_S, t


def obj(x):
    grow_S, proc_S, t = unpack_vars(x)
    return t[0]


def con_obj(x, p):
    grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min = unpack_params(p)
    grow_S, proc_S, t = unpack_vars(x)
    c = 0
    for i in range(I):
        for j in range(J):
            c += grow_T[i, j] * grow_S[i, j] * grow_w[i]
    return c - t[0]


con_list = [con_obj]

# balance constraint
def make_c(j):
    def c(x, p):
        grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min = unpack_params(p)
        grow_S, proc_S, t = unpack_vars(x)
        c = 0
        for i in range(I):
            c += grow_S[i, j]
        d = 0
        for k in range(K):
            d += proc_S[j, k]
        return c - d

    return c


for j in range(J):
    c = make_c(j)
    con_list += [c]


def make_c(j):
    def c(x, p):
        grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min = unpack_params(p)
        grow_S, proc_S, t = unpack_vars(x)
        c = 0
        for i in range(I):
            c += grow_S[i, j]
        d = 0
        for k in range(K):
            d += proc_S[j, k]
        return d - c

    return c


for j in range(J):
    c = make_c(j)
    con_list += [c]


def make_c(i):
    def c(x, p):
        grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min = unpack_params(p)
        grow_S, proc_S, t = unpack_vars(x)
        c = 0
        for j in range(J):
            c += grow_S[i, j]
        return c - grow_max[i]

    return c


for i in range(I):
    c = make_c(i)
    con_list += [c]


def make_c(j):
    def c(x, p):
        grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min = unpack_params(p)
        grow_S, proc_S, t = unpack_vars(x)
        c = 0
        for k in range(K):
            c += proc_S[j, k]
        return c - proc_max[j]

    return c


for j in range(J):
    c = make_c(j)
    con_list += [c]


def make_c(k):
    def c(x, p):
        grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min = unpack_params(p)
        grow_S, proc_S, t = unpack_vars(x)
        c = 0
        for j in range(J):
            c += proc_S[j, k]
        return -c + dem_min[k]

    return c


for k in range(K):
    c = make_c(k)
    con_list += [c]


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


def plot_solution(x_list, p_list):
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    names = ["Nominal", "Robust"]
    for a in range(2):
        x = x_list[a]
        axs[a].set_title(names[a])
        p = p_list[a]
        grow_w, proc_w, grow_T, proc_T, grow_max, proc_max, dem_min = unpack_params(p)
        grow_S, proc_S, t = unpack_vars(x)
        axs[a].grid(alpha=0.5)
        axs[a].scatter(
            loc_I[:, 0], loc_I[:, 1], c="k", marker="x", label="Production", s=100
        )
        axs[a].scatter(
            loc_J[:, 0], loc_J[:, 1], c="k", marker="o", label="Processing", s=100
        )
        axs[a].scatter(
            loc_K[:, 0], loc_K[:, 1], c="k", marker="^", label="Demand", s=100
        )
        e = 0.75
        for i in range(I):
            for j in range(J):
                if grow_S[i, j] > 0.001:
                    axs[a].arrow(
                        loc_I[i, 0],
                        loc_I[i, 1],
                        (loc_J[j, 0] - loc_I[i, 0]) * e,
                        (loc_J[j, 1] - loc_I[i, 1]) * e,
                        width=grow_S[i, j] * 0.01,
                        color="k",
                        alpha=0.5,
                    )
        e = 0.9
        for j in range(J):
            for k in range(K):
                if proc_S[j, k] > 0.001:
                    axs[a].arrow(
                        loc_J[j, 0],
                        loc_J[j, 1],
                        (loc_K[k, 0] - loc_J[j, 0]) * e,
                        (loc_K[k, 1] - loc_J[j, 1]) * e,
                        width=proc_S[j, k] * 0.01,
                        color="k",
                        alpha=0.5,
                    )
        axs[a].set_xticks(np.linspace(0, 1, 10), ["" for i in range(10)])
        axs[a].set_yticks(np.linspace(0, 1, 10), ["" for i in range(10)])
    axs[0].legend()
    plt.savefig("output_images/supply_chain.pdf")
    return


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
            SolverFactory("ipopt").solve(m_lower)
            p_opt = value(m_lower.p_v[:])
            p_list.append(p_opt)
            print("Constraint violation: ", value(m_lower.obj))
            if value(m_lower.obj) > epsilon:
                robust = False
                m_upper.cons.add(expr=con(x_vars, p_opt) <= 0)
        except ValueError:
            continue

    if robust is True:

        print("\nRobust solution: ", x_opt)
        break

    SolverFactory("ipopt").solve(m_upper)

    x_opt = value(m_upper.x_v[:])
    x_list.append(x_opt)


plot_solution([x_list[0], x_list[-1]], [p_nominal, p_nominal])
