from flask import request
import hashlib

from app import app
from modules.dao import insert_into, select_from

@app.route('/api/v1/users', methods=['POST'])
def register_user():
    username = request.form.get('username')
    password = request.form.get('password')
    if len(select_from('users', ['id'], "username = \'" + username + "\'")) == 0:
        insert_into("users", ["username", "password"], [username, hashlib.sha256(password.encode("utf-8")).hexdigest()])
        return 'ok'
    return 'user already exists'

def authorize(username, password):
    user_id = select_from('users', ['id'], "username = \'" + username + "\'")
    if user_id is None or len(user_id) == 0:
        return False
    user_id = user_id[0][0]
    password_hash = select_from('users', ['password'], "id = " + str(user_id))[0][0]
    return password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_id_by_username(username):
    user_id = select_from('users', ['id'], "username = \'" + username + "\'")
    if len(user_id) > 0:
        return user_id[0][0]
    return None
