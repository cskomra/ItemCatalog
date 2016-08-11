from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from final_database_setup import Base, Event, Telling, User

#NEW IMPORTS FOR OAUTH
#login_session - dict for duration of user's session
from flask import session as login_session
# to create a pseudo-random string to id each session
import random, string

# IMPORTS FOR GCONNECT
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///lifrary.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


###########  OAUTH Handlers  #############

def isLoggedIn():
	loggedIn = False
	if 'username' in login_session:
		loggedIn = True
	return loggedIn

# Create a state token to prevent request forgery.
# Store it in the session for later validation.
@app.route('/login')
def showLogin():
	#creates a new random anti-forgery state token each time
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html',
							STATE=login_session['state'],
							isLoggedIn=isLoggedIn())

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
	if 'provider' in login_session:
		if login_session['provider'] == 'google':
			gdisconnect()
			del login_session['gplus_id']
			del login_session['credentials']
		if login_session['provider'] == 'facebook':
			fbdisconnect()
			del login_session['facebook_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		del login_session['provider']
		flash("You have been successfully loged out.")
		return redirect('/story')
	else:
		flash("You are not logged in.")
		return redirect('/story')

# CONNECT
@app.route('/gconnect', methods=['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# obtain authorization code
	code = request.data

	try:
		#Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		print "Token's user ID does not match given user ID."
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's"
		response.headers['Content-Type'] = 'application/json'
		return response


	# Check to see if user is already logged in
	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')

	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(
			json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	# data should have available user values from openid filled in
	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']
	# add provider to login_session
	login_session['provider'] = 'google'

	# see if user exists, if it doesn't make a new one
	user_id = getUserID()
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '</br></br><h2>Welcome, '
	output += login_session['username']
	output += '!</h2>'
	output += '<img src="'
	output += login_session['picture']
	output += '" style="width: 100px; height: 100px; border-radius: 50px; -webkit-border-radius: 50px; -moz-border-radius: 50px;">'
	flash("You are now logged in as %s" % login_session['username'])
	return output

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data
	print "access token received %s" % access_token

	#Exchange client token for long-lived server-side token...
	app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
	app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	#Use token to get user info from API
	userinfo_url = "https://graph.facebook.com/v2.4/me"
	#Strip expire tag from access token
	token = result.split("&")[0]
	url = "https://graph.facebook.com/v2.4/me?%s&fields=name,id,email,picture" % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data['name']
	login_session['email'] = data['email']
	login_session['facebook_id'] = data['id']

	# The token must be stored in the login_session in order to properly logout.
	# Strip out the information before the equals sign in
	stored_token = token.split("=")[1]
	login_session['access_token'] = stored_token

	#Get user picture
	url = "https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200" % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)

	login_session['picture'] = data['data']['url']

	#see if user exists
	user_id = getUserID()
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	output = ''
	output += '</br></br><h2>Welcome, '
	output += login_session['username']
	output += '!</h2>'
	output += '<img src="'
	output += login_session['picture']
	output += '" style="width: 100px; height: 100px; border-radius: 50px; -webkit-border-radius: 50px; -moz-border-radius: 50px;">'
	flash("You are now logged in as %s" % login_session['username'])
	return output

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route("/gdisconnect")
def gdisconnect():
	# Only disconnect a connected user.
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(
			json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Execute HTTP GET request to revoke current token.
	access_token = credentials.access_token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	if result['status'] != '200':
		response = make_response(
			json.dumps('Failed to revoke token for given user.'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response

@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['facebook_id']
	# The access token must be included to successfully logout
	access_token = login_session['access_token']
	url = "https://graph.facebook.com/%s/permissions?access_token=%s" % (facebook_id, access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	return "You have been successfully logged out."


##########  API ENDPOINTS (GET Requests)  #############

# GET all events
@app.route('/events/JSON')
def eventsJSON():
	events = session.query(Event).all()
	#return jsonify class
	return jsonify(Events=[e.serialize for e in events])

# GET a specific event
@app.route('/events/<int:event_id>/event/JSON')
def eventJSON(event_id):
	event = session.query(Event).filter_by(id=event_id).one()
	# must call .serialize() in the object sending
	return jsonify(Event=[event.serialize])

# GET all tellings from a specific event
@app.route('/events/<int:event_id>/tellings/JSON')
def tellingsJSON(event_id):
	tellings = session.query(Telling).filter_by(event_id=event_id).all()
	#return jsonify class
	return jsonify(Tellings=[t.serialize for t in tellings])

# GET a specific telling from a specific event
@app.route('/events/<int:event_id>/telling/<int:telling_id>/JSON')
def eventTellingJSON(event_id, telling_id):
	telling = session.query(Telling).filter_by(event_id=event_id).filter_by(id=telling_id).one()
	return jsonify(Telling=[telling.serialize])


###########  UI Handlers  #############

#1. STORY - List of ALL EVENTS
@app.route('/')
@app.route('/story')
def showStory():
	events = session.query(Event).all()
	return render_template('events.html',
							events = events,
							isLoggedIn=isLoggedIn(),
							user_id=getUserID())

#2. NEW EVENT
@app.route('/event/new/', methods=['GET', 'POST'])
def newEvent():
	# check for logged in user
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == "POST":
		# create get values from the form using request.form[<fieldName>]
		newEvent = Event(name=request.form['name'],
						 eventType=request.form['eventType'],
						 location=request.form['location'],
						 description=request.form['description'],
						 user_id=login_session['user_id'])
		session.add(newEvent)
		session.commit()
		flash("New event created!")
		# then, redirect user back to story
		return redirect(url_for('showStory'))
	else:
		return render_template('newevent.html')

#3. EDIT EVENT
@app.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
def editEvent(event_id):
	if 'username' not in login_session:
		return redirect('/login')
	event = session.query(Event).filter_by(id=event_id).one()
	# Error is user is not owner
	if event.user_id != login_session['user_id']:
		error = ''
		error += "Error: unauthorized edit request for Event: %s" % event.name
		error += "<br><a href='/'>Lifrary Home</a>"
		return error

	else:
		if request.method == "POST":
			# create get values from the form using request.form[<fieldName>]
			if request.form['eventType']:
				event.eventType = request.form['eventType']
			if request.form['name']:
				event.name = request.form['name']
			if request.form['location']:
				event.location = request.form['location']
			if request.form['description']:
				event.description = request.form['description']
			session.add(event)
			session.commit()
			flash("%s event edited!" % event.name)
			# then, redirect user back to story
			return redirect(url_for('showStory'))
		else:
			return render_template('editevent.html', event_id=event_id, event=event, isLoggedIn=isLoggedIn())

#4. DETELE EVENT
@app.route('/event/<int:event_id>/delete', methods=['GET', 'POST'])
def deleteEvent(event_id):
	if 'username' not in login_session:
		return redirect('/login')
	event = session.query(Event).filter_by(id=event_id).one()
	# Error if user is not owner
	if event.user_id != login_session['user_id']:
		error = ''
		error += "Error: unauthorized delete request for Event: %s" % event.name
		error += "<br><a href='/'>Lifrary Home</a>"
		return error
	else:
		if request.method == "POST":
			session.delete(event)
			session.commit
			flash("%s event deleted!" % event.name)
			return redirect(url_for('showStory'))
		else:
			return render_template('deleteevent.html', event_id=event_id, event=event, isLoggedIn=isLoggedIn())

#5. SHOW EVENT
@app.route('/event/<int:event_id>/event', methods=['GET', 'POST'])
@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
def showEvent(event_id):
	event = session.query(Event).filter_by(id=event_id).one()
	tellings = session.query(Telling).filter_by(event_id=event_id).order_by(desc(Telling.id))
	return render_template('event.html', event_id=event_id,
										 event=event,
										 tellings=tellings,
										 isLoggedIn=isLoggedIn(),
										 user_id=getUserID())

#6. NEW TELLING
@app.route('/event/<int:event_id>/telling/new/', methods=['GET', 'POST'])
def newTelling(event_id):
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == "POST":
		# create get values from the form using request.form[<fieldName>]
		telling = Telling(mediaFilepath=request.form['mediaFilepath'],
						  title=request.form['title'],
						  description=request.form['description'],
						  event_id=event_id,
						  user_id=login_session['user_id'])
		session.add(telling)
		session.commit()
		flash("New telling created!")
		# then, redirect user back to event
		return redirect(url_for('showEvent', event_id=event_id))
	else:
		event = session.query(Event).filter_by(id=event_id).one()
		return render_template('newtelling.html', event_id=event_id, event=event, isLoggedIn=isLoggedIn())

#7. EDIT TELLING
@app.route('/event/<int:event_id>/telling/<int:telling_id>/edit/', methods=['GET', 'POST'])
def editTelling(event_id, telling_id):
	if 'username' not in login_session:
		return redirect('/login')
	telling = session.query(Telling).filter_by(id=telling_id).one()
	# Error if user is not owner
	if telling.user_id != login_session['user_id']:
		error = ''
		error += "Error: unauthorized edit request for Telling: %s" % telling.title
		error += "<br><a href='"
		error += url_for('showEvent', event_id=event_id)
		error += "'>Back to Event</a>"
		return error
	else:
		if request.method == "POST":
			if request.form['mediaFilepath']:
				telling.name = request.form['mediaFilepath']
			if request.form['title']:
				telling.title = request.form['title']
			if request.form['description']:
				telling.description = request.form['description']

			session.add(telling)
			session.commit()
			flash("Telling '%s' edited!" % telling.title)
        		return redirect(url_for('showEvent', event_id=event_id))
		else:
			event = session.query(Event).filter_by(id=event_id).one()
			return render_template('edittelling.html', event=event, telling=telling, isLoggedIn=isLoggedIn())

#8. DELETE TELLING
@app.route('/event/<int:event_id>/telling/<int:telling_id>/delete/', methods=['GET', 'POST'])
def deleteTelling(event_id, telling_id):
	if 'username' not in login_session:
		return redirect('/login')
	telling = session.query(Telling).filter_by(id=telling_id).one()
	# Error if user is not owner
	if telling.user_id != login_session['user_id']:
		error = ''
		error += "Error: unauthorized delete request for Telling: %s" % telling.title
		error += "<br><a href='"
		error += url_for('showEvent', event_id=event_id)
		error += "'>Back to Event</a>"
		return error
	else:
		if request.method == "POST":
			session.delete(telling)
			session.commit
			flash("'%s' deleted!" % telling.title)
			return redirect(url_for('showStory'))
		else:
			return render_template('deletetelling.html', event_id=event_id, telling=telling, isLoggedIn=isLoggedIn())


# USER MANAGEMENT
def isOwner(document):
	isOwner = False
	if isLoggedIn():
		print login_session['user_id']
		if login_session['user_id'] == document.user_id:
			isOwner = True
	return isOwner

def getUserID():
	if isLoggedIn():
		try:
			email=login_session['email']
			user = session.query(User).filter_by(email=email).all()[0]
			return user.id
		except:
			return None
	return None

def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user

def createUser(login_session):
	newUser = User(name=login_session['username'],
				   email=login_session['email'],
				   picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id

if __name__ == '__main__':
	app.secret_key = ""
	app.debug = True
	app.run(host = '0.0.0.0', port = 5001)
