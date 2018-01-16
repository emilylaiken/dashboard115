from __future__ import print_function
import sys
import csv
import sqlite3
import datetime
import helpers
import json

def tbl_atr():
    all_public, chosen_public, all_hc, chosen_hc = helpers.getDiseases()
    call_atr = ['call_id', 'date', 'datenum', 'month', 'year', 'time', 'week_id', 'duration', 'caller_id', 'status', 'type']
    public_atr = ['call_id', 'hotline_menu', 'disease_menu'] + [disease + '_menu' for disease in all_public]
    hc_atr = ['call_id', 'caller_id', 'week_id'] + all_hc
    return call_atr, public_atr, hc_atr

def tbl_atr_types():
    # Get the attributes themselves
    call_atr, public_atr, hc_atr = tbl_atr()
    # Fill out types for attributes in calls table
    call_atr_types = {}
    for atr in call_atr:
        if atr == 'call_id':
            call_atr_types[atr] = 'INTEGER PRIMARY KEY'
        elif atr == 'datenum' or atr == 'duration' or atr == 'time' or atr == 'caller_id':
            call_atr_types[atr] = 'VARCHAR'
        else:
            call_atr_types[atr] = 'INTEGER'
    # Fill out types for attributes in public_interactions table
    public_atr_types = {}
    for atr in public_atr:
        if atr == 'call_id':
            public_atr_types[atr] = 'INTEGER PRIMARY KEY'
        else:
            public_atr_types[atr] = 'INTEGER'
    # Fill out types for attributes in hc_reports table
    hc_atr_types = {}
    for atr in hc_atr:
        if atr == 'call_id':
            hc_atr_types[atr] = 'INTEGER PRIMARY KEY'
        elif atr == 'caller_id' or atr == 'week_id':
            hc_atr_types[atr] = 'VARCHAR'
        else:
            hc_atr_types[atr] = 'INTEGER DEFAULT 0'
    return call_atr_types, public_atr_types, hc_atr_types


# Checks if the uploaded file is a CSV
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in set(['csv'])

# For the caller-ID cell, sets anonymous callers to NULL
def removeAnonymous(caller_id):
    if caller_id[0] == 'A':
        return None
    else:
        return caller_id

# Deletes stars at end of disease reports
def deleteStar(disease_report):
    for i in range(len(disease_report)):
        if disease_report[i] == "*":
            return disease_report[0:i]
    return disease_report

# Parses the start and end date/time object into two seperate objects, one for date and one for time
def parseDateTime(fulldate):
    if fulldate == "":
        return "", ""
    elif "/" in fulldate: #Call log format
        for i in range(len(fulldate)):
            if fulldate[i] == " ":
                backwards_date = fulldate[0:i]
                day = backwards_date[0:2]
                month = backwards_date[3:5]
                year = backwards_date[6:10]
                forwards_date = year + '-' + month + '-' + day
                return forwards_date, fulldate[i:len(fulldate)]
    elif "Z" in fulldate: #Realtime callback format
        fulldate = fulldate[0:10] + " " + fulldate[11:19]
        datestamp = datetime.datetime.strptime(fulldate, '%Y-%m-%d %H:%M:%S') 
        datestamp_cambodia = datestamp + datetime.timedelta(hours=7) #Can do this more elegantly
        date = datetime.datetime.strftime(datestamp_cambodia, '%Y-%m-%d')
        time = datetime.datetime.strftime(datestamp_cambodia, '%H:%M:%S')
        return date, time
    return "", ""

# Refreshes tables and available diseases
def refresh(cur):
    cur.execute("DROP TABLE calls;")
    cur.execute("DROP TABLE hc_reports;")
    cur.execute("DROP TABLE public_interactions;")
    helpers.setDiseases([], [], [], [])
    call_atr, public_atr, hc_atr = tbl_atr()
    call_atr_types, public_atr_types, hc_atr_types = tbl_atr_types()
    cur.execute("CREATE TABLE IF NOT EXISTS calls (" + ", ".join([atr + " " + call_atr_types[atr] for atr in call_atr]) + ");")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON calls (datenum);")
    cur.execute("CREATE TABLE IF NOT EXISTS public_interactions (" + ", ".join([atr + " " + public_atr_types[atr] for atr in public_atr]) + ");")
    cur.execute("CREATE TABLE IF NOT EXISTS hc_reports (" + ", ".join([atr + " " + hc_atr_types[atr] for atr in hc_atr]) + ");")

