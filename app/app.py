import os
import uuid
import psycopg2
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, url_for, redirect, request, flash, Blueprint
from flask_wtf.csrf import CSRFProtect

#Creamos una tag con la ayuda de Blueprint y la iniciamos en nuestro proyecto (al crear nuestra applicación)
custom_tags = Blueprint('custom_tags', __name__)

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
    
def my_random_string(string_length=10):
    """Regresa una cadena aleatoria de la longitud de string_length."""
    random = str(uuid.uuid4()) # Conviente el formato UUID a una cadena de Python.
    random = random.upper() # Hace todos los caracteres mayusculas.
    random = random.replace("-","") # remueve el separador UUID '-'.
    return random[0:string_length] # regresa la cadena aleatoria.

#print(my_random_string(10)) # Por ejemplo, 9BC871E354

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ruta_alumnos=app.config['UPLOAD_FOLDER']='./app/static/img/uploads/alumnos/'
ruta_profesores=app.config['UPLOAD_FOLDER']='./app/static/img/uploads/profesores/'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@custom_tags.app_template_global()
def listar_profesores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM profesores WHERE activo=true ORDER BY nombre ASC;')
    profesores = cur.fetchall()
    cur.close()
    conn.close()
    return profesores

app.secret_key='mysecretkey'

@app.route("/")
def index():
    titulo = "Plataforma de cursos"
    return render_template('index.html', titulo=titulo)

@app.route("/about-us")
def about_us():
    return render_template('about_us.html')

@app.route("/dashboard")
def dashboard():
    titulo = "Panel de Administración"
    return render_template('dashboard.html', titulo=titulo)

#------------------------- DASHBOARD -------------------------
#------------------------- CRUD Alumnos -------------------------

@app.route("/dashboard/alumnos")
def alumnos_dashboard():
    titulo = "Alumnos"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM alumnos WHERE activo=true ORDER BY id_alumno DESC;')
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
        creado = datetime.now()
        editado = datetime.now()
        situacion = True
        imagen=request.files['Foto']

        if imagen and allowed_file(imagen.filename):
            # Verificar si el archivo con el mismo nombre ya existe
            # Creamos un nombre dinamico para la foto de perfil con el nombre del alumno y una cadena aleatoria
            cadena_aleatoria = my_random_string(10)
            filename = paterno + "_" + materno + "_" + nombre + "_" + str(creado)[:10] + "_" + cadena_aleatoria + "_" + secure_filename(imagen.filename)
            file_path = os.path.join(ruta_alumnos, filename)
            if os.path.exists(file_path):
                flash('Error: ¡Un archivo con el mismo nombre ya existe! Intente renombrar su archivo.')
                return redirect(url_for('alumnos_dashboard'))
            # Guardar el archivo y registrar en la base de datos
            imagen.save(file_path)

            conn = get_db_connection()
            cur = conn.cursor()
            sql="INSERT INTO alumnos (nombre, apellido_paterno, apellido_materno, activo, creado, editado, imagen, situacion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            valores=(nombre, paterno, materno, activo, creado, editado,filename,situacion)
            cur.execute(sql,valores)
            conn.commit()
            cur.close()
            conn.close()

            flash('¡Alumno agregado exitosamente!')
            return redirect(url_for('alumnos_dashboard'))
        else:
            flash('Error: ¡Extensión de archivo invalida! Intente con una imagen valida PNG, JPG o JPEG')
            return redirect(url_for('alumnos_dashboard'))

    return redirect(url_for('alumnos_nuevo'))

@app.route('/dashboard/alumnos/<string:id>')
def alumnos_detalles(id):
    titulo = "Detalles del Alumno"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM alumnos WHERE id_alumno={0}'.format(id))
    alumno=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('alumnos_detalles.html', titulo=titulo, alumno=alumno[0])

@app.route('/dashboard/alumnos/editar/<string:id>')
def alumnos_editar(id):
    titulo = "Editar Alumno"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM alumnos WHERE id_alumno={0}'.format(id))
    alumno=cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('alumnos_editar.html', titulo=titulo, alumno=alumno[0])

