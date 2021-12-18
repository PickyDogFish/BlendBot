from os import read
from os.path import isfile
from sqlite3 import connect
from apscheduler.triggers.cron import CronTrigger
import csv

DB_PATH = "./database.db"
cxn = connect(DB_PATH, check_same_thread=False)
cur = cxn.cursor()

def db_commit():
    cxn.commit()

def db_execute(command, *values):
    cur.execute(command, tuple(values))

def db_multiexec(command, valueset):
    cur.executemany(command, valueset)


users = open("users.csv", "r")
challengeTypes = open("challengeTypes.csv", "r")
themes = open("themes.csv", "r")
submissions = open("submission.csv", "r")
votes = open("votes.csv", "r")
challenges = open("challenge.csv", "r")
currentChallenge = open("currentChallenge.csv", "r")


def copyToNew(file, newTableName):
    reader = csv.reader(file)
    first = True
    columns = ""
    for row in reader:
        if first:
            columns = "{0}".format(tuple(row))
            print(columns)
            first = False
        else:
            print("{0}".format(tuple(row)))
            db_execute("INSERT OR IGNORE INTO " + newTableName +" " + columns + " VALUES " + "{0}".format(tuple(row)))
    db_commit()

copyToNew(users, "users")
print("copied users")
copyToNew(themes, "themes")
print("copied themes")
copyToNew(challenges, "challenges")
print("copied challenges")
copyToNew(submissions, "submissions")
print("copied submissions")
copyToNew(currentChallenge, "currentChallenge")
print("copied currentChallenge")
copyToNew(votes, "votes")
print("copied votes")