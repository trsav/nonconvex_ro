def create_heat_exchange_problem():
    p = {}
    p["Q"] = {"val": 3.1 * 10 ** 6, "unc": 0}
    p["T_2_in"] = {"val": 460, "unc": 5}
    p["T_1_in"] = {"val": 300, "unc": 5}
    p["M_1"] = {"val": 25.4, "unc": 0.5}
    p["M_2"] = {"val": 25, "unc": 0.5}
    p["rho_1"] = {"val": 0.54, "unc": 0.1}
    p["rho_2"] = {"val": 4.86, "unc": 0.75}
    p["eta"] = {"val": 3.2 * 10 ** -5, "unc": 0.1 * 10 ** -5}
    p["Pr"] = {"val": 0.69, "unc": 0.1}
    p["con"] = {"val": 0.05, "unc": 0.005}
    p["con_ss"] = {"val": 15, "unc": 1}
    p["cp"] = {"val": 1060, "unc": 100}
    p["K"] = {"val": 0.8, "unc": 0.1}

    x = {
        "w": [0.05 * 10 ** -3, 0.3 * 10 ** -3],
        "s": [1 * 10 ** -3, 3 * 10 ** -3],
        "a": [0.1 * 10 ** -3, 0.8 * 10 ** -3],
        "b": [3 * 10 ** -3, 10 * 10 ** -3],
        "W": [0.5, 3],
        "L": [0.5, 3],
        "H": [0.5, 3],
    }

    def HE_model(x, p):
        w, s, a, b, W, L, H = x
        Q, T_2_in, T_1_in, M_1, M_2, rho_1, rho_2, eta, Pr, con, con_ss, cp, K = p
        h = b - a - w
        Dh = (4 * h * s) / (2 * (h + s))
        S1 = (W * h * s) / (w + s) * (H / (2 * b))
        S2 = (L * h * s) / (w + s) * (H / (2 * b))
        A = ((2 * W * (h + s) * L) / (w + s)) * (H / (2 * b))
        Af = ((2 * W * h * L) / (w + s)) * (H / (2 * b))
        Ap = (2 * L * W * H) / (2 * b)
        sigma_1 = S1 / (W * H)
        sigma_2 = S2 / (W * H)
        v1 = M_1 / (rho_1 * S1)
        v2 = M_2 / (rho_2 * S2)
        Re_1 = (v1 * Dh * rho_1) / eta
        Re_2 = (v2 * Dh * rho_2) / eta
        j_1 = 0.04 * Re_1 ** (-0.28)
        j_2 = 0.04 * Re_2 ** (-0.28)
        Nu_1 = j_1 * Re_1 * (Pr ** (1 / 3))
        Nu_2 = j_2 * Re_2 * Pr ** (1 / 3)
        alpha_1 = (Nu_1 * con) / Dh
        alpha_2 = (Nu_2 * con) / Dh
        f_eff_1 = (((2 * alpha_1) / (con_ss * w)) ** 0.5) * (h / 2)
        f_eff_2 = (((2 * alpha_2) / (con_ss * w)) ** 0.5) * (h / 2)
        tan_1_approx = f_eff_1 / (
            1 + ((f_eff_1 ** 2) / (3 + ((f_eff_1 ** 2) / (5 + f_eff_1 ** 2))))
        )
        tan_2_approx = f_eff_2 / (
            1 + ((f_eff_2 ** 2) / (3 + ((f_eff_2 ** 2) / (5 + f_eff_2 ** 2))))
        )
        n_eq_1 = tan_1_approx / f_eff_1
        n_eq_2 = tan_2_approx / f_eff_2
        A_1_eff = A - Af * (1 - n_eq_1)
        A_2_eff = A - Af * (1 - n_eq_2)
        alpha_p1 = (alpha_1 * A_1_eff) / Ap
        alpha_p2 = (alpha_2 * A_2_eff) / Ap
        U_p = 1 / ((1 / alpha_p1) + (a / con_ss) + (1 / alpha_p2))
        T_2_out = T_2_in - Q / (U_p * Ap)
        # T_1_out = T_1_in + Q / (U_p * Ap)
        f1 = sigma_1 * (Re_1) ** (-0.44)
        f2 = sigma_2 * (Re_2) ** (-0.44)
        DP_1 = (((v1 * rho_1) ** 2) / (2 * rho_1)) * (K + (4 * f1 * (L / Dh)))
        DP_2 = (((v2 * rho_2) ** 2) / (2 * rho_2)) * (K + (4 * f2 * (L / Dh)))
        return T_2_out, DP_1, DP_2, A

    def obj(x):
        w, s, a, b, W, L, H = x
        h = b - a - w
        A = ((2 * W * (h + s) * L) / (w + s)) * (H / (2 * b))
        return A

    def con1(x, p):
        w, s, a, b, W, L, H = x
        Q, T_2_in, T_1_in, M_1, M_2, rho_1, rho_2, eta, Pr, con, con_ss, cp, K = p
        h = b - a - w
        Dh = (4 * h * s) / (2 * (h + s))
        S1 = (W * h * s) / (w + s) * (H / (2 * b))
        S2 = (L * h * s) / (w + s) * (H / (2 * b))
        A = ((2 * W * (h + s) * L) / (w + s)) * (H / (2 * b))
        Af = ((2 * W * h * L) / (w + s)) * (H / (2 * b))
        Ap = (2 * L * W * H) / (2 * b)
        v1 = M_1 * (1 / (rho_1 * S1))
        v2 = M_2 * (1 / (rho_2 * S2))
        Re_1 = (v1 * Dh * rho_1) * (1 / eta)
        Re_2 = (v2 * Dh * rho_2) * (1 / eta)
        j_1 = 0.04 * (1 / (Re_1 ** 0.28))
        j_2 = 0.04 * (1 / (Re_2 ** 0.28))
        Nu_1 = j_1 * Re_1 * (Pr ** (1 / 3))
        Nu_2 = j_2 * Re_2 * Pr ** (1 / 3)
        alpha_1 = (Nu_1 * con) * (1 / Dh)
        alpha_2 = (Nu_2 * con) * (1 / Dh)
        f_eff_1 = (((2 * alpha_1) * (1 / (con_ss * w))) ** 0.5) * (h * (1 / 2))
        f_eff_2 = (((2 * alpha_2) * (1 / (con_ss * w))) ** 0.5) * (h * (1 / 2))
        tan_1_approx = f_eff_1 * (
            1
            / (
                1
                + (
                    (f_eff_1 ** 2)
                    * (1 / (3 + ((f_eff_1 ** 2) * (1 / (5 + f_eff_1 ** 2)))))
                )
            )
        )
        tan_2_approx = f_eff_2 * (
            1
            / (
                1
                + (
                    (f_eff_2 ** 2)
                    * (1 / (3 + ((f_eff_2 ** 2) * (1 / (5 + f_eff_2 ** 2)))))
                )
            )
        )
        n_eq_1 = tan_1_approx * (1 / f_eff_1)
        n_eq_2 = tan_2_approx * (1 / f_eff_2)
        A_1_eff = A - Af * (1 - n_eq_1)
        A_2_eff = A - Af * (1 - n_eq_2)
        alpha_p1 = (alpha_1 * A_1_eff) * (1 / Ap)
        alpha_p2 = (alpha_2 * A_2_eff) * (1 / Ap)
        U_p = 1 / ((1 / alpha_p1) + (a * (1 / con_ss)) + (1 / alpha_p2))
        T_2_out = T_2_in - Q * (1 / (U_p * Ap))
        return T_2_out - 400

    def con2(x, p):
        w, s, a, b, W, L, H = x
        Q, T_2_in, T_1_in, M_1, M_2, rho_1, rho_2, eta, Pr, con, con_ss, cp, K = p
        h = b - a - w
        Dh = (4 * h * s) / (2 * (h + s))
        S1 = (W * h * s) / (w + s) * (H / (2 * b))
        sigma_1 = S1 * (1 / (W * H))
        v1 = M_1 * (1 / (rho_1 * S1))
        Re_1 = (v1 * Dh * rho_1) * (1 / eta)
        f1 = sigma_1 * (1 / ((Re_1) ** (0.44)))
        DP_1 = (((v1 * rho_1) ** 2) * (1 / (2 * rho_1))) * (
            K + (4 * f1 * (L * (1 / Dh)))
        )
        return DP_1 - 1500

    def con3(x, p):
        w, s, a, b, W, L, H = x
        Q, T_2_in, T_1_in, M_1, M_2, rho_1, rho_2, eta, Pr, con, con_ss, cp, K = p
        h = b - a - w
        Dh = (4 * h * s) / (2 * (h + s))
        S2 = (L * h * s) / (w + s) * (H / (2 * b))
        sigma_2 = S2 * (1 / (W * H))
        v2 = M_2 * (1 / (rho_2 * S2))
        Re_2 = (v2 * Dh * rho_2) * (1 / eta)
        f2 = sigma_2 * (1 / ((Re_2) ** (0.44)))
        DP_2 = (((v2 * rho_2) ** 2) * (1 / (2 * rho_2))) * (
            K + (4 * f2 * (L * (1 / Dh)))
        )
        return DP_2 - 500

    con_list = [con1, con2, con3]
    return x, p, con_list, obj


