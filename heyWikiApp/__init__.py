import gc
import logging
import os
from functools import wraps
from urllib.parse import urlparse
from flask_migrate import Migrate
from flask import Flask, render_template, url_for, redirect, flash, request, session, jsonify, Blueprint
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
from wtforms import Form, validators, PasswordField, TextField

from .logic.dbOperations import *
from .translate.translator import _translate
from pprint import pprint

app = Flask(__name__, template_folder='templates')
logging.basicConfig(filename='error.log', level=logging.DEBUG)
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
db.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)
# Add a user

# Decorators 

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:

            flash("You need to login first")
            return redirect(url_for('login'))

    return wrap

def remainingCharacterLimitNotZero(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            remainingLimit = getRemainingLimit()
            if remainingLimit > 0:
                return f(*args, **kwargs)
        flash("Your limit for voice conversion is over contact siddharthdv77@gmail.com for upgrade.")
    return wrap


@app.route('/')
def homepage():
    try:
        app.logger.info("Inside homepage")
        if 'logged_in' in session:
            app.logger.info("User is logged in")
            return redirect(url_for('dashboard'))
        else:
            app.logger.info("User is NOT logged in")
            return render_template('layout/homepage.html')
    except Exception as e:
        return str(e)


#
@app.route('/dashboard/')
@login_required
def dashboard():
    app.logger.info("Inside dashboard")
    return render_template("/layout/dashboard.html")


@app.errorhandler(404)
def page_not_found(e):
    app.logger.info("Inside page_not_found")
    return render_template('helper_templates/404.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = ''
    try:
        app.logger.info("Inside login")
        if 'logged_in' in session:
            return redirect(url_for('homepage'))
        elif request.method == "POST":
            app.logger.info("Inside login route ")
            app.logger.info("request  is %s" % request)

            app.logger.info("login request form is %s" % request.form)
            app.logger.info('thwarted username is %s' %
                            thwart(request.form['username']))
            user = getUserDataFirst(thwart(request.form['username']))
            app.logger.info('user info received from db is %s' % user)
            UserPassword = user.password

            app.logger.info(sha256_crypt.verify(
                request.form['password'], UserPassword))

            if sha256_crypt.verify(request.form['password'], UserPassword):
                session['logged_in'] = True
                session['username'] = request.form['username']
                app.logger.info("You are now logged in")
                flash("You are now logged in")
                return redirect(url_for('dashboard'))
            else:
                app.logger.info("Invalid credentials ")
                error = "Invalid credentials, try again."

        gc.collect()
        return render_template("user_Management/login.html", error=error)

    except Exception as e:
        # flash(e)
        app.logger.error("Error occured ----> %s" % e)
        error = "Invalid credentials, try again."
        return render_template("user_Management/login.html", error=error)


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',
                           message='Passwords must match'
                           )
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/register/', methods=["GET", "POST"])
def register_page():
    try:
        app.logger.info("Inside register_page  ")
        form = RegistrationForm(request.form)
        app.logger.info("username of user ---> %s" % form.username.data)
        if 'logged_in' in session:
            app.logger.info("Already logged in ")
            return redirect(url_for('dashboard'))
        elif request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.hash(thwart(str(form.password.data)))
            app.logger.info("username,email,password are : %s, %s, %s"
                            % (username, email, password))
            foundUser = getUserDataFirst(thwart(username))
            app.logger.info("value of foundUser is  %s" % foundUser)
            if foundUser is not None:
                flash("That username is already taken, please choose another")
                return render_template('user_Management/register.html', form=form)

            else:

                createNewUser(
                    username=thwart(username),
                    email=thwart(email),
                    password=password
                )

                flash("Thanks for registering!")
                gc.collect()
                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('dashboard'))

        return render_template("user_Management/register.html", form=form)

    except Exception as e:
        return str(e)

@app.route('/getRemainingLimit/', methods=['GET'])
@login_required
def getRemainingLimit():
    username = session['username']
    remainingLimit = getUserRemainingLimit(username)
    return remainingLimit


