import os
import uuid
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, url_for, redirect, request, flash, Blueprint, jsonify
from flask_wtf.csrf import CSRFProtect

from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from Models.ModelUser import ModuleUser
from Models.entities.user import User

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

""" 
Conexión a Ubuntu
"""
def get_db_connection():
    try:
        conn = psycopg2.connect(host="localhost",
                                dbname="escuela",
                                user="postgres",
                                password="admin")
        return conn
    except psycopg2.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None
""" 
Conexión a Windows

def get_db_connection():
    try:
        conn = psycopg2.connect(host="localhost",
                                dbname="escuela",
                                user=os.environ['DB_USERNAME'],
                                password=os.environ['DB_PASSWORD'])
        return conn
    except psycopg2.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None
"""    

Login_manager_app=LoginManager(app)

@Login_manager_app.user_loader
def load_user(idusuarios):
    return ModuleUser.get_by_id(get_db_connection(),idusuarios)

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

def allowed_username(username):
    # Define el patrón de la expresión regular para letras y números sin espacios ni caracteres especiales
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    # Comprueba si el nombre de usuario coincide con el patrón
    if pattern.match(username):
        return True
    else:
        return False
        
#------------------------- CUSTOM TAGS -------------------------

@custom_tags.app_template_global()
def listar_tipos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM tipos_usuarios WHERE activo=true ORDER BY nombre ASC;')
    tipos = cur.fetchall()
    cur.close()
    conn.close()
    return tipos

@custom_tags.app_template_global()
def listar_carreras():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM carreras WHERE activo=true ORDER BY nombre ASC;')
    carreras = cur.fetchall()
    cur.close()
    conn.close()
    return carreras

@custom_tags.app_template_global()
def listar_grupos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT G.id_grupo, G.grado, G.grupo, G.anio, C.nombre FROM grupos AS G INNER JOIN carreras AS C ON G.id_carrera = C.id_carrera  WHERE G.activo=true ORDER BY nombre ASC;')
    carreras = cur.fetchall()
    cur.close()
    conn.close()
    return carreras

app.secret_key='mysecretkey'

#------------------------- PUBLIC -------------------------

@app.route("/")
def index():
    titulo = "Clase chidita"
    return render_template('public/index.html', titulo=titulo)

@app.route("/about-us")
def about_us():
    return render_template('public/about_us.html')

#------------------------- Paginador -------------------------

def paginador(sql_count: str, sql_lim: str, search_query: str, in_page: int, per_pages: int) -> tuple[list[dict], int, int, int, int]:
# Obtener parámetros de paginación
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)

    # Validar los valores de entrada
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    offset = (page - 1) * per_page

    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Ejecutar consulta para contar el total de elementos que coinciden con la búsqueda
        cursor.execute(sql_count, (f"%{search_query}%",f"%{search_query}%"))
        total_items = cursor.fetchone()['count']

        # Ejecutar consulta para obtener elementos paginados que coinciden con la búsqueda
        cursor.execute(sql_lim, (f"%{search_query}%",f"%{search_query}%", per_page, offset))
        items = cursor.fetchall()

    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        # Asegurar el cierre de la conexión
        cursor.close()
        conn.close()

    # Calcular el total de páginas
    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages

#------------------------- Paginador Muestra -------------------------

@app.route('/items')
def get_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 2, type=int)

    offset = (page - 1) * per_page

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT COUNT(*) FROM alumnos')
    total_items = cursor.fetchone()['count']

    cursor.execute('SELECT * FROM alumnos LIMIT %s OFFSET %s', (per_page, offset))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    total_pages = (total_items + per_page - 1) // per_page

    return render_template(
        'items.html',
        items=items,
        page=page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages
    )

