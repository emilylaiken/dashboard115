from __future__ import print_function
import os
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session
import sys
from werkzeug import secure_filename
from threading import Thread
import chartmaker
import graph_helpers as ghelpers
import download_helpers as dhelpers
import upload_helpers as uhelpers
import helpers


#App configurations--set folders and allowed extensions for file uploads
app = Flask(__name__)
app.secret_key = 'secret key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SESSION_TYPE'] = 'filesystem'
    
############ LOGIN PAGES ###########
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method=="POST":
        # Extract correct username and password--if none have been set, default is "cdc" and "cdc"
        username, pwd = helpers.getCorrectLogin()
        if request.form.get('username') == None or request.form.get('pwd') == None:
            return render_template('index.html')
        if request.form.get('username') != username or request.form.get('pwd') != pwd:
            return render_template('wronglogin.html')
        else:
            session['logged_in'] = True
            return redirect('/overview')
    else:
        return render_template('index.html')

@app.route("/changelogin", methods=["GET", "POST"])
def changelogin():
    if request.method=="POST":
        username, pwd = helpers.getCorrectLogin()
        if request.form.get('oldusername') == None or request.form.get('oldpwd') == None or request.form.get('newusername') == None or request.form.get('newpwd') == None:
            return render_template('changelogin.html')
        elif request.form.get('oldusername') != username or request.form.get('oldpwd') != pwd:
            return render_template('wronglogin.html')
        else:
            con = sqlite3.connect("logs115.db")
            cur = con.cursor()
            cur.execute("DELETE FROM login")
            cur.executemany("INSERT INTO login (username, pwd) VALUES (?, ?);", [(request.form.get('newusername'), request.form.get('newpwd'))])
            con.commit()
            con.close()
            return redirect('/')
    else:
        return render_template('changelogin.html')


########## DASHBOARD PAGES: OVERVIEW, PUBLIC, AND HC REPORTS ##########
@app.route('/overview', methods=["GET"])
def overview():  
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.argsMissing():
        return redirect(helpers.redirectWithArgs('/overview'))
    # Parse duration and dates from URL parameters
    duration_string, title_addon = ghelpers.parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    # Create figures
    charts, totals, averages = [], [], []
    charts, totals, averages = ghelpers.addFigure(condition_string = "call_id != ''", table='all', title="Calls to Entire Hotline by Day", charts=charts, totals=totals, averages=averages)
    charts, totals, averages = ghelpers.addCompletedAttemptedChart(charts, totals, averages)
    return render_template("overview.html", figures = zip(charts, totals, averages))

@app.route("/public", methods=["GET", "POST"])
def public():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.argsMissing():
        return redirect(helpers.redirectWithArgs('/public'))
    # Create figures
    charts, totals, averages = [], [], []
    charts, totals, averages = ghelpers.addFigure(condition_string=" type='public' ", table='all', title="Calls to Public Hotline by Day", charts=charts, totals=totals, averages=averages)
    charts, totals, averages = ghelpers.addDiseaseFigures(["h5n1", "mers", "zika"], charts, totals, averages)
    charts, totals, averages = ghelpers.addFigure(condition_string="public_report_confirmation='0'", table="public", title="Public Disease Reports by Day", charts=charts, totals=totals, averages=averages)
    charts, totals, averages = ghelpers.addFigure(condition_string="hotline_menu='3'", table="public", title="Calls Requesting Additional Information by Day", charts=charts, totals=totals, averages=averages)
    charts, totals, averages = ghelpers.addFigure(condition_string="hotline_menu='4'", table="public", title="Calls Requesting Ambulance Information by Day", charts=charts, totals=totals, averages=averages)
    return render_template("public.html", figures=zip(charts, totals, averages))

@app.route("/hcreports", methods=["GET", "POST"])
def hcreports():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.timeArgsMissing():
        return redirect(helpers.redirectWithArgs('/hcreports'))
    # Create figures
    charts = []
    charts.append(ghelpers.addOnTimeChart('calls JOIN hc_reports ON calls.call_id = hc_reports.call_id', "HC Reports by Week (On-Time vs Late)"))
    diseases = ['diarrhea', 'fever', 'flaccid', 'respiratory', 'dengue', 'meningitis', 'jaundice', 'diphteria', 'rabies', 'neonatal']
    charts.append(ghelpers.addHCReportChart([disease + '_cases' for disease in diseases], "Reports of Disease Cases by Week"))
    charts.append(ghelpers.addHCReportChart([disease + '_deaths' for disease in diseases], "Reports of Disease Deaths by Week"))
    return render_template("hcreports.html", charts=charts)

########## DOWNLOADABLE REPORTS ##########
@app.route("/download")
def download():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.timeArgsMissing():
        return redirect(helpers.redirectWithArgs('/download'))
    # Parse dates from URL parameters
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    return render_template("download.html", redirect_string = "/downloading?datestart=" + starting_date_string + "&dateend=" + ending_date_string)

@app.route("/downloading", methods=["GET", "POST"])
def downloading():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.timeArgsMissing():
        return redirect(helpers.redirectWithArgs('/downloading'))
    # Check for necessary elements from form
    if request.form['email'] == None or request.form['email'] == "":
        return render_template("downloadfail.html", message="Please enter an email address.")
    # Fork thread to send email with PDF report
    num_days = (datetime.datetime.strptime(request.args.get('dateend'), '%Y-%m-%d') - datetime.datetime.strptime(request.args.get('datestart'), '%Y-%m-%d')).days + 1
    th = Thread(target=dhelpers.genReport, args=(request.args.get('datestart'), request.args.get('dateend'), request.form['qualitative'], request.form['email'], url_for('downloaded'), num_days))
    th.start()
    return render_template("downloading.html")

@app.route("/downloaded", methods=["GET"])
def downloaded():
    # Load PDF file to send in email
    filetitle = request.args.get('filename') + ".pdf"
    return send_file(filetitle, attachment_filename=filetitle, as_attachment=True)
    

########## CSV UPLOAD ###########    
@app.route("/upload", methods=["GET", "POST"])
def upload():
    # Check for log-in 
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Use URL parameter for step to determine which step of upload process we are on
    if request.args.get('step') == None or request.args.get('step') == '1':
        return render_template("upload1.html")
    elif request.args.get('step') == '2':
        return render_template("upload2.html")
    elif request.args.get('step') == 'template':
        return send_file('static/call_logs_template.csv', as_attachment = True)
    else:
        return render_template("upload3.html")


@app.route("/dataload", methods=["GET", "POST"])
def dataload():
    # Check for log-in
    if not session.get('logged_in'):
       return redirect(url_for('index'))
    # Get file
    csv = request.files['log']
    # The file must be a CSV
    if csv and uhelpers.allowed_file(csv.filename):
        # Secure the file name so it doesn't have any illegal characters
        filename = secure_filename(csv.filename)
        csv.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Upload data from the saved file to the dashboard
        uploaded = uhelpers.loadData("uploads/" + filename)
        if uploaded[0] != 'N':
            return render_template("uploadfail.html", message=uploaded)
    else:
        return render_template("uploadfail.html", 'Unknown reason.')
    return render_template("uploadcomplete.html", message=uploaded)

# Run application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)