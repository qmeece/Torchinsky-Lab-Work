import scipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

start_pol = 0

def read(path):
    data = pd.read_csv(path, header=None, delimiter = "\t")
    info = str(path)[0:-4].split("-")
    Polarization_num = int(info[-1])
    THz_orientation = info[-2]
    return [data, info, THz_orientation, Polarization_num]

def H_fit(phi, xyz, beta):
    return -np.sqrt(2/3) * xyz * np.cos((3 * beta) - (2 * phi))

def second_derivative_gaussian(x, a, mu, sigma, omega):
    """
    a: amplitude
    mu: center (mean)
    sigma: standard deviation
    """
    term0 = -x/(sigma**2)
    term1 = (x - mu)**2 / sigma**4
    term2 = 1 / sigma**2
    return a * (term0+term1 - term2) * np.exp(-0.5 * ((x - mu) / sigma)**2) * np.cos(omega * x)

def gaussian_wavepacket(x, a, x0, sigma, k0):
    """
    Generates a normalized 1D Gaussian wavepacket.
    
    Parameters:
    -----------
    x     : array_like -> Spatial grid coordinates.
    x0    : float      -> Mean initial position (center of the packet).
    sigma : float      -> Width/spread parameter of the Gaussian envelope.
    k0    : float      -> Mean wavenumber (related to momentum via p = hbar * k0).
    
    Returns:
    --------
    psi   : ndarray    -> Complex wavepacket array evaluated over the grid 'x'.
    """
    # 1. Compute the normalization prefactor
    prefactor = a
    
    # 2. Compute the localized Gaussian envelope
    envelope = np.exp(-0.5 * ((x - x0) / sigma) ** 2)
    
    # 3. Compute the plane-wave component (adds momentum)
    plane_wave = np.exp(1j * k0 * x)
    
    # Combined complex wave function
    psi = prefactor * envelope * plane_wave
    
    return psi

def get_sig(scan):
    popt, pcov = scipy.optimize.curve_fit(gaussian_wavepacket, scan[0], scan[1], maxfev=5000)
    # a_fit, mu_fit, sigma_fit, omega_fit = popt
    a_fit, x_0_fit, sigma_fit, k_0_fit = popt
    return a_fit

def get_max(scan):
    y_np = np.array(scan[1])
    maximum = scan[1][abs(y_np).argmax()]
    return maximum

def get_pol(num):
    return np.radians(((num-1) * 10) + start_pol)

