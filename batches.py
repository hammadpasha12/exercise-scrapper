import pandas as pd
import math

# input file
input_csv = "virtuagym_exercises.csv"

# rows per batch
batch_size = 500

# read csv
df = pd.read_csv(input_csv)

total_rows = len(df)
num_batches = math.ceil(total_rows / batch_size)

for i in range(num_batches):
    start = i * batch_size
    end = start + batch_size

    batch_df = df.iloc[start:end]

    output_file = f"output_batch_{i+1}.csv"
    batch_df.to_csv(output_file, index=False)

    print(f"Created {output_file} with {len(batch_df)} rows")
