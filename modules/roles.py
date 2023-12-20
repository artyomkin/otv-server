# Import Libraries 
import os
import subprocess
import hashlib
import string
import zipfile
import shutil
import random
from app import app
from modules.users import *
from modules.hosts import *
import psycopg2
from flask import request, send_file
from modules.dao import *
from modules.cipher import *

ANSIBLE_FOLDER = 'ansible'
ROLES_FOLDER = os.path.join(ANSIBLE_FOLDER, 'roles')
GROUP_VARS_FOLDER = os.path.join(ANSIBLE_FOLDER, 'group_vars')
HOST_VARS_FOLDER = os.path.join(ANSIBLE_FOLDER, 'host_vars')
ALLOWED_EXTENSIONS = {'yml', 'yaml'}

app.config['ANSIBLE_FOLDER'] = ANSIBLE_FOLDER
app.config['ROLES_FOLDER'] = ROLES_FOLDER
app.config['GROUP_VARS_FOLDER'] = GROUP_VARS_FOLDER
app.config['HOST_VARS_FOLDER'] = HOST_VARS_FOLDER

def copytree(src, dst, symlinks=False, ignore=None):
    #for item in os.listdir(src):
    #    s = os.path.join(src, item)
    #    if not os.path.exists(s):
    #        continue
    #    d = os.path.join(dst, item)
    #    if os.path.isdir(s):
    #        shutil.copytree(s, d, symlinks, ignore)
    #        print(os.listdir(d))
    #    else:
    #        shutil.copy2(s, dst)
    if not os.path.exists(src):
        return
    if os.path.isdir(src):
        shutil.copytree(src, dst, symlinks, ignore)
        print(os.listdir(dst))
    else:
        shutil.copy2(src, dst)


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file),
                                       os.path.join(path, '..')))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_file(werkzeug_file, path):
    basename = os.path.basename(os.path.normpath(path))
    path = path.replace(basename + ".yaml", basename + ".yml")
    werkzeug_file.save(path)


@app.route('/api/v1/roles', methods=['POST'])
def create_role():
    role_name = request.form.get('role_name')
    username = request.form.get('username')
    password = request.form.get('password')
    if not authorize(username, password):
        return 'Unauthorized.'

    main_tasks_file = request.files.get("main_tasks_file")
    main_defaults_file = request.files.get("main_defaults_file")
    if not allowed_file(main_defaults_file.filename) or not allowed_file(main_tasks_file.filename):
        return 'File is not allowed'

    role_path = os.path.join('otv', username, app.config['ROLES_FOLDER'], role_name)
    tasks_path = os.path.join(role_path, 'tasks')
    defaults_path = os.path.join(role_path, 'defaults')

    create_dir(tasks_path)
    create_dir(defaults_path)

    main_tasks_filename = "main.yml"
    main_defaults_filename = "main.yml"

    save_file(main_tasks_file, os.path.join(tasks_path, main_tasks_filename))
    save_file(main_defaults_file, os.path.join(defaults_path, main_defaults_filename))

    insert_into('roles', ['name', 'path'], [role_name, role_path])

    return 'Ok.'


@app.route('/api/v1/group_vars', methods=['POST'])
def create_group_vars():
    role_name = request.form.get('group_name')

    username = request.form.get('username')
    password = request.form.get('password')
    if not authorize(username, password):
        return 'Unauthorized.'

    group_vars_file = request.files.get("group_vars_file")
    if not allowed_file(group_vars_file.filename):
        return 'File is not allowed'

    group_vars_path = os.path.join('otv', username, app.config['GROUP_VARS_FOLDER'], role_name)
    create_dir(group_vars_path)
    group_vars_filename = 'main.yml'

    save_file(group_vars_file, os.path.join(group_vars_path, group_vars_filename))
    return 'Ok.'


