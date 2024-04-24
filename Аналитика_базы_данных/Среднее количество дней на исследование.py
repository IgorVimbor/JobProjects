import pandas as pd
import numpy as np


df = pd.read_excel(
    "D:/РАБОТА/2024-2019_ЖУРНАЛ УЧЁТА.xlsx",
    sheet_name="2024",
    usecols=["Дата поступления изделия", "Дата акта исследования"],
    header=1,
)

df = df.apply(pd.to_datetime)

df1 = df.dropna()

"""
Data columns (total 2 columns):
 #   Column                    Non-Null Count  Dtype
---  ------                    --------------  -----
 0   Дата поступления изделия  374 non-null    datetime64[ns]
 1   Дата акта исследования    374 non-null    datetime64[ns]
dtypes: datetime64[ns](2)
memory usage: 8.8 KB
"""

df1["DIFF"] = (
    df1["Дата акта исследования"] - df1["Дата поступления изделия"]
) / np.timedelta64(1, "D")
"""
  Дата поступления изделия Дата акта исследования  DIFF
0               2024-01-24             2024-01-31   7.0
1               2024-01-24             2024-01-31   7.0
2               2024-01-24             2024-01-29   5.0
3               2024-01-24             2024-01-31   7.0
4               2024-01-24             2024-01-31   7.0
"""

print(df1["DIFF"].mean())
# 4.9
