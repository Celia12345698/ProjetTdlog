from flask import Flask
import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import Form
from wtforms import StringField, TextField, TextAreaField, SubmitField, PasswordField, SelectField
from wtforms.validators import InputRequired,Email, DataRequired, Length
from flask_wtf.file import FileField, FileAllowed
from flask_socketio import SocketIO

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.secret_key = "ju_867!LM_4"
app.permanent_session_lifetime = datetime.timedelta(minutes=20)

db=SQLAlchemy(app)

socketio = SocketIO(app, manage_session=False)


Regions=[(1,'Auvergne-Rhônes-Alpes'),(2,'Bourgogne-Franche-Comté'),(3,'Bretagne'),(4,'Centre-Val de Loire'),(5,'Corse'),(6,'Grand Est'),(7,'Hauts-de-France'),(8,'Île-de-France'),(9,'Normandie'),(10,'Nouvelle-Acquitaine'),(11,'Occitanie'),(12,'Pays de la Loire'),(13,"Provence-Alpes-Côte-d'Azur"),(14,'Guadeloupe'),(15,'Martinique'),(16,'Guyane'),(17,'La Réunion'),(18,'Mayotte')]

Genders=[(1,'Homme'), (2,'Femme')]

Age=[(1,'18-25'),(2,'26-30'),(3,'31-35'),(4,'36-40'),(5,'41 et +')]


class users(db.Model):
  __tablename__='users'
  __bind_key__ = 'users'
  _id = db.Column("id",db.Integer,primary_key=True)
  firstname = db.Column(db.String(100))
  lastname = db.Column(db.String(100))
  email = db.Column(db.String(120), unique=True)
  gender=db.Column(db.Integer) #=1 if man and 2 if woman
  man=db.Column(db.Integer,default="0")
  woman=db.Column(db.Integer,default="0")
  region=db.Column(db.Integer)
  same_region=db.Column(db.Integer,default="0")
  all_answered=db.Column(db.Integer,default="0")
  pwdhash = db.Column(db.String(54))
  image_file = db.Column(db.String(20), nullable=False, default='..\profile_pics\default.jpg')
  description = db.Column(db.String(200),default="Non renseigné")
  recherche=db.Column(db.String(200),default="Non renseigné")
  messages_sent = db.relationship('Message',foreign_keys='Message.sender_id',backref='author', lazy='dynamic')
  messages_received = db.relationship('Message',foreign_keys='Message.recipient_id',backref='recipient', lazy='dynamic')


  def __init__(self, firstname, lastname, email, password, gender, region):
    self.firstname = firstname.title()
    self.lastname = lastname.title()
    self.email = email.lower()
    self.set_password(password)
    self.gender=gender.lower()
    self.region=region.lower()
    self.image_file = "default.jpg"

  def set_password(self, password):
    self.pwdhash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.pwdhash, password)

class Message(db.Model):
    __tablename__='Message'
    __bind_key__ = 'Message'
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    sender_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    body = db.Column(db.String(140))

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Question:
    def __init__(self, title):
        self.title = title
    def register(self, model):
        setattr(model, self.title, db.Column(db.Integer))


class MessageForm(Form):
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=0, max=140)])
    submit = SubmitField('Envoyer')

class SignupForm(Form):
  firstname = TextField("Prénom",  validators=[InputRequired("Merci d'entrer un prénom.")])
  lastname = TextField("Nom", validators=[InputRequired("Merci d'entrer un nom.")])
  email = TextField("Email",  [InputRequired("Merci d'entrer une adresse mail."), Email("L'adresse mail doit être valide.")])
  password = PasswordField('Mot de passe', validators=[InputRequired("Merci d'entrer un mot de passe.")])
  region = SelectField(u'Région', choices = Regions, validators = [InputRequired("Merci de renseigner votre région.")])
  gender = SelectField(u'Sexe', choices = Genders, validators = [InputRequired("Merci de sélectionner votre genre.")])
  age = SelectField(u"Tranche d'âge", choices = Age, validators = [InputRequired("Merci de sélectionner votre tranche d'âge'.")])
  submit = SubmitField("Créer le compte")

  def __init__(self, *args, **kwargs):
    Form.__init__(self, *args, **kwargs)

  def validate(self):
    if not Form.validate(self):
      return False

    user = users.query.filter_by(email = self.email.data.lower()).first()
    if user:
      self.email.errors.append("Cet email est déjà pris.")
      return False
    else:
      return True



# se connecter
class SigninForm(Form):
  email = TextField("Email",  [InputRequired("Merci d'entrer votre adresse mail."), Email("L'adresse mail doit être valide. ")])
  password = PasswordField('Mot de passe', validators=[InputRequired("Merci d'entrer votre mot de passe.")])
  submit = SubmitField("Se connecter")

  def __init__(self, *args, **kwargs):
    Form.__init__(self, *args, **kwargs)

  def validate(self):
    if not Form.validate(self):
      return False

    user = users.query.filter_by(email = self.email.data.lower()).first()
    if user and user.check_password(self.password.data):
      return True
    else:
      self.email.errors.append("Email ou mot de passe invalide")
      return False

class UpdateAccountForm(Form):
    firstname = StringField('Prénom',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Photo de profil', validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField('Mettre à jour')
    description = TextAreaField('Description')
    recherche = TextAreaField('Recherche')

class SendMessage(Form):
    message=TextAreaField('Envoyer un message')
    submit = SubmitField('Envoyer')