@app.route('/dashboard/alumnos/actualizar/<string:id>', methods=['POST'])
def alumnos_actualizar(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form['materno']
        situacion = request.form['estado']
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="UPDATE alumnos SET nombre=%s, apellido_paterno=%s, apellido_materno=%s , situacion=%s, editado=%s WHERE id_alumno=%s"        
        valores=(nombre, paterno, materno, situacion, editado, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Alumno modificado exitosamente!')
    return redirect(url_for('alumnos_dashboard'))

@app.route('/dashboard/alumnos/actualizar/foto/<string:id>', methods=['POST'])
def alumnos_actualizar_foto(id):
    if request.method == 'POST':
        imagen=request.files['Foto']
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form['materno']
        foto_anterior = request.form['anterior']
        foto_anterior = os.path.join(ruta_alumnos,foto_anterior)
        editado = datetime.now()

        if imagen and allowed_file(imagen.filename):
            # Verificar si el archivo con el mismo nombre ya existe
            # Creamos un nombre dinamico para la foto de perfil con el nombre del alumno y una cadena aleatoria
            cadena_aleatoria = my_random_string(10)
            filename = paterno + "_" + materno + "_" + nombre + "_" + str(editado)[:10] + "_" + cadena_aleatoria + "_" + secure_filename(imagen.filename)
            file_path = os.path.join(ruta_alumnos, filename)
            if os.path.exists(file_path):
                flash('Error: ¡Un archivo con el mismo nombre ya existe! Intente renombrar su archivo.')
                return redirect(url_for('alumnos_dashboard'))
            # Guardar el archivo y registrar en la base de datos
            imagen.save(file_path)

            conn = get_db_connection()
            cur = conn.cursor()
            sql=" UPDATE alumnos SET editado=%s, imagen=%s WHERE id_alumno=%s"
            valores=(editado,filename,id)
            cur.execute(sql,valores)
            conn.commit()
            cur.close()
            conn.close()
            
            #Eliminar foto de perfil antigua
            if request.form['anterior'] != "":
                if os.path.exists(foto_anterior):
                    os.remove(foto_anterior)

            flash('¡Foto de perfil actualizada exitosamente!')
            return redirect(url_for('alumnos_editar', id=id))
        else:
            flash('Error: ¡Extensión de archivo invalida! Intente con una imagen valida PNG, JPG o JPEG')
            return redirect(url_for('alumnos_editar', id=id))

    return redirect(url_for('alumnos_dashboard'))

@app.route('/dashboard/alumnos/eliminar/<string:id>')
def alumnos_eliminar(id):
    activo = False
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM alumnos WHERE id_alumno={0}".format(id)
    sql="UPDATE alumnos SET activo=%s, editado=%s WHERE id_alumno=%s"
    valores=(activo,editado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Alumno  eliminado correctamente!')
    return redirect(url_for('alumnos_dashboard'))

@app.route('/dashboard/alumnos/eliminar/foto/<string:foto>/<string:id>')
def alumnos_eliminar_foto(foto,id):
    foto_anterior = os.path.join(ruta_alumnos,foto)
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM alumnos WHERE id_alumno={0}".format(id)
    sql="UPDATE alumnos SET imagen=%s, editado=%s WHERE id_alumno=%s"
    valores=("",editado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    #Eliminar foto de perfil antigua
    print(foto_anterior)
    if foto != "":
        if os.path.exists(foto_anterior):
            os.remove(foto_anterior)
            flash('¡Foto eliminada correctamente!')
            return redirect(url_for('alumnos_editar', id=id))
    else:
        flash('Error: ¡No se puede ejecutar esta acción!')
        return redirect(url_for('alumnos_editar', id=id))


#------------------------- CRUD Profesores -------------------------

#------------------------- CRUD Materias -------------------------

#------------------------- CRUD Grupos -------------------------
def pagina_no_encontrada(error):
    return render_template('404.html')

def acceso_no_autorizado(error):
    return redirect(url_for('login'))

if __name__ == '__main__':
    csrf.init_app(app)
    app.register_blueprint(custom_tags)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(debug=True, port=5000)

#Activar entorno    virtual .venv\Scripts\activate
#Correr aplicación  python app\app.py run
#                   flask --app app\app.py run


