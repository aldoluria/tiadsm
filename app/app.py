from flask import Flask, render_template, url_for, redirect

app = Flask(__name__)

@app.route("/")
def index():
    titulo = "Clase Chidita del dia de HOY!!!!!!!!!"
    return render_template('index.html', titulo=titulo)

@app.route("/about-us")
def about_us():
    return render_template('about_us.html')

@app.route("/dashboard")
def dashboard():
    titulo = "Panel de Administración"
    return render_template('dashboard.html', titulo=titulo)

@app.route("/dashboard/users")
def users():
    titulo = "Usuarios"
    return render_template('users.html', titulo=titulo)

def pagina_no_encontrada(error):
    return render_template('404.html')

def acceso_no_autorizado(error):
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(debug=True, port=5000)

#Activar entorno    virtual .venv\Scripts\activate
#Correr aplicación  python app\app.py run
#                   flask --app app\app.py run


