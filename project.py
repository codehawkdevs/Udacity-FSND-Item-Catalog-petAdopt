#!/usr/bin/env python3

import requests
import json
import httplib2
from dict2xml import dict2xml as xmlify
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from database_setup import Base, Pets, PetSub, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import string
import random
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask import session as login_session
from sqlalchemy.orm import scoped_session
from flask import redirect, url_for, jsonify
from flask import Flask, render_template, make_response, flash, request
import os
import sys


app = Flask(__name__)

# Load the Google Login API Client ID.
CLIENT_ID = json.loads(open('client_secrets.json', 'r')
                       .read())['web']['client_id']

# Connects to the database.
# Creates a session.
engine = create_engine('sqlite:///petadopt.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

# Binds the engine to a session
DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)

# Flask Dance Blueprints
google_blueprint = make_google_blueprint(
    client_id='982428003194-1tfbs2gpljhvmdp006nucagb1r7b7bsh.apps.googleusercontent.com', client_secret='U8AcWMrfk6hiMrPIYMleaRda', scope=['profile', 'email'], redirect_url='/login/google/authorize'
)
twitter_blueprint = make_twitter_blueprint(
    api_key='iAbxfD8aWSC0YHmcl0RJ8etea', api_secret='ve1RJNCiB9yRHxZum9D5GNPJLQYeS7Nc3FuMdZbXCZ8duSNypy ')
facebook_blueprint = make_facebook_blueprint(
    client_id='550662108678573', client_secret='6b7adbf8a30ffe761277ed62b150e9a3', redirect_url='/login/facebook/authorize')

# register blueprint
app.register_blueprint(google_blueprint, url_prefix="/login")
app.register_blueprint(twitter_blueprint, url_prefix="/login")
app.register_blueprint(facebook_blueprint, url_prefix="/login")


@app.route('/login/twitter')
def twitter_loggin():
    if not twitter.authorized:
        return redirect(url_for("twitter.login"))
    resp = twitter.get("account/verify_credentials.json")
    assert resp.ok
    return "You are @{screen_name} on Twitter".format(screen_name=resp.json()["screen_name"])


@app.route('/login/google')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))


@app.route('/login/google/authorize')
def google_auth():
    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        data = resp.json()
        print(data, file=sys.stderr)
        login_session['username'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']
        user_id = getUserID(login_session['email'])
        if not user_id:
            user_id = createUser(login_session)
        login_session['user_id'] = user_id
        flash("Welcome! You are logged in as {email}".format(
            email=data["name"]))
        return redirect(url_for('catList'))


@app.route("/login/facebook")
def fb_login():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))


@app.route('/login/facebook/authorize')
def fb_auth():
    resp = facebook.get("/me")
    assert resp.ok, resp.text
    return "You are {name} on Facebook".format(name=resp.json()["name"])


# Route to JSON of categories.
@app.route('/JSON/')
@app.route('/pets/JSON/')
def catListJSON():  # cat can be understand as Category.
    cat = session.query(Pets).all()
    return jsonify(Pets=[i.serialize for i in cat])


# Route to JSON of categories.
@app.route('/XML/')
@app.route('/pets/XML/')
def catListXML():  # cat can be understand as Category.
    cat = session.query(Pets).all()
    return xmlify(data=[i.serialize for i in cat], wrap="all", indent="  ")


# Route to Categories.
@app.route('/')
@app.route('/pets/')
def catList():  # cat can be understand as Category.
    cat = session.query(Pets).all()
    return render_template('catlist.html', cat=cat)

# Route for creating a new categories.
@app.route('/pets/new/', methods=['GET', 'POST'])
def newCat():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newCat = Pets(category=request.form['category'],
                      img_url=(
                      "https://i.ibb.co/t8TKqgF/qm.jpg"
                      if request.form['img_url'] == ""
                      else request.form['img_url']),
                      user_id=login_session['user_id'])
        session.add(newCat)
        session.commit()
        flash("The category has successfully been created!")
        return redirect(url_for('catList'))
    else:
        return render_template('newcat.html')


