from __future__ import print_function
import os
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session, Response, json
import sys
from werkzeug import secure_filename
from threading import Thread
import graph_helpers as ghelpers
import download_helpers as dhelpers
import upload_helpers as uhelpers
import settings_helpers as shelpers
import helpers
import calendar
import datetime
import collections
import time
import requests
import urllib
from passlib.hash import pbkdf2_sha256
import base64
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import psycopg2


#App configurations--set folders and allowed extensions for file uploads
app = Flask(__name__)
app.secret_key = 'secret key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SESSION_TYPE'] = 'filesystem'

############ AUTOMATIC NOTIFICATIONS ############
def sendNotification():
    thresholdcases = -1
    thresholddeaths = -1
    con = sqlite3.connect('logs115.db')
    cur = con.cursor()
    week_id = helpers.getWeekId(datetime.datetime.now())
    _, _, hc_diseases, _ = helpers.getDiseases()
    totalcases = 0
    for disease in [d for d in hc_diseases if "case" in d]:
        cur.execute("SELECT SUM(" + disease + ") FROM hc_reports WHERE week_id='" + week_id + "'") 
        diseasecases = cur.fetchall()
        if diseasecases[0][0] is not None:
            totalcases = totalcases + int(diseasecases[0][0])
    totaldeaths = 0
    for disease in [d for d in hc_diseases if "death" in d]:
        cur.execute("SELECT SUM(" + disease + ") FROM hc_reports WHERE week_id='" + week_id + "'") 
        diseasedeaths = cur.fetchall()
        if diseasedeaths[0][0] is not None:
            totaldeaths = totaldeaths + int(diseasedeaths[0][0])
    if totalcases > thresholdcases or totaldeaths > thresholddeaths:
        body_text = "There were an exceptional number of cases and/or deaths reported on the 115 holine this week (the week of " + week_id + "). " + str(totalcases) + " cases were reported and " + str(totaldeaths) + " deaths were reported. The threshold number of cases is " + str(thresholdcases) + " and the threshold number of deaths is " + str(thresholddeaths) + ". Visit the 115 hotline dashboard to change these thresholds."
        dhelpers.sendEmail("115 Hotline - Exceptional Number of Cases/Deaths Reported", body_text, None, "emily.aiken@instedd.org", None, None)

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(sendNotification, 'cron', day_of_week='thu', hour=7) #Assuming GMT time zone
#Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


############ LOGIN PAGES ###########
@app.route("/", methods=["GET", "POST"])
def index():
    helpers.cleanUp()
    if request.method=="POST":
        # Extract correct username and password--if none have been set, default is "cdc" and "cdc"
        username, pwd = helpers.getCorrectLogin()
        inputed_username = request.form.get('username')
        inputed_pwd = request.form.get('pwd')
        if inputed_username == None or inputed_pwd == None:
            return render_template('index.html')
        elif (pbkdf2_sha256.verify(inputed_username, username) == True) and (pbkdf2_sha256.verify(inputed_pwd, pwd) == True):
            session['logged_in'] = True
            return redirect('/overview')
        else:
            return render_template('wronglogin.html')
    else:
        return render_template('index.html')

@app.route("/changelogin", methods=["GET", "POST"])
def changelogin():
    if request.method=="POST":
        username, pwd = helpers.getCorrectLogin()
        oldusername = request.form.get('oldusername')
        oldpwd = request.form.get('oldpwd')
        newusername = request.form.get('newusername')
        newpwd = request.form.get('newpwd')
        if oldusername == None or oldpwd == None or newusername == None or newpwd == None:
            return render_template('changelogin.html')
        elif (pbkdf2_sha256.verify(oldusername, username) == True) and (pbkdf2_sha256.verify(oldpwd, pwd) == True):
            helpers.editLogin(pbkdf2_sha256.hash(newusername), pbkdf2_sha256.hash(newpwd))
            return redirect('/')
        else:
            return render_template('wronglogin.html')
    else:
        return render_template('changelogin.html')

########## DASHBOARD PAGES: OVERVIEW, PUBLIC, AND HC REPORTS ##########
@app.route('/overview', methods=["GET", "POST"])
def overview():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.argsMissing():
        return redirect(helpers.redirectWithArgs('/overview'))
    # Open database
    #uhelpers.loadRandom("2017-09-01", "2017-12-01")
    con = sqlite3.connect('logs115.db')
    cur = con.cursor()
    # Parse duration and dates from URL parameters
    duration_string, title_addon = ghelpers.parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    figures = []
    # OVERVIEW CHARTS
    figures.append(ghelpers.publicLineChart(cur, 'all', ["call_id != ''"], starting_date_string, ending_date_string, duration_string, ["Calls to Entire Hotline"], "Calls to Entire Hotline by Day", False, "publicallcalls"))
    figures.append(ghelpers.hotlineBreakdown(cur, 'all', ["Public Callers", "HC Workers"], [" type='public' ", " type='hc_worker' "], starting_date_string, ending_date_string, duration_string, "Hotline Breakdown", "hotlinebreakdown"))
    figures.append(ghelpers.statusChart(cur,"public", starting_date_string, ending_date_string, duration_string, "statuspublic"))
    figures.append(ghelpers.statusChart(cur,"healthcare workers", starting_date_string, ending_date_string, duration_string, "statushc"))
    con.close()
    return render_template("dashboardpage.html", figures=figures, ap = 'overviewlink')

