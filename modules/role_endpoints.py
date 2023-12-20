from flask import Flask, request
from modules.roles import *
from app import app

@app.route("/api/v1/roles/add", methods=["POST"])
def add_role_to_group():
    role_group_name = request.form.get('role_group_name')
    role_name = request.form.get('role_name')
    return add_entity_to_group(role_name, role_group_name, "roles")

@app.route("/api/v1/hosts/add", methods=["POST"])
def add_host_to_group():
    host_group_name = request.form.get('host_group_name')
    host_name = request.form.get('host_name')
    return add_entity_to_group(host_name, host_group_name, "hosts")

@app.route("/api/v1/role-groups/add", methods=["POST"])
def add_role_group_to_group():
    child_group_name = request.form.get('child_group_name')
    parent_group_name = request.form.get('parent_group_name')
    return add_group_to_group(child_group_name, parent_group_name, "role_groups")

@app.route("/api/v1/host-groups/add", methods=["POST"])
def add_host_group_to_group():
    child_group_name = request.form.get('child_group_name')
    parent_group_name = request.form.get('parent_group_name')
    return add_group_to_group(child_group_name, parent_group_name, "host_groups")