# Route to edit a category.
@app.route('/pets/<int:pet_id>/edit/', methods=['GET', 'POST'])
def editCat(pet_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedCat = session.query(Pets).filter_by(id=pet_id).one()
    if login_session['user_id'] != editedCat.user_id:
        flash("You were not authorised to access that page.")
        return redirect(url_for('catList'))
    if request.method == 'POST':
        if request.form['category']:
            editedCat.category = request.form['category']
        if request.form['img_url']:
            editedCat.img_url = request.form['img_url']
        session.add(editedCat)
        session.commit()
        flash("Your changes have been saved!")
        return redirect(url_for('catList'))
    else:
        return render_template('editcat.html', i=editedCat)


# Route to delete a category.
@app.route('/pets/<int:pet_id>/delete/', methods=['GET', 'POST'])
def deleteCat(pet_id):
    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('showLogin'))
    catToDelete = session.query(Pets).filter_by(id=pet_id).one()
    if login_session['user_id'] != catToDelete.user_id:
        flash("You were not authorised to access that page.")
        return redirect(url_for('catList'))
    if request.method == 'POST':
        session.delete(catToDelete)
        session.commit()
        flash("Category has been deleted")
        return redirect(url_for('catList'))
    else:
        return render_template('deletecat.html', i=catToDelete)


# Route to JSON of a category's list.
@app.route('/pets/<int:pet_id>/list/JSON/')
def petListJSON(pet_id):
    pets = session.query(Pets).filter_by(id=pet_id).one()
    names = session.query(PetSub).filter_by(pet_id=pet_id).all()
    return jsonify(PetSub=[i.serialize for i in names])


# Route to XML of a category's list.
@app.route('/pets/<int:pet_id>/list/XML/')
def petListXML(pet_id):
    pets = session.query(Pets).filter_by(id=pet_id).one()
    names = session.query(PetSub).filter_by(pet_id=pet_id).all()
    return xmlify(data=[i.serialize for i in names], wrap="all", indent="  ")


# Route to JSON of a particular pet in a category's list.
@app.route('/pets/<int:pet_id>/list/<int:p_id>/JSON/')
def petJSON(pet_id, p_id):
    pet = session.query(PetSub).filter_by(id=p_id).one()
    return jsonify(PetSub=pet.serialize)


# Route to XML of a particular pet in a category's list.
@app.route('/pets/<int:pet_id>/list/<int:p_id>/XML/')
def petXML(pet_id, p_id):
    pet = session.query(PetSub).filter_by(id=p_id).one()
    return xmlify(data=[pet.serialize], wrap="all", indent="  ")


# Route to the list of a selected category.
@app.route('/pets/<int:pet_id>/')
@app.route('/pets/<int:pet_id>/list/')
def petList(pet_id):
    pets = session.query(Pets).filter_by(id=pet_id).one()
    creator = getUserInfo(pets.user_id)
    names = session.query(PetSub).filter_by(pet_id=pet_id).all()
    return render_template('list.html', pets=pets, names=names)