# # uncomment to run plot

# x,p,con_list,obj = create_heat_exchange_problem()


# def var_bounds(m, i):
#     return (x[i][0], x[i][1])


# def uncertain_bounds(m, i):
#     return (p[i]["val"] - p[i]["unc"], p[i]["val"] + p[i]["unc"])


# epsilon = 1e-6

# m_upper = ConcreteModel()
# m_upper.x = Set(initialize=x.keys())
# m_upper.x_v = Var(m_upper.x, domain=Reals, bounds=var_bounds)
# p_nominal = [p[key]["val"] for key in p.keys()]
# x_vars = [m_upper.x_v[i] for i in x.keys()]
# m_upper.cons = ConstraintList()
# for con in con_list:
#     m_upper.cons.add(expr=con(x_vars, p_nominal) <= 0)
# m_upper.obj = Objective(expr=obj(x_vars, p_nominal), sense=minimize)


# SolverFactory("ipopt").solve(m_upper)
# x_opt = value(m_upper.x_v[:])


# def cuboid_data(center, size):
#     """
#     Create a data array for cuboid plotting.


#     ============= ================================================
#     Argument      Description
#     ============= ================================================
#     center        center of the cuboid, triple
#     size          size of the cuboid, triple, (x_length,y_width,z_height)
#     :type size: tuple, numpy.array, list
#     :param size: size of the cuboid, triple, (x_length,y_width,z_height)
#     :type center: tuple, numpy.array, list
#     :param center: center of the cuboid, triple, (x,y,z)


