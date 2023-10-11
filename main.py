import bcrypt
import sqlalchemy
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from flask import request, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.functions import current_user

from config import LOGIN_DATABASE, PASSWORD_DATABASE, HOST_DATABASE, PORT_DATABASE, NAME_DATABASE

app = Flask (__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+LOGIN_DATABASE+':'+PASSWORD_DATABASE+'@'+HOST_DATABASE+':'+PORT_DATABASE+'/'+NAME_DATABASE

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

@app.route ('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    firstname = data['firstname']
    name = data['name']
    email = data['email']


    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    query = 'SELECT username FROM users WHERE username = :username'
    parameters = {'username': username}
    stmt = sqlalchemy.text(query)
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, parameters=parameters)
            res = result.fetchone()
            print(f'res = {res}')
        print(f'OK select user name')
    except Exception as e:
        print(f' Error {e}')

    if res is not None :
        return jsonify({'message':'User already registered !'})
    else:
        query = (
            'INSERT INTO users (username, firstname, name, email, password) VALUES (:username, :firstname, :name, :email, :password)')
        parameters = {'username': username, 'firstname': firstname, 'name': name, 'email': email,
                      'password': hashed_password}
        stmt = sqlalchemy.text(query)
        try:
            with engine.connect() as conn:
                conn.execute(stmt, parameters=parameters)
                conn.commit()
            return jsonify({'message': 'User registered successfully !'})
        except Exception as e:
            return jsonify({'message': f'probleme insert users{e}'})

def verify_password(username, password):
    query = 'SELECT username, password FROM users WHERE username = :username'
    parameters = {'username': username}
    stmt = sqlalchemy.text(query)
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt, parameters=parameters)
            res = result.fetchone()
            print(f"res = {res[1]}")
        print(f"OK select password")
    except Exception as e:
        print(f" Error {e}")
    # Récupérer les informations utilisateur à partir de la base de données

    if res is not None:
        if bcrypt.checkpw(password.encode('utf-8'), bytes(res[1])):
            return True
    else:
        return False

# Route Flask pour vérifier le mot de passe
@app.route('/api/login', methods=['POST'])
def login():
    # Récupérer les données de la requête POST
    data = request.get_json()
    username = data['username']
    password = data['password']


    # Vérifier si le mot de passe est correct
    if verify_password(username, password):
        return jsonify({'message': 'true'})
    else:
        return jsonify({'message': 'false'})


def get_id_machines(machine_name):
    query = """SELECT id_machines FROM machines WHERE machine_name = :machine_name"""
    parameters = {'machine_name': machine_name}
    stmt = sqlalchemy.text(query)

    with engine.connect() as conn:
        result = conn.execute(stmt, parameters=parameters)
        id_machine = result.fetchone()  # Récupère la valeur unique
        if id_machine is not None:
            return id_machine[0]  # Renvoie l'ID de la machine
        else:
            return None  # Ou renvoyez None si la machine n'a pas été trouvée

def get_id_users(username):
    query = """SELECT id_users FROM users WHERE username = :username"""
    parameters = {'username': username}
    stmt = sqlalchemy.text(query)

    with engine.connect() as conn:
        result = conn.execute(stmt, parameters=parameters)
        id_users = result.fetchone()  # Récupère la valeur unique
    if id_users is not None:
        return id_users[0]  # Renvoie l'ID de la machine
    else:
        return None  # Ou renvoyez None si la machine n'a pas été trouvée


@app.route("/api/v1/workouts", methods=["POST"])
def create_workout() :
    # Récupérez les données de la demande POST
    data = request.get_json()
    machine_name = data["selectedMachine"]
    exercice_date = data["exercice_date"]
    weight = data["weight"]
    remark = data["remark"]
    username = data["username"]

    id_machines = get_id_machines(machine_name)
    id_users = get_id_users(username)

    query = (
        "INSERT INTO exercice (id_machines, weight, exercice_date, remark, id_users) VALUES (:id_machines, :weight, :exercice_date, :remark, :id_users)")
    parameters = {'id_machines': id_machines, 'weight': weight, 'exercice_date': exercice_date, 'remark': remark, 'id_users': id_users}
    stmt = sqlalchemy.text(query)
    try:
        with engine.connect() as conn:
            conn.execute(stmt, parameters=parameters)
            conn.commit()
            return jsonify({'message': 'Workout enregistré'})
    except Exception as e:
        return jsonify({'message': f'probleme insert users{e}'})


@app.route('/api/v1/workouts/<username>', methods=['GET'])
def get_last_workouts(username):
    query = """
        SELECT
          e.exercice_date,
          m.machine_name,
          e.weight,
          e.remark
        FROM
          users u
          JOIN exercice e ON u.id_users = e.id_users
          JOIN machines m ON e.id_machines = m.id_machines
        WHERE
          u.username = :username
          AND e.exercice_date = (
            SELECT MAX(exercice_date)
            FROM exercice
            WHERE id_users = u.id_users
            AND id_machines = m.id_machines
        );
      """
    parameters = {'username': username}
    stmt = sqlalchemy.text(query)
    with engine.connect() as conn:
        result = conn.execute(stmt, parameters)
        workouts = []
        for row in result:
            # Convertissez l'objet Row en objet Python standard
            workout = {'exercice_date': row[0], 'selectedMachine': row[1], 'weight': row[2], 'remark': row[3]}
            workouts.append(workout)

        # Retournez la liste des derniers exercices
    return jsonify({"workouts": workouts})


if __name__ == '__main__':
    app.run()