# Route to add a new pet in a category.
@app.route('/pets/<int:pet_id>/new/', methods=['GET', 'POST'])
def newCatItem(pet_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newItem = PetSub(name=request.form['name'],
                         user_id=login_session['user_id'],
                         description=request.form['description'],
                         gender=request.form['gender'],
                         breed=request.form['breed'],
                         medical_record_info=request
                         .form['medical_record_info'],
                         owner=request.form['owner'],
                         contact=request.form['contact'],
                         location=request.form['location'],
                         img_url=(
            "https://i.ibb.co/t8TKqgF/qm.jpg"
            if request.form['img_url'] == ""
            else request.form['img_url']),
            pet_id=pet_id)
        session.add(newItem)
        session.commit()
        flash("Your Pet has beed added to our list!")
        return redirect(url_for('petList', pet_id=pet_id))
    else:
        return render_template('newitem.html', pet_id=pet_id)


# Route to edit a pet in category.
@app.route('/pets/<int:pet_id>/<int:p_id>/edit/', methods=['GET', 'POST'])
def editCatItem(pet_id, p_id):
    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('showLogin'))

    editedItem = session.query(PetSub).filter_by(id=p_id).one()
    if login_session['user_id'] != editedItem.user_id:
        flash("You were not authorised to access that page.")
        return redirect(url_for('catList'))

    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['gender']:
            editedItem.gender = request.form['gender']
        if request.form['breed']:
            editedItem.breed = request.form['breed']
        if request.form['medical_record_info']:
            editedItem.medical_record_info = request.form[
                'medical_record_info']
        if request.form['owner']:
            editedItem.owner = request.form['owner']
        if request.form['contact']:
            editedItem.contact = request.form['contact']
        if request.form['location']:
            editedItem.location = request.form['location']
        if request.form['img_url']:
            editedItem.img_url = request.form['img_url']
        session.add(editedItem)
        session.commit()
        flash("The changes have been saved!")
        return redirect(url_for('petList', pet_id=pet_id))
    else:
        return render_template('edititem.html',
                               pet_id=pet_id, p_id=p_id, i=editedItem)


# Route to delete a pet in category.
@app.route('/pets/<int:pet_id>/<int:p_id>/delete/', methods=['GET', 'POST'])
def deleteCatItem(pet_id, p_id):
    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('showLogin'))
    itemToDelete = session.query(PetSub).filter_by(id=p_id).one()
    if login_session['user_id'] != itemToDelete.user_id:
        flash("You were not authorised to access that page.")
        return redirect(url_for('catList'))

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Successfully deleted")
        return redirect(url_for('petList', pet_id=pet_id))
    else:
        return render_template('deleteitem.html',
                               pet_id=pet_id, p_id=p_id, i=itemToDelete)


# Route to get JSON of information of a pet.
@app.route('/pets/<int:pet_id>/<int:p_id>/info/JSON/')
@app.route('/pets/<int:pet_id>/list/<int:p_id>/info/JSON/')
def petListItemJSON(pet_id, p_id):
    info = session.query(PetSub).filter_by(id=p_id).one()
    return jsonify(PetSub=info.serialize)


# Route to get XML of information of a pet.
@app.route('/pets/<int:pet_id>/<int:p_id>/info/XML/')
@app.route('/pets/<int:pet_id>/list/<int:p_id>/info/XML/')
def petListItemXML(pet_id, p_id):
    info = session.query(PetSub).filter_by(id=p_id).one()
    return xmlify(data=[info.serialize], wrap="all", indent="  ")


# Route to get information of a pet.
@app.route('/pets/<int:pet_id>/<int:p_id>/info/')
@app.route('/pets/<int:pet_id>/list/<int:p_id>/info/')
def petListItem(pet_id, p_id):
    info = session.query(PetSub).filter_by(id=p_id).one()
    return render_template('iteminfo.html', info=info)

# Create anti-forgery state token.
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Log out the current user.
@app.route('/logout/')
def logout():
    # Logs out the current user
    if 'username' in login_session:
        token = google_blueprint.token["access_token"]
        resp = google.post(
            "https://accounts.google.com/o/oauth2/revoke",
            params={"token": token},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert resp.ok, resp.text
        del google_blueprint.token
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        flash("You have been successfully logged out!")
        return redirect(url_for('catList'))
    else:
        flash("You were not logged in!")
        return redirect(url_for('catList'))

# For the creation of new user.


def createUser(login_session):
    newUsr = User(name=login_session['username'], email=login_session['email'],
                  img_url=login_session['picture'])
    session.add(newUsr)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# Collects user info by user id.


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# Gets user info by email.


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
