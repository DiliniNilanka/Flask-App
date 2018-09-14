from flask import Flask, render_template, request, redirect, flash, url_for, session, logging, send_file
from flask_mysqldb import MySQL
import bcrypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, FileField
#from passlib.hash import sha256_crypt
from functools import wraps
from io import BytesIO
import datetime



app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='flaskdb'
app.config['MYSQL_CURSORCLASS']='DictCursor'
#init MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')

#class for the register users
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#router for register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data

        #Create cursor
        cur = mysql.connection.cursor()

        #Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()
        flash('You are now registered and can log in', 'success')
        redirect(url_for('login'))

    return render_template('register.html', form=form)
    
#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create cursor
        cur = mysql.connection.cursor()

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare Passwords
            if(password_candidate == password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            #Close connection
            cur.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
            
    return render_template('login.html')

#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get articles
    result= cur.execute("SELECT * FROM gallery")

    gallery = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', gallery=gallery)
    else:
        msg = "No Photos Found"
        return render_template('dashboard.html', msg=msg)
    #return render_template('dashboard.html')

    #Close connection
    cur.close()

#photo form class

class PhotoForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    photo = FileField('Photo')

#Add Photo
@app.route('/add_photo', methods=['GET','POST'])
@is_logged_in
def add_photo():
    form = PhotoForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        photo = form.photo.data

        #Create Cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("INSERT INTO gallery(title,photo,upload_by) VALUES(%s, %s, %s)",(title, photo, session['username']))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('photo added', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_photo.html', form=form)

#Edit Photo
@app.route('/edit_photo/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_photo(id):
    currentDT = datetime.datetime.now()
    #Create cursor
    cur = mysql.connection.cursor()

    #Get photo by id
    result = cur.execute("SELECT * FROM gallery WHERE id = %s", [id])

    gallery = cur.fetchone()

    #Get form
    form = PhotoForm(request.form)

    #populate photo form field
    form.title.data = gallery['title']
    form.photo.data = gallery['photo']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        photo = request.form['photo']

        #Create Cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("UPDATE gallery SET title=%s, photo=%s WHERE id = %s", (title, photo, id))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Photo Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_photo.html', form=form)

#Delete Photo
@app.route('/delete_photo/<string:id>', methods=['POST'])
@is_logged_in
def delete_photo(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Execute
    cur.execute("DELETE FROM gallery WHERE id = %s", [id])

    #Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Photo Deleted', 'success')
    return redirect(url_for('dashboard'))

#Download
#@app.route('/dashboard/download')
#def download():
    #Create cursor
    #cur = mysql.connection.cursor()
    #result = cur.execute("SELECT * FROM gallery")
    
    #gallery = cur.fetchall()
    #print(gallery.photo)
    #return send_file(BytesIO(gallery.photo), attachment_filename='flask.jpg', as_attachment=True)


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
