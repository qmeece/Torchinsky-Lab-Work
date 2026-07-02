import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv(r"C:\Users\quinn\OneDrive\Documents\Torchinsky Lab Work\Analysis\GaAs-111-19.0K-THz-1400nm-LIN(H)-LOB-NA-001.txt", header=None, delimiter="\t")

number_of_samples = len(df[1])
sample_spacing = df[0][1] - df[0][0]

fig, ax = plt.subplots(2, 1)

ax[0].plot(df[0], df[1])
ax[0].set_title("Time Domain")
ax[0].set_xlabel("Time (ps)")

ax[1].plot(np.fft.rfftfreq(number_of_samples, d=sample_spacing), np.abs(np.fft.rfft(df[1])))
ax[1].set_title("Frequency Domain")
ax[1].set_xlabel("Frequency (THz)")

plt.tight_layout()
plt.show()