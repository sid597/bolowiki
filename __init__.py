from flask import Flask, render_template, url_for, redirect, flash, request, session, send_file, jsonify
from wtforms import Form, BooleanField, validators, PasswordField, TextField
# from dbconnect import connection
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
from functools import wraps
# from content_management import Content
from tts import GoogleTextToSpeech
from urllib.parse import urlparse
from wikipedia import WikipediaParser
# from markupsafe import escape
# from querydb import queryDb
import os
import gc
import json
import logging
from models import *

app = Flask(__name__)
logging.basicConfig(filename='error.log', level=logging.DEBUG)
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://siddharth:dragonking@localhost/tts"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
db.init_app(app)


# Add a user
def adduser():
    dummy = User(username="qwer", password="%s" % sha256_crypt.encrypt("1"), email="siddharthdv77@gmail.com")
    db.session.add(dummy)
    db.session.commit()


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:

            flash("You need to login first")
            return redirect(url_for('login'))

    return wrap


@app.route('/')
def homepage():
    app.logger.info("hello there")
    try:
        if 'logged_in' in session:
            return redirect(url_for('dashboard'))
        else:
            return render_template("main.html")
    except Exception as e:
        return str(e)


#
@app.route('/dashboard/')
@login_required
def dashboard():
    return render_template("dashboard.html")


# #
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = ''
    try:
        # c, conn = connection()
        if 'logged_in' in session:
            return redirect(url_for('dashboard'))
        elif request.method == "POST":
            app.logger.info("Inside login route %s" % db)
            app.logger.info("login request form is %s" % request.form)
            data = User.query.filter_by(username="%s" % thwart(request.form['username'])).first()

            passwd = data.password
            app.logger.info(sha256_crypt.verify(request.form['password'], passwd))
            app.logger.info("FLASK_SECRET_KEY ------> %s" % os.getenv("FLASK_SECRET_KEY"))

            if sha256_crypt.verify(request.form['password'], passwd):
                session['logged_in'] = True
                session['username'] = request.form['username']
                app.logger.info("You are now logged in")
                flash("You are now logged in")
                return redirect(url_for('dashboard'))
            else:
                app.logger.info("Invalid credentials ")
                error = "Invalid credentials, try again."

        gc.collect()
        return render_template("login.html", error=error)

    except Exception as e:
        flash(e)
        app.logger.error("Error occured ----> %s" % e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error=error)


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/register/', methods=["GET", "POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)
        app.logger.info("username of user ---> %s" % form.username.data)
        if 'logged_in' in session:
            app.logger.info("Already logged in ")
            return redirect(url_for('dashboard'))
        elif request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))

            foundUser = User.query.filter_by(username="%s" % thwart(username)).first()
            app.logger.info("value of x is  type is %s" % foundUser)
            if foundUser is not None:
                flash("That username is already taken, please choose another")
                return render_template('register.html', form=form)

            else:

                newUser = User(username="%s" % thwart(username), email="%s" % thwart(email),
                               password="%s" % thwart(password))
                db.session.add(newUser)
                db.session.commit()

                flash("Thanks for registering!")
                gc.collect()
                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('dashboard'))

        return render_template("register.html", form=form)

    except Exception as e:
        return str(e)


# @app.route('/converttospeech/', methods=['GET', 'POST'])
# @app.route('/converttospeech/', methods=['GET', 'POST'])
# @login_required
# def convertToSpeech():
#     return jsonify({'txt': 'Congrats !'})


# # #
# # #