#------------------------- Tiempo -------------------------
@app.template_filter('formatear_tiempo')
def formatear_tiempo(fecha_pasada):
    ahora = datetime.now()
    diferencia = relativedelta(ahora, fecha_pasada)

    if diferencia.years > 0:
        return f"Hace {diferencia.years} años"
    elif diferencia.years == 1:
        return f"Hace {diferencia.years} año"
    elif diferencia.months > 0:
        return f"Hace {diferencia.months} meses"
    elif diferencia.months == 1:
        return f"Hace {diferencia.months} mes"
    elif diferencia.days > 0:
        return f"Hace {diferencia.days} días"
    elif diferencia.days == 1:
        return f"Hace {diferencia.days} día"
    elif diferencia.hours > 0:
        return f"Hace {diferencia.hours} horas"
    elif diferencia.hours == 1:
        return f"Hace {diferencia.hours} hora"
    elif diferencia.minutes > 0:
        return f"Hace {diferencia.minutes} minutos"
    elif diferencia.minutes == 1:
        return f"Hace {diferencia.minutes} minuto"
    else:
        return "Hace unos segundos"

#------------------------- DASHBOARD -------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    titulo = "Panel de Administración"
    return render_template('admin/dashboard.html', titulo=titulo)

#------------------------- CRUD Tipo Usuarios -------------------------

@app.route("/tipo")
@login_required
def tipo_usuarios_crear():
    return render_template("tipo.html") 

@app.route('/tipo/crear', methods=('GET', 'POST'))
@login_required
def tipo_crear():
    if request.method == 'POST':
        nombre=request.form['nombre']
        activo = True
        creado = datetime.now()
        editado = datetime.now()
        print(nombre)

        conn = get_db_connection()
        cur = conn.cursor()
        sql="INSERT INTO tipos_usuarios (nombre, activo, creado, editado) VALUES (%s, %s, %s, %s)"
        valores=(nombre, activo, creado, editado)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        print("-----------------------------------------------------------------ya we------------------------------")

        flash('¡Usuario agregado exitosamente!')
        return redirect(url_for('index'))
    return redirect(url_for('index'))

#------------------------- CRUD Usuarios -------------------------

@app.route("/dashboard/usuarios")
@login_required
def usuarios_dashboard():
    titulo = "Usuarios"
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM usuarios AS U INNER JOIN tipos_usuarios AS T ON U.id_tipo = T.id_tipo WHERE U.activo=true AND (U.username ILIKE %s OR T.nombre ILIKE %s);'
    sql_lim = 'SELECT U.id_usuario, U.username, T. id_tipo, T.nombre, U.creado FROM usuarios AS U INNER JOIN tipos_usuarios AS T ON U.id_tipo = T.id_tipo WHERE U.activo=true AND (U.username ILIKE %s OR T.nombre ILIKE %s) ORDER BY U.id_usuario DESC LIMIT %s OFFSET %s;'
    paginado = paginador(sql_count, sql_lim, search_query, 1, 10)
    return render_template('admin/usuarios/usuarios.html', titulo=titulo,
                            usuarios=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4],
                            search_query=search_query)

@app.route("/dashboard/usuarios/nuevo")
@login_required
def usuarios_nuevo():
    titulo = "Usuario nuevo"
    return render_template('admin/usuarios/crear.html', titulo=titulo)

@app.route('/dashboard/usuarios/crear', methods=('GET', 'POST'))
@login_required
def usuarios_crear():
    if request.method == 'POST':
        username=request.form['username']
        if allowed_username(username):
            password=request.form['password']
            Pass=generate_password_hash(password)
            tipo_usuario=int(request.form['tipo_usuario'])
            activo = True
            creado = datetime.now()
            editado = datetime.now()
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            sql_validar="SELECT COUNT(*) FROM usuarios WHERE username = '{}'".format(username)
            cur.execute(sql_validar)
            existe = cur.fetchone()['count']
            if existe:
                cur.close()
                conn.close()
                flash('Error: El nombre de usuario seleccionado ya existe. Intente con otro.')
                return redirect(url_for('usuarios_nuevo'))
            else:
                sql="INSERT INTO usuarios (username, password, id_tipo, activo, creado, editado) VALUES (%s, %s, %s, %s, %s, %s)"
                valores=(username, Pass, tipo_usuario, activo, creado, editado)
                cur.execute(sql,valores)
                conn.commit()
                cur.close()
                conn.close()
                flash('¡Usuario agregado exitosamente!')
                return redirect(url_for('usuarios_dashboard'))
        else:
            flash('Error: El nombre de usuario no cumple con las características. Intente con otro.')
            return redirect(url_for('usuarios_nuevo'))
    return redirect(url_for('usuarios_nuevo'))

