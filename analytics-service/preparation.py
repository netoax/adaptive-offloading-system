import pandas as pd
import os

input_file = os.environ.get('INPUT_FILE') or '../data.csv'
output_file = os.environ.get('OUTPUT_FILE') or '../data.csv'

df = pd.read_csv(input_file, nrows=100000)
df = df.dropna(axis=0, subset=['AirportCode'])
# .sort_values(by="StartTime(UTC)")
# data = data.groupby
print(df.loc[df['AirportCode'] == 'KOAK'])
# print(df.loc[df['AirportCode'] == 'KOAK'])
# print(df.groupby('AirportCode').count())
# print(df.shape[0])
# for index, row in df.iterrows():
#     print(row)
# data.to_csv(output_file, index=False)

