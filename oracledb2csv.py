#Performance of Extract 1,612,903 Records/Minute


import csv
import os
import getpass
import oracledb

#un = os.environ.get('PYTHON_USERNAME')
#cs = os.environ.get('PYTHON_CONNECTSTRING')
#pw = getpass.getpass(f'Enter password for {un}@{cs}: ')

un="konerna"
cs="hostname:port/servicename"  # hostname:port/servicename

pw="password"

connection = oracledb.connect(user=un, password=pw, dsn=cs)

sql = 'select t1.* from PEGAIH.PR_DATA_IH_FACT t1 cross join (select 1 from dual connect by level <= 2000) t2 where rownum<=50000000'

with connection.cursor() as cursor:
    cursor.prefetchrows = 19000000
    cursor.arraysize = 2000000

    with open("output.csv", "w", encoding='utf-8') as outputfile:
        writer = csv.writer(outputfile, lineterminator="\n")

        cursor.execute(sql)

        while True:
            rows = cursor.fetchmany(2000000)  # Adjust batch size as needed
            if not rows:
                break
            writer.writerows(rows)






''' version 2
import csv
import os
import getpass

import oracledb

# Get the PYTHON_USERNAME and PYTHON_CONNECTSTRING from the environment
#un = os.environ.get('PYTHON_USERNAME')
#cs = os.environ.get('PYTHON_CONNECTSTRING')
#pw = getpass.getpass(f"Enter password for {un}@{cs}: ")

un="konerna"
cs="hostname:port/servicename"  # hostname:port/servicename
pw="pasword"


# Connect to the Oracle database
connection = oracledb.connect(user=un, password=pw, dsn=cs)

# Execute the SQL query
cursor = connection.cursor()
cursor.prefetchrows = 19000000
cursor.arraysize = 2000000

sql = "select t1.* from PEGAIH.PR_DATA_IH_FACT t1 cross join (select 1 from dual connect by level <= 50000000) where rownum<=50000000"
cursor.execute(sql)

# Write the output to a CSV file
with open("output.csv", "w", newline="", encoding="utf-8") as outputfile:
    writer = csv.writer(outputfile, lineterminator="\n")
    while True:
        rows = cursor.fetchmany(2000000)  # Adjust batch size as needed
        if not rows:
            break
        writer.writerows(rows)

# Close the database connection
cursor.close()
connection.close()
'''