@app.route('/dashboard/usuarios/<string:id>')
@login_required
def usuarios_detalles(id):
    titulo = "Detalles del usuario"
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT U.id_usuario, U.username, T. id_tipo, T.nombre, U.creado, U.editado FROM usuarios AS U INNER JOIN tipos_usuarios AS T ON U.id_tipo = T.id_tipo WHERE U.activo=true AND U.id_usuario={0};'.format(id))
    usuario=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/usuarios/detalles.html', titulo=titulo, usuario=usuario)

@app.route('/dashboard/usuarios/editar/<string:id>')
@login_required
def usuarios_editar(id):
    titulo = "Editar usuario"
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT U.id_usuario, U.username, T. id_tipo, T.nombre, U.creado, U.editado FROM usuarios AS U INNER JOIN tipos_usuarios AS T ON U.id_tipo = T.id_tipo WHERE U.activo=true AND U.id_usuario={0};'.format(id))
    usuario=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/usuarios/editar.html', titulo=titulo, usuario=usuario)

@app.route('/dashboard/usuarios/actualizar/<string:id>', methods=['POST'])
@login_required
def usuarios_actualizar(id):
    if request.method == 'POST':
        username = request.form['username']
        if allowed_username(username):
            tipo_usuario=request.form['tipo_usuario']
            editado = datetime.now()
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            sql_validar="SELECT COUNT(*) FROM usuarios WHERE username = '{}'".format(username)
            cur.execute(sql_validar)
            existe = cur.fetchone()['count']
            if existe:
                cur.close()
                conn.close()
                flash('Error: El nombre de usuario seleccionado ya existe. Intente con otro.')
                return redirect(url_for('usuarios_editar',id=id))
            else:
                sql="UPDATE usuarios SET username=%s, id_tipo=%s, editado=%s WHERE id_usuario=%s"        
                valores=(username, tipo_usuario, editado, id)
                cur.execute(sql,valores)
                conn.commit()
                cur.close()
                conn.close()

                flash('¡Usuario modificado exitosamente!')
        else:
            flash('Error: El nombre de usuario no cumple con las características. Intente con otro.')
            return redirect(url_for('usuarios_editar',id=id))
    return redirect(url_for('usuarios_dashboard'))

@app.route('/dashboard/usuarios/eliminar/<string:id>')
@login_required
def usuarios_eliminar(id):
    activo = False
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM usuarios WHERE id_usuario={0}".format(id)
    sql="UPDATE usuarios SET activo=%s, editado=%s WHERE id_usuario=%s"
    valores=(activo,editado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Usuario eliminada correctamente!')
    return redirect(url_for('usuarios_dashboard'))

@app.route('/dashboard/usuarios/perfil')
@login_required
def perfil():
    return render_template('auth/perfil.html')

#------------------------- CRUD Datos/Perfil -------------------------

@app.route("/dashboard/alumnos")
@login_required
def alumnos_dashboard():
    titulo = "Alumnos"
    sql_count = 'SELECT COUNT(*) FROM alumnos WHERE activo=true;'
    sql_lim = 'SELECT A.*, G.grado, G.grupo, G.anio, C.id_carrera, C.nombre AS carrera FROM alumnos AS A INNER JOIN grupos AS G ON A.id_grupo = G.id_grupo INNER JOIN carreras AS C on G.id_carrera = C.id_carrera  WHERE A.activo=true ORDER BY A.id_alumno DESC  LIMIT %s OFFSET %s;'
    paginado = paginador(sql_count,sql_lim,1,1)
    return render_template('admin/alumnos/alumnos.html', titulo=titulo,
                            alumnos=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4])

@app.route("/dashboard/alumnos/nuevo")
@login_required
def alumnos_nuevo():
    titulo = "Alumno nuevo"
    return render_template('admin/alumnos/crear.html', titulo=titulo)

