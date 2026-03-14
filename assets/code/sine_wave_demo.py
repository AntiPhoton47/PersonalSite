"""Sine wave demo"""

from math import pi, sin

import matplotlib.pyplot as plt

PARAMS = globals().get("CODE_EXAMPLE_PARAMS", {})
AMPLITUDE = float(PARAMS.get("amplitude", 1.0))
FREQUENCY = float(PARAMS.get("frequency", 1.0))
STEP = float(PARAMS.get("step", 0.05))

sample_count = max(2, int(round(12.5 / STEP)) + 1)
xs = [index * STEP for index in range(sample_count)]
ys = [AMPLITUDE * sin(2 * pi * FREQUENCY * value) for value in xs]

plt.figure(figsize=(7, 3.8))
plt.plot(xs, ys, color="#0ea5e9", linewidth=2.4, label=f"{AMPLITUDE:.2f} sin(2π {FREQUENCY:.2f} x)")
plt.axhline(0.0, color="#94a3b8", linewidth=1, linestyle="--")
plt.xlabel("x")
plt.ylabel("Amplitude")
plt.title("Sine wave")
plt.legend()
plt.tight_layout()
plt.show()

print(f"Generated {len(xs)} sample points with amplitude={AMPLITUDE} and frequency={FREQUENCY}.")
