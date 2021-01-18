from flask import render_template, request, redirect, url_for, flash
from flask import session
import time
from functions import *
from models import Message, socketio, db, SignupForm, UpdateAccountForm, SendMessage, SigninForm, MessageForm
from flask_socketio import send, leave_room, join_room

number_q = 2
names = init_quest(number_q)  # register the questions in the db, names is the list of the names of the questions (q1,q2...)

ROOMS = ["Sérieux", "Fun", "Actualité"]


# Links to the Home Page
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/qui')
def qui():
    return render_template('qui.html')


# Links to Signup Form: pour créer un compte, ajouter ici l'ensemble des questions
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()
        return redirect(url_for('profile'))

    if request.method == 'POST':
        if form.validate() == False:
            return render_template('signup.html', form=form)
        else:
            newuser = users(form.firstname.data, form.lastname.data, form.email.data, form.password.data,
                            form.gender.data, form.region.data)
            db.session.add(newuser)
            db.session.commit()
            session['email'] = newuser.email
            return redirect(url_for('question'))

    elif request.method == 'GET':
        return render_template('signup.html', form=form)


@app.route('/question', methods=['GET', 'POST'])
def question():
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()
        session['firstname'] = user.firstname
        answers = []
        if request.method == "POST":
            for q in range(number_q):
                answers.append(request.form[str(names[q])])
            user.q1, user.q2 = answers[0], answers[1]
            db.session.commit()
            if request.form.get("homme"):
                user.man = 1
                db.session.commit()
            else:
                user.man = 0
                db.session.commit()
            if request.form.get("femme"):
                user.woman = 1
                db.session.commit()
            else:
                user.woman = 0
                db.session.commit()
                # region
            if request.form.get("oui"):
                user.same_region = 1
                db.session.commit()
            else:
                user.same_region = 0
                db.session.commit()
            user.all_answered=1
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            return render_template('question.html')

    else:
        return redirect(url_for('signup'))


@app.route('/compatibilite')
def compa():
    form = UpdateAccountForm()
    if 'email' not in session:
        return redirect(url_for('signin'))
    user = users.query.filter_by(email=session['email']).first()
    values = users.query.all()
    L2 = []
    L3 = filtre_matching(user._id, names)
    for i in range(len(L3)):
        value = users.query.filter_by(_id=L3[i][0]).first()
        image_file = url_for('static', filename='profile_pics/' + value.image_file)
        L2.append([value, L3[i][1], image_file])
    return render_template('compatibilite.html', values=values, L2=L2, form=form, user=user)


@app.route('/profil/<id>', methods=['GET', 'POST'])
def profilext(id):
    user = users.query.filter_by(_id=id).first()
    image_file = url_for('static', filename='profile_pics/' + user.image_file)
    form = SendMessage()
    if form.validate_on_submit():
        if form.message.data:
            flash('Ton message a bien été envoyé!', 'success')

            form.message.data = None
            return render_template("profilext.html", user=user, image_file=image_file, form=form)
    return render_template("profilext.html", user=user, image_file=image_file, form=form)


@app.route('/profil')
def profile():
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()
        image_file = url_for('static', filename='profile_pics/' + user.image_file)
        return render_template("profil.html", user=user, image_file=image_file)
    else:
        return redirect(url_for('signin'))


@app.route("/modifprofil", methods=['GET', 'POST'])
def modifprofil():
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()
        form = UpdateAccountForm()
        if form.validate_on_submit():
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                user.image_file = picture_file
            user.description = form.description.data
            if form.recherche.data:
                user.recherche = form.recherche.data
            user.firstname = form.firstname.data
            user.email = form.email.data
            db.session.commit()
            flash('Tes informations ont été mises à jour!', 'success')
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.firstname.data = user.firstname
            form.email.data = user.email
            form.description.data = user.description
            form.recherche.data = user.recherche
        image_file = url_for('static', filename='profile_pics/' + user.image_file)
        return render_template('modifprofil.html', title='modifprofil',
                               image_file=image_file, form=form)
    else:
        return redirect(url_for('signin'))


# Signin
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()

    if 'email' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        if form.validate() == False:
            return render_template('signin.html', form=form)
        else:
            session['email'] = form.email.data
            user = users.query.filter_by(email=session['email']).first()
            print(user._id)
            session['firstname'] = user.firstname
            session['id'] = user._id
            questions = select_questions(user._id, names)
            for answer in questions:
                if answer == None:
                    flash("Vous n'avez pas répondu à toutes les questions.")
                    return redirect(url_for('question'))
            return redirect(url_for('profile'))

    elif request.method == 'GET':
        return render_template('signin.html', form=form)


# Signout
@app.route('/signout')
def signout():
    if 'email' not in session:
        return redirect(url_for('signin'))

    session.pop('email', None)
    return redirect(url_for('home'))


@app.route('/mesmessages')
def my_messages():
    if 'email' in session:
        received_msg_list = []
        user = users.query.filter_by(email=session['email']).first()
        Message = sqlite3.connect("Message.sqlite3")
        cur = Message.cursor()
        received_msg = cur.execute("SELECT * FROM Message WHERE recipient_id={}".format(user._id))
        row = received_msg.fetchone()
        while row is not None:
            print(row)
            sender = users.query.filter_by(_id=row[2]).first()
            msg = [sender.firstname, row[3]]
            received_msg_list.append(msg)
            row = received_msg.fetchone()

        return render_template('messages.html', messages_list=received_msg_list)
    else:
        return redirect(url_for('signin'))


@app.route('/send_message/<id>', methods=['GET', 'POST'])
def send_message(id):
    recipient = users.query.filter_by(_id=id).first()  # The one who receives the msg
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()  # The one who sends the message
        form = MessageForm()
        if form.validate_on_submit():
            msg = Message(author=user, recipient=recipient, body=form.message.data)
            db.session.add(msg)
            db.session.commit()
            idsender = msg.sender_id
            prenomsender = users.query.filter_by(_id=idsender).first().firstname
            print("Sender")
            print(prenomsender)
            print("Recipient")
            print(recipient.firstname)
            flash('Your message has been sent.')
            return redirect(url_for('profile'))
        return render_template('sendmessage.html', form=form, author=user, recipient=recipient)

    return (True)


@app.route("/chat", methods=['GET', 'POST'])
def chat():
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()
        return render_template("chat.html", username=user.firstname, rooms=ROOMS)

    else:
        flash('Please login', 'danger')
        return redirect(url_for('signin'))


@socketio.on('incoming-msg')
def on_message(data):
    "Broadcast messages"

    msg = data["msg"]
    username = data["username"]
    room = data["room"]
    # Set timestamp
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    send({"username": username, "msg": msg, "time_stamp": time_stamp}, room=room)


# When a user joins a room
@socketio.on('join')
def on_join(data):
    username = data["username"]
    room = data["room"]
    join_room(room)

    send({"msg": username + " a rejoint la salle " + room + "."}, room=room)


# When a user leaves a room
@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send({"msg": username + " has left the room"}, room=room)


if __name__ == "__main__":
    db.create_all(bind=['Message', 'users'])
    socketio.run(app, debug=True)