@app.route('/dashboard/alumnos/crear', methods=('GET', 'POST'))
@login_required
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
        id_grupo = request.form['id_grupo']

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
            sql="INSERT INTO alumnos (nombre, apellido_paterno, apellido_materno, activo, creado, editado, imagen, situacion, id_grupo) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)"
            valores=(nombre, paterno, materno, activo, creado, editado,filename,situacion,id_grupo)
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
@login_required
def alumnos_detalles(id):
    titulo = "Detalles del Alumno"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT A.*, G.grado, G.grupo, G.anio, C.id_carrera, C.nombre FROM alumnos AS A INNER JOIN grupos AS G ON A.id_grupo = G.id_grupo INNER JOIN carreras AS C on G.id_carrera = C.id_carrera WHERE id_alumno={0}'.format(id))
    alumno=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/alumnos/detalles.html', titulo=titulo, alumno=alumno)

@app.route('/dashboard/alumnos/editar/<string:id>')
@login_required
def alumnos_editar(id):
    if current_user.tipo == "Administrador":
        titulo = "Editar Alumno"
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT A.*, G.grado, G.grupo, G.anio, C.id_carrera, C.nombre FROM alumnos AS A INNER JOIN grupos AS G ON A.id_grupo = G.id_grupo INNER JOIN carreras AS C on G.id_carrera = C.id_carrera WHERE id_alumno={0}'.format(id))
        alumno=cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return render_template('admin/alumnos/editar.html', titulo=titulo, alumno=alumno)
    else:
        return redirect(url_for('index'))