@app.route('/api/v1/host_vars', methods=['POST'])
def create_host_vars():
    host_name = request.form.get('host_name')

    host_vars_file = request.files.get("host_vars_file")
    if not allowed_file(host_vars_file.filename):
        return 'File is not allowed'

    username = request.form.get('username')
    password = request.form.get('password')
    if not authorize(username, password):
        return 'Unauthorized.'

    host_vars_path = os.path.join('otv', username, app.config['HOST_VARS_FOLDER'], host_name)
    create_dir(host_vars_path)
    host_vars_filename = 'main.yml'

    save_file(host_vars_file, os.path.join(host_vars_path, host_vars_filename))
    return 'Ok.'


def get_checksum(paths):
    files = []
    for path in paths:
        if path == "":
            continue
        files.extend(subprocess.run(['/bin/bash', '-c', 'find ' + path + ' -type f'],
                               capture_output=True).stdout.decode().split('\n'))
    files = [file for file in files if file != ""]
    content = ""
    for path in files:
        with open(path) as p:
            content += p.read()

    res = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return res


def gen_tmp_path():
    temp_dirname = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
    temp_dir_path = os.path.join('tmp', '.tmp-otv-' + temp_dirname)
    print(temp_dir_path)
    return temp_dir_path

def init_tmp(base_path):
    create_dir(os.path.join(base_path, "roles"))
    create_dir(os.path.join(base_path, "group_vars"))
    create_dir(os.path.join(base_path, "host_vars"))

def copy_ansible_to_tmp(roles_paths, host_vars_paths, group_vars_paths, tmp_roles_path, tmp_host_vars_path, tmp_group_vars_path):
    if roles_paths is not None:
        for role_path in roles_paths:
            if role_path == "":
                continue
            copytree(role_path, os.path.join(tmp_roles_path, os.path.basename(role_path)))
    if host_vars_paths is not None:
        for host_vars_path in host_vars_paths:
            if host_vars_path == "":
                continue
            copytree(host_vars_path, os.path.join(tmp_host_vars_path, os.path.basename(host_vars_path)))
    if group_vars_paths is not None:
        for group_vars_path in group_vars_paths:
            if group_vars_path == "":
                continue
            copytree(group_vars_path, os.path.join(tmp_group_vars_path, os.path.basename(group_vars_path)))

