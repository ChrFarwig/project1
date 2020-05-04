import os
import sys
import json
from flask import Flask, session,render_template, request, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import requests

app = Flask(__name__)

goodreadkey="2FG4DpgcCXQwwDcakNjeQ"
database_url="postgres://ohitlixfprqpax:b151b52e31f041f65efc12e5a9ae20a80c8212fdc7e2f3998252735a6f4883f9@ec2-79-125-26-232.eu-west-1.compute.amazonaws.com:5432/d46ma3q8bqmf27"

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Initialize variables
sAuthor  = ""
sTitle   = ""
pISBN    = ""

pTitle  = "%"
pAuthor = "%"
pISBN   = "%"

pUserid = 0


@app.route("/")
def index():
        session["user_id"] = 0
        session["user_name"] = ""
        u = db.execute("SELECT * FROM userlogin").fetchall()
        return render_template("login.html", msg = "Please log in", users=u)

@app.route("/createuser", methods=["POST","GET"])
def createuser():

       pUsername = request.form.get("sUsername")
       pUserpassword = request.form.get("sPassword")
       pConfirmpassword = request.form.get("sConfirmPassword")

       try:

           if db.execute("SELECT * FROM userlogin WHERE username = :sUsername", {"sUsername": pUsername}).rowcount > 0:
              return render_template("error.html", page="Create User", errorcode="User [" + pUsername + "] already exists")

           if pUserpassword != pConfirmpassword or pUserpassword == "":
              return render_template("error.html", page="Create User", errorcode="Passwords for creating user do not match")

           if pUsername == "":
              return render_template("error.html", page="Create User", errorcode="Username for creating user necessary")

           db.execute("INSERT INTO userlogin (usernr, username, userpassword) VALUES (:nr, :na, :pw)", {"nr": 100, "na": pUsername, "pw": pUserpassword})
           db.commit
           u = db.execute("SELECT * FROM userlogin").fetchall()
           return render_template("login.html", msg="New user " + pUsername+ "(password " + pUserpassword + ") created", users=u)

       except:
           return render_template("error.html", page="Create User", errorcode="Error when inserting user")

@app.route("/login", methods=["POST"])
def login():
        pTitle  = "%"
        pAuthor = "%"
        pISBN   = "%"

        pUsername = request.form.get("sUsername")
        pUserpassword = request.form.get("sPassword")
        pUserid = 0

        if db.execute("SELECT * FROM userlogin WHERE username = :sUsername AND userpassword = :sUserpassword", {"sUsername": pUsername, "sUserpassword": pUserpassword}).rowcount == 0:
            return render_template("error.html", page="Create User", errorcode="User [" + pUsername + "], Password [" + pUserpassword + "] cannot be found")

        x = db.execute("SELECT usernr FROM userlogin WHERE username = :sUsername AND userpassword = :sUserpassword", {"sUsername": pUsername, "sUserpassword": pUserpassword}).fetchone()

#        return render_template("error.html", page="login", errorcode=x[0])
        pUserid = int(x[0])

        session["user_id"]   = pUserid
        session["user_name"] = pUsername

        books = db.execute("SELECT * FROM books where author like :sAuthor AND title like :sTitle AND isbn like :sISBN", {"sAuthor": pAuthor, "sTitle": pTitle, "sISBN": pISBN}).fetchall()
        return render_template("booklist_select.html", selection="Search", books=books, sAuthor=pAuthor, sTitle=pTitle, sISBN=pISBN, userid=pUserid)


@app.route("/book_search", methods=["POST"])
def bookselect():

        pTitle  = request.form.get("sTitle")
        pAuthor = request.form.get("sAuthor")
        pISBN   = request.form.get("sISBN")

        if len(pTitle) == 0:
            pTitle = "%"
        if len(pAuthor) == 0:
            pAuthor = "%"
        if len(pISBN) == 0:
            pISBN = "%"

        books = db.execute("SELECT * FROM books where author like :sAuthor AND title like :sTitle AND isbn like :sISBN", {"sAuthor": pAuthor, "sTitle": pTitle, "sISBN": pISBN}).fetchall()
        return render_template("booklist_select.html", selection="Search", books=books, sAuthor=pAuthor, sTitle=pTitle, sISBN=pISBN, userid= session["user_id"])

@app.route("/book_listing", methods=["GET"])
def bookslisting():

        books = db.execute("SELECT * FROM books where author like :sAuthor AND title like :sTitle AND isbn like :sISBN", {"sAuthor": pAuthor, "sTitle": pTitle, "sISBN": pISBN}).fetchall()
        return render_template("booklist_select.html", selection="Search", books=books, sAuthor=pAuthor, sTitle=pTitle, sISBN=pISBN, userid= session["user_id"])

@app.route("/book_review/<string:ISBN>")
def review(ISBN):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodreadkey, "isbns": ISBN})
    data = res.json()

    bratings = data["books"][0]["ratings_count"]
    baverage = data["books"][0]["average_rating"]

    books    = db.execute("SELECT * FROM books where ISBN = :sISBN", {"sISBN": ISBN}).fetchall()
    reviews  = db.execute("SELECT * FROM reviews WHERE ISBN = :sISBN", {"sISBN": ISBN}).fetchall()

    return render_template("review.html", books=books, total=data, ratings=bratings, average=baverage, currentreviews=reviews, userid=session["user_id"])

@app.route("/api/<string:ISBN>")
def API(ISBN):

    if db.execute("SELECT * FROM books where ISBN = :sISBN", {"sISBN": ISBN}).rowcount == 0:
       abort(404)

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodreadkey, "isbns": ISBN})
    data = res.json()

    bratings = data["books"][0]["ratings_count"]
    baverage = data["books"][0]["average_rating"]

    books    = db.execute("SELECT * FROM books where ISBN = :sISBN", {"sISBN": ISBN}).fetchall()

    for book in books:
        returndata = {
            'title': book.title,
            'author': book.author,
            'year': book.year,
            'isbn': ISBN,
            'review_count': bratings,
            'average_score': baverage
            }

    return json.dumps(returndata )

@app.route("/review_submit", methods=["POST"])
def reviewsubmit():
    pISBN   = request.form.get("sISBN")
    pReview = request.form.get("review")
    pRating = request.form.get("sRating")

    if db.execute("SELECT * FROM reviews WHERE ISBN = :sISBN and Usernr = :sUsernr", {"sISBN": pISBN, "sUsernr": session["user_id"]}).rowcount > 0:
       eCode = "[User: " + str(UserID) + "] [isdn: " + pISBN + "] [review: " + pReview + "] [rating: " + str(pRating) + "] " + " - this user has already reviewed the book"
       return render_template("error.html", page="Reviewsubmit", errorcode= eCode)

    db.execute("INSERT INTO reviews (isbn, usernr, review, rating)  VALUES (:i, :u, :t, :r)",
            {"i": pISBN, "u": session["user_id"], "t": pReview, "r": pRating})

    db.commit()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": goodreadkey, "isbns": pISBN})
    data = res.json()

    bratings = data["books"][0]["ratings_count"]
    baverage = data["books"][0]["average_rating"]

    books = db.execute("SELECT * FROM books where ISBN = :sISBN", {"sISBN": pISBN}).fetchall()
    reviews = db.execute("SELECT * FROM reviews WHERE ISBN = :sISBN", {"sISBN": pISBN}).fetchall()

    return render_template("review.html", books=books, total=data, ratings=bratings, average=baverage, currentreviews=reviews)