@app.route('/dashboard/alumnos/actualizar/<string:id>', methods=['POST'])
@login_required
def alumnos_actualizar(id):
    if request.method == 'POST' and current_user.tipo == "Administrador":
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form['materno']
        situacion = request.form['estado']
        editado = datetime.now()
        id_grupo = request.form['id_grupo']

        conn = get_db_connection()
        cur = conn.cursor()
        sql="UPDATE alumnos SET nombre=%s, apellido_paterno=%s, apellido_materno=%s , situacion=%s, editado=%s, id_grupo=%s WHERE id_alumno=%s"        
        valores=(nombre, paterno, materno, situacion, editado, id_grupo, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Alumno modificado exitosamente!')
    return redirect(url_for('alumnos_dashboard'))

@app.route('/dashboard/alumnos/actualizar/foto/<string:id>', methods=['POST'])
@login_required
def alumnos_actualizar_foto(id):
    if request.method == 'POST' and current_user.tipo == "Administrador":
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
@login_required
def alumnos_eliminar(id):
    if current_user.tipo == "Administrador":
        activo = False
        situacion = False
        editado = datetime.now()
        conn = get_db_connection()
        cur = conn.cursor()
        #sql="DELETE FROM alumnos WHERE id_alumno={0}".format(id)
        sql="UPDATE alumnos SET activo=%s, editado=%s, situacion=%s WHERE id_alumno=%s"
        valores=(activo,editado,situacion,id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash('¡Alumno  eliminado correctamente!')
        return redirect(url_for('alumnos_dashboard'))
    else:
        return redirect(url_for('alumnos_dashboard'))

@app.route('/dashboard/alumnos/eliminar/foto/<string:foto>/<string:id>')
@login_required
def alumnos_eliminar_foto(foto,id):
    if current_user.tipo == "Administrador":
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
    else:
        return redirect(url_for('alumnos_dashboard'))

#------------------------- CRUD Materias -------------------------

@app.route("/dashboard/materias")
@login_required
def materias_dashboard():
    titulo = "Materias"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT M.*, P.nombre, P.apellido_paterno, P.apellido_materno FROM materias AS M INNER JOIN profesores AS P ON M.id_profesor = P.id_profesor  WHERE M.activo=true and P.activo=true ORDER BY id_materia DESC;')
    materias = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/materias/materias.html', titulo=titulo,materias=materias)

@app.route("/dashboard/materias/nuevo")
@login_required
def materias_nuevo():
    titulo = "Materia nueva"
    return render_template('admin/materias/crear.html', titulo=titulo)

@app.route('/dashboard/materias/crear', methods=('GET', 'POST'))
@login_required
def materias_crear():
    if request.method == 'POST':
        nombre = request.form['nombre']
        profesor = request.form['id_profesor']
        activo = True
        creado = datetime.now()
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="INSERT INTO materias (nombre, id_profesor, activo, creado, editado) VALUES (%s, %s, %s, %s, %s)"
        valores=(nombre, profesor, activo, creado, editado)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Materia agregada exitosamente!')
        return redirect(url_for('materias_dashboard'))
    return redirect(url_for('materias_nuevo'))

@app.route('/dashboard/materias/<string:id>')
@login_required
def materias_detalles(id):
    titulo = "Detalles de la Materia"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT M.*, P.nombre, P.apellido_paterno, P.apellido_paterno FROM materias AS M INNER JOIN profesores AS P ON M.id_profesor = P.id_profesor  WHERE M.activo=true and P.activo=true and id_materia={0};'.format(id))
    materia=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/materias/detalles.html', titulo=titulo, materia=materia)

@app.route('/dashboard/materias/editar/<string:id>')
@login_required
def materias_editar(id):
    titulo = "Editar Materia"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT M.*, P.nombre, P.apellido_paterno, P.apellido_paterno FROM materias AS M INNER JOIN profesores AS P ON M.id_profesor = P.id_profesor  WHERE M.activo=true and P.activo=true and id_materia={0};'.format(id))
    materia=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/materias/editar.html', titulo=titulo, materia=materia)

@app.route('/dashboard/materias/actualizar/<string:id>', methods=['POST'])
@login_required
def materias_actualizar(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        profesor = request.form['id_profesor']
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="UPDATE materias SET nombre=%s, id_profesor=%s, editado=%s WHERE id_materia=%s"        
        valores=(nombre, profesor, editado, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Materia modificada exitosamente!')
    return redirect(url_for('materias_dashboard'))

@app.route('/dashboard/materias/eliminar/<string:id>')
@login_required
def materias_eliminar(id):
    activo = False
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM materias WHERE id_materia={0}".format(id)
    sql="UPDATE materias SET activo=%s, editado=%s WHERE id_materia=%s"
    valores=(activo,editado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Materia eliminada correctamente!')
    return redirect(url_for('materias_dashboard'))

#------------------------- CRUD Carreras -------------------------

@app.route("/dashboard/carreras")
@login_required
def carreras_dashboard():
    titulo = "Carreras"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM carreras WHERE activo=true ORDER BY id_carrera DESC;')
    carreras = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/carreras/carreras.html', titulo=titulo,carreras=carreras)

@app.route("/dashboard/carreras/nuevo")
@login_required
def carreras_nuevo():
    titulo = "Carrera nueva"
    return render_template('admin/carreras/crear.html', titulo=titulo)

@app.route('/dashboard/carreras/crear', methods=('GET', 'POST'))
@login_required
def carreras_crear():
    if request.method == 'POST':
        nombre = request.form['nombre']
        activo = True
        creado = datetime.now()
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="INSERT INTO carreras (nombre, activo, creado, editado) VALUES (%s, %s, %s, %s)"
        valores=(nombre, activo, creado, editado)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Carrera agregada exitosamente!')
        return redirect(url_for('carreras_dashboard'))
    return redirect(url_for('carreras_nuevo'))

@app.route('/dashboard/carreras/<string:id>')
@login_required
def carreras_detalles(id):
    titulo = "Detalles de la Carrera"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM carreras WHERE id_carrera={0};'.format(id))
    carrera=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/carreras/detalles.html', titulo=titulo, carrera=carrera)

@app.route('/dashboard/carreras/editar/<string:id>')
@login_required
def carreras_editar(id):
    titulo = "Editar Carrera"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM carreras WHERE id_carrera={0};'.format(id))
    carrera=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/carreras/editar.html', titulo=titulo, carrera=carrera)

@app.route('/dashboard/carreras/actualizar/<string:id>', methods=['POST'])
@login_required
def carreras_actualizar(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="UPDATE carreras SET nombre=%s, editado=%s WHERE id_carrera=%s"        
        valores=(nombre, editado, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Carrera modificada exitosamente!')
    return redirect(url_for('carreras_dashboard'))

@app.route('/dashboard/carreras/eliminar/<string:id>')
@login_required
def carreras_eliminar(id):
    activo = False
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM carreras WHERE id_carrera={0}".format(id)
    sql="UPDATE carreras SET activo=%s, editado=%s WHERE id_carrera=%s"
    valores=(activo,editado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Carrera eliminada correctamente!')
    return redirect(url_for('carreras_dashboard'))

#------------------------- CRUD Grupos -------------------------

@app.route("/dashboard/grupos")
@login_required
def grupos_dashboard():
    titulo = "Grupos"
    conn = get_db_connection()
    cur = conn.cursor()
    sql= 'SELECT G.*, C.nombre, P.nombre, P.apellido_paterno, P.apellido_materno FROM grupos AS G INNER JOIN profesores AS P ON G.id_profesor = P.id_profesor INNER JOIN carreras AS C ON G.id_carrera = C.id_carrera WHERE G.activo=true and P.activo=true ORDER BY id_grupo DESC;'
    cur.execute(sql)
    grupos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/grupos/grupos.html', titulo=titulo,grupos=grupos)

@app.route("/dashboard/grupos/nuevo")
@login_required
def grupos_nuevo():
    titulo = "Grupo nuevo"
    return render_template('admin/grupos/crear.html', titulo=titulo)

@app.route('/dashboard/grupos/crear', methods=('GET', 'POST'))
@login_required
def grupos_crear():
    if request.method == 'POST':
        grado = request.form['grado']
        grupo = request.form['grupo']
        anio = request.form['anio']
        profesor = request.form['id_profesor']
        carrera = request.form['id_carrera']
        activo = True
        creado = datetime.now()
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="INSERT INTO grupos (grado, grupo, anio, id_profesor, id_carrera, activo, creado, editado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        valores=(grado, grupo, anio, profesor, carrera, activo, creado, editado)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Grupo agregado exitosamente!')
        return redirect(url_for('grupos_dashboard'))
    return redirect(url_for('grupos_nuevo'))

@app.route('/dashboard/grupos/<string:id>')
@login_required
def grupos_detalles(id):
    titulo = "Detalles del Grupo"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT G.*, C.nombre, P.nombre, P.apellido_paterno, P.apellido_materno FROM grupos AS G INNER JOIN profesores AS P ON G.id_profesor = P.id_profesor INNER JOIN carreras AS C ON G.id_carrera = C.id_carrera WHERE G.activo=true and P.activo=true and id_grupo={0} ORDER BY id_grupo DESC;'.format(id))
    grupo=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/grupos/detalles.html', titulo=titulo, grupo=grupo)

@app.route('/dashboard/grupos/editar/<string:id>')
@login_required
def grupos_editar(id):
    titulo = "Editar Grupo"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT G.*, C.nombre, P.nombre, P.apellido_paterno, P.apellido_materno FROM grupos AS G INNER JOIN profesores AS P ON G.id_profesor = P.id_profesor INNER JOIN carreras AS C ON G.id_carrera = C.id_carrera WHERE G.activo=true and P.activo=true and id_grupo={0} ORDER BY id_grupo DESC;'.format(id))
    grupo=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/grupos/editar.html', titulo=titulo, grupo=grupo)

@app.route('/dashboard/grupos/actualizar/<string:id>', methods=['POST'])
@login_required
def grupos_actualizar(id):
    if request.method == 'POST':
        grado = request.form['grado']
        grupo = request.form['grupo']
        anio = request.form['anio']
        profesor = request.form['id_profesor']
        carrera = request.form['id_carrera']
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="UPDATE grupos SET grado=%s, grupo=%s, anio=%s, id_profesor=%s, id_carrera=%s, editado=%s WHERE id_grupo=%s"        
        valores=(grado, grupo, anio, profesor, carrera, editado, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Grupo modificada exitosamente!')
    return redirect(url_for('grupos_dashboard'))

@app.route('/dashboard/grupos/eliminar/<string:id>')
@login_required
def grupos_eliminar(id):
    activo = False
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM grupos WHERE id_grupo={0}".format(id)
    sql="UPDATE grupos SET activo=%s, editado=%s WHERE id_grupo=%s"
    valores=(activo,editado,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Grupo eliminada correctamente!')
    return redirect(url_for('grupos_dashboard'))

#------------------------- CRUD Salones -------------------------

#------------------------- CRUD Calificaciones -------------------------
"""

@app.route("/dashboard/profesores")
@login_required
def profesores_dashboard():
    titulo = "Profesores"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM profesores WHERE activo=true ORDER BY id_profesor DESC;')
    profesores = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/profesores/profesores.html', titulo=titulo,profesores=profesores)

@app.route("/dashboard/profesores/nuevo")
@login_required
def profesores_nuevo():
    titulo = "Profesor nuevo"
    return render_template('admin/profesores/crear.html', titulo=titulo)

@app.route('/dashboard/profesores/crear', methods=('GET', 'POST'))
@login_required
def profesores_crear():
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
            # Creamos un nombre dinamico para la foto de perfil con el nombre del profesor y una cadena aleatoria
            cadena_aleatoria = my_random_string(10)
            filename = paterno + "_" + materno + "_" + nombre + "_" + str(creado)[:10] + "_" + cadena_aleatoria + "_" + secure_filename(imagen.filename)
            file_path = os.path.join(ruta_profesores, filename)
            if os.path.exists(file_path):
                flash('Error: ¡Un archivo con el mismo nombre ya existe! Intente renombrar su archivo.')
                return redirect(url_for('profesores_dashboard'))
            # Guardar el archivo y registrar en la base de datos
            imagen.save(file_path)

            conn = get_db_connection()
            cur = conn.cursor()
            sql="INSERT INTO profesores (nombre, apellido_paterno, apellido_materno, activo, creado, editado, imagen, situacion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            valores=(nombre, paterno, materno, activo, creado, editado,filename,situacion)
            cur.execute(sql,valores)
            conn.commit()
            cur.close()
            conn.close()

            flash('¡Profesor agregado exitosamente!')
            return redirect(url_for('profesores_dashboard'))
        else:
            flash('Error: ¡Extensión de archivo invalida! Intente con una imagen valida PNG, JPG o JPEG')
            return redirect(url_for('profesores_dashboard'))

    return redirect(url_for('profesores_nuevo'))

@app.route('/dashboard/profesores/<string:id>')
@login_required
def profesores_detalles(id):
    titulo = "Detalles del Profesor"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM profesores WHERE id_profesor={0}'.format(id))
    profesor=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/profesores/detalles.html', titulo=titulo, profesor=profesor)

@app.route('/dashboard/profesores/editar/<string:id>')
@login_required
def profesores_editar(id):
    titulo = "Editar Profesor"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM profesores WHERE id_profesor={0}'.format(id))
    profesor=cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('admin/profesores/editar.html', titulo=titulo, profesor=profesor)

@app.route('/dashboard/profesores/actualizar/<string:id>', methods=['POST'])
@login_required
def profesores_actualizar(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form['materno']
        situacion = request.form['estado']
        editado = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql="UPDATE profesores SET nombre=%s, apellido_paterno=%s, apellido_materno=%s , situacion=%s, editado=%s WHERE id_profesor=%s"        
        valores=(nombre, paterno, materno, situacion, editado, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Profesor modificado exitosamente!')
    return redirect(url_for('profesores_dashboard'))

@app.route('/dashboard/profesores/actualizar/foto/<string:id>', methods=['POST'])
@login_required
def profesores_actualizar_foto(id):
    if request.method == 'POST':
        imagen=request.files['Foto']
        nombre = request.form['nombre']
        paterno = request.form['paterno']
        materno = request.form['materno']
        foto_anterior = request.form['anterior']
        foto_anterior = os.path.join(ruta_profesores,foto_anterior)
        editado = datetime.now()

        if imagen and allowed_file(imagen.filename):
            # Verificar si el archivo con el mismo nombre ya existe
            # Creamos un nombre dinamico para la foto de perfil con el nombre del profesor y una cadena aleatoria
            cadena_aleatoria = my_random_string(10)
            filename = paterno + "_" + materno + "_" + nombre + "_" + str(editado)[:10] + "_" + cadena_aleatoria + "_" + secure_filename(imagen.filename)
            file_path = os.path.join(ruta_profesores, filename)
            if os.path.exists(file_path):
                flash('Error: ¡Un archivo con el mismo nombre ya existe! Intente renombrar su archivo.')
                return redirect(url_for('profesor_dashboard'))
            # Guardar el archivo y registrar en la base de datos
            imagen.save(file_path)

            conn = get_db_connection()
            cur = conn.cursor()
            sql=" UPDATE profesores SET editado=%s, imagen=%s WHERE id_profesor=%s"
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
            return redirect(url_for('profesores_editar', id=id))
        else:
            flash('Error: ¡Extensión de archivo invalida! Intente con una imagen valida PNG, JPG o JPEG')
            return redirect(url_for('profesores_editar', id=id))

    return redirect(url_for('profesores_dashboard'))

@app.route('/dashboard/profesores/eliminar/<string:id>')
@login_required
def profesores_eliminar(id):
    activo = False
    situacion = False
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM profesores WHERE id_profesor={0}".format(id)
    sql="UPDATE profesores SET activo=%s, editado=%s, situacion=%s WHERE id_profesor=%s"
    valores=(activo,editado,situacion,id)
    cur.execute(sql,valores)
    conn.commit()
    cur.close()
    conn.close()
    flash('¡Profesor  eliminado correctamente!')
    return redirect(url_for('profesores_dashboard'))

@app.route('/dashboard/profesores/eliminar/foto/<string:foto>/<string:id>')
@login_required
def profesores_eliminar_foto(foto,id):
    foto_anterior = os.path.join(ruta_profesores,foto)
    editado = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    #sql="DELETE FROM profesores WHERE id_profesor={0}".format(id)
    sql="UPDATE profesores SET imagen=%s, editado=%s WHERE id_profesor=%s"
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
            return redirect(url_for('profesores_editar', id=id))
    else:
        flash('Error: ¡No se puede ejecutar esta acción!')
        return redirect(url_for('profesores_editar', id=id))

        
"""

#------------------------- Apartado Login -------------------------

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/loguear', methods=('GET', 'POST'))
def loguear():
    if request.method == 'POST':
        Username=request.form['Username']
        Password=request.form['Password']
        user=User(0,Username,Password,None,None,None,None)
        loged_user=ModuleUser.login(get_db_connection(),user)

        if loged_user!= None:
            if loged_user.password:
                login_user(loged_user)
                return redirect(url_for('dashboard'))
            else:
                flash('Nombre de usuario y/o Contraseña incorrecta.')
                return redirect(url_for('login'))
        else:
            flash('Nombre de usuario y/o Contraseña incorrecta.')
            return redirect(url_for('login'))
    else:
        #flash('3 - Nombre de usuario y/o Contraseña incorrecta.')  #Valida si ingresan correctamente a la ruta
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#------------------------- Error Handlers -------------------------
def pagina_no_encontrada(error):
    return render_template('error/404.html')

def acceso_no_autorizado(error):
    return redirect(url_for('login'))

#------------------------- App Building -------------------------

""" 
Configuración de Ubuntu
"""

if __name__ == '__main__':
    csrf.init_app(app)
    app.register_blueprint(custom_tags)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(host='0.0.0.0', port=5000)

""" 
Configuración de Windows
"""
"""
if __name__ == '__main__':
    csrf.init_app(app)
    app.register_blueprint(custom_tags)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(debug=True, port=5000)
"""

#Activar entorno    virtual .venv\Scripts\activate
#Correr aplicación  python app\app.py run
#                   flask --app app\app.py run