# Checks to see if the schema for a call log or set of call logs has the minimum necessary fields
def checkReqAtr(call_log_vars):
    req_attributes = ['ID', 'Started', 'Duration(second)', 'Caller ID', 'Status', 'level_worker']
    for atr in req_attributes:
        if atr not in call_log_vars:
            return False
    return True

# Given a call id, queries database for other calls with the same call ID, returns whether or not there is a duplicate
def checkDuplicateLogs(cur, call_id):
    cur.execute("SELECT * FROM calls WHERE call_id = " + "'" + call_id + "'");
    duplicate_calls = cur.fetchall()
    if len(duplicate_calls) == 0:
        return False
    else:
        return True

# Given the schema of a call log or set of call logs, finds which public and HC fields exist in the log
def availableFields(call_log_vars):
    hc_fields_available = []
    public_fields_available = []
    other_public_fields = ['welcome', 'hotline', 'disease', 'nchad']
    for field in call_log_vars:
        # Search for HC worker diseases--begin with 'va' and end with 'case' or 'death'
        if (field[-4:] == 'case' or field[-5:] == 'death') and field[:2] == 'va':
            hc_fields_available.append(field)
        # Search for public diseases--end with 'menu'
        elif field[-4:] == 'menu' and not field.split("_")[0] in other_public_fields and not field.split("_")[0] in public_fields_available:
            public_fields_available.append(field.split("_")[0])
    return public_fields_available, hc_fields_available

def addNewFields(cur, public_fields_available, hc_fields_available):
    all_public, chosen_public, all_hc, chosen_hc = helpers.getDiseases()
    new_public_diseases = [disease for disease in public_fields_available if disease not in all_public]
    new_hc_diseases = [disease for disease in hc_fields_available if disease not in all_hc]
    for disease in new_public_diseases:
        cur.execute("ALTER TABLE public_interactions ADD " + disease + "_menu INTEGER;")
        all_public, chosen_public, all_hc, chosen_hc = helpers.setDiseases(all_public + [disease], chosen_public + [disease], all_hc, chosen_hc)
    for disease in new_hc_diseases:
        cur.execute("ALTER TABLE hc_reports ADD " + disease + " INTEGER DEFAULT 0;")
        all_public, chosen_public, all_hc, chosen_hc = helpers.setDiseases(all_public, chosen_public, all_hc + [disease], chosen_hc + [disease])
    return new_public_diseases, new_hc_diseases

def insertCallLog(cur, call, public_fields_available, hc_fields_available):
    # Get time and date from 'started' field
    dateTime = parseDateTime(call['Started'])
    date = dateTime[0]
    time = dateTime[1]
    # Calculate week ID (for grouping by weeks)
    day_of_week = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
    if day_of_week in [1, 2, 3]:
        days_since_wed = day_of_week + 5
    else:
        days_since_wed = day_of_week - 2
    week_id = datetime.datetime.strftime(datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=days_since_wed), '%y-%m-%d')
    datenum = helpers.dtoi(date)
    # Decide which type of call it is--HC worker or public
    if (call['level_worker'] == '2'):
        call_type = 'hc_worker'
    else:
        call_type = 'public'
    calls_attributes, _, _ = tbl_atr()
    general_info = [(call['ID'], date, datenum, datenum[4:6], datenum[0:4], time, week_id, call['Duration(second)'], removeAnonymous(call['Caller ID']), call['Status'], call_type)]
    cur.executemany("INSERT INTO calls (" +  ", ".join(calls_attributes) + ") VALUES (" + ", ".join(["?" for atr in calls_attributes]) + ");", general_info)
    # Record disease report information--disease type and disease # inputs
    if (call_type == "hc_worker"):
        reports = ()
        for var in hc_fields_available:
            if call[var] == "": # Did not enter any of this disease
                reports = reports + (0,)
            else: # Some of disease reported
                reports = reports + (deleteStar(call[var]),)
        to_db = [(call['ID'], call['Caller ID'], week_id) + reports]
        hc_attributes = ['call_id', 'caller_id', 'week_id'] + hc_fields_available
        cur.executemany("INSERT INTO hc_reports (" + ", ".join(hc_attributes) + ") VALUES (" + ", ".join(["?" for atr in hc_attributes]) + ");", to_db)
        #cur.execute("UPDATE hc_reports SET " +  ", ".join([field + " = 0" for field in hc_fields_available]) + " WHERE caller_id = " + call['Caller ID'] + " AND week_id = " + week_id + ";")
    # Record public interaction with menus
    else:
        disease_menus = ['hotline_menu', 'disease_menu'] + [disease + "_menu" for disease in public_fields_available]
        interaction = ()
        for menu in disease_menus:
            try:
                if call[menu] == "":
                    interaction = interaction + (None,) #did not reach this step - call logs
                else:
                    interaction = interaction + (call[menu],)
            except: #Did not reach this step - realtime analytics
                interaction = interaction + (None,)
        to_db = [(call['ID'],) + interaction]
        cur.executemany("INSERT INTO public_interactions (" + ", ".join(['call_id'] + disease_menus) + ") VALUES (" + ", ".join(["?" for atr in ['call_id'] + disease_menus]) + ");", to_db)

