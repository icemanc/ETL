import re

def convert_ddl_to_bigquery_sql(ddl):
    ddl = ddl.strip()

    # Type mappings. this will only cast columns in source sql output
    source_type_mapping = {
        'time(0)': 'varchar(40)',
        'DECIMAL(*,*)': 'STRING',
        'NUMERIC(*,*)': 'STRING',
        'BYTEINT': 'STRING',
        'VARCHAR(*)': 'STRING',
        'CHAR(*)': 'STRING'
    }

    stage_type_mapping = {
        'SMALLINT': 'STRING',
        'DECIMAL(*,*)': 'STRING',
        'NUMERIC(*,*)': 'numeric(*,*)',
        'BYTEINT': 'STRING',
        'INTEGER': 'STRING',
        'DATE': 'DATE',
        'time(0)': 'STRING',
        'TIMESTAMP(6)': 'STRING',
        'VARCHAR(*)': 'STRING',
        'CHAR(*)': 'STRING'
    }

    target_type_mapping = {
        'SMALLINT': 'INT64',
        'DECIMAL(*,*)': 'NUMERIC(*,*)',
        'NUMERIC(*,*)': 'NUMERIC(*,*)',
        'BYTEINT': 'INT64',
        'INTEGER': 'INT64',
        'DATE': 'DATE',
        'time(0)': 'TIME',
        'TIMESTAMP(6)': 'TIMESTAMP',
        'VARCHAR(*)': 'STRING',
        'CHAR(*)': 'STRING'
    }

    def resolve_type(teradata_type, mapping):
        # Match DECIMAL(p,s) or NUMERIC(p,s)
        numeric_match = re.match(r'(DECIMAL|NUMERIC)\((\d+),\s*(\d+)\)', teradata_type, re.IGNORECASE)
        if numeric_match:
            base_type, precision, scale = numeric_match.groups()
            key = f'{base_type.upper()}(*,*)'
            if key in mapping:
                return mapping[key].replace('*', precision, 1).replace('*', scale, 1)
            return mapping.get(teradata_type, 'STRING')

        if teradata_type.startswith('VARCHAR'):
            return mapping.get('VARCHAR(*)', 'STRING')
        if teradata_type.startswith('CHAR'):
            return mapping.get('CHAR(*)', 'STRING')

        return mapping.get(teradata_type, 'STRING')

    # Extract table name
    table_match = re.search(r'TABLE\s+([\w\.]+)', ddl, re.IGNORECASE)
    if not table_match:
        raise ValueError("Table name not found in DDL")
    table_name = table_match.group(1)

    # Extract column definitions
    start_idx = ddl.find('(')
    end_idx = ddl.rfind(')')
    if start_idx == -1 or end_idx == -1:
        raise ValueError("Column definitions not found in DDL")
    column_section = ddl[start_idx+1:end_idx].strip()

    column_text = ' '.join(line.strip() for line in column_section.split('\n') if line.strip())

    # Smart column splitting
    columns_raw = []
    current = ""
    paren_level = 0
    for char in column_text:
        if char == '(':
            paren_level += 1
            current += char
        elif char == ')':
            paren_level -= 1
            current += char
        elif char == ',' and paren_level == 0:
            columns_raw.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        columns_raw.append(current.strip())

    # Filter out non-column lines
    columns = [col for col in columns_raw if not col.upper().startswith(('PRIMARY', 'PARTITION', 'INDEX'))]

    column_defs = []
    for col in columns:
        col = re.sub(r'\s*COMPRESS\s*\([^)]*\)', '', col, flags=re.IGNORECASE)
        col = re.sub(r'\s*CHARACTER\s+SET\s+\w+\s+NOT\s+CASESPECIFIC', '', col, flags=re.IGNORECASE)
        col = re.sub(r'\s*FORMAT\s*\'[^\']*\'', '', col, flags=re.IGNORECASE)

        parts = col.split()
        if len(parts) >= 2:
            col_name = parts[0]
            col_type = parts[1]
            if len(parts) > 2 and parts[2].startswith('('):
                col_type += parts[2]
            column_defs.append((col_name, col_type))

    stage_columns = []
    target_columns = []
    insert_select_columns = []
    source_select_columns = []

    for col_name, teradata_type in column_defs:
        col_name = col_name.replace(' ', '_')

        stage_type = resolve_type(teradata_type, stage_type_mapping)
        target_type = resolve_type(teradata_type, target_type_mapping)
        source_type = resolve_type(teradata_type, source_type_mapping)

        stage_columns.append(f"{col_name} {stage_type}")
        target_columns.append(f"{col_name} {target_type}")

        if stage_type != target_type:
            insert_select_columns.append(f"CAST({col_name} AS {target_type}) AS {col_name}")
        else:
            insert_select_columns.append(f"{col_name}")

        if source_type:
            source_select_columns.append(f"CAST({col_name} AS {source_type}) AS {col_name}")
        else:
            source_select_columns.append(f"{col_name}")

    def format_with_leading_commas(items):
        return "\n  " + "\n  , ".join(items)

    # Generate SQL strings
    source_sql = (
        "===================="
        "\n*    SOURCE SQL    *"
        "\n===================="
        "\nSELECT" +
        format_with_leading_commas(source_select_columns) +
        f"\nFROM {table_name};"
    )

    stage_table_sql = (
        "===================="
        "\n-   STAGE TABLE   -"
        "\n===================="
        f"\nCREATE TABLE {table_name}_stg (" +
        format_with_leading_commas(stage_columns) +
        "\n);"
    )

    target_table_sql = (
        "===================="
        "\n-  TARGET TABLE   -"
        "\n===================="
        f"\nCREATE TABLE {table_name} (" +
        format_with_leading_commas(target_columns) +
        "\n);"
    )

    insert_sql = (
        "===================="
        "\n- TRANSFORMATION  -"
        "\n===================="
        f"\nINSERT INTO {table_name} (" +
        format_with_leading_commas([col_name.replace(' ', '_') for col_name, _ in column_defs]) +
        "\n)\nSELECT" +
        format_with_leading_commas(insert_select_columns) +
        f"\nFROM {table_name}_stg;"
    )

    return f"{source_sql}\n\n{stage_table_sql}\n\n{target_table_sql}\n\n{insert_sql}"


# ✅ Example DDL
ddl = """
CREATE MULTISET TABLE finance.transactions (
    txn_id INTEGER,
    account_id INTEGER,
    amount DECIMAL(10,2),
    tax NUMERIC(5,3),
    created_at TIMESTAMP(6),
    txn_type VARCHAR(20),
    remarks CHAR(100)
);
"""

# Run the function
result = convert_ddl_to_bigquery_sql(ddl)
print(result)
