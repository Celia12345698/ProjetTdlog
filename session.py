import sqlite3
from flask import Flask
from flask import render_template, request, redirect, url_for, g, flash
from flask import session
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import time
from flask_mail import Message, Mail
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import Form
from wtforms import StringField, TextField, TextAreaField, SubmitField, PasswordField, SelectField, FileField
from wtforms.validators import InputRequired, ValidationError, Email, DataRequired, Length, EqualTo
import os
import secrets
from PIL import Image
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_socketio import SocketIO, send, join_room, leave_room, emit

number_q = 2

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.secret_key = "hello"
app.permanent_session_lifetime = timedelta(minutes=5)

db=SQLAlchemy(app)
socketio=SocketIO(app)

class users(db.Model):
  _id = db.Column("id",db.Integer,primary_key=True)
  firstname = db.Column(db.String(100))
  lastname = db.Column(db.String(100))
  email = db.Column(db.String(120), unique=True)
  #list_genders=[]
  gender=db.Column(db.Integer) #=1 si man et 2 si woman
  man=db.Column(db.Integer)
  woman=db.Column(db.Integer)
  region=db.Column(db.Integer)
  same_region=db.Column(db.Integer)
  pwdhash = db.Column(db.String(54))
  image_file = db.Column(db.String(20), nullable=False, default='..\profile_pics\default.jpg')
  description = db.Column(db.String(200),default="")
  recherche=db.Column(db.String(200),default="")



  def __init__(self, firstname, lastname, email, password, gender, region):
    self.firstname = firstname.title()
    self.lastname = lastname.title()
    self.email = email.lower()
    self.set_password(password)
    self.gender=gender.lower()
    self.region=region.lower()
    self.image_file = "default.jpg"

  #Salted Hash Password
  def set_password(self, password):
    self.pwdhash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.pwdhash, password)

class Question:
    def __init__(self, title):
        self.title = title
    def register(self, model):
        setattr(model, self.title, db.Column(db.Integer))

def question_name(n):
    questions_names=[]
    for i in range(n):
        questions_names.append('q'+str(i+1))
    return questions_names

names=question_name(number_q)
questions = [Question(names[i]) for i in range(number_q) ]

for question in questions:
    question.register(users)

Regions=[(1,'Auvergne-Rhônes-Alpes'),(2,'Bourgogne-Franche-Comté'),(3,'Bretagne'),(4,'Centre-Val de Loire'),(5,'Corse'),(6,'Grand Est'),(7,'Hauts-de-France'),(8,'Île-de-France'),(9,'Normandie'),(10,'Nouvelle-Acquitaine'),(11,'Occitanie'),(12,'Pays de la Loire'),(13,"Provence-Alpes-Côte-d'Azur"),(14,'Guadeloupe'),(15,'Martinique'),(16,'Guyane'),(17,'La Réunion'),(18,'Mayotte')]

Genders=[(1,'Homme'), (2,'Femme')]

Age=[(1,'18-25'),(2,'26-30'),(3,'31-35'),(4,'36-40'),(5,'41 et +')]


# créer un compte
class SignupForm(Form):
  firstname = TextField("Prénom",  validators=[InputRequired("Please Enter First Name.")])
  lastname = TextField("Nom", validators=[InputRequired("Please Enter Last Name.")])
  email = TextField("Email",  [InputRequired("Please enter your email address."), Email("This field requires a valid email address")])
  password = PasswordField('Mot de passe', validators=[InputRequired("Please Enter a Password.")])
  region = SelectField(u'Region', choices = Regions, validators = [InputRequired("Please Select a Region.")])
  gender = SelectField(u'Sexe', choices = Genders, validators = [InputRequired("Please Select a Gender.")])
  age = SelectField(u"Tranche d'âge", choices = Age, validators = [InputRequired("Please Select Tranche d'âge'.")])
  submit = SubmitField("Create account")

  def __init__(self, *args, **kwargs):
    Form.__init__(self, *args, **kwargs)

  def validate(self):
    if not Form.validate(self):
      return False

    user = users.query.filter_by(email = self.email.data.lower()).first()
    if user:
      self.email.errors.append("That email is already taken")
      return False
    else:
      return True