@app.route('/public', methods=["GET", "POST"])
def public():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.argsMissing():
        return redirect(helpers.redirectWithArgs('/public'))
    # Open database
    con = sqlite3.connect('logs115.db')
    cur = con.cursor()
    # Parse duration and dates from URL parameters
    duration_string, title_addon = ghelpers.parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    figures = []
    # PUBLIC CHARTS
    _, public_diseases, _, _ = helpers.getDiseases()
    figures.append(ghelpers.publicLineChart(cur, 'all', [" type='public' "], starting_date_string, ending_date_string, duration_string, ["Calls to Public Hotline"], "Calls to Public Hotline by Day", False, "publiccalls"))
    figures.append(ghelpers.hotlineBreakdown(cur, 'public', ["Visit " + disease + " Information" for disease in public_diseases] + ['Make a Report', 'Request More Information', 'Request Ambulance Information'], [disease + "_menu IS NOT NULL" for disease in public_diseases] + ["hotline_menu='2'", "hotline_menu='3'", "hotline_menu='4'"], starting_date_string, ending_date_string, duration_string, "Public Hotline Breakdown", "publicbreakdown"))
    for disease in sorted(public_diseases):
        figures.append(ghelpers.publicLineChart(cur, 'public', [disease + "_menu IS NOT NULL", disease + "_menu=1", disease + "_menu=2"], starting_date_string, ending_date_string, duration_string, ["Visit Menu", "Listen to Overview Info", "Listen to Prevention Info"], "Calls to " + disease.title() + " Menu", True, "public" + disease))
    figures.append(ghelpers.publicLineChart(cur, 'public', ["hotline_menu='2'"], starting_date_string, ending_date_string, duration_string, ["Public Disease Reports"], "Public Disease Reports by Day", False, "publicreports"))
    figures.append(ghelpers.publicLineChart(cur, 'public', ["hotline_menu='3'"], starting_date_string, ending_date_string, duration_string, ["Calls Requesting More Information"], "Calls Requesting More Information by Day", False, "publicmoreinfo"))
    figures.append(ghelpers.publicLineChart(cur, 'public', ["hotline_menu='4'"], starting_date_string, ending_date_string, duration_string, ["Calls Requesting Ambulance Information"], "Calls Requesting Ambulance Information by Day", False, "publicambulanceinfo"))
    # Close database
    con.close()
    return render_template("dashboardpage.html", figures=figures, ap = 'publiclink')

@app.route('/hcreports', methods=["GET", "POST"])
def hcreports():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
   # Check for all necessary parameters
    if helpers.timeArgsMissing():
        return redirect(helpers.redirectWithArgs('/hcreports'))
    # Open database
    con = sqlite3.connect('logs115.db')
    cur = con.cursor()
    # Parse duration and dates from URL parameters
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    figures = []
    # HC REPORT CHARTS
    figures.append(ghelpers.hcOntimeChart(cur, starting_date_string, ending_date_string, "ontime"))
    for addon in ['_case', '_death']:
        figures.append(ghelpers.hcDiseaseChart(cur, starting_date_string, ending_date_string, addon, "hc" + addon[1:]))
    # Close database
    con.close()
    return render_template("dashboardpage.html", figures=figures, ap = 'hcreportslink')


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
    _, public_diseases, _, hc_diseases = helpers.getDiseases()
    charts_with_ids = []
    charts = helpers.getCharts()
    for i in range (0, len(charts)):
        chart = charts[i]
        charts_with_ids.append((str(i).zfill(2) + chart[0], chart[1], chart[2]))
    return render_template("download.html", redirect_string = "/downloading?datestart=" + starting_date_string + "&dateend=" + ending_date_string, figureoptions=charts_with_ids)

@app.route("/downloading", methods=["GET", "POST"])
def downloading():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Check for all necessary parameters
    if helpers.timeArgsMissing():
        return redirect(helpers.redirectWithArgs('/downloading'))
    if request.form['submit'] == 'Email Report':
        # Check for necessary elements from form
        if request.form['email'] == None or request.form['email'] == "":
            return render_template("downloadfail.html", message="Please enter an email address.")
        try:
            emails = request.form['email'].split(",")
            ccs = request.form['cc'].split(",")
            bccs = request.form['bcc'].split(",")
        except:
            return render_template("downloadfail.html", message="Please enter a single email or a comma-seperated list of emails for the recipient, cc, and bcc fields.")
        # Fork thread to send email with PDF report
        th = Thread(target=dhelpers.genReport, args=(request.args.get('datestart'), request.args.get('dateend'), request.form['qualitative'], request.form['email'], request.form['cc'], request.form['bcc'], [key for key in request.form if not key in ["qualitative", "email", "cc", "bcc", "submit"]], 'email'))
        th.start()
        return render_template("downloading.html")
    elif request.form['submit'] == 'Download Now':
        filetitle = dhelpers.genReport(request.args.get('datestart'), request.args.get('dateend'), request.form['qualitative'], None, None, None, [key for key in request.form if not key in ["qualitative", "email", "cc", "bcc", "submit"]], 'download')
        return redirect('/downloaded?filename=' + filetitle)
    else:
        return render_template("downloadfail.html", message="")

