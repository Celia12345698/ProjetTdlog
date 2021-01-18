import sqlite3
import numpy as np
import os
import secrets
from PIL import Image
from models import users,Question,app

#app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///users.sqlite3'
app.config['SQLALCHEMY_BINDS'] = {'users':'sqlite:///users.sqlite3','Message':'sqlite:///Message.sqlite3'}


def question_name(n):
    questions_names=[]
    for i in range(n):
        questions_names.append('q'+str(i+1))
    return questions_names


def init_quest(nb_quest): #Nb_quest : number of questions
    names = question_name(nb_quest)
    questions = [Question(names[i]) for i in range(nb_quest)]
    for question in questions:
        question.register(users)
    return(names)

def gender_filter(id):
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

def region_filter(id):
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

def save_picture(form_picture):
    #Generating a random combination to register the image (unique for each user)
    random_hex = secrets.token_hex(8)  
    #Getting the name and the extension of the image
    _, f_ext = os.path.splitext(form_picture.filename)  
    #rename the image with the random combination, but keeping the same extension
    picture_fn = random_hex + f_ext 
    #Registering the image in our file
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn) 
    #Dimensions
    output_size = (125, 125)    
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def all_quest(names_quest):
  all_questions = ""
  for i in range(len(names_quest)):
    if i == len(names_quest) - 1:
      all_questions += str(names_quest[i])
    else:
      all_questions += (str(names_quest[i]) + ", ")
  return all_questions


def matching(id,names_quest): #names_quest : list of the names of the questions (q1,q2...)
  nb_quest=len(names_quest)
  users=sqlite3.connect("users.sqlite3")
  cur=users.cursor()
  all_users=cur.execute("select {} from users".format(all_quest(names_quest)))
  row=all_users.fetchone()
  all_answers=[]
  L=[]
  while row is not None:
    print(row)
    L.append(row)
    row=all_users.fetchone()
  nombre_u=cur.execute("select count(email) from users")
  row1=nombre_u.fetchone()
  for i in range (0,row1[0]):
    all_answers.append(L[i][0])
    all_answers.append(L[i][1])
  answers=all_answers[nb_quest*(id-1):nb_quest*id]
  L_arrange=[]
  L_gap=[]
  L_percent=[]

  for i in range(0,nb_quest):
      for j in range(row1[0]):
          L_arrange.append(all_answers[i+nb_quest*j])

  for i in range(0,nb_quest):
      for j in range(row1[0]):
          L_gap.append(((4-np.abs(L_arrange[j+i*row1[0]]-answers[i]))))

  for i in range(row1[0]):
      somme=0
      for j in range(0,nb_quest):
          somme+=L_gap[i+row1[0]*j]
      L_percent.append(100*somme/(4*nb_quest))

  users.close()

  return L_percent


def filtre_matching(id,names_quest):
  L_percent=matching(id,names_quest)
  L_gender=gender_filter(id)
  L_region=region_filter(id)
  values=users.query.all()
  L_percent_new=[]
  L_ind=[]
  if len(values)!=len(L_region):
    for id1 in L_region:
      for id2 in L_gender:
        if id1==id2:
          L_ind.append(id1)
  else:
    L_ind=L_gender

  for id1 in L_ind:
    L_percent_new.append([id1,L_percent[id1-1]])

  L_percent_new=sorted(L_percent_new, key=lambda colonnes: colonnes[1], reverse=True)

  for elem in L_percent_new:
    if elem[1]<=50:
      L_percent_new.remove(elem)

  for elem in L_percent_new:
    if elem[0]==id:
      L_percent_new.remove(elem)

  return L_percent_new

def select_questions(id,names_quest):
  users=sqlite3.connect("users.sqlite3")
  cur=users.cursor()
  all_users=cur.execute("select {} from users".format(str(all_quest(names_quest))))
  row=all_users.fetchone()
  nb_quest=len(names_quest)
  all_answers=[]
  L=[]
  while row is not None:
    L.append(row)
    row=all_users.fetchone()
  nombre_u=cur.execute("select count(email) from users")
  row1=nombre_u.fetchone()
  for i in range (0,row1[0]):
    all_answers.append(L[i][0])
    all_answers.append(L[i][1])

  answers=all_answers[nb_quest*(id-1):nb_quest*id]
  return answers

