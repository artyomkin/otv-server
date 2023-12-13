# Import Libraries 
import os
import hashlib
import string
import zipfile
import shutil
import random
from app import app
import psycopg2
from flask import request, send_file
from modules.dao import insert_into

ANSIBLE_FOLDER = 'ansible'
ROLES_FOLDER = os.path.join(ANSIBLE_FOLDER, 'roles')
GROUP_VARS_FOLDER = os.path.join(ANSIBLE_FOLDER, 'group_vars')
HOST_VARS_FOLDER = os.path.join(ANSIBLE_FOLDER, 'host_vars')
ALLOWED_EXTENSIONS = {'yml', 'yaml'}

app.config['ANSIBLE_FOLDER'] = ANSIBLE_FOLDER
app.config['ROLES_FOLDER'] = ROLES_FOLDER
app.config['GROUP_VARS_FOLDER'] = GROUP_VARS_FOLDER
app.config['HOST_VARS_FOLDER'] = HOST_VARS_FOLDER

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

  main_tasks_file = request.files.get("main_tasks_file")
  main_defaults_file = request.files.get("main_defaults_file")
  if not allowed_file(main_defaults_file.filename) or not allowed_file(main_tasks_file.filename):
    return 'File is not allowed'

  role_path = os.path.join(app.config['ROLES_FOLDER'], role_name)
  tasks_path = os.path.join(role_path, 'tasks')
  defaults_path = os.path.join(role_path, 'defaults')

  create_dir(tasks_path)
  create_dir(defaults_path)

  main_tasks_filename = "main.yml"
  main_defaults_filename = "main.yml"

  save_file(main_tasks_file, os.path.join(tasks_path, main_tasks_filename))
  save_file(main_defaults_file, os.path.join(defaults_path, main_defaults_filename))

  insert_into('roles', ['name', 'path'], [role_name, role_name])

  return 'Ok.'



@app.route('/api/v1/group_vars', methods=['POST'])
def create_group_vars():
  role_name = request.form.get('group_name')

  group_vars_file = request.files.get("group_vars_file")
  if not allowed_file(group_vars_file.filename):
    return 'File is not allowed'

  group_vars_path = os.path.join(app.config['GROUP_VARS_FOLDER'], role_name)
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

  host_vars_path = os.path.join(app.config['HOST_VARS_FOLDER'], host_name)
  create_dir(host_vars_path)
  host_vars_filename = 'main.yml'

  save_file(host_vars_file, os.path.join(host_vars_path, host_vars_filename))
  return 'Ok.'

def get_server_role_checksum(role_name, host_name):

  role_path = os.path.join(app.config['ROLES_FOLDER'], role_name)
  group_vars_path = os.path.join(app.config['GROUP_VARS_FOLDER'], role_name)
  host_vars_path = os.path.join(app.config['HOST_VARS_FOLDER'], host_name)

  with open(os.path.join(role_path, 'tasks', 'main.yml')) as tasks:
    server_role = tasks.read()
    print(server_role)
  with open(os.path.join(role_path, 'defaults', 'main.yml')) as defaults:
    server_role = server_role + defaults.read()
    print(server_role)
  with open(os.path.join(group_vars_path, 'main.yml')) as group_vars:
    server_role = server_role + group_vars.read()
    print(server_role)
  with open(os.path.join(host_vars_path, 'main.yml')) as host_vars:
    server_role = server_role + host_vars.read()
    print(server_role)

  print(server_role)

  return hashlib.sha256(server_role.encode('utf-8')).hexdigest()

def gen_tmp_path():
  temp_dirname = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
  temp_dir_path = os.path.join('/tmp', '.tmp-role-' + temp_dirname)
  return temp_dir_path

def copy_to_tmp_dirs(role_name, tmp_dir_path, host_name):

  role_path = os.path.join(app.config['ROLES_FOLDER'], role_name)
  group_vars_path = os.path.join(app.config['GROUP_VARS_FOLDER'], role_name)
  host_vars_path = os.path.join(app.config['HOST_VARS_FOLDER'], host_name)

  copy = {
    os.path.join(role_path, 'defaults', 'main.yml'): os.path.join(tmp_dir_path, "defaults"),
    os.path.join(role_path, 'tasks', 'main.yml'): os.path.join(tmp_dir_path, "tasks"),
    os.path.join(group_vars_path, 'main.yml'): os.path.join(tmp_dir_path, "group_vars"),
    os.path.join(host_vars_path, 'main.yml'): os.path.join(tmp_dir_path, "host_vars")
  }

  for key, val in copy.items():
    create_dir(val)
    shutil.copy(key, val)

@app.route('/api/v1/roles/<role_name>/<host_name>', methods=['GET'])
def get_role(role_name, host_name):
  user_role_checksum = request.args.get('role_checksum')
  server_role_checksum = get_server_role_checksum(role_name, host_name)
  if user_role_checksum != server_role_checksum:
    temp_dir_path = gen_tmp_path()

    copy_to_tmp_dirs(role_name, temp_dir_path, host_name)

    with zipfile.ZipFile(temp_dir_path+'.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
      zipdir(temp_dir_path, zipf)

    return send_file(temp_dir_path+'.zip')
  return 'Nothing changed.'

@app.route('/api/v1/roles/<role_name>/<host_name>', methods=['POST'])
def allow_role_to_host(role_name, host_name):
  connect = psycopg2.connect(host='localhost', user='otv', password='otv', dbname='otv')
  cursor = connect.cursor()

  cursor.execute("SELECT id from roles where name=" + "\'" + role_name + "\'")
  role_fetch = cursor.fetchone()
  if role_fetch is not None:
    role_id = role_fetch[0]
  else:
    return 'No such role.'

  cursor.execute("SELECT id from hosts where ip=" + "\'" + host_name + "\'")
  host_fetch = cursor.fetchone()
  if host_fetch is not None:
    host_id = host_fetch[0]
  else:
    return 'No such host.'

  cursor.execute("INSERT INTO role_host_binding (role_id, host_id) VALUES (\'" + str(role_id) + "\', \'" + str(host_id) +"\');")
  connect.commit()
  cursor.close()
  connect.close()
  return 'Ok.'

