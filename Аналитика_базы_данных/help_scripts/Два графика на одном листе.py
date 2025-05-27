# Два графика на одном листе

import pandas as pd
import random
import matplotlib.pyplot as plt

d_arr = [[random.randrange(-10, 10), random.randrange(0, 30)] for _ in range(10)]
df = pd.DataFrame(d_arr, columns=['A1', 'A2'])
df.plot(subplots=True, figsize=(10, 5))
plt.show()
