from __future__ import print_function
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session
import chartmaker
import sys
import helpers
import datetime
import collections

# Get the specified column of a table (used to get specific series for graphs)
def column(matrix, i):
    return [row[i] for row in matrix]

# Parse the duration in string/minutes format (the format used in the URL parameters) into seconds format for SQL; aso produces add-on for duration in title
def parseDuration(duration_start, duration_end):
    if (duration_start == '0' and duration_end == '5'):
        duration_string = " AND duration <= 300"
        title_addon = " (0-5 minutes)"
    elif (duration_start == '5' and duration_end == '10'):
        duration_string = " AND duration > 300 AND duration <= 600"
        title_addon = " (5-10 minutes)"
    elif (duration_start == '10' and duration_end == "end"):
        duration_string = " AND duration > 600"
        title_addon = " (10+ minutes)"
    else:
        duration_string = ""
        title_addon = ""       
    return (duration_string, title_addon)

# Generates the SQL query on a given date, duration, and additional constraints. Only for single-series charts.
def generateSQL(table, starting_date_string, ending_date_string, duration_string, condition_string):
    if table == "all":
        from_string = "calls"
    elif table == "public":
        from_string = "calls JOIN public_interactions ON calls.call_id = public_interactions.call_id"
    elif table == "hc_reports":
        from_string = "calls JOIN hc_reports ON calls.call_id = hc_reports.call_id"
    filter_string = " datenum >=" + "'" + helpers.dtoi(starting_date_string) + "'" " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " "
    chart_sql = "SELECT date, count(calls.call_id) as count FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string + "GROUP BY date ORDER BY date desc"
    total_sql = "SELECT count(calls.call_id) FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string
    avg_sql = "SELECT avg(count) FROM (" + chart_sql + ")"
    return (chart_sql, total_sql, avg_sql)

# Given three SQL statements (one for the chart, one for the total, and one for the average), executes the SQL statements and calls the helper chart function to create the figure
def generateFigures(chart_sql, total_sql, avg_sql, title, daterange, cur):
    num_days = (datetime.datetime.strptime(request.args.get('dateend'), '%Y-%m-%d') - datetime.datetime.strptime(request.args.get('datestart'), '%Y-%m-%d')).days + 1
    cur.execute(chart_sql)
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    chart = chartmaker.calls_by_day(dates, numcalls, title, daterange)
    # Total
    cur.execute(total_sql)
    totals = cur.fetchall()
    total = totals[0][0]
    # Average
    avg = total/num_days
    return (chart, total, avg)

# Same as the above function, but the chart created by this function is downloadable
def generateFiguresDownload(chart_sql, total_sql, avg_sql, title, filename, numdays, daterange):
    con = sqlite3.connect('logs115.db')
    cur = con.cursor()
    cur.execute(chart_sql)
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    chart = chartmaker.calls_by_day_offline(dates, numcalls, title, filename, daterange)
    # Total
    cur.execute(total_sql)
    totals = cur.fetchall()
    total = totals[0][0]
    # Average by day
    avg = total/numdays
    con.close()
    return (total, avg)

# Calls generateFigures to add single-series figure to the page's list of figures
def addFigure(condition_string, table, title, charts, totals, averages, cur):
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    chart_sql, total_sql, avg_sql = generateSQL(table, starting_date_string, ending_date_string, duration_string, condition_string)
    chart, total, avg = generateFigures(chart_sql, total_sql, avg_sql, title + title_addon, [starting_date_string, ending_date_string], cur)
    charts.append(chart)
    totals.append(total)
    averages.append(avg)
    return charts, totals, averages

