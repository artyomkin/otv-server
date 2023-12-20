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
    connect = psycopg2.connect("""
    host=rc1b-4h6vv303i4w7rege.mdb.yandexcloud.net
    port=6432
    sslmode=verify-full
    dbname=db1
    user=otv
    password=otvotvotv
    target_session_attrs=read-write
    """)
    cursor = connect.cursor()
    cursor.execute(
        "INSERT INTO " + table_name + " (" + columns_str + ") VALUES ("+ values_str + ");")
    connect.commit()
    cursor.close()
    connect.close()
    return 'Ok.'

def select_from(table_name, columns, condition):
    columns_str = ""
    for i in range(len(columns)):
        columns_str += columns[i]
        if i < len(columns) - 1:
            columns_str += ", "
    connect = psycopg2.connect("""
    host=rc1b-4h6vv303i4w7rege.mdb.yandexcloud.net
    port=6432
    sslmode=verify-full
    dbname=db1
    user=otv
    password=otvotvotv
    target_session_attrs=read-write
    """)
    cursor = connect.cursor()
    cursor.execute(
        "select " + columns_str + " from " + table_name + " where " + condition + ";")
    res = cursor.fetchall()
    connect.commit()
    cursor.close()
    connect.close()
    return res

def get_id_by_name(tablename, name):
    query = Query()
    findres = query.sel(["id"]).fro(tablename).where("name = \'" + name + "\'").execute(True)
    if findres is not None:
        return findres[0]
    return None

class Query:
    q = ""
    def sel(self, columns):
        self.q += "select "
        for i in range(len(columns)):
            self.q += columns[i]
            if i < len(columns) - 1:
                self.q += ", "
            else:
                self.q += " "
        return self

    def fro(self, table_name):
        self.q += "from " + table_name + " "
        return self

    def where(self, condition):
        self.q += "where " + condition
        return self

    def insert_into(self, tablename, columns):
        self.q += "insert into " + tablename + " ("
        for i in range(len(columns)):
            self.q += columns[i]
            if i < len(columns) - 1:
                self.q += ", "
            else:
                self.q += ") "
        return self

    def values(self, values):
        self.q += "values ("
        for i in range(len(values)):
            self.q += "\'" + str(values[i]) + "\'"
            if i < len(values) - 1:
                self.q += ", "
            else:
                self.q += ") "
        return self

    def execute(self, find):
        connect = psycopg2.connect("""
        host=rc1b-4h6vv303i4w7rege.mdb.yandexcloud.net
        port=6432
        sslmode=verify-full
        dbname=db1
        user=otv
        password=otvotvotv
        target_session_attrs=read-write
        """)
        cursor = connect.cursor()
        cursor.execute(self.q)
        res = None
        if find:
            res = cursor.fetchall()
        connect.commit()
        cursor.close()
        connect.close()
        if find:
            if len(res) > 0:
                x = map(list, list(res))
                x = sum(x, [])
                return x
            else:
                return None
        return None

