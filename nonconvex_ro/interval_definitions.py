import numpy as np
from itertools import product
from pyomo.environ import Var, Binary
from pyomo.environ import exp as pexp
import uuid
from pyomo.core.expr.visitor import identify_variables


class Interval:
    def __init__(self, lower_bound=0, upper_bound=0):
        self.l = lower_bound
        self.u = upper_bound

    def __str__(self):
        return "({0}, {1})".format(self.l, self.u)

    def __add__(self, other):

        if other.__class__ is Interval:
            return Interval(self.l + other.l, self.u + other.u)

        else:
            return Interval(other + self.l, other + self.u)

    __radd__ = __add__

    def __sub__(self, other):
        if other.__class__ is Interval:
            return Interval(self.l - other.u, self.u - other.l)

        else:
            return Interval(self.l - other, self.u - other)

    __rsub__ = __sub__

    def __neg__(self):
        return Interval(-self.u, -self.l)

    def __truediv__(self, other):
        if other.__class__ in [float, int]:
            return Interval(self.l / other, self.u / other)

    def __rtruediv__(self, other):
        if other.__class__ in [float, int]:
            return Interval(other / self.u, other / self.l)

    def __mul__(self, other):

        if other.__class__ is Interval:
            try:
                a = other.l * self.l
                a = list(identify_variables(a))
                m = a[0].model()
                pu1 = self.u
                pb1 = self.l
                pu2 = other.u
                pb2 = other.l
                name = str(uuid.uuid1())
                m.add_component(name, Var([1, 2, 3, 4], within=Binary))

                y = list(m.component_objects(Var, descend_into=True))[-1]

                PU1 = y[1] * pb1 * pb2 + (1 - y[1] * pb1 * pu2)

                PB1 = (1 - y[1]) * pb1 * pb2 + y[1] * pb1 * pu2
                m.cons.add(
                    expr=0
                    <= y[1] * (pb1 * pb2 - pb1 * pu2)
                    + (1 - y[1]) * (pb1 * pu2 - pb1 * pb2)
                )

                PU2 = y[2] * pu1 * pb2 + (1 - y[2] * pu1 * pu2)
                PB2 = (1 - y[2]) * pu1 * pb2 + y[2] * pu1 * pu2
                m.cons.add(
                    expr=0
                    <= y[2] * (pu1 * pb2 - pu1 * pu2)
                    + (1 - y[2]) * (pu1 * pu2 - pu1 * pb2)
                )
                PUN = y[3] * PU1 + (1 - y[3] * (PU2 - PU1))
                m.cons.add(0 <= y[3] * (PU1 - PU2) + (1 - y[3] * (PU2 - PU1)))
                PBN = y[4] * PB1 + (1 - y[4]) * PB2
                m.cons.add(0 <= y[4] * (PB1 - PB2) + (1 - y[4] * (PB2 - PB1)))
                return Interval(PUN, PBN)
            except IndexError:
                a = self.l * other.l
                b = self.l * other.u
                c = self.u * other.l
                d = self.u * other.u
                return Interval(min(a, b, c, d), max(a, b, c, d))
        else:
            return Interval(self.l * other, self.u * other)

    def __pow__(self, other):
        return Interval(self.l ** other, self.u ** other)

    __rmul__ = __mul__


def exp(self):
    if self.__class__ is Interval:
        a = self.l
        b = self.u
        if a.__class__ in [float, int]:
            a = np.exp(a)
            b = np.exp(b)
            return Interval(a, b)
        else:
            a = pexp(a)
            b = pexp(b)
            return Interval(a, b)

    # def __truediv__(self, other):
    #     return Interval(self.l / other, self.u / other)

    # def __rtruediv__(self, other):
    #     if self.l < 0:
    #         return Interval(other/self.l, other/self.u)
    #     else:
    #         return Interval(other/self.u, other/self.l)

    # def __abs__(self):
    #     return max(abs(self.l), abs(self.u))

    # def __pow__(self, other: int):
    #     if self.l > 0 or other % 2 != 0:
    #         return Interval(self.l ** other, self.u ** other)
    #     elif self.u < 0 and other % 2 == 0:
    #         return Interval(self.u ** other, self.l ** other)
    #     else:
    #         return Interval(0, abs(self) ** other)

    # def exp(self):
    #     return Interval(np.exp(self.l),np.exp(self.u))


def subdivide(x, N):
    A = np.zeros(N + 1, dtype="object")
    A[0] = x.l
    w_x = x.u - x.l
    for j in range(1, N + 1):
        A[j] = A[j - 1] + (w_x / N)
    return A


def for_recursive(
    G, res, number_of_loops, range_list, execute_function, current_index=0, iter_list=[]
):
    if iter_list == []:
        iter_list = [0] * number_of_loops

    if current_index == number_of_loops - 1:
        for iter_list[current_index] in range_list[current_index]:
            execute_function(iter_list, G, res)
    else:
        for iter_list[current_index] in range_list[current_index]:
            res = for_recursive(
                G,
                res,
                number_of_loops,
                iter_list=iter_list,
                range_list=range_list,
                current_index=current_index + 1,
                execute_function=execute_function,
            )
    return res


def subdivide_vector(int_list, N):
    l = len(int_list)
    d = [list(subdivide(int_list[i], N)) for i in range(l)]
    i = [[Interval(j[k], j[k + 1]) for k in range(N)] for j in d]
    res = list(product(*i))
    return res
