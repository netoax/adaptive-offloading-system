import pandas as pd
from matplotlib import pyplot as plt

COLUMNS_CP_13 = [
    "I0507_OIL_TEMP",
    "VFD_SCALED_FEEDBACK",
    "VFD_SCALED_PERCENT_OF_LOAD",
    "TEMPERATURA_BED_OIL",
    "timestamp",
]

COLUMNS_CP_26 = [
    "I0507_OIL_TEMP",
    "VFD_SCALED_FEEDBACK",
    "VFD_SCALED_PERCENT_OF_LOAD",
    "timestamp",
]

DATASET_TYPE_CP_13 = {
    "I0507_OIL_TEMP": float,
    "VFD_SCALED_FEEDBACK": float,
    "VFD_SCALED_PERCENT_OF_LOAD": float,
    "TEMPERATURA_BED_OIL": float,
    "timestamp": str,
}

DATASET_TYPE_CP_26 = {
    "I0507_OIL_TEMP": float,
    "VFD_SCALED_FEEDBACK": float,
    "VFD_SCALED_PERCENT_OF_LOAD": float,
    "timestamp": str,
}


df = pd.read_csv("/Users/jneto/dados-tampas/cp26.csv", usecols=COLUMNS_CP_26)
df = df.dropna()
df = df.astype(DATASET_TYPE_CP_26)

# Remove CP26 temp outliers
# df = df[~(df['I0507_OIL_TEMP'] >= 100)]
# df = df[~(df['I0507_OIL_TEMP'] < 0)]

print(df.info())
print(df.describe())


# Save to CSV file
# df.to_csv("./cp26.csv", index=False)

# Plot charts
# ax = plt.gca()
# df.plot(kind='line', x="timestamp", ax=ax, subplots=True, title="CP 13")
# plt.show()
