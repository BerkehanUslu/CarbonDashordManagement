import pandas as pd
import mysql.connector
import os

# Connect to MySQL database
my_db = mysql.connector.connect(
    host="localhost",
    user="root",
    port = 8111,
    password = "",
    database = "pltd8468_wp172",
)

print(my_db)
cursor = my_db.cursor(buffered=True)  # Create a cursor object using buffered=True to fetch multiple results

# Load CSV into DataFrame
os.chdir('G:\\Shared drives\\Carbon Pole\\Carbon Projects and Development\\Alternance Berkehan\\Carbon Management Dashboard\\CarbonManagementDashoard_envisa\\app\\data')
csv_file = 'Data_Entry_Template_v2.csv'
df = pd.read_csv(csv_file, delimiter=';')
if df.iloc[:, -1].isnull().all():  # Check if all values in the last column are NaN
    df = df.drop(df.columns[-1], axis=1)  # Drop the last column

# Split data into sections
# Section 1: Columns for Table Emissions
df_table1 = df.iloc[:, -7:]  # Select the last 6 columns and all rows

#data handling before inserting data into database
#One column needs to be mapped to the foreign key id_emission_type
df_table1_primary = df_table1 #copy the dataframe to keep the original data
df_table1.columns = df_table1.columns.str.strip() # remove the whitespace from the column names
df_table1 = df_table1.rename(columns={'emission type': 'id_emission_type'})
columns_table1 = ', '.join(df_table1.columns)

int_columns = ['quantity', 'emission_factor', 'emission_value_tCO2e'] #columns that need to be converted to integer
for col in int_columns:
    df_table1[col] = df_table1[col].str.replace(',', '.', regex=False) #remove the commas from the numbers
    # Convert to numeric, setting errors='coerce' to handle non-numeric values
    df_table1[col] = pd.to_numeric(df_table1[col], errors='coerce') #coerce will replace non-numeric values with NaN
    df_table1[col] = df_table1[col].astype(float) #convert the column to float

# Cleaning function to standardize values
def clean_string(value):
    if isinstance(value, str):  # Check if the value is a string
        return value.strip().lower()  # Remove whitespace and convert to lowercase
    return value  # If not a string, return as-is

cursor.execute("SELECT id, TRIM(UPPER(type_name)) FROM emission_type") #convert them to uppercase and remove the whitespace
emission_type_mapping = {type_name: id for id, type_name in cursor.fetchall()}
# Apply cleaning to the mapping dictionary
emission_type_mapping = {clean_string(k): v for k, v in emission_type_mapping.items()}
# print("\n"), print(emission_type_mapping), print("\n")

# Apply cleaning to the DataFrame column before mapping
df_table1['id_emission_type'] = df_table1['id_emission_type'].apply(clean_string)
# Replace the type name in the CSV with the corresponding id
df_table1['id_emission_type'] = df_table1['id_emission_type'].map(emission_type_mapping) #here, id_emission_type column still have names of the emission types

# Check if there are any emission types that are not in the database and add hem to the database in that case
unmatched_values = df_table1[df_table1['id_emission_type'].isna()]
unmatched_indices = unmatched_values.index
add_to_db = df_table1_primary.loc[unmatched_indices,'emission type'].tolist() #list of emission types that are not in the database
print(add_to_db), print("\n")

insert_query1 = "INSERT INTO emission_type (type_name) VALUES (%s)" #query to insert the new emission types
for emission_type in add_to_db: #insert the new emission types into the database
    cursor.execute(insert_query1 (emission_type,))
    my_db.commit()

df_table1['id_emission_type'] = df_table1['id_emission_type'].astype(int) #convert the decimal column to integer
print(df_table1.head()), print("\n")

cursor.execute("SELECT quantity FROM emissions")
# valid_ids = sorted({id for id in cursor.fetchall()})
# print(valid_ids), print("\n")
# print(sorted(df_table1['id_emission_type'].unique())), print("\n")

# Insert Section 1 data into Table 1
table1_name = 'emissions'
for _, row in df_table1.iterrows(): #_ is the index of the row, row is the data in the row
    values = tuple(row)
    placeholders = ', '.join(['%s'] * len(values))
    insert_query2 = f"INSERT INTO {table1_name} ({columns_table1}) VALUES ({placeholders})"
    # Replace NaN values with None, which MySQL will interpret as NULL
    values = [None if pd.isna(value) else value for value in row]
    print(values)
    cursor.execute(insert_query2, values)
    my_db.commit() #commit the changes to the database

# Close cursor and connection
cursor.close()
my_db.close()

print("Data imported successfully into multiple tables.")
