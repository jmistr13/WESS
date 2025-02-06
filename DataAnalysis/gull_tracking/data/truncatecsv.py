import pandas as pd

def truncate_csv(input_file, output_file):
	df = pd.read_csv(input_file)
	
	num_rows_to_keep = len(df) // 16
	
	truncated_df = df.iloc[:num_rows_to_keep]
	
	truncated_df.to_csv(output_file, index=False)
	
	print(f"Truncated file saved as {output_file} with {num_rows_to_keep} rows.")
	
	
input_file = "gullEdit.csv"
output_file = "gullEdit2.csv"

truncate_csv(input_file, output_file)