def loadCsv(data_file_name):
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    #refresh(cur)
    with open(data_file_name, 'rU') as fin: 
        dr = csv.DictReader(fin) 
        schema = dr.fieldnames
        if checkReqAtr(schema) == False:
            return "Missing attribute: " + req_attribute, "", ""
        public_fields_available, hc_fields_available = availableFields(schema)
        new_public_diseases, new_hc_diseases = addNewFields(cur, public_fields_available, hc_fields_available) 
        numInserted = 0
        numDuplicates = 0
        for call in dr:
            if call['ID'] == "": # If we are passed the end of the call records, stop
                break
            if checkDuplicateLogs(cur, call['ID']) == True:
                numDuplicates = numDuplicates + 1
            else:
                insertCallLog(cur, call, public_fields_available, hc_fields_available)
                numInserted = numInserted + 1
    con.commit()
    con.close()
    # Messages to print on HTML template: number of calls inserted/duplicates, new public diseases detected, new HC diseases detected
    num_loaded_msg = "Number of call logs successfully loaded: " + str(numInserted) + ". Number of duplicates (not loaded): " + str(numDuplicates)+ "."
    new_public_msg = ""
    if len(new_public_diseases) == 0:
        new_public_msg = "New public diseases detected: None."
    else:
        new_public_msg = "New public diseases detected: " + str.title(", ".join(new_public_diseases)) + "."
    new_hc_msg = ""
    if len(new_hc_diseases) == 0:
        new_hc_msg = "New HC diseases detected: None."
    else:
        hc_disease_titles = [str.title(disease.split('_')[1] + " " + disease.split('_')[2]) for disease in new_hc_diseases]
        new_hc_msg = "New public diseases detected: " + str.title(", ".join(hc_disease_titles)) + "."
    return num_loaded_msg, new_public_msg, new_hc_msg

def loadLog(calldict):
    try:
        con = sqlite3.connect("logs115.db")
        cur = con.cursor()
        schema = [key for key, value in calldict].iteritems()
        if checkReqAtr(schema) == False:
            con.close()
            return "Missing required attribute"
        public_fields_available, hc_fields_available = availableFields(schema)
        new_public_diseases, new_hc_diseases = addNewFields(cur, public_fields_available, hc_fields_available) 
        if checkDuplicateLogs(cur, calldict['ID']) == True:
            con.close()
            return "Duplicate call"
        else:
            insertCallLog(cur, call, public_fields_available, hc_fields_available)
            con.commit()
            con.close()
            return "Successfully loaded into DB"
    except:
        return "error"

def oldcallback():
    # Check to make sure we are not acessing the page in a browser
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
            public_fields_available = []
            other_public_fields = ['welcome', 'hotline', 'disease', 'nchad']
            hc_fields_available = []
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
                    if (field[-4:] == 'case' or field[-5:] == 'death') and field[:2] == 'va':
                        hc_fields_available.append(field)
                    elif field[-4:] == 'menu' and not field.split("_")[0] in other_public_fields and not field.split("_")[0] in public_fields_available:
                        public_fields_available.append(field.split("_")[0])
                con = sqlite3.connect('logs115.db')
                cur = con.cursor()
                uhelpers.insertCallLog(cur, call_data, public_fields_available, hc_fields_available)
            except:
                print('ERROR WITH CALLBACK')
                dhelpers.sendEmail("callback error", 'error with callback ' + call_id + ": " + str(er), None, 'emily.aiken@instedd.org', None, None)
            con.commit()
            con.close()
    response = app.response_class(status=200)
    return response

