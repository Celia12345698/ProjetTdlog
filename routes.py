from flask import render_template, request, redirect, url_for, flash
from flask import session
import time
from functions import *
from models import Message, socketio, db, SignupForm, UpdateAccountForm, SendMessage, SigninForm, MessageForm
from flask_socketio import send, leave_room, join_room

number_q = 10
names = init_quest(number_q)  # register the questions in the db, names is the list of the names of the questions (q1,q2...)

ROOMS = ["Sérieux", "Fun", "Actualité"]



# Links to the Home Page
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/qui')
def qui():
    return render_template('qui.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if 'email' in session:
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
            user.q1, user.q2, user.q3, user.q4, user.q5, user.q6, user.q7, user.q8, user.q9, user.q10 = answers[0], answers[1], answers[2], answers[3], answers[4],answers[5],answers[6],answers[7],answers[8],answers[9]
            db.session.commit()
            if request.form.get("homme"):
                user.man = 1
                db.session.commit()
            if request.form.get("femme"):
                user.woman = 1
                db.session.commit()
            if request.form.get("oui"):
                user.same_region = 1
                db.session.commit()
            user.all_answered=1
            db.session.commit()
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
    if user.all_answered==0:
        flash("Vous n'avez pas répondu à toutes les questions.")
        return(redirect(url_for('question')))
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
    if 'email' in session:
        user = users.query.filter_by(_id=id).first()
        if user.all_answered==0:
            flash("Vous n'avez pas répondu à toutes les questions.")
            return(redirect(url_for('question')))
        image_file = url_for('static', filename='profile_pics/' + user.image_file)
        form = SendMessage()
        if form.validate_on_submit():
            if form.message.data:
                flash('Votre message a bien été envoyé!', 'success')
                form.message.data = None
                return render_template("profilext.html", user=user, image_file=image_file, form=form)
        return render_template("profilext.html", user=user, image_file=image_file, form=form)
    else:
        return redirect(url_for('signin'))


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
            flash('Vos informations ont été mises à jour!', 'success')
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
            session['firstname'] = user.firstname
            session['id'] = user._id
            if user.all_answered==0:
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
        if user.all_answered == 0:
            flash("Vous n'avez pas répondu à toutes les questions.")
            return (redirect(url_for('question')))
        Message = sqlite3.connect("Message.sqlite3")
        cur = Message.cursor()
        received_msg = cur.execute("SELECT * FROM Message WHERE recipient_id={}".format(user._id))
        row = received_msg.fetchone()
        while row is not None:
            sender = users.query.filter_by(_id=row[2]).first()
            image = url_for('static', filename='profile_pics/' + sender.image_file)
            msg = [sender._id,sender.firstname, row[3],image]
            received_msg_list.append(msg)
            row = received_msg.fetchone()

        return render_template('messages.html', messages_list=received_msg_list)
    else:
        return redirect(url_for('signin'))

@app.route('/messagesenvoyés')
def sent_msg():
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()
        if user.all_answered == 0:
            flash("Vous n'avez pas répondu à toutes les questions.")
            return (redirect(url_for('question')))
        sent_msg_list=[]
        Message = sqlite3.connect("Message.sqlite3")
        cur = Message.cursor()
        sent_msg = cur.execute("SELECT * FROM Message WHERE sender_id={}".format(user._id))
        row = sent_msg.fetchone()
        while row is not None:
            recipient = users.query.filter_by(_id=row[1]).first()
            image = url_for('static', filename='profile_pics/' + recipient.image_file)
            msg = [recipient._id,recipient.firstname, row[3],image]
            sent_msg_list.append(msg)
            row = sent_msg.fetchone()

        return render_template('messagesenvoyés.html', messages_list=sent_msg_list)
    else:
        return redirect(url_for('signin'))

@app.route('/send_message/<id>', methods=['GET', 'POST'])
def send_message(id):
    recipient = users.query.filter_by(_id=id).first()  # The one who receives the msg
    image = url_for('static', filename='profile_pics/' + recipient.image_file)
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()  # The one who sends the message
        if user.all_answered == 0:
            flash("Vous n'avez pas répondu à toutes les questions.")
            return (redirect(url_for('question')))
        form = MessageForm()
        if form.validate_on_submit():
            msg = Message(author=user, recipient=recipient, body=form.message.data)
            db.session.add(msg)
            db.session.commit()
            flash('Votre message a bien été envoyé.')
            return redirect(url_for('profile'))
        return render_template('sendmessage.html', form=form, author=user, recipient=recipient,image=image)
    else:
        return redirect(url_for('signin'))


@app.route("/chat", methods=['GET', 'POST'])
def chat():
    if 'email' in session:
        user = users.query.filter_by(email=session['email']).first()
        if user.all_answered == 0:
            flash("Vous n'avez pas répondu à toutes les questions.")
            return (redirect(url_for('question')))
        return render_template("chat.html", firstname=user.firstname, rooms=ROOMS)

    else:
        return redirect(url_for('signin'))


@socketio.on('incoming-msg')
def on_message(data):
    msg = data["msg"]
    firstname = data["firstname"]
    room = data["room"]
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    send({"firstname": firstname, "msg": msg, "time_stamp": time_stamp}, room=room)


# When a user joins a room
@socketio.on('join')
def on_join(data):
    firstname = data["firstname"]
    room = data["room"]
    join_room(room)
    send({"msg": firstname + " a rejoint la salle " + room + "."}, room=room)


# When a user leaves a room
@socketio.on('leave')
def on_leave(data):
    firstname = data['firstname']
    room = data['room']
    leave_room(room)
    send({"msg": firstname + " a quitté la salle."}, room=room)


if __name__ == "__main__":
    db.create_all(bind=['Message', 'users'])
    socketio.run(app, debug=True)

