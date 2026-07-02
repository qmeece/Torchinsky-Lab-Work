import numpy as np
import Sympy_Crystal
# model = sp.lambdify(
#     (theta, d15, d31, d33),
#     I,
#     modules="numpy"
# )


d11,d12,d13,d14,d15,d16 = sp.symbols('d11:17')
d21,d22,d23,d24,d25,d26 = sp.symbols('d21:27')
d31,d32,d33,d34,d35,d36 = sp.symbols('d31:37')
xyz = sp.symbols('xyz')

d = sp.Matrix([
    [0,0,0,xyz,0,0],
    [0,0,0,0,xyz,0],
    [0,0,0,0,0,xyz]
])

gaas111 = Crystal(d, d_rep=True, face = [1,1,1], analyzer_mode = 'H', incidence = 0)
print(gaas111.intensity())