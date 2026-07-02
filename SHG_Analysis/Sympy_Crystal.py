import sympy as sp
from sympy import tensorproduct
from sympy import tensorcontraction
from sympy import Matrix, sqrt, eye, pi, sin, cos

phi = sp.symbols("phi")

class Crystal:
    def __init__(self, chi, face = [0,0,1], analyzer_mode = 'H', incidence = 0, d_rep = False, E=None):
        if d_rep:
            self.chi = d_to_chi(chi)
        else:
            self.chi = chi
        if E == None:
            self.E = sp.MutableDenseNDimArray([cos(phi), sin(phi), 0])
        else:
            self.E = sp.MutableDenseNDimArray(E)
        self.face = face
        self.analyzer_mode = analyzer_mode
        self.incidence = incidence
    
    def rotate_face(self, chi):
        R = rotation_matrix_from_normal(self.face)
        return rotate_chi(chi, R)
    
    def rotate_incidence(self, chi):
        R = Ry(-self.incidence)
        return rotate_chi(chi, R)
    
    def rotate_beta(self, chi, beta=sp.symbols('beta')):
        R = Rz(beta)
        return rotate_chi(chi, R)

    def polarization(self, beta=sp.symbols('beta')):

        R_total = Ry(-self.incidence) * Rz(beta) * rotation_matrix_from_normal(self.face)
        chi_rot = rotate_chi(self.chi, R_total)

        return sp.simplify(tensorcontraction(
            tensorproduct(chi_rot, self.E, self.E),
            (1,3),
            (2,4)
        ))
    
    def E_det(self):

        P = self.polarization()

        if self.analyzer_mode == "H":
            A = Matrix([1,0,0])
        elif self.analyzer_mode == "V":
            A = Matrix([0,1,0])
        elif self.analyzer_mode == "SAME":
            A = Matrix([sin(phi),cos(phi),0])
        elif self.analyzer_mode == "OPPOSITE":
            A = Matrix([cos(phi), -sin(phi), 0])
        else:
            print("Not valid analyzer mode")

        return sp.simplify(tensorcontraction(
            tensorproduct(P, A),
            (0,1)
        ))
    
    def intensity(self):
        E_det = Matrix(self.E_det())
        return sp.simplify(E_det.dot(E_det))

def d_to_chi(d):
    """
    Convert a 3×6 d-matrix (Voigt notation) into a
    fully symmetric 3×3×3 nonlinear susceptibility tensor.

    Parameters
    ----------
    d : Matrix or nested list
        3×6 matrix

    Returns
    -------
    MutableDenseNDimArray
        χ[i,j,k]
    """

    d = Matrix(d)

    chi = sp.MutableDenseNDimArray.zeros(3,3,3)

    # Voigt mapping
    mapping = {
        0: [(0,0)],          # xx
        1: [(1,1)],          # yy
        2: [(2,2)],          # zz
        3: [(1,2),(2,1)],    # yz
        4: [(0,2),(2,0)],    # xz
        5: [(0,1),(1,0)]     # xy
    }

    for i in range(3):
        for l in range(6):
            for j,k in mapping[l]:
                chi[i,j,k] = d[i,l]

    return chi

def rotation_matrix_from_normal(hkl):
    """
    Returns a rotation matrix that maps the crystal z-axis
    ([001]) onto the direction hkl.
    """

    # Desired surface normal
    n = Matrix(hkl)
    n = n / sp.sqrt(n.dot(n))

    # Original normal
    z = Matrix([0, 0, 1])

    # Already aligned
    if sp.simplify((n - z).norm()) == 0:
        return eye(3)

    # Opposite direction
    if sp.simplify((n + z).norm()) == 0:
        return Matrix([
            [1,0,0],
            [0,-1,0],
            [0,0,-1]
        ])

    # Rodrigues' rotation formula
    axis = z.cross(n)
    axis = axis / sqrt(axis.dot(axis))

    c = sp.simplify(z.dot(n))
    s = sp.sqrt(1 - c**2)

    K = Matrix([
        [0, -axis[2], axis[1]],
        [axis[2], 0, -axis[0]],
        [-axis[1], axis[0], 0]
    ])

    R = eye(3) + s*K + (1-c)*(K*K)

    return sp.simplify(R)

def rotate_chi(chi, rotation_matrix):
    """
    Rotate a rank-3 susceptibility tensor
    """

    R = Matrix(rotation_matrix)

    return tensorcontraction(
        tensorproduct(R, R, R, chi),
        (1,6),
        (3,7),
        (5,8)
    )

def Rz(theta):
    R = Matrix([
        [cos(theta), -sin(theta), 0],
        [sin(theta), cos(theta), 0],
        [0,0,1]
    ])
    return R

def Rx(theta):
    R = Matrix([
        [1,0,0],
        [0, cos(theta), -sin(theta)],
        [0, sin(theta), cos(theta)]
    ])
    return R

def Ry(theta):
    R = Matrix([
        [cos(theta), 0, sin(theta)],
        [0,1,0],
        [-sin(theta), 0, cos(theta)]
    ])
    return R


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
