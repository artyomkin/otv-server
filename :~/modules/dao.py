import psycopg2

def insert_into(table_name, columns, values):
    columns_str = ""
    values_str = ""
    if len(columns) != len(values):
        print("columns dont match values")
        exit(1)
    for i in range(len(columns)):
        columns_str += columns[i]
        values_str += '\'' + values[i] + '\''
        if i < len(columns) - 1:
            columns_str += ", "
            values_str += ", "
    connect = psycopg2.connect(host='localhost', user='otv', password='otv', dbname='otv')
    cursor = connect.cursor()
    cursor.execute(
        "INSERT INTO " + table_name + " (" + columns_str + ") VALUES ("+ values_str + ");")
    connect.commit()
    cursor.close()
    connect.close()
    return 'Ok.'
