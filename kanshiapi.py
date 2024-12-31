from flask import Flask,jsonify,g,send_from_directory,request
import sqlite3
import datetime

app = Flask(__name__)

### Functions to deal with Database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("kanshi.db")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
### / Functions to deal with Database

@app.route('/api/filemonitors')
def filemonitors():
    cur = get_db().cursor()
    cur.execute("SELECT * from fileMonitors");
    fm = cur.fetchall()
    fm = list(map(lambda o: {"title":o[0], "bbpUrl":o[1], "company":o[2], "frequency":o[3], "procModule":o[4], "lastRun":o[5], "createdAt":o[6]}, fm))
    return jsonify(fm)

@app.route('/api/alerts')
def alerts():
    cur = get_db().cursor()
    if 'user' in request.args:
        cur.execute("SELECT * from alerts where calledBy=? AND state=\"claimed\"", (request.args['user'],));
    else:
        cur.execute("SELECT * from alerts where calledBy is NULL");
    fm = cur.fetchall()
    fm = list(map(lambda o: {"gitCommit":o[0], "bbpUrl":o[1], "company":o[2], "title":o[3], "jsFile":o[4], "regex":o[5], "createdAt":o[6], "severity":o[7], "state":o[8], "calledAt":o[9], "calledBy":o[10]}, fm))
    return jsonify(fm)

@app.route('/api/tables')
def tables():
    cur = get_db().cursor()
    cur.execute("SELECT calledBy from alerts where calledBy IS NOT NULL");
    fm = list(set(map(lambda e: e[0], cur.fetchall())))
    return jsonify(fm)


@app.route('/api/claim')
def claim():
    db = get_db()
    cur = db.cursor()
    if 'gitCommit' not in request.args:
        return jsonify({"error":"No gitCommit provided"})
    if 'user' not in request.args:
        return jsonify({"error":"No user provided"})
    cur.execute("UPDATE alerts SET calledAt=?, calledBy=?, state=\"claimed\" where gitCommit=?", (str(datetime.datetime.utcnow()), request.args['user'], request.args['gitCommit']))
    db.commit()
    return jsonify({"error":False, "message":"Alert successfully assigned to "+request.args['user']})

@app.route('/api/report')
def report():
    db = get_db()
    cur = db.cursor()
    if 'gitCommit' not in request.args:
        return jsonify({"error":"No gitCommit provided"})
    if 'user' not in request.args:
        return jsonify({"error":"No user provided"})
    if 'state' not in request.args:
        return jsonify({"error":"No state provided"})
    cur.execute("UPDATE alerts SET state=? WHERE gitCommit=?", (request.args['state'], request.args['gitCommit']))
    db.commit()
    return jsonify({"error":False, "message":"Alert successfully updated by "+request.args['user']})

@app.route('/<path:path>')
def home(path):
    return send_from_directory("./", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8083)
