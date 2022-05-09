from pyomo.environ import (
    ConcreteModel,
    Var,
    Objective,
    Constraint,
    SolverFactory,
    value,
)
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np


def obj(x):
    x1, x2 = x
    return x2 - 2 * x1 ** 2


def con(x, p_v):
    x1, x2 = x
    p = p_v[0]
    return (p * p) * 2 * x1 ** 2 - (p * p * p * p) + x1 ** 2 - x2 - 0.5 * x1


n = 600
x1 = np.linspace(-2.25, 2.25, n)
x2 = np.linspace(-2.25, 2.25, n)
X1, X2 = np.meshgrid(x1, x2)
p_list = np.linspace(0, 2, 14)

fig, ax = plt.subplots(figsize=(6, 5))
ax.set_xlabel("$x_1$")
ax.set_ylabel("$x_2$")
Z_obj = np.zeros((n, n))
Z = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        Z_obj[i, j] = obj([X1[i, j], X2[i, j]])


# Z_obj = Z_obj.T
plt.contourf(X1, X2, Z_obj, 100, cmap="plasma")
sol_list = []
for p in p_list:
    m = ConcreteModel()
    m.x1 = Var(bounds=(-2, 2))
    m.x2 = Var(bounds=(-2, 2))
    m.f = Objective(expr=m.x2 - 2 * m.x1 ** 2)
    m.c = Constraint(
        expr=2 * p ** 2 * m.x1 ** 2 - p ** 4 + m.x1 ** 2 - m.x2 - 0.5 * m.x1 <= 0
    )
    SolverFactory("baron").solve(m)
    sol = [value(m.x1), value(m.x2)]
    sol_list.append(sol)
    Z = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            Z_obj[i, j] = obj([X1[i, j], X2[i, j]])

            Z[i, j] = con([X1[i, j], X2[i, j]], [p])
            if Z[i, j] < 0:
                Z[i, j] = 0
    # Z = Z.T
    ax.contour(
        X1,
        X2,
        Z,
        [0],
        cmap=colors.ListedColormap(["black"]),
        linestyles="dashed",
        alpha=0.7,
    )
# for sol in sol_list:
#     ax.scatter(sol[0], sol[1], c="w", zorder=2)

# rect = patches.Rectangle(
#     (-2, -2), 4, 4, linewidth=1, edgecolor="k", facecolor="none", ls="dashed"
# )

# Add the patch to the Axes
# ax.add_patch(rect)
plt.savefig("output_images/robust_example.pdf")
