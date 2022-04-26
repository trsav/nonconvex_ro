def create_toy_problem():
    # uncertain variables
    p = {}
    p["p"] = {"val": 1, "unc": 1}

    def con(x, p_v):
        x1, x2 = x
        p = p_v[0]
        a = (p * p) * 2 * x1 ** 2
        b = -(p * p * p * p) + x1 ** 2 - x2 - 0.5 * x1
        return a + b

    def obj(x):
        x1, x2 = x
        return x2 - 2 * x1 ** 2

    # def con(x, p_v):
    #     x1, x2 = x
    #     p = p_v[0]
    #     return (x1-p)**3 - x2 + 1

    # def obj(x):
    #     x1, x2 = x
    #     return (x2 - 2 * x1 ** 1-x1)**2 + 100*(x2-x1**2)**2

    con_list = [con]

    x = {"x1": [-2, 2], "x2": [-2, 2]}

    return x, p, con_list, obj
