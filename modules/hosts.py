from flask import request, send_file
import psycopg2
from app import app
from modules.users import *
from modules.dao import Query

@app.route('/api/v1/hosts', methods=['POST'])
def create_host_endpoint():
    username = request.form.get('username')
    password = request.form.get('password')
    if not authorize(username, password):
        return 'Unauthorized.'

    host_name = request.form.get('host_name')

    create_host(host_name)
    return 'Ok'

@app.route('/api/v1/host_groups', methods=['POST'])
def create_host_group():
    username = request.form.get('username')
    password = request.form.get('password')
    host_group_name = request.form.get('host_group_name')
    if not authorize(username, password):
        return 'Unauthorized.'

    host_group_children = request.form.get('host_group_children').split(', ')
    host_group_hosts_ids = []
    host_group_host_groups_ids = []
    for host_group_child in host_group_children:
        check_status = check_host_exists(host_group_child)
        if check_status == 0:
            host_group_hosts_ids.append(str(Query().sel(["id"]).fro("hosts").where("name = \'" + host_group_child + "\'").execute(True)[0]))
        elif check_status == 1:
            host_group_host_groups_ids.append(str(Query().sel(["id"]).fro("host_groups").where("name = \'" + host_group_child + "\'").execute(True)[0]))
        else:
            return host_group_child + " doesn't exist."

    Query().insert_into("host_groups", ["name"]).values([host_group_name]).execute(False)
    host_group_id = str(Query().sel(["id"]).fro("host_groups").where("name = \'" + host_group_name + "\'").execute(True)[0])
    for i in range(len(host_group_hosts_ids)):
        Query().insert_into("host_groups_host_bindings", ["host_id", "host_group_id"]).values([host_group_hosts_ids[i], host_group_id]).execute(False)
    for i in range(len(host_group_host_groups_ids)):
        Query().insert_into("host_group_host_group_bindings", ["host_group1_id", "host_group2_id"]).values([host_group_host_groups_ids[i], host_group_id]).execute(False)
    return "Ok."
@app.route('/api/v1/role_groups', methods=['POST'])
def create_role_group():
    username = request.form.get('username')
    password = request.form.get('password')
    role_group_name = request.form.get('role_group_name')
    if not authorize(username, password):
        return 'Unauthorized.'

    role_group_children = request.form.get('role_group_children').split(', ')
    role_group_roles_ids = []
    role_group_role_groups_ids = []
    for role_group_child in role_group_children:
        check_status = check_role_exists(role_group_child)
        if check_status == 0:
            role_group_roles_ids.append(str(Query().sel(["id"]).fro("roles").where("name = \'" + role_group_child + "\'").execute(True)[0]))
        elif check_status == 1:
            role_group_role_groups_ids.append(str(Query().sel(["id"]).fro("role_groups").where("name = \'" + role_group_child + "\'").execute(True)[0]))
        else:
            return role_group_child + " doesn't exist."

    Query().insert_into("role_groups", ["name"]).values([role_group_name]).execute(False)
    role_group_id = str(Query().sel(["id"]).fro("role_groups").where("name = \'" + role_group_name + "\'").execute(True)[0])
    for i in range(len(role_group_roles_ids)):
        Query().insert_into("role_groups_bindings", ["role_id", "role_group_id"]).values([role_group_roles_ids[i], role_group_id]).execute(False)
    for i in range(len(role_group_role_groups_ids)):
        Query().insert_into("role_group_role_group_bindings", ["role_group1_id", "role_group2_id"]).values([role_group_role_groups_ids[i], role_group_id]).execute(False)
    return "Ok."

def check_host_exists(host_name):
    res = Query().sel(["id"]).fro("hosts").where("name = \'" + host_name + "\'").execute(True)
    if res is not None and len(res) > 0:
        return 0
    else:
        res = Query().sel(["id"]).fro("host_groups").where("name = \'" + host_name + "\'").execute(True)
        if res is not None and len(res) > 0:
            return 1
    return 2

def check_role_exists(role_name):
    res = Query().sel(["id"]).fro("roles").where("name = \'" + role_name + "\'").execute(True)
    if res is not None and len(res) > 0:
        return 0
    else:
        res = Query().sel(["id"]).fro("role_groups").where("name = \'" + role_name + "\'").execute(True)
        if res is not None and len(res) > 0:
            return 1
    return 2

def check_exists(tablename, name):
    res = Query().sel(["id"]).fro(tablename).where("name = \'" + name + "\'").execute(True)
    return res is not None and len(res) > 0

def create_host(host_name):
    query = Query()
    query.insert_into("hosts", ['name']).values([host_name]).execute(False)

#@app.route('/api/v1/host_groups', methods=['POST'])
#def create_host_group():
#    username = request.form.get('username')
#    password = request.form.get('password')
#    if not authorize(username, password):
#        return 'Unauthorized.'
