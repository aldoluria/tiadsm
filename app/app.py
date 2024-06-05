import os
import psycopg2
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf=CSRFProtect()

"""
Para realizar la conexión a la base de datos con postgresql es importante intalar psycopg2

    pip install psycopg2

Despues, debemos configurar nuestras variables de entorno (Variables de usuario)
    DB_USERNAME = Nombre_Postgres
    DB_PASSWORD = Contraseña_Postgres
"""

def get_db_connection():
    try:
        conn = psycopg2.connect(host='localhost',
                                dbname='escuela_aglg',
                                user=os.environ['DB_USERNAME'],
                                password=os.environ['DB_PASSWORD'])
        return conn
    except psycopg2.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None

app.secret_key='mysecretkey'

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM alumnos;')
    alumnos = cur.fetchall()
    cur.close()
    conn.close()
    titulo = "Clase Chidita del dia de HOY!!!!!!!!!"
    return render_template('index.html', titulo=titulo, alumnos=alumnos)

@app.route("/about-us")
def about_us():
    return render_template('about_us.html')

@app.route("/dashboard")
def dashboard():
    titulo = "Panel de Administración"
    return render_template('dashboard.html', titulo=titulo)

#------------------------- CRUD Alumnos -------------------------

@app.route("/dashboard/alumnos")
def alumnos():
    titulo = "Alumnos"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM alumnos;')
    alumnos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('alumnos.html', titulo=titulo,alumnos=alumnos)

@app.route("/dashboard/alumnos/nuevo")
def alumnos_nuevo():
    titulo = "Alumno nuevo"
    return render_template('alumnos_nuevo.html', titulo=titulo)

@app.route('/dashboard/alumnos/crear', methods=('GET', 'POST'))
def alumnos_crear():
    if request.method == 'POST':
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form['materno']
        activo = True

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO alumnos (nombre, apellido_paternno, apellido_materno, activo)'
                    'VALUES (%s, %s, %s, %s)',
                    (nombre, paterno, materno, activo))
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Alumno agregado exitosamente!')

        return redirect(url_for('alumnos'))

    return redirect(url_for('alumnos_nuevo'))

#------------------------- CRUD Profesores -------------------------

#------------------------- CRUD Materias -------------------------

#------------------------- CRUD Grupos -------------------------
def pagina_no_encontrada(error):
    return render_template('404.html')

def acceso_no_autorizado(error):
    return redirect(url_for('login'))

if __name__ == '__main__':
    csrf.init_app(app)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(debug=True, port=5000)

#Activar entorno    virtual .venv\Scripts\activate
#Correr aplicación  python app\app.py run
#                   flask --app app\app.py run