@app.route('/api/v1/agent', methods=['POST'])
def get_all_endpoint():
    checksum = request.args.get('checksum')

    username = decrypt(request.json.get('username')).rstrip()
    password = decrypt(request.json.get('password')).rstrip()
    host_name = request.json.get('host_name')
    if not authorize(username, password):
        return 'Unauthorized.'

    allowed_roles, allowed_host_groups, allowed_role_groups = get_all_for_host(host_name)
    role_paths, host_vars_path, group_vars_paths = generate_paths_for_agent(username, allowed_roles, allowed_host_groups,
                                                                            allowed_role_groups, host_name)
    server_checksum = get_checksum([*role_paths, host_vars_path, *group_vars_paths])
    if checksum == server_checksum:
        return 'Nothing changed.'

    tmp_dir_path = gen_tmp_path()

    init_tmp(tmp_dir_path)
    tmp_roles_path = os.path.join(tmp_dir_path, 'roles')
    tmp_group_vars_path = os.path.join(tmp_dir_path, 'group_vars')
    tmp_host_vars_path = os.path.join(tmp_dir_path, 'host_vars')
    copy_ansible_to_tmp(role_paths, [host_vars_path], group_vars_paths, tmp_roles_path, tmp_host_vars_path, tmp_group_vars_path)

    with zipfile.ZipFile(tmp_dir_path + '.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(tmp_dir_path, zipf)

    return send_file(tmp_dir_path + ".zip")

def get_all_for_host(host_name):
    allowed_roles_ids = get_all_allowed_roles_for_host(host_name)
    host_id = get_id_by_name("hosts", host_name)
    host_groups_ids = get_tree_of(host_id, "hosts")
    role_groups_ids = set()
    for role_id in allowed_roles_ids:
        role_groups_ids.update(set(get_tree_of(role_id, "roles")))
    allowed_roles = get_names_by_ids(allowed_roles_ids, "roles") if len(allowed_roles_ids) > 0 else []
    allowed_host_groups = get_names_by_ids(host_groups_ids, "host_groups") if len(host_groups_ids) > 0 else []
    allowed_role_groups = get_names_by_ids(list(role_groups_ids), "role_groups") if len(role_groups_ids) > 0 else []

    return allowed_roles, allowed_host_groups, allowed_role_groups

def generate_paths_for_agent(username, roles, host_groups, role_groups, host_name):

    role_base_path = os.path.join("otv", username, app.config["ROLES_FOLDER"])
    group_vars_base_path = os.path.join("otv", username, app.config["GROUP_VARS_FOLDER"])

    roles_paths = [os.path.join(role_base_path, role_name) for role_name in roles if roles is not None]
    res_roles_paths = [path for path in roles_paths if os.path.exists(path)]

    res_host_vars_path = os.path.join("otv", username, app.config["HOST_VARS_FOLDER"], host_name)
    if not os.path.exists(res_host_vars_path):
        res_host_vars_path = ""

    group_vars = host_groups
    if role_groups is not None and group_vars is not None:
        group_vars.extend(role_groups)
    elif role_groups is not None and group_vars is None:
        group_vars = role_groups
    group_vars_paths = [os.path.join(group_vars_base_path, group_vars_name) for group_vars_name in group_vars if group_vars is not None]
    res_group_vars_paths = [path for path in group_vars_paths if os.path.exists(path)]
    return res_roles_paths, res_host_vars_path, res_group_vars_paths

def get_all_allowed_roles_for_host(host_name):
    host_id = get_id_by_name("hosts", host_name)
    host_groups_tree = get_tree_of(host_id, "hosts")
    allowed_role_groups, allowed_roles = get_allows(host_id, "hosts")
    allowed_roles = set(allowed_roles) if allowed_roles is not None else set()
    allowed_role_groups = set(allowed_role_groups) if allowed_role_groups is not None else set()
    for host_group_id in host_groups_tree:
        temp_allowed_role_groups, temp_allowed_roles = get_allows(host_group_id, "host_groups")
        if temp_allowed_roles is not None:
            allowed_roles.update(set(temp_allowed_roles))
        if temp_allowed_role_groups is not None:
            allowed_role_groups.update(set(temp_allowed_role_groups))

    allowed_roles.update(set(get_all_entities_of(
        allowed_role_groups,
        "role_groups",
        "parent_role_group_id",
        "child_role_group_id",
        "role_group_role_group_bindings",
        "role_groups_bindings"
    )))
    return list(allowed_roles)


@app.route('/api/v1/roles/allow', methods=['POST'])
def allow_role_to_host():
    host_entity_name = request.form.get('host_entity_name')
    host_entity_type = request.form.get('host_entity_type')
    role_entity_name = request.form.get('role_entity_name')
    role_entity_type = request.form.get('role_entity_type')

    username = request.form.get('username')
    password = request.form.get('password')
    if not authorize(username, password):
        return 'Unauthorized.'

    if role_entity_type == 'role':
        role_entity_type = 'roles'
        if not check_exists("roles", role_entity_name):
            return 'No such role.'
    elif role_entity_type == 'role_group':
        role_entity_type = 'role_groups'
        if not check_exists("role_groups", role_entity_name):
            return 'No such role group.'

    if host_entity_type == 'host':
        host_entity_type = 'hosts'
        if not check_exists("hosts", host_entity_name):
            return 'No such host.'
    elif host_entity_type == 'host_group':
        host_entity_type = 'host_groups'
        if not check_exists("host_groups", host_entity_name):
            return 'No such host group.'

    host_entity_id = str(get_id_by_name(host_entity_type, host_entity_name))
    role_entity_id = str(get_id_by_name(role_entity_type, role_entity_name))

    Query().insert_into("role_host_allow",
                        ["role_entity_id", "host_entity_id", "role_entity_type", "host_entity_type"]) \
        .values([role_entity_id, host_entity_id, role_entity_type, host_entity_type]) \
        .execute(False)

    return 'Ok.'


def get_all_groups_ids(groups_table):
    return Query().sel(["id"]).fro(groups_table).execute(True)

def get_parent_groups_of(group_id, parent_group_id_col, child_group_id_col, group_to_group_binding):
    groups_ids = Query().sel([parent_group_id_col]).fro(group_to_group_binding).where(
        child_group_id_col + " = " + str(group_id)).execute(True)
    return groups_ids

def get_child_groups_of(group_id, parent_group_id_col, child_group_id_col, group_to_group_binding):
    groups_ids = Query().sel([child_group_id_col]).fro(group_to_group_binding).where(
        parent_group_id_col + " = " + str(group_id)).execute(True)
    return groups_ids

def get_all_groups_of(groups_ids, groups_table, parent_group_id_col, child_group_id_col, group_to_group_binding):
    q_groups_ids = groups_ids
    visited_groups = dict()
    for group_id in get_all_groups_ids(groups_table):
        visited_groups[group_id] = "n"

    while q_groups_ids is not None and len(q_groups_ids) > 0:
        current_group_id = q_groups_ids.pop()
        if visited_groups[current_group_id] == "y":
            continue
        visited_groups[current_group_id] = "y"
        parent_groups = get_parent_groups_of(current_group_id, parent_group_id_col, child_group_id_col, group_to_group_binding)
        if parent_groups is None:
            continue
        q_groups_ids.extend(parent_groups)

    res_groups_ids = [id for id, visited in visited_groups.items() if visited == "y"]
    return res_groups_ids

def get_all_entities_of(groups_ids, groups_table, parent_group_id_col, child_group_id_col, group_to_group_binding, entity_to_group_binding):
    q_groups_ids = groups_ids
    entities_ids = set()
    visited_groups = dict()
    for group_id in get_all_groups_ids(groups_table):
        visited_groups[group_id] = "n"

    entity_id_col_name = "host_id"
    group_id_col_name = "host_group_id"
    if groups_table == "role_groups":
        entity_id_col_name = "role_id"
        group_id_col_name = "role_group_id"
    while len(q_groups_ids) > 0:
        current_group_id = q_groups_ids.pop()
        entities_ids.update(get_all_direct_entities_of(current_group_id, entity_to_group_binding,entity_id_col_name, group_id_col_name))
        if visited_groups[current_group_id] == "y":
            continue
        visited_groups[current_group_id] = "y"
        child_groups = get_parent_groups_of(current_group_id, parent_group_id_col, child_group_id_col, group_to_group_binding)
        if child_groups is None:
            continue
        q_groups_ids.extend(child_groups)

    return list(entities_ids)

def get_all_direct_entities_of(group_id, entity_to_group_binding, entity_id_col_name, group_id_col_name):
    return Query().sel([entity_id_col_name]).fro(entity_to_group_binding).where(str(group_id_col_name) + " = " + str(group_id)).execute(True)

def get_tree_of(id, type):
    if type not in ["roles", "hosts"]:
        return None
    group_to_group_binding = "role_group_role_group_bindings"
    group_to_entity_binding = "role_groups_bindings"
    groups_table = "role_groups"
    group_id = "role_group_id"
    entity_id = "role_id"
    parent_group_id_col = "parent_role_group_id"
    child_group_id_col = "child_role_group_id"
    if type == "hosts":
        group_to_group_binding = "host_group_host_group_bindings"
        group_to_entity_binding = "host_groups_host_bindings"
        groups_table = "host_groups"
        group_id = "host_group_id"
        entity_id = "host_id"
        parent_group_id_col = "parent_host_group_id"
        child_group_id_col = "child_host_group_id"

    groups_ids = Query().sel([group_id]).fro(group_to_entity_binding).where(entity_id + " = \'" + str(id) + "\'").execute(True)
    return get_all_groups_of(groups_ids, groups_table, parent_group_id_col, child_group_id_col, group_to_group_binding)

def get_allows(host_entity_id, host_entity_type):
    role_groups = Query().sel(["role_entity_id"]).fro("role_host_allow").where(
        "role_entity_type = 'role_groups' and " +
        "host_entity_type = \'" + str(host_entity_type) + "\' and " +
        "host_entity_id = \'" + str(host_entity_id) + "\'"
    ).execute(True)
    roles = Query().sel(["role_entity_id"]).fro("role_host_allow").where(
        "role_entity_type = 'roles' and " +
        "host_entity_type = \'" + str(host_entity_type) + "\' and " +
        "host_entity_id = \'" + str(host_entity_id) + "\'"
    ).execute(True)

    return role_groups, roles

def check_allowed(role_name, host_name):
    host_id = get_id_by_name("hosts", host_name)
    role_id = get_id_by_name("roles", role_name)
    allowed_role_groups_ids, allowed_roles_ids = get_allows(host_id, "hosts")
    if allowed_roles_ids is not None and role_id in allowed_roles_ids:
        return True
    role_groups_ids = get_tree_of(role_id, "roles")
    host_groups_ids = get_tree_of(host_id, "hosts")
    if allowed_role_groups_ids is not None and len(set(allowed_role_groups_ids).intersection(role_groups_ids)) > 0:
        return True

    for host_group_id in host_groups_ids:
        allowed_role_groups, allowed_roles = get_allows(host_group_id, "host_groups")
        if allowed_roles is not None and role_id in allowed_roles or allowed_role_groups is not None and len(set(allowed_role_groups_ids).intersection(role_groups_ids)) > 0:
            return True
    return False

def create_group(group_name, tablename):
    if group_name is not None:
        Query().insert_into(tablename, ["name"]).values([group_name]).execute(False)
        return "Ok."
    else:
        return "Specify group name."

def add_entity_to_group(name, group_name, type):
    entity_table_name = "roles"
    group_table_name = "role_groups"
    bindings_table_name = "role_groups_bindings"
    id_col_name = "role_id"
    group_id_col_name = "role_group_id"
    if type == 'hosts':
        entity_table_name = "hosts"
        group_table_name = "host_groups"
        bindings_table_name = "host_groups_host_bindings"
        id_col_name = "host_id"
        group_id_col_name = "host_group_id"

    if name is not None and group_name is not None:
        id = get_id_by_name(entity_table_name, name)
        group_id = get_id_by_name(group_table_name, group_name)
        Query().insert_into(bindings_table_name, [id_col_name, group_id_col_name]).values([id, group_id]).execute(False)
        return "Ok."
    else:
        return "Specify name and group name."

def add_group_to_group(child_group_name, parent_group_name, type):
    group_table_name = "role_groups"
    bindings_table_name = "role_group_role_group_bindings"
    parent_id_col_name = "parent_role_group_id"
    child_id_col_name = "child_role_group_id"
    if type == 'host_groups':
        group_table_name = "host_groups"
        bindings_table_name = "host_group_host_group_bindings"
        parent_id_col_name = "parent_host_group_id"
        child_id_col_name = "child_host_group_id"
    if child_group_name is not None and parent_group_name is not None:
        child_id = get_id_by_name(group_table_name, child_group_name)
        parent_id = get_id_by_name(group_table_name, parent_group_name)
        Query().insert_into(bindings_table_name, [parent_id_col_name, child_id_col_name]).values([parent_id, child_id]).execute(False)
        return "Ok."
    else:
        return "Specify child role group name and parent role group name."

def get_names_by_ids(ids, table_name):
    idStr = ""
    for i in range(len(ids)):
        idStr += str(ids[i])
        if i < len(ids) - 1:
            idStr += ", "
    return Query().sel(["name"]).fro(table_name).where("id in (" + idStr + ")").execute(True)