# se connecter
class SigninForm(Form):
  email = TextField("Email",  [InputRequired("Please enter your email address."), Email("This field requires a valid email address")])
  password = PasswordField('Password', validators=[InputRequired("Please Enter a Password.")])
  submit = SubmitField("Sign In")

  def __init__(self, *args, **kwargs):
    Form.__init__(self, *args, **kwargs)

  def validate(self):
    if not Form.validate(self):
      return False

    user = users.query.filter_by(email = self.email.data.lower()).first()
    if user and user.check_password(self.password.data):
      return True
    else:
      self.email.errors.append("Invalid e-mail or password")
      return False

class UpdateAccountForm(FlaskForm):
    firstname = StringField('firstname',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    #mettre les autres trucs
    picture = FileField('Photo de profil', validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField('Update')
    description = TextAreaField('Description')
    recherche = TextAreaField('Recherche')


#Links to the Home Page
@app.route('/')
def home():
  return render_template('home.html')


#Links to the qui Page: explique le principe du site
@app.route('/qui')
def qui():
  return render_template('qui.html')



#Links to Signup Form: pour créer un compte, ajouter ici l'ensemble des questions
@app.route('/signup', methods=['GET', 'POST'])
def signup():
  form = SignupForm()

  if 'email' in session:
    user=users.query.filter_by(email = session['email']).first()
    return redirect(url_for('profile'))

  if request.method == 'POST':
    if form.validate() == False:
      return render_template('signup.html', form=form)
    else:
      newuser = users(form.firstname.data, form.lastname.data, form.email.data, form.password.data, form.gender.data, form.region.data)
      db.session.add(newuser)
      db.session.commit()
      session['email'] = newuser.email
      user=users.query.filter_by(email = session['email']).first()
      session['firstname']=user.firstname
      session['gender']=user.gender
      session['region']=user.region
      return redirect(url_for('question'))

  elif request.method == 'GET':
    return render_template('signup.html', form=form)

@app.route('/question', methods=['GET', 'POST'])
def question():
  q1=0
  q2=0
  if 'email' in session:
    mail = session['email']
    user=users.query.filter_by(email = session['email']).first()
    session['firstname']=user.firstname
    if request.method=="POST":
      #requête q1
      q1=request.form["q1"]
      user.q1=q1
      #requête q2
      q2=request.form["q2"]
      user.q2=q2
      db.session.commit()
      #age
      if request.form.get("homme"):
        user.man=1
        db.session.commit()
      else:
        user.man=0
        db.session.commit()
      if request.form.get("femme"):
        user.woman=1
        db.session.commit()
      else:
        user.woman=0
        db.session.commit()
      #region
      if request.form.get("oui"):
        user.same_region=1
        db.session.commit()
      else:
        user.same_region=0
        db.session.commit()
      return redirect(url_for('profile'))
    elif request.method == 'GET':
      return render_template('question.html')

  else:
    return redirect(url_for('signup'))

def filtre_gender(id):
  L=[]
  user=users.query.filter_by(_id=id).first()
  others=users.query.all()
  if user.man==1:
    for person in others:
      if person.gender==1 and user.gender==1 and person.man==1:
        L.append(person._id)
      if person.gender==1 and user.gender==2 and person.woman==1:
        L.append(person._id)
  if user.woman==1:
    for person in others:
      if person.gender==2 and user.gender==1 and person.man==1:
        L.append(person._id)
      if person.gender==2 and user.gender==2 and person.woman==1:
        L.append(person._id)
  return L

def filtre_region(id):
  L=[]
  user=users.query.filter_by(_id=id).first()
  others=users.query.all()
  if user.same_region==1:
    for person in others:
      if person.region==user.region:
        L.append(person._id)
  if user.same_region==0:
    for person in others:
      if person.same_region==0 or person.region==user.region:
        L.append(person._id)
  return L

@app.route('/compatibilite')
def compa():
  form = UpdateAccountForm()
  if 'email' not in session:
    return redirect(url_for('signin'))
  user = users.query.filter_by(email = session['email']).first()
  image_file = url_for('static', filename='profile_pics/' + user.image_file)
  #if user is None:
  #  return redirect(url_for('signin'))
  L1=matching(user._id)
  values=users.query.all()
  L2=[]
  L3=filtre_matching(user._id)
  for i in range(len(L3)):
    value=users.query.filter_by(_id=L3[i][0]).first()
    L2.append([value,L3[i][1]])
  return render_template('compatibilite.html', values=values, L2=L2, image_file=image_file, form=form, user=user)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)  #on génère une combinaison aléatoire en hexa, ça sera le nom sous lequel sera enregistré l'image dans la bdd (différent pour chaque user)
    _, f_ext = os.path.splitext(form_picture.filename)  # on récupère le nom et l'extension de l'image que l'user a renseignée
    picture_fn = random_hex + f_ext  # on renomme cette image avec le code généré plus haut et l'extension de l'image qu'a donnée l'user
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn) # on enregistre l'image dans notre dossier ...

    output_size = (125, 125)     # redimensionne
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route('/profil/<id>')
def profilext(id):
  user = users.query.filter_by(_id = id).first()
  image_file = url_for('static', filename='profile_pics/' + user.image_file)
  return render_template("profilext.html",user=user,image_file=image_file)