# app.logger.info("")
@app.route('/converttospeech/', methods=['GET', 'POST'])
# @login_required
@remainingCharacterLimitNotZero
def getWiki():
    """ Receive a request to convert the clicked link to audio
        check if link is present in AllWikiLinks
            yes :
                return from there
            no  :
                get the parsed page from wikipedia class
                save that to allwikilinks list with the wikilink being path and text being the dict
                call convertospeech with necessary fragment
                get the location where this is saved
        Link in users wikilinks ?
        no : then add
        else: take user to that location

        https://en.wikipedia.org/wiki/Anarchy#Etymology
        ParseResult(scheme='https', netloc='en.wikipedia.org', path='/wiki/Anarchy',
                    params='', query='', fragment='Etymology')
    """
    try:
        acceptedWikipediaUrls = {'en.wikipedia.org', 'hi.wikipedia.org'}
        getLanguageSpecificUrl = {
            'en': 'https://en.wikipedia.org',
            'hi': 'https://hi.wikipedia.org'
        }
        app.logger.info("Inside getWiki")
        app.logger.info("request received is %s" % request)
        app.logger.info("request form received is %s" % request.form)

        wikiLinkToBeParsed = str(request.form['wikipediaLink']).strip()
        articleLanguage = str(request.form['articleLanguage'])
        app.logger.info(
            "wikiLink to be parsed is : %s, artice language is %s, and its type is %s" % (wikiLinkToBeParsed, articleLanguage, type(wikiLinkToBeParsed)))
        parsedUrl = urlparse(wikiLinkToBeParsed)
        app.logger.info("parsedUrl is : %s" % str(parsedUrl))
        if parsedUrl.netloc not in acceptedWikipediaUrls or parsedUrl.scheme != 'https':

            msg = "Pass a valid wikipedia url, for e.g :  https://en.wikipedia.org/wiki/Anarchy"
            return jsonify({
                'txt': msg, 'mediaLocation':
                '', "success": False,
            })
        else:
            wikipediaNetLoc = getLanguageSpecificUrl[articleLanguage]
            path = parsedUrl.path
            fragment = parsedUrl.fragment

            if 'logged_in' in session:
                username = session['username']
                newTTS = methodsForTTS(
                    username,
                    path,
                    articleLanguage,
                    wikipediaNetLoc,
                    fragment
                )
                mediaLocation, articleFragment, articleContentsList, articleFragmentLength, articalTotalLength = newTTS.orchestrator()
                # TODO : Uncomment the following line
                # setUserRemainingLimit(username, articleFragmentLength)

                return jsonify({
                    'mediaLocation': mediaLocation + '.mp3',
                    'txt': articleFragment,
                    "success": True,
                    'articleContents': articleContentsList,
                    'articleFragmentLength': articleFragmentLength,
                    'articalTotalLength': articalTotalLength, 
                })
            else:
                username = 'UserNotLoggedIn'
                fragment = ''
                newTTS = methodsForTTS(
                    username,
                    path,
                    articleLanguage,
                    wikipediaNetLoc,
                    fragment
                )
                mediaLocation, articleFragment, articleContentsList, articleFragmentLength, articalTotalLength = newTTS.orchestrator()
                return jsonify({
                    'mediaLocation': mediaLocation + '.mp3',
                    'txt': articleFragment,
                    "success": True,
                    'articleContents': '',
                    'articleFragmentLength': articleFragmentLength,
                    'articalTotalLength': articalTotalLength
                })
    except Exception as e:
        app.logger.info("error in get wiki : %s" % e)
        return str(e)


@app.route('/translate/', methods=["POST", "GET"])
@login_required
def translate():
    try:
        data = request.get_json()
        srcLanguage = data['srcLanguage']
        destLanguage = data['destLanguage']
        textToTranlate = data['textToTranslate']
        app.logger.info("Text to translate is : %s " % data)
        translatedText = _translate(
            textToTranlate,
            src=srcLanguage,
            dest=destLanguage)
        app.logger.info("Translated Text is %s " % translatedText)
        returnData = {'translatedTextResponse': translatedText,
                      'textWhichWasToBeTranslated': data['textToTranslate']}
        return jsonify(returnData)
    except Exception as e:
        return "noob"
        # print(e)
        app.logger.error('Error in translate :%s' % e)


@app.route('/translateToSpeech/', methods=["POST", "GET"])
@login_required
@remainingCharacterLimitNotZero
def translateToSpeech():
    data = request.get_json()
    app.logger.info("Request to translate text to speech with data %s" % data)
    textToConvert = data['textToConvert']
    nameToSaveWith = data['nameToSaveWith']
    translateLanguage = data['translateLanguage']
    voiceGender = data['voiceGender']
    setUserRemainingLimit(session['username'], len(textToConvert))
    mediaLocation = GoogleTextToSpeech(textToConvert=textToConvert,
                                       nameToSaveWith=nameToSaveWith,
                                       translateLanguage=translateLanguage,
                                       voiceGender=voiceGender,
                                       convertType='translate'
                                       )
    app.logger.info("Text to speech request audio file location is : %s" % mediaLocation)
    return mediaLocation


@app.route('/logout/')
@login_required
def logout():
    app.logger.info("Inside logout")
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('homepage'))


###########################################
## My utility functions will clean later ##
###########################################


# ParseResult(scheme='https', netloc='en.wikipedia.org', path='/wiki/Anarchy',
#                         params='', query='', fragment='Description')

def createTables():
    db.create_all()


def drop():
    db.drop_all()


def dc():
    drop()
    createTables()
    app.run(host="0.0.0.0", debug=True)


if __name__ == '__main__':
    with app.app_context():
        app.run(host="0.0.0.0", debug=True)
        # testTTS()
        # dc()
        # print(removeWikiLinkFromUser('qwer','_wiki_Anarchy#French Revolution (1789–1799)'))
