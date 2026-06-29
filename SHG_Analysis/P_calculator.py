import numpy as np

eps0 = 8.854187817e-12

class NonlinearCrystal:
    def __init__(self, chi2):
        """
        chi2 : 3x3x3 tensor
        """
        self.chi2 = np.asarray(chi2, dtype=float)

    def polarization(self, E):
        """
        Calculate nonlinear polarization

        P_i = eps0 * chi_ijk * E_j * E_k

        Parameters
        ----------
        E : array_like
            Electric field vector [Ex,Ey,Ez]

        Returns
        -------
        P : ndarray
            Nonlinear polarization vector
        """
        E = np.asarray(E)

        return eps0 * np.einsum('ijk,j,k->i', self.chi2, E, E)
    
def rotate_tensor(chi, R):
    """
    Rotate a rank-3 tensor.

    chi_rot[i,j,k] =
        R[i,a] R[j,b] R[k,c] chi[a,b,c]
    """
    return np.einsum(
        'ia,jb,kc,abc->ijk',
        R, R, R, chi
    )

def Rx(theta):
    c = np.cos(theta)
    s = np.sin(theta)

    return np.array([
        [1,0,0],
        [0,c,-s],
        [0,s,c]
    ])


def Ry(theta):
    c = np.cos(theta)
    s = np.sin(theta)

    return np.array([
        [c,0,s],
        [0,1,0],
        [-s,0,c]
    ])


def Rz(theta):
    c = np.cos(theta)
    s = np.sin(theta)

    return np.array([
        [c,-s,0],
        [s,c,0],
        [0,0,1]
    ])

def electric_field(theta, amplitude=1.0):
    """
    theta = angle from z-axis

    Returns Ex,Ey,Ez
    """
    return amplitude * np.array([
        np.sin(theta),
        0.0,
        np.cos(theta)
    ])

chi = np.zeros((3,3,3))

chi[0,0,0] = 1.2
chi[0,1,1] = 0.4
chi[1,0,1] = 0.8
chi[1,1,0] = 0.8
chi[2,2,2] = 2.0

crystal = NonlinearCrystal(chi)

theta = np.deg2rad(45)

R = Ry(theta)

chi_rot = rotate_tensor(chi, R)

rotated_crystal = NonlinearCrystal(chi_rot)

theta_light = np.deg2rad(30)

E = electric_field(theta_light)

P = rotated_crystal.polarization(E)

print("Electric field")
print(E)

print()

print("Nonlinear polarization")
print(P)

angles = np.linspace(0, 2*np.pi, 361)

Px = []
Py = []
Pz = []

for angle in angles:

    E = electric_field(angle)

    P = rotated_crystal.polarization(E)

    Px.append(P[0])
    Py.append(P[1])
    Pz.append(P[2])

Px = np.array(Px)
Py = np.array(Py)
Pz = np.array(Pz)

faces = {
    "001": np.eye(3),
    "100": Ry(np.pi/2),
    "010": Rx(-np.pi/2),
}

for name, R in faces.items():
    chi_face = rotate_tensor(chi, R)

    crystal = NonlinearCrystal(chi_face)

    E = electric_field(np.deg2rad(45))

    P = crystal.polarization(E)

    print(name, P)