@app.route('/profil')
def profile():
  user = users.query.filter_by(email = session['email']).first()
  image_file = url_for('static', filename='profile_pics/' + user.image_file)
  return render_template("profil.html",user=user,image_file=image_file)

@app.route("/modifprofil", methods=['GET', 'POST'])
def modifprofil():
  user = users.query.filter_by(email = session['email']).first()
  form = UpdateAccountForm()
  if form.validate_on_submit():
      if form.picture.data:
          picture_file = save_picture(form.picture.data)
          user.image_file = picture_file
      user.description=form.description.data
      if form.recherche.data:
          user.recherche=form.recherche.data
      user.firstname = form.firstname.data
      user.email = form.email.data
      db.session.commit()
      flash('Tes informations ont été mises à jour!', 'success')
      return redirect(url_for('profile'))
  elif request.method == 'GET':
      form.firstname.data = user.firstname
      form.email.data = user.email
      form.description.data=user.description
      form.recherche.data=user.recherche
  image_file = url_for('static', filename='profile_pics/' + user.image_file)
  return render_template('modifprofil.html', title='modifprofil',
                          image_file=image_file, form=form)


#Signin
@app.route('/signin', methods=['GET', 'POST'])
def signin():
  form = SigninForm()

  if 'email' in session:
    user = users.query.filter_by(email=session['email']).first()
    return redirect(url_for('profile'))

  if request.method == 'POST':
    if form.validate() == False:
      return render_template('signin.html', form=form)
    else:
      session['email'] = form.email.data
      user=users.query.filter_by(email = session['email']).first()
      session['firstname']=user.firstname
      session['id']=user._id
      L_reponses=select_questions(user._id)
      for elem in L_reponses:
        if elem==None:
          flash("tu n'as pas répondu à toutes les questions!")
          return redirect(url_for('question'))
      return redirect(url_for('profile'))

  elif request.method == 'GET':
    return render_template('signin.html', form=form)

#Signout
@app.route('/signout')
def signout():

  if 'email' not in session:
    return redirect(url_for('signin'))

  session.pop('email', None)
  return redirect(url_for('home'))



def all_quest():
  names = question_name(number_q)
  all_questions = ""
  for i in range(len(names)):
    if i == len(names) - 1:
      all_questions += str(names[i])
    else:
      all_questions += (str(names[i]) + ", ")
  return all_questions