@app.route("/downloaded", methods=["GET"])
def downloaded():
    # Load PDF file to send in email
    filetitle = request.args.get('filename')
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

@app.route("/callback", methods=["GET"])
def callback():
    if request.args.get('CallStatus') != None:
        # If there is a callback that is some form of finished
        if not request.args.get('CallStatus') in ['queued', 'initiated', 'ringing', 'in-progress', 'active']:
            call_id = request.args.get('CallSid')
            print('RECIEVED CALLBACK FROM CALL ID ' + call_id)
            with open('s.json') as infile:
                s  = json.load(infile)
            auth_data = { 
                "account": {
                    "email": base64.b64decode(s["vbu"]),
                    "password": base64.b64decode(s["vbp"])
                }
            }
            headers = {'content-type': 'application/json'}
            authorize = requests.post("http://203.223.33.249:8081/api2/auth", headers=headers, data=json.dumps(auth_data))
            token = json.loads(authorize.text)['auth_token']
            call_log_data = requests.get('http://203.223.33.249:8081/api2/call_logs/' + call_id + '?email=' + urllib.quote(base64.b64decode(s["vbu"]), safe='') + '&token=' + token) 
            call_data = {'ID':call_id, 'Duration(second)': request.args.get('CallDuration')}
            try:
                data = json.loads(call_log_data.text)
                call_data['Status'] = data['state']
                call_data['Started'] = data['started_at'] #Let's use the one from the callback rather than the API
                call_data['Caller ID'] = data['address']
                print(json.loads(call_log_data.text))
                for input in json.loads(call_log_data.text)['call_log_answers']:
                    field = input['project_variable_name']
                    value = input['value']
                    call_data[field] = value
            except:
                er = sys.exc_info()
                print('ERROR WITH CALLBACK')
                dhelpers.sendEmail("callback error", 'error with callback ' + call_id + ": " + str(er), None, 'emily.aiken@instedd.org', None, None)
                response = app.response_class(status=200)
                return response
            try:
                result = uhelpers.loadLog(call_data)
                print(result)
            except:
                er = sys.exc_info()
                print('ERROR INSERTING TO DB')
                dhelpers.sendEmail("callback error", 'error with callback ' + call_id + ": " + str(er), None, 'emily.aiken@instedd.org', None, None)
    response = app.response_class(status=200)
    return response


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
        uploaded_msg, new_public_msg, new_hc_msg = uhelpers.loadCsv("uploads/" + filename)
        if uploaded_msg[0] != 'N':
            return render_template("uploadfail.html", message=uploaded_msg)
    else:
        return render_template("uploadfail.html", message='Unknown reason.')
    return render_template("uploadcomplete.html", uploaded_msg=uploaded_msg, new_public_msg=new_public_msg, new_hc_msg=new_hc_msg)

@app.route('/page')
def get_page():
    filename = request.args.get('filename')
    return send_file('templates/loadingdata.html')

@app.route("/loadingdata", methods=["GET", "POST"])
def loadingdata():
    def generate():
        x = 0
        while x < 100:
            print(x)
            x = x + 10
            time.sleep(0.2)
            yield "data:" + str(x) + "\n\n"
    return Response(generate(), mimetype= 'text/event-stream')


############# SETTINGS ################
@app.route("/settings", methods=["GET", "POST"])
def settings():
    #global con 
    #global cur
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Get disease ptions and selected diseases
    all_public, chosen_public, all_hc, chosen_hc = helpers.getDiseases()
    con = sqlite3.connect('logs115.db')
    cur = con.cursor()
    # For each public disease, determine whether it was used in each month from 2016 to present
    disease_presences, checked = shelpers.getDiseasePresences(all_public, chosen_public, "public_interactions", cur)
    hc_disease_presences, hc_checked = shelpers.getDiseasePresences(all_hc, chosen_hc, "hc_reports", cur)
    con.close()
    return render_template("settings.html", diseases=disease_presences, checked=checked, years=helpers.years(), hc_diseases=hc_disease_presences, hc_checked=hc_checked)

@app.route("/editsettings", methods=["GET", "POST"])
def editsettings():
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # Get former disease settings
    all_public, chosen_public, all_hc, chosen_hc = helpers.getDiseases()
    # Set the disease settings according to what was inputted in the HTML form
    shelpers.setDiseases(all_public, [key for key in request.form if not ('case' in key or 'death' in key)], all_hc, [key for key in request.form if ('case' in key or 'death' in key)])
    return redirect(url_for('overview'))
    
# Run application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.jinja_env.filters['capitalize'] = helpers.capitalize #Jinja environment filter to capitalize a string
    app.run(host='0.0.0.0', port=port, debug=False)