# Adds multi-series public disease figure to the page's list of figures
def addDiseaseFigures(diseases, charts, totals, averages, cur):
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    num_days = (datetime.datetime.strptime(request.args.get('dateend'), '%Y-%m-%d') - datetime.datetime.strptime(request.args.get('datestart'), '%Y-%m-%d')).days + 1
    for i in range (0, len(diseases)):
        disease = diseases[i]
        menu_string = disease + "_menu"
        condition_string_all = menu_string + " IS NOT NULL"
        condition_string_overview = menu_string + "=1"
        condition_string_prevention = menu_string + "=2"
        chart_sql_all, total_sql_all, avg_sql_all = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_all)
        chart_sql_overview, total_sql_overview, avg_sql_overview = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_overview)
        chart_sql_prevention, total_sql_prevention, avg_sql_prevention = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_prevention)
        cur.execute(chart_sql_all)
        all_visits = cur.fetchall()
        cur.execute(chart_sql_overview)
        overview_visits = cur.fetchall()
        cur.execute(chart_sql_prevention)
        prevention_visits = cur.fetchall()
        dates = column(overview_visits, 0)
        all = column(all_visits, 1)
        overview = column(overview_visits, 1)
        prevention = column(prevention_visits, 1)
        disease_chart = chartmaker.overview_and_prevention_by_day(dates, all, overview, prevention, str.title(diseases[i]) + title_addon, [starting_date_string, ending_date_string])
        charts.append(disease_chart)
        #Total visits to menu
        cur.execute(total_sql_all)
        total = cur.fetchall()
        totals.append(total[0][0])
        #Average visits to menu
        averages.append(total[0][0]/num_days)
    return charts, totals, averages