def matching(id):
  users=sqlite3.connect("users.sqlite3")
  cur=users.cursor()
  utilisateurs=cur.execute("select {} from users".format(all_quest()))
  row=utilisateurs.fetchone()

  L_reponses_tout=[]
  L=[]
  while row is not None:
    L.append(row)
    row=utilisateurs.fetchone()

  nombre_u=cur.execute("select count(email) from users")
  row1=nombre_u.fetchone()
  #print(row1[0])
  for i in range (0,row1[0]):
    L_reponses_tout.append(L[i][0])
    L_reponses_tout.append(L[i][1])
  L_reponses=L_reponses_tout[number_q*(id-1):number_q*id]
  #print(L_reponses)
  L_arrange=[]
  L_ecart=[]
  L_pourc=[]

  for i in range(0,number_q):
      for j in range(row1[0]):
          L_arrange.append(L_reponses_tout[i+number_q*j])

  for i in range(0,number_q):
      for j in range(row1[0]):
          L_ecart.append(((4-np.abs(L_arrange[j+i*row1[0]]-L_reponses[i]))))

  for i in range(row1[0]):
      somme=0
      for j in range(0,number_q):
          somme+=L_ecart[i+row1[0]*j]
      L_pourc.append(100*somme/(4*number_q))

  users.close()

  return L_pourc


lambda colonnes: colonnes[1]


def filtre_matching(id):
  L_pourc=matching(id)
  L_gender=filtre_gender(id)
  L_region=filtre_region(id)
  values=users.query.all()
  L_pourc_new=[]
  L_ind=[]
  if len(values)!=len(L_region):
    for id1 in L_region:
      for id2 in L_gender:
        if id1==id2:
          L_ind.append(id1)
  else:
    L_ind=L_gender

  for id1 in L_ind:
    L_pourc_new.append([id1,L_pourc[id1-1]])

  L_pourc_new=sorted(L_pourc_new, key=lambda colonnes: colonnes[1], reverse=True)

  for elem in L_pourc_new:
    if elem[1]<=50:
      L_pourc_new.remove(elem)

  for elem in L_pourc_new:
    if elem[0]==id:
      L_pourc_new.remove(elem)

  return L_pourc_new

def select_questions(id):
  users=sqlite3.connect("users.sqlite3")
  cur=users.cursor()
  utilisateurs=cur.execute("select {} from users".format(all_quest()))
  row=utilisateurs.fetchone()

  L_reponses_tout=[]
  L=[]
  while row is not None:
    L.append(row)
    row=utilisateurs.fetchone()

  nombre_u=cur.execute("select count(email) from users")
  row1=nombre_u.fetchone()
  #print(row1[0])
  for i in range (0,row1[0]):
    L_reponses_tout.append(L[i][0])
    L_reponses_tout.append(L[i][1])


  L_reponses=L_reponses_tout[number_q*(id-1):number_q*id]
  return L_reponses


def fonction(id,L):
  for elem in L:
    if elem[0]==id:
      L.remove(elem)
  return L

def room():
    Rooms=[]
    all=users.query.all()
    for user1 in all:
        for user2 in all:
            if user1._id < user2._id:
                Rooms.append((user1._id,user2._id))

ROOMS=["Salut","Saaa"]


@app.route("/chat", methods=['GET', 'POST'])
def chat():
    if 'email' not in session:
        flash('Please login', 'danger')
        return redirect(url_for('login'))
    user = users.query.filter_by(email=session['email']).first()
    return render_template("chat.html", firstname=user.firstname, rooms=ROOMS)


@socketio.on('incoming-msg')
def on_message(data):
    """Broadcast messages"""

    msg = data["msg"]
    username = data["username"]
    room = data["room"]
    # Set timestamp
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    user = users.query.filter_by(email=session['email']).first()
    send({"username": username, "msg": msg, "time_stamp": time_stamp}, room=user._id)



@socketio.on('join')
def on_join(data):
    """User joins a room"""

    username = data["username"]
    room = data["room"]
    join_room(room)

    # Broadcast that new user has joined
    send({"msg": username + " has joined the " + room + " room."}, room=room)


@socketio.on('leave')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room = data['room']
    leave_room(room)
    send({"msg": username + " has left the room"}, room=room)



if __name__=="__main__":
    db.create_all()
    socketio.run(app, debug=True)



