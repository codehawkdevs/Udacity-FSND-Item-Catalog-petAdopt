#!/usr/bin/env python3
import os
from flask import Flask, render_template, make_response, flash, request
from flask import redirect, url_for, jsonify
from sqlalchemy.orm import scoped_session
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Pets, PetSub, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import json
import requests

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# Load the Google Login API Client ID.
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
CLIENT_ID = json.loads(open(APP_ROOT + '/client_secrets.json', 'r').read())['web']['client_id']
# Connects to the database.
# Creates a session.
engine = create_engine('postgresql://catalog:yourpassword@localhost/catalog',pool_size=20, max_overflow=0)
Base.metadata.bind = engine

# Binds the engine to a session
DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)


# Route to JSON of categories.
@app.route('/JSON/')
@app.route('/pets/JSON/')
def catListJSON():  # cat can be understand as Category.
    cat = session.query(Pets).all()
    return jsonify(Pets=[i.serialize for i in cat])# Route to JSON of categories.


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
# Route to get XML of informatio of aet

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


# Route to connect to the Google login oAuth method.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(APP_ROOT + '/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

# Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
# If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        x = 'Current user is already connected.'
        response = make_response(json.dumps(x),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print(data)
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# Disconnect method for Google oAuth.
def gdisconnect():

    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Log out the current user.
@app.route('/logout/')
def logout():
    # Logs out the current user
    if 'username' in login_session:
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
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
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
