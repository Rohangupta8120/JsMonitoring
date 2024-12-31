#! /usr/bin/env python3
import importlib
import argparse
import datetime
import requests
import sqlite3
import json
import sys
import os
sys.path.insert(1, os.path.abspath(os.path.expanduser(os.path.expandvars("./procurementModules/"))))


dbExists = os.path.exists('./kanshi.db')
db = sqlite3.connect("./kanshi.db")
if not dbExists:
    print("Building DB")
    db.cursor().executescript(open("schema.sql").read())
    db.commit()

def addFileMonitor(title, bbpUrl, company, frequency, procMod):
    assert bbpUrl.startswith("https://"), "Bug Bounty URL should point to the target program."
    assert frequency.isdigit(), "Frequency should be how often this file should be checked in on."
    assert os.path.exists(procMod), "Cannot locate the procurement module."
    cur = db.cursor()
    cur.execute("INSERT INTO fileMonitors values(?,?,?,?,?,?,?)",
            (title, bbpUrl, company, frequency, procMod, datetime.datetime(1996, 8,16, 0, 0), datetime.datetime.utcnow()))
    db.commit()
    print("fileMonitor successfully added!")


def runKanshi():
    cur = db.cursor()
    cur.execute("SELECT * from fileMonitors")
    r = cur.fetchall()
    for fm in r:
        if (datetime.datetime.utcnow()-datetime.timedelta(minutes=fm[3])) > datetime.datetime.strptime(fm[5], "%Y-%m-%d %H:%M:%S") or args.o:
            print("Launching: "+fm[0])
            fileMonitor = importlib.import_module(fm[4].split("/")[-1][:-3])
            alerts = fileMonitor.run(fm[1], fm[2])
            for alert in alerts:
                cur.execute("INSERT INTO alerts VALUES(?,?,?,?,?,?,?,?,?,?,?)", alert)
                db.commit()
            for alert in alerts:
                r = requests.post(fileMonitor.discordWebhook,
                        data=json.dumps({"content":"["+fm[0]+"] "+alert[3]}), headers={"Content-Type":"application/json"})
            cur.execute("UPDATE fileMonitors SET lastRun=? WHERE title=?", (datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),fm[0]))
            db.commit()

def deleteFileMonitor(title):
    cur = db.cursor()
    cur.execute("DELETE FROM fileMonitors WHERE title = ?", (title,))
    if cur.rowcount == 0:
        print(f"No file monitor found with title: {title}")
    else:
        print(f"Successfully deleted file monitor: {title}")
    db.commit()

def listFileMonitors():
    cur = db.cursor()
    cur.execute("SELECT title, bbpUrl, company, frequency, lastRun FROM fileMonitors")
    monitors = cur.fetchall()
    if not monitors:
        print("No file monitors found")
        return
    
    print("\nCurrent File Monitors:")
    print("-" * 80)
    for monitor in monitors:
        print(f"Title: {monitor[0]}")
        print(f"URL: {monitor[1]}")
        print(f"Company: {monitor[2]}")
        print(f"Frequency: {monitor[3]} minutes")
        print(f"Last Run: {monitor[4]}")
        print("-" * 80)

parser = argparse.ArgumentParser(description='Kanshi Command Line Interface')
subparsers = parser.add_subparsers(help="Choose which command to use", dest="command")

#Add Subcommand
addParser = subparsers.add_parser('add')
addParser.add_argument("-t", required=True, help="Title")
addParser.add_argument("-b", required=True, help="Bug Bounty Program URL")
addParser.add_argument("-c", required=True, help="Company Name")
addParser.add_argument("-f", required=True, help="Frequency in minutes")
addParser.add_argument("-p", required=True, help="Path to Procurement Module")
#

#Delete Subcommand
deleteParser = subparsers.add_parser('delete')
deleteParser.add_argument("-t", required=True, help="Title of monitor to delete")

#List Subcommand
listParser = subparsers.add_parser('list')

#Run Subcommand
runParser = subparsers.add_parser('run')
runParser.add_argument("-o", required=False, help="Override time", action='store_true')
#

args = parser.parse_args()
if args.command == "add":
    addFileMonitor(args.t, args.b, args.c, args.f, args.p)
elif args.command == "run":
    runKanshi()
elif args.command == "delete":
    deleteFileMonitor(args.t)
elif args.command == "list":
    listFileMonitors()
