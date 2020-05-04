import csv
import os

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

def main():
    print("Importing book-list for Project1")
    count = 0

    engine = create_engine(os.getenv("DATABASE_URL"))
    db = scoped_session(sessionmaker(bind=engine))

    meta = MetaData()

    print("- dropping tables")
    db.execute("DROP TABLE books")
    db.execute("DROP TABLE reviews")
    db.execute("DROP TABLE userlogin")

    print("- creating tables")
    db.execute("CREATE TABLE books (isbn varchar(255) primary key, title varchar(255), author varchar(255), year integer)")
    db.execute("CREATE TABLE reviews(isbn varchar(255), usernr integer, review varchar(255), rating integer)")
    db.execute("CREATE TABLE userlogin (usernr serial primary key, username varchar(255), userpassword varchar(255))")

    review   = "Default review text"
    rating   = 3
    defid    = 0
    defname  = "Default User"
    defpwd   = "password"

    print("- Insert default user 1")
    db.execute("INSERT INTO userlogin (username, userpassword)  VALUES ( :n, :p)",
            { "n": defname, "p": defpwd})

    print("- Insert default user 2")
    db.execute("INSERT INTO userlogin (username, userpassword)  VALUES ( :n, :p)",
            { "n": defname + "2", "p": defpwd})
    print("- reading CSV-file")
    f = open("books.csv")
    reader = csv.reader(f)

    for isbn, title, author, year in reader:
        if isbn != "isbn":
            db.execute("INSERT INTO books   (isbn, title, author, year) VALUES (:i, :t, :a, :y)",
            {"i": isbn, "t": title, "a": author, "y": year})

            # Inserting dummy reviews only for every 10 numbers
            # Necessary to circumvent the limit of 10k rows in the basic db-plan
            if (count % 10) == 0:
                if (count % 2) == 0:
                    defid = 1
                else
                    defid = 2;
                db.execute("INSERT INTO reviews (isbn, usernr, review, rating)  VALUES (:i, :u, :t, :r)",
                {"i": isbn, "u": defid, "t": review, "r": rating})
            count += 1


    print("- books added: ", count)
    db.commit()
    db.close()

if __name__ == "__main__":
    main()
