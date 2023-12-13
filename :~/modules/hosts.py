from flask import request, send_file
import psycopg2
from app import app

@app.route('/api/v1/hosts', methods=['POST'])
def create_host():
    host_ip = request.form.get('host_name')
    connect = psycopg2.connect(host='localhost', user='otv', password='otv', dbname='otv')
    cursor = connect.cursor()
    cursor.execute("INSERT INTO hosts (ip) VALUES (\'" + host_ip + "\');")
    connect.commit()
    cursor.close()
    connect.close()
    return 'Ok'
