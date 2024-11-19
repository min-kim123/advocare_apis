import pandas as pd

# Read the CSV files
addendum_a = pd.read_csv('addendum_a.csv')
addendum_b = pd.read_csv('addendum_b.csv')

# Merge the datasets on the APC column
merged_data = pd.merge(addendum_a, addendum_b, on='APC', how='inner')

# Group the data by APC and aggregate HCPCS Codes, Descriptions, and Payment Rates
grouped_data = merged_data.groupby('APC').agg({
    'HCPCS Code': lambda x: '; '.join(x),
    'Short Descriptor': lambda x: '; '.join(x),
    'Payment Rate': 'first'  # Assuming Payment Rate is the same for each APC
}).reset_index()

# Rename the columns to match final requirements
grouped_data = grouped_data.rename(columns={'Short Descriptor': 'Description'})

# Reorder columns to desired order
final_data = grouped_data[['APC', 'HCPCS Code', 'Description', 'Payment Rate']]

# Save the final merged data to a new CSV file
final_data.to_csv('medicare_rates.csv', index=False)

# Print the final grouped data
print(final_data)