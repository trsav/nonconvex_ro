class Interval:
    def __init__(self, lower_bound=0, upper_bound=0):
        self.l = lower_bound
        self.u = upper_bound

    def __str__(self):
        return "({0}, {1})".format(self.l, self.u)

    def __add__(self, other):
        return Interval(self.l + other.l, self.u + other.u)

    def __sub__(self, other):
        return Interval(self.l - other.l, self.u - other.u)

    def __neg__(self):
        return Interval(-self.u, -self.l)

    def __mul__(self, other):
        return Interval(self.l * other, self.u * other)

    def __abs__(self):
        return max(abs(self.l), abs(self.u))

    def __pow__(self, other: int):
        if self.l > 0 or other % 2 != 0:
            return Interval(self.l ** other, self.u ** other)
        elif self.u < 0 and other % 2 == 0:
            return Interval(self.u ** other, self.l ** other)
        else:
            return Interval(0, abs(self) ** other)