def calculate_ellipticity(x, y):
    """
    Calculates the ellipticity (flattening) and orientation of a scatter plot 
    based on the covariance matrix of the data.
    
    Returns:
        ellipticity (float): The ellipticity of the data (0 = circle, < 1 = ellipse).
        angle (float): The orientation angle of the ellipse in radians.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Requires at least two (x, y) data points.")
    
    # Create the covariance matrix
    cov_matrix = np.cov(x, y)
    
    # Calculate eigenvalues and eigenvectors of the covariance matrix
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    
    # The major (a) and minor (b) radii are the square roots of the eigenvalues
    major_axis = np.sqrt(np.max(eigenvalues))
    minor_axis = np.sqrt(np.min(eigenvalues))
    
    # Ellipticity definition: e = 1 - (b / a)
    ellipticity = 1.0 - (minor_axis / major_axis)
    
    # Determine the angle of rotation for the major axis
    # The eigenvector corresponding to the largest eigenvalue
    max_eigvec = eigenvectors[:, np.argmax(eigenvalues)]
    angle = np.arctan2(max_eigvec[1], max_eigvec[0])
    
    return ellipticity, angle

# Specify the folder path
folder_path = Path(r"C:\Data\THz\GaAs-Aniso\19K")

pol_and_mag = []

col = ["File Name", "Polarization", "Abs Maximum", "Fit Amplitude", "THz Orientation", "Data"]
aniso_df = pd.DataFrame(columns=col)

# Loop through all items in the directory
for file_path in folder_path.iterdir():
    # Check if the item is a file (skips folders)
    if file_path.is_file() and not file_path.name == "log.txt":
        scan_data = read(file_path)
        pol_and_mag.append([get_pol(scan_data[3]), get_max(scan_data[0]), scan_data[2], scan_data[0]])
        # aniso_df.loc[len(aniso_df)] = [file_path.name, get_pol(scan_data[3]), abs(get_max(scan_data[0])), abs(get_sig(scan_data[0])), scan_data[2], scan_data[0]]

pol_graph_H = []
pol_graph_V = []

# print(aniso_df.head())

elip = {}

for i in pol_and_mag:
    # if elip[f'{i[0]}'] == None:
    #     elip[f'{i[0]}'].append
    if i[2] == "V":
        pol_graph_V.append(i[0:2])
    elif i[2] == "H":
        pol_graph_H.append(i[0:2])
    else:
        pass

x, y = zip(*pol_graph_H)
x1, y1 = zip(*pol_graph_V)

# x3 = x
# y3 = []
# for i in elip:
#     y3.append(calculate_ellipticity(i[]))

# print(y3)

popt1, pcov1 = scipy.optimize.curve_fit(H_fit, x, y, maxfev=800)
xyz_fit, beta_fit = popt1
# print(xyz_fit, beta_fit)
x_fit = np.linspace(np.min(x), np.max(x), 200)
y_fit = H_fit(x_fit, xyz_fit, beta_fit)

print(x_fit)

fig = plt.figure()

# Plot 1: 
ax1 = fig.add_subplot(2, 3, 1, projection='polar')
ax1.plot(x, abs(np.array(y)), color='red')
ax1.plot(x_fit, abs(y_fit))
ax1.set_title('H')

# Plot 2: 
ax2 = fig.add_subplot(2, 3, 2, projection='polar')
ax2.plot(x1, abs(np.array(y1)), color='blue')
ax2.set_title('V')


# Plot 3: 
ax3 = fig.add_subplot(2, 3, 3)
ax3.plot(read(r"C:\Data\THz\GaAs-Aniso\19K\GaAs-Aniso-19.0K-THz-1400nm-LIN(H)-LOB-V-028.txt")[0][0], read(r"C:\Data\THz\GaAs-Aniso\19K\GaAs-Aniso-19.0K-THz-1400nm-LIN(H)-LOB-V-028.txt")[0][1], color='green')
ax3.set_title('V')

# Plot 4: 
ax4 = fig.add_subplot(2, 3, 4)
ax4.plot(read(r"C:\Data\THz\GaAs-Aniso\19K\GaAs-Aniso-19.0K-THz-1400nm-LIN(H)-LOB-H-015.txt")[0][0], read(r"C:\Data\THz\GaAs-Aniso\19K\GaAs-Aniso-19.0K-THz-1400nm-LIN(H)-LOB-H-015.txt")[0][1], color='purple')
ax4.set_title('H')

x2 = read(r"C:\Data\THz\GaAs-Aniso\19K\GaAs-Aniso-19.0K-THz-1400nm-LIN(H)-LOB-V-020.txt")[0][1]
y2 = read(r"C:\Data\THz\GaAs-Aniso\19K\GaAs-Aniso-19.0K-THz-1400nm-LIN(H)-LOB-V-020.txt")[0][0]
z2 = read(r"C:\Data\THz\GaAs-Aniso\19K\GaAs-Aniso-19.0K-THz-1400nm-LIN(H)-LOB-H-020.txt")[0][1]

ax5 = fig.add_subplot(2, 3, 5, projection='3d')
ax5.plot(x2, y2, z2)

ax6 = fig.add_subplot(2, 3, 6)
ax6.scatter(x, y, color='red')
ax6.plot(x_fit, y_fit)
ax6.set_title('H')
# ax6 = fig.add_subplot(2, 3, 6, projection='polar')
# ax6.plot(x3, y3)
# ax6.set_title("Ellipticity")

# Automatically fix overlapping labels or titles
plt.tight_layout()
plt.show()