#     """

#     # suppose axis direction: x: to left; y: to inside; z: to upper
#     # get the (left, outside, bottom) point
#     o = [a - b / 2 for a, b in zip(center, size)]
#     # get the length, width, and height
#     l, w, h = size
#     x = [
#         [
#             o[0],
#             o[0] + l,
#             o[0] + l,
#             o[0],
#             o[0],
#         ],  # x coordinate of points in bottom surface
#         [
#             o[0],
#             o[0] + l,
#             o[0] + l,
#             o[0],
#             o[0],
#         ],  # x coordinate of points in upper surface
#         [
#             o[0],
#             o[0] + l,
#             o[0] + l,
#             o[0],
#             o[0],
#         ],  # x coordinate of points in outside surface
#         [o[0], o[0] + l, o[0] + l, o[0], o[0]],
#     ]  # x coordinate of points in inside surface
#     y = [
#         [
#             o[1],
#             o[1],
#             o[1] + w,
#             o[1] + w,
#             o[1],
#         ],  # y coordinate of points in bottom surface
#         [
#             o[1],
#             o[1],
#             o[1] + w,
#             o[1] + w,
#             o[1],
#         ],  # y coordinate of points in upper surface
#         [o[1], o[1], o[1], o[1], o[1]],  # y coordinate of points in outside surface
#         [o[1] + w, o[1] + w, o[1] + w, o[1] + w, o[1] + w],
#     ]  # y coordinate of points in inside surface
#     z = [
#         [o[2], o[2], o[2], o[2], o[2]],  # z coordinate of points in bottom surface
#         [
#             o[2] + h,
#             o[2] + h,
#             o[2] + h,
#             o[2] + h,
#             o[2] + h,
#         ],  # z coordinate of points in upper surface
#         [
#             o[2],
#             o[2],
#             o[2] + h,
#             o[2] + h,
#             o[2],
#         ],  # z coordinate of points in outside surface
#         [o[2], o[2], o[2] + h, o[2] + h, o[2]],
#     ]  # z coordinate of points in inside surface
#     return np.array(x), np.array(y), np.array(z)


# def plot_fins(x):

#     fig = plt.figure(figsize=(10, 5))
#     ax = fig.add_subplot(1, 2, 1)
#     ax.grid(alpha=0.5)
#     offset = [0, 0.012]
#     ax.spines["left"].set_position(("data", -0.0005))
#     ax.spines["top"].set_visible(False)
#     ax.spines["right"].set_visible(False)
#     ax.spines["bottom"].set_position(("data", -0.001))
#     for j in range(len(x)):
#         w, s, a, b, W, L, H = x[j]
#         ax.set_xlim(0, 0.015)
#         ax.set_ylim(-2 * a, 2 * 0.014 - 4 * a)
#         if j == 0:
#             ls = "None"
#             fc = "grey"
#             al = 1
#             lab = "nominal"
#         else:
#             ls = "None"
#             fc = "k"
#             al = 1
#             lab = "robust"