# Adds multi-serires HC reports figure to the page's list of figures
def addHCReportChart(diseases, title, cur):
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    series = []
    # Initialize empty dictionary to hold reports
    reports = collections.OrderedDict()
    for disease in diseases:
        reports[disease] = []
    reports['dates'] = []
    # Query database for sum of reports of each disease eah week
    cur.execute("SELECT week_id, " + ", ".join(["sum(" + disease + ")" for disease in diseases]) + " FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + " GROUP BY week_id;")
    weeks = cur.fetchall()
    # Write sums from SQL query into database
    for week in weeks:
        reports['dates'].append(week[0])
        for i in range (0, len(diseases)):
            reports[diseases[i]].append(week[i+1])
    return chartmaker.case_reports_by_week(reports, title)

# Adds multi-series completed vs. attempted figure to the page's list of figures
def addOnTimeChart(table, title, cur):
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    cur.execute("SELECT week_id, count(calls.call_id) FROM " + table + " WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) == 2 OR CAST(strftime('%w', date) as integer) == 3)) GROUP BY week_id ORDER BY week_id asc;")
    completed_reports_by_week = cur.fetchall()
    cur.execute("SELECT week_id, count(calls.call_id) FROM " + table + " WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) < 2 OR CAST(strftime('%w', date) as integer) > 3)) GROUP BY week_id ORDER BY week_id asc;")
    attempted_reports_by_week = cur.fetchall()
    weeks = column(completed_reports_by_week, 0)
    completed = column(completed_reports_by_week, 1)
    attempted = column(attempted_reports_by_week, 1)
    return chartmaker.reports_by_week(weeks, completed, attempted, title)

# Adds two-subplots pie charts depicting percentage of calls successful, failed, etc (one for HC workers and one for public)
def addCompletedAttemptedChart(charts, totals, averages, cur):
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    data_public = []
    data_hc = []
    statuses = ['incompleted', 'completed', 'terminated']
    for status in statuses:
        cur.execute("SELECT count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " AND status == '" + unicode(status) + "';")
        calls_by_status_public = cur.fetchall()
        data_public.append(calls_by_status_public[0][0])
        cur.execute("SELECT count(calls.call_id) AS count FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " AND status == '" + unicode(status) + "';")
        calls_by_status_hc = cur.fetchall()
        data_hc.append(calls_by_status_hc[0][0])
    charts.append(chartmaker.calls_by_status(statuses, data_public, data_hc, "Calls by Status" + title_addon))
    totals.append(None)
    averages.append(None)
    return charts, totals, averages

########## NEW PLOTTING LIBRARY FUNCTIONS #########

def hcOntimeChart(cur, starting_date_string, ending_date_string):
    cur.execute("SELECT week_id, count(calls.call_id) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) == 2 OR CAST(strftime('%w', date) as integer) == 3)) GROUP BY week_id ORDER BY week_id asc;")
    completed_reports_by_week = cur.fetchall()
    cur.execute("SELECT week_id, count(calls.call_id) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) < 2 OR CAST(strftime('%w', date) as integer) > 3)) GROUP BY week_id ORDER BY week_id asc;")
    attempted_reports_by_week = cur.fetchall()
    weeks = column(completed_reports_by_week, 0)
    completed = column(completed_reports_by_week, 1)
    attempted = column(attempted_reports_by_week, 1)
    return lineChart(weeks, [completed, attempted], ["On-Time Reports", "Late Reports"], palette[0:2], "HC Reports by Week - On-Time vs. Late", True, "None", "None", "completeness") + ("", "")

def addHcDiseaseCharts(cur, figures, starting_date_string, ending_date_string):
    for addon in ["_case", "_death"]:
        series = []
        # Initialize empty dictionary to hold reports
        reports = collections.OrderedDict()
        _, _, _, hc_diseases = helpers.getDiseases()
        diseases = [disease for disease in hc_diseases if addon in disease]
        for disease in sorted(diseases):
            reports[disease] = []
        reports['dates'] = []
        # Query database for sum of reports of each disease eah week
        cur.execute("SELECT week_id, " + ", ".join(["sum(" + disease + ")" for disease in diseases]) + " FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + " GROUP BY week_id;")
        weeks = cur.fetchall()
        # Write sums from SQL query into database
        for week in weeks:
            reports['dates'].append(week[0])
            for i in range (0, len(diseases)):
                reports[diseases[i]].append(week[i+1])
        series, labels, colors = [], [], []
        i = 0
        for key, value in reports.items():
            if key != 'dates':
                series.append(value)
                labels.append(key.split("_")[1].title() + " " + key.split("_")[2].title() + "s")
                colors.append(palette[i])
                i = i+1
        figures.append(lineChart(reports['dates'], series, labels, colors, "Reports of Disease " + addon[1:].title() + "s by Week", True, "None", "None", "hc" + addon[1:]) + ("", ""))
    return figures

def addPublicDiseaseCharts(cur, figures, starting_date_string, ending_date_string, duration_string):
    _, public_diseases, _, _ = helpers.getDiseases()
   # filter_string = " datenum >=" + "'" + helpers.dtoi(starting_date_string) + "'" " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " "
   # for disease in sorted(public_diseases):
   #     series_labels = ["Visit Menu", "Listen to Overview Info", "Listen to Prevention Info"]
   #     series = {}
   #     for label in series_labels:
   #         series[label] = []
   #     series['dates'] = []
   #     menu_string = disease + "_menu"
   #     cur.execute("SELECT date, " + menu_string + ", COUNT(*) FROM calls JOIN public_interactions ON calls.call_id=public_interactions.call_id WHERE " + filter_string + " GROUP BY date," + menu_string + " ORDER BY date asc;")
   #     records = cur.fetchall()
   #     for i in range (0, len(records)):
   #         record = records[i]
   #         totalvisit = 0
   #         if record[1] == 1:
   #             series['Listen to Overview Info'].append(record[2])
   #         elif record[1] == 2:
   #             series['Listen to Prevention Info'].append(record[2])
   #         if record[1] is not None:
   #             totalvisit = totalvisit + record[2]
   #         if i == len(records)-1 or record[0] != records[i+1][0]:
   #             series['Visit Menu'].append(totalvisit)
   #             totalvisit = 0
   #             series['dates'].append(record[0])
   #     total = sum(series['Visit Menu'])
   #     if total == 0:
   #         avg = 0
   #     else:
   #         avg = total / len(series['dates'])
   #     figures.append(lineChart(series['dates'], [series["Visit Menu"], series["Listen to Overview Info"], series["Listen to Prevention Info"]], series_labels, palette[0:3], "Calls to " + disease.title() + " Menu", True, starting_date_string, ending_date_string, "public" + disease) + (total, avg))
   # return figures 
    for disease in sorted(public_diseases):
        figures.append(publicLineChart(cur, 'public', [disease + "_menu IS NOT NULL", disease + "_menu=1", disease + "_menu=2"], starting_date_string, ending_date_string, duration_string, ["Visit Menu", "Listen to Overview Info", "Listen to Prevention Info"], "Calls to " + disease.title() + " Menu", True, "public" + disease))
    return figures


def publicLineChart(cur, table, condition_strings, starting_date_string, ending_date_string, duration_string, seriesnames, title, legend, canvasid):
    series = []
    colors = []
    dates = []
    for i in range (0, len(condition_strings)):
        condition_string = condition_strings[i]
        chart_sql, _, _ = generateSQL(table, starting_date_string, ending_date_string, duration_string, condition_string)
        cur.execute(chart_sql)
        calls_by_date = cur.fetchall()
        numcalls = []
        for log in calls_by_date:
            if i == 0:
                dates = dates + [log[0]]
            numcalls = numcalls + [log[1]]
        series.append(list(reversed(numcalls)))
        colors.append(palette[i])
        if i == 0:
            total = sum(numcalls)
            if total == 0:
                avg = 0
            else:
                avg = sum(numcalls) / len(numcalls)
    return lineChart(list(reversed(dates)), series, seriesnames, colors, title, legend, starting_date_string, ending_date_string, canvasid) + (total, avg)

def lineChart(labels, data, seriesnames, colors, title, legend, minx, maxx, canvasid):
    type_str = '"line"'
    labels_str = "[" + ", ".join(['"' + str(label) + '"' for label in labels]) + "]"
    data_str = "[" + ", ".join(["[" + ", ".join([str(point) for point in series]) + "]" for series in data]) + "]"
    seriesnames_str = '[' + ", ".join(['"' + name + '"' for name in seriesnames]) + ']'
    colors_str = '[' + ", ".join(['"' + color + '"' for color in colors]) + ']'
    title_str = '"' + title + '"'
    if legend:
        legend_str = '"True"'
    else:
        legend_str = '"False"'
    minx_str, maxx_str = '"' + minx + '"', '"' + maxx + '"'
    canvasid_str = '"' + canvasid + '"'
    javascript_func = "setUpChart(" + type_str + ", " + labels_str + ", " + data_str + ", " + seriesnames_str + ", " + colors_str + ", " +  title_str + ", " + legend_str + ", " + minx_str + ", " + maxx_str + ", " + canvasid_str +  ");"
    return canvasid_str, javascript_func

def statusChart(cur, table, starting_date_string, ending_date_string, duration_string):
    data = []
    statuses = ['completed', 'incompleted', 'terminated']
    if table == 'public':
        table_name = "public_interactions"
    else:
        table_name = "hc_reports"
    for status in statuses:
        cur.execute("SELECT count(calls.call_id) FROM calls JOIN " + table_name + " ON calls.call_id = " + table_name + ".call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " AND status == '" + unicode(status) + "';")
        calls_by_status = cur.fetchall()
        data.append(calls_by_status[0][0])
    return pieChart([status.title() for status in statuses], data, palette[0:len(statuses)], "Calls by Status - " + table.title(), "callsbystatus" + table[0]) + ("", "")

def pieChart(labels, data, colors, title, canvasid):
    type_str = '"pie"'
    labels_str = "[" + ", ".join(['"' + str(label) + '"' for label in labels]) + "]"
    data_str = "[" + ", ".join([str(point) for point in data]) + "]"
    seriesnames_str = "[]"
    legend_str = '"False"'
    minx_str, maxx_str = '"None"', '"None"'
    colors_str = '[' + ", ".join(['"' + color + '"' for color in colors]) + ']'
    title_str = '"' + title + '"'
    canvasid_str = '"' + canvasid + '"'
    javascript_func = "setUpChart(" + type_str + ", " + labels_str + ", " + data_str + ", " + seriesnames_str + ", " + colors_str + ", " +  title_str + ", " + legend_str + ", " + minx_str + ", " + maxx_str + ", " + canvasid_str +  ");"
    return canvasid_str, javascript_func



palette = ["#147a14", "#ff6b6b", "#43b2ab", "#dbc65e", "#4f545a", "#59344f", "#eb8258", "#6689a1", "#9dad6f", "#7d6d61"]


