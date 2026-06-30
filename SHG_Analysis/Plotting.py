import matplotlib.pyplot as plt
import numpy as np
# import Crystal_rotate

def P_H_0(phi, xyz, beta):
    first_term = -(xyz/np.sqrt(3)) * (np.cos(3* beta + 2 * phi) + np.sin(3 * beta + 2 * phi))
    return first_term

def P_V_0(phi, xyz, beta):
    return (xyz/np.sqrt(3)) * (np.cos(3* beta + 2 * phi) - np.sin(3 * beta + 2 * phi))



def P_H_45(phi, theta, xyz, beta):
    first_term = (-(np.cos(phi) ** 2))*(np.cos(3 * beta) + np.sin(3 * beta))
    second_term = 2 * np.cos(theta) * np.cos(phi) * np.sin(phi) * (-np.cos(3 * beta) + np.sin(3 * beta))
    third_term = (np.sin(phi) ** 2) * ((np.cos(theta) ** 2) * (np.cos(3 * beta) + np.sin(3 * beta)) + np.sin(2 * theta))
    return (xyz/np.sqrt(3)) * (first_term + second_term + third_term)

def P_V_45(phi, theta, xyz, beta):
    first_term = (np.cos(3 * beta) - np.sin(3 * beta)) * (np.cos(phi) ** 2 - np.cos(theta) ** 2 * np.sin(phi) ** 2)
    second_term = np.sin(2 * phi) * (-np.cos(theta) * (np.cos(3 * beta) + np.sin(3 * beta)) + np.sin(theta))
    return xyz/np.sqrt(3) * (first_term + second_term)

def P_SAME_45(phi, theta, xyz, beta):

    return

def P_OPPOSITE_45(phi, theta, xyz, beta):
    return


x_deg = np.linspace(0, 360, 100)
phi = np.deg2rad(x_deg)

# Beta 75?
y = P_H_45(phi, np.deg2rad(45), 1, np.deg2rad(0)) ** 2

plt.polar(phi, y)
plt.title("I_V_45 vs phi, beta = 15°")
plt.show()