#         ax.add_patch(
#             Rectangle(
#                 (0, offset[j]),
#                 0.1,
#                 a,
#                 lw=1,
#                 edgecolor="k",
#                 facecolor=fc,
#                 linestyle=ls,
#                 alpha=al,
#                 label=lab,
#             )
#         )
#         ax.add_patch(
#             Rectangle(
#                 (0, b + offset[j]),
#                 0.1,
#                 a,
#                 lw=1,
#                 edgecolor="k",
#                 facecolor=fc,
#                 linestyle=ls,
#                 alpha=al,
#             )
#         )
#         ax.legend()
#         i = 0
#         for it in range(5):
#             ax.add_patch(
#                 Rectangle(
#                     (0 + i, offset[j] + a),
#                     s,
#                     w,
#                     facecolor=fc,
#                     linestyle=ls,
#                     edgecolor="k",
#                     lw=1,
#                     alpha=al,
#                 )
#             )
#             ax.add_patch(
#                 Rectangle(
#                     (s + i, offset[j] + a),
#                     w,
#                     b - a,
#                     facecolor=fc,
#                     linestyle=ls,
#                     edgecolor="k",
#                     lw=1,
#                     alpha=al,
#                 )
#             )
#             ax.add_patch(
#                 Rectangle(
#                     (s + i, offset[j] + b - w),
#                     s,
#                     w,
#                     facecolor=fc,
#                     linestyle=ls,
#                     edgecolor="k",
#                     lw=1,
#                     alpha=al,
#                 )
#             )
#             ax.add_patch(
#                 Rectangle(
#                     (2 * s + i, offset[j] + a),
#                     w,
#                     b - a,
#                     facecolor=fc,
#                     linestyle=ls,
#                     edgecolor="k",
#                     lw=1,
#                     alpha=al,
#                 )
#             )
#             i += 2 * s
#         ax.set_xlabel("mm")
#         ax.set_ylabel("mm")
#     handles, labels = ax.get_legend_handles_labels()
#     ax.legend(handles[::-1], labels[::-1])
#     ax = fig.add_subplot(1, 2, 2, projection="3d")
#     ax.set_xlabel("W (m)")
#     ax.set_ylabel("L (m)")
#     ax.set_zlabel("H (m)")
#     for j in range(len(x)):
#         w, s, a, b, W, L, H = x[j]
#         center = [L / 2, W / 2, H / 2]
#         X, Y, Z = cuboid_data(center, (L, W, H))
#         if j == 0:
#             et = "dotted"
#             al = 1
#             c = "grey"
#             lab = "nominal"
#         else:
#             et = "solid"
#             al = 1
#             c = "k"
#             lab = "robust"
#         ax.plot_wireframe(
#             X,
#             Y,
#             Z,
#             color=c,
#             rstride=1,
#             cstride=1,
#             alpha=al,
#             lw=2,
#             linestyle=et,
#             label=lab,
#         )
#     ax.legend()
#     ax.set_xlim(0, x_og["W"][1] - x_og["W"][0])
#     ax.set_ylim(0, x_og["L"][1] - x_og["L"][0])
#     ax.set_zlim(0, x_og["H"][1] - x_og["H"][0])
#     ax.view_init(30, 225)
#     handles, labels = ax.get_legend_handles_labels()
#     ax.legend(handles[::-1], labels[::-1])
#     plt.savefig("output_images/heat_exchange.pdf")
#     return


# p_list = [p_nominal]
# x_list = [x_opt]

# robust = True
# while True:
#     robust = True

#     for con in con_list:

#         m_lower = ConcreteModel()
#         m_lower.pprint()
#         m_lower.p = Set(initialize=p.keys())
#         m_lower.pprint()
#         m_lower.p_v = Var(m_lower.p, domain=Reals, bounds=uncertain_bounds)
#         m_lower.pprint()
#         param_vars = [m_lower.p_v[str(i)] for i in p.keys()]
#         m_lower.obj = Objective(expr=con(x_opt, param_vars), sense=maximize)
#         m_lower.pprint()

#         SolverFactory("ipopt").solve(m_lower)

#         p_opt = value(m_lower.p_v[:])
#         p_list.append(p_opt)
#         print("Constraint violation: ", value(m_lower.obj))
#         if value(m_lower.obj) > epsilon:
#             robust = False
#             # filling in the blanks...
#             for k in range(len(p_opt)):
#                 if p_opt[k] is None:
#                     p_opt[k] = p_nominal[k]

#             m_upper.cons.add(expr=con(x_vars, p_opt) <= 0)
#     # plot_upper(x_opt,p_list)
#     if robust is True:

#         print("\nRobust solution: ", x_opt)
#         break

#     SolverFactory("ipopt").solve(m_upper)

#     x_opt = value(m_upper.x_v[:])
#     x_list.append(x_opt)


# plot_fins([x_list[0], x_list[-1]])