# app.logger.info("")
@app.route('/converttospeech/', methods=['GET', 'POST'])
@login_required
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
    """
    try:
        app.logger.info("Inside try converttospeech")
        app.logger.info("request received is %s" % request.form)

        wikiLinkToBeParsed = request.form['textforspeech']
        parsedUrl = urlparse(str(wikiLinkToBeParsed))
        app.logger.info("parsedUrl is : %s" % parsedUrl)
        if parsedUrl.netloc != 'en.wikipedia.org' or parsedUrl.scheme != 'https':

            msg = "Pass a valid wikipedia url, for e.g :  https://en.wikipedia.org/wiki/Anarchy"
            return jsonify({'txt': msg, 'mediaLocation': ''})
        else:
            path = parsedUrl.path
            fragment = parsedUrl.fragment
            combinedPath = path + "#" + fragment
            app.logger.info("Path and fragment are %s and %s" % (path, fragment))
            articleLocation = (AllWikiLinks.query.filter_by(wikilink=combinedPath).first()).location
            app.logger.info("Article location value is : %s" % articleLocation)
            if articleLocation is not None:
                mediaLocation = textToSpeech(path, fragment)
            else:
                articleFrag = getWikipediaArticleFragment(path, fragment)
                mediaLocation = textToSpeech(articleFrag, path, fragment)
            return jsonify({'mediaLocation': mediaLocation, 'txt': 'Congrats !'})
    except Exception as e:
        app.logger.info("error in get wiki : %s" % e)
        return str(e)


def addToUsersWikiLinks(combinedPath, username):
    try:
        user = User.query.filter_by(username=username).first()
        userWikiLinks = user.wikiLinks
        app.logger.info(str(combinedPath) not in userWikiLinks)
        if (str(combinedPath) not in userWikiLinks) or (userWikiLinks is None):
            user.wikiLinks += ' ' + str(combinedPath)
            app.logger.info("username is %s : links are %s" % (username, user.wikiLinks))
            db.session.commit()
        else:
            app.logger.info('something went wrong')

    except Exception as e:
        app.logger.info("error in addToUsersWikiLinks : %s" % e)
        return str(e)


def getWikipediaArticleFragment(articleName, fragment):
    try:
        article = WikipediaArticles.query.filter_by(articleName=articleName).first()
        app.logger.info("article is : %s" % article)
        if article is not None:
            articleFrag = json.loads(article.articleDict)[str(fragment)]
            return articleFrag

        wikiUrl = 'https://en.wikipedia.org' + articleName
        app.logger.info("wikipedia url is : %s" % wikiUrl)
        parsedArticle = WikipediaParser(wikiUrl)
        parsedArticle.instantiate()
        articleDict = parsedArticle.wikiDict
        jsonifiedArticle = json.dumps(articleDict)
        newWikiArticle = WikipediaArticles(articleName=articleName, articleDict=jsonifiedArticle)
        db.session.add(newWikiArticle)
        db.session.commit()
        app.logger.info("Commit successful")

        app.logger.info("Checking if article got commited :  %s" %
                        (WikipediaArticles.query.filter_by(articleName=articleName).first()).articleDict)
        return articleDict[fragment]
    except Exception as e:
        app.logger.info("error in get wiki : %s" % e)
        return str(e)


def textToSpeech(path, fragment, article=""):
    try:
        combinedPath = path + "#" + fragment
        article = (AllWikiLinks.query.filter_by(wikiLink=combinedPath).first())

        if article.location is None:
            app.logger.info("articleLocation is : %s" % article.location)
            mediaLocation = GoogleTextToSpeech(article, combinedPath)
            newWikiLinkWithFragment = AllWikiLinks(wikiLink=combinedPath, location=mediaLocation, text=article)
            db.session.add(newWikiLinkWithFragment)
            db.session.commit()
            return mediaLocation

        media = AllWikiLinks.query.filter_by(wikiLink=combinedPath).first()
        return media.location

    except Exception as e:
        app.logger.info("error in get wiki : %s" % e)
        return str(e)


def convertToSpeech():
    """ Convert the passed query result to audio files. this method will return the audio file
        for requested url.

        First I was thinking of adding some computation related to user but I think 1 method should
        do 1 job only.

        How ?
        I expect the query to be like : https://en.wikipedia.org/wiki/Anarchy#Description
        When this query is parsed by urlparse we get :
            ParseResult(scheme='https', netloc='en.wikipedia.org', path='/wiki/Anarchy',
                        params='', query='', fragment='Description')

        From this parsed result we can now get the website address and also the
        wikipedia section( fragment in ParseResult) in which the user is interested in.

    """

    try:
        app.logger.info("Inside try converttospeech")
        app.logger.info("request received is %s" % request.form)

        wikiLinkToBeParsed = request.form['textforspeech']

        app.logger.info("wikiLinkToBeParsed is : %s" % type(wikiLinkToBeParsed))

        parsedUrl = urlparse(str(wikiLinkToBeParsed))

        app.logger.info(parsedUrl)
        flash(wikiLinkToBeParsed)
        app.logger.info("user passed this link : %s " % wikiLinkToBeParsed)

        if parsedUrl.netloc != 'en.wikipedia.org' or parsedUrl.scheme != 'https':
            msg = "Pass a valid wikipedia url, for e.g :  https://en.wikipedia.org/wiki/Anarchy"
            return jsonify({'txt': msg, 'mediaLocation': ''})
        else:
            # path means the article user wants to convert
            path = parsedUrl.path
            fragment = parsedUrl.fragment
            combinedPath = path + '#' + fragment

            articleLocation = (AllWikiLinks.query.filter_by(wikilink=combinedPath).first()).location

            if articleLocation is None:
                # TODO :
                #  convert to audio,
                #  return saved location
                #  update location and article in db
                article = (AllWikiLinks.query.filter_by(wikilink=combinedPath).first()).text
                mediaLocation = GoogleTextToSpeech(article, combinedPath)
                wikiLink = AllWikiLinks.query.filter_by(wikiLink=combinedPath)
                wikiLink.location = mediaLocation
                db.session.commit()


            else:
                mediaLocation = AllWikiLinks.query.filter_by(wikiLink=combinedPath).first()
            return jsonify({'txt': '', 'mediaLocation': mediaLocation.location})
            # TODO : get the location of saved url, convert to audio, return


    except Exception as e:
        # flash(e)
        app.logger.info("error in converttospeech :  %s" % e)
        return str(e)


#
#         contentTitle = escape(contentTitle)
#         url = request.form['wikiLink']
#         parsedUrl = urlparse(url)
#         # If its url to some other website
#         if parsedUrl.netloc != 'en.wikipedia.org' or parsedUrl.scheme not in ['http', 'https']:
#             return "website should be en.wikipedia.org"
#         elif parsedUrl.path == 'wiki/Main_Page':
#             return "Search for some other path"
#         else:

#             wikipediaLink = parsedUrl.scheme + parsedUrl.netloc + parsedUrl.path
#             if contentTitle is not None:
#                 # TODO: Query db for wikipediaPage if not present save to db with key as wikipediaLink
#                 # Get users username
#                 userId = c.execute("SELECT id  FROM users WHERE username = (%s)",
#                                    (thwart(request.form["username"]),))

#                 # Get all the wikilinks in user's wikilinks
#                 userLinks = c.execute("SELECT wikiLinks FROM userWikiLinks WHERE userId=(%s)",
#                                       (thwart(userId),))

#                 # Check if the link user asked for is in their list ?
#                 if wikipediaLink in userLinks:
#                     # TODO : get location where the link audio files are located in server
#                     return
#                 else:
#                     # TODO : get parsed wikipedia page, save that
#                     return

#                 wikipediaPage = WikipediaParser(wikipediaLink)
#                 introText = wikipediaPage['Intro']


#                 GoogleTextToSpeech(url)
#             else:
#                 # TODO : Query db for the Link and get the necessary section

#                 return

#                 # return jsonify({'txt': txt})
#                 # return jsonify({'txt':"<p>Hello Friend</p>"})
#     except Exception as e:
#         return str(e)

# # #
# # # @app.route('/return-files/')
# # # def returnFiles():
# # #     try:
# # #         return send_file('/media/icon.svg')
# # #     except Exception as e:
# # #         return str(e)
# # #
# # #
# # # @app.route('/get-file/')
# # # def getFile():
# # #     return send_file('/media/exam.mp3')
# # #
# # #
@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('homepage'))


# # #
# # #
# ParseResult(scheme='https', netloc='en.wikipedia.org', path='/wiki/Anarchy',
#                         params='', query='', fragment='Description')
# Testing for db creating
def createTables():
    db.create_all()


def drop():
    db.drop_all()


def update(username):
    user = User.query.filter_by(username=username).first()
    user.wikiLinks = ' '
    db.session.commit()


def splitCheck(username):
    user = User.query.filter_by(username=username).first()
    uw = user.wikiLinks
    print(uw.split())


if __name__ == '__main__':
    with app.app_context():
        # app.run(host="0.0.0.0", debug=True)
        # createTables()
        # addToUsersWikiLinks('/wiki/Anarchy#Etymology', 'qwer')
        # drop()
        # update('qwer')
        # splitCheck('qwer')
        article = getWikipediaArticleFragment('/wiki/Anarchy', '')
        print(article)
        print(textToSpeech('/wiki/Anarchy', '', article))
