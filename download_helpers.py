from __future__ import print_function
import sys
import os
import sqlite3
import datetime
from fpdf import FPDF
from PIL import Image
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics  
from reportlab.pdfbase.ttfonts import TTFont  
from pyPdf import PdfFileWriter, PdfFileReader
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from flask import Flask, redirect, render_template, request, url_for, send_file, session
import smtplib
import graph_helpers as ghelpers
import chartmaker
import helpers

# Append PDFs (input files) to a PDF file writer (output)
def append_pdf(input,output):
    [output.addPage(input.getPage(page_num)) for page_num in range(input.numPages)]

# Make PDF out of a list of images
def makePdf(pdfFileName, listPages, dir = ''):
    if (dir):
        dir += "/"
    cover = Image.open(dir + str(listPages[0]))
    width, height = cover.size
    pdf = FPDF(unit = "pt", format = [width, height])
    for page in listPages:
        pdf.add_page()
        pdf.image(dir + str(page), 0, 0)
    pdf.output(dir + pdfFileName + ".pdf", "F")

# Creates single-series line chart in PNG, generates statistics, and appends statistics to parts
def addSingleSeriesChart(table, condition_string, starting_date_string, ending_date_string, numdays, title, fname, parts, styles):
    duration_string, title_addon = ghelpers.parseDuration('0', 'end')
    chart_sql, total_sql, avg_sql = ghelpers.generateSQL(table, starting_date_string, ending_date_string, duration_string, condition_string)
    total, avg = ghelpers.generateFiguresDownload(chart_sql, total_sql, avg_sql, title + " By Day " + title_addon, fname, numdays, [starting_date_string, ending_date_string])
    parts.append(Paragraph("Total " + title + ": " + str(total), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    parts.append(Paragraph("Average " + title + " (by day): " + str(avg), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    return parts

# Creates mutli-series line chart in PNG, generates statistics, and appends statistics to parts
def addMultiSeriesChart(disease, starting_date_string, ending_date_string, numdays, parts, styles, cur):
    duration_string, title_addon = ghelpers.parseDuration('0', 'end')
    menu_string = disease + "_menu"
    condition_string_all = menu_string + " IS NOT NULL"
    condition_string_overview = menu_string + "=1"
    condition_string_prevention = menu_string + "=2"
    chart_sql_all, total_sql_all, avg_sql_all = ghelpers.generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_all)
    chart_sql_overview, total_sql_overview, avg_sql_overview = ghelpers.generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_overview)
    chart_sql_prevention, total_sql_prevention, avg_sql_prevention = ghelpers.generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_prevention)
    cur.execute(chart_sql_overview)
    overview_visits = cur.fetchall()
    cur.execute(chart_sql_prevention)
    prevention_visits = cur.fetchall()
    cur.execute(chart_sql_all)
    all_visits = cur.fetchall()
    dates = ghelpers.column(overview_visits, 0)
    overview = ghelpers.column(overview_visits, 1)
    prevention = ghelpers.column(prevention_visits, 1)
    all = ghelpers.column(all_visits, 1)
    disease_chart = chartmaker.overview_and_prevention_by_day_download(dates, overview, prevention, all, str.title(disease) + title_addon, disease + ".png", [starting_date_string, ending_date_string])
    cur.execute(total_sql_all)
    total = cur.fetchall()
    parts.append(Paragraph("Total calls to " + disease + " menu: " + str(total[0][0]), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    if numdays == 0:
        avg = 0
    else:
        avg = total[0][0]/numdays
    parts.append(Paragraph("Average calls to " + disease + " menu (overview or prevention): " + str(avg), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    return parts

# Sends email given subject line, text, distination email, and optional filetitle
def sendEmail(subject, body_text, filetitle, to_email):
    print('sending email', file=sys.stderr)
    fromaddr = "emily.aiken@instedd.org"
    toaddr = to_email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    body = body_text
    msg.attach(MIMEText(body, 'plain'))
    if filetitle != None:
        attachment = open(filetitle, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filetitle) 
        msg.attach(part)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "dolphin1997")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def genReport(starting_date_string, ending_date_string, qualitative, to_email, target_url, numdays):
    # File title includes current timestamp for unique identification
    now = datetime.datetime.now()
    filetitle = "report" + now.strftime("%d-%m-%y-%H-%M-%S") + ".pdf"
    print('writing qualitative', file=sys.stderr)
    #Set up PDF document and styles
    if True:
        doc = SimpleDocTemplate("hello.pdf", pagesize=letter)
        parts = []
        folder = os.path.dirname(reportlab.__file__) + os.sep + 'fonts'   
        ttfFile = os.path.join(folder, 'Vera.ttf')   
        pdfmetrics.registerFont(TTFont("Vera", ttfFile))
        styles = {
            'paragraph': ParagraphStyle('paragraph', fontName='Vera', fontSize=10, alignment=TA_LEFT),
            'title': ParagraphStyle('title', fontName='Vera', fontSize=20, alignment=TA_CENTER),
            'report_title': ParagraphStyle('report_title', fontName='Vera', fontSize=30, alignment=TA_CENTER),
        }
        #Title Page
        parts.append(Spacer(1, 3*inch))
        parts.append(Paragraph("115 Hotline Report", styles['report_title']))
        parts.append(Spacer(1, 0.7*inch))
        parts.append(Paragraph(starting_date_string + " to " + ending_date_string, styles['report_title']))
        parts.append(PageBreak())
        #Qualitative description page
        parts.append(Paragraph("Qualitative Description", styles['title']))
        parts.append(Spacer(1, inch))
        parts.append(Paragraph(qualitative, styles['paragraph']))
        parts.append(PageBreak())
        parts.append(Paragraph("Summary Statistics", styles['title']))
        parts.append(Spacer(1, inch))
        #Rest of report: statistics and graphs
        con = sqlite3.connect("logs115.db")
        cur = con.cursor()
        print('making sql queries and generating pngs', file=sys.stderr)
        # Summary pie chart
        _, public_diseases, _, _ = helpers.getDiseases()
        cur.execute("SELECT COUNT(*) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE date >=" + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "';")
        public_calls = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >=" + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "';")
        hc_calls = cur.fetchall()
        chartmaker.pie_offline([hc_calls[0][0], public_calls[0][0]], ['Public', 'HC Workers'], "callsbytype.png", "Breakdown of Callers to 115: Public vs. HC Workers")
        # Summary of public hotline pie chart
        values = []
        num_accounted_for = 0
        condition_strings = [disease + "_menu IS NOT NULL" for disease in public_diseases] + ["hotline_menu='2'", "hotline_menu='3'", "hotline_menu='4'"]
        labels = ["Visit " + disease + " Information" for disease in public_diseases] + ['Make a Report', 'Request More Information', 'Request Ambulance Information', 'No Action']
        for condition_string in condition_strings:
            cur.execute("SELECT COUNT(*) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE " + condition_string + " AND date >=" + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "';")
            value = cur.fetchall()
            values.append(value[0][0])
            num_accounted_for = num_accounted_for + value[0][0]
        cur.execute("SELECT COUNT(*) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE date >=" + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "';")
        total = cur.fetchall()
        dif = total[0][0] - num_accounted_for
        values.append(dif)
        chartmaker.pie_offline(values, labels, "publicbreakdown.png", "Actions of Callers to Public Hotline")
        # Line charts and statistics
        parts = addSingleSeriesChart("all", "call_id != ''", starting_date_string, ending_date_string, numdays, "Calls to Entire Hotline", "overview.png", parts, styles)
        parts = addSingleSeriesChart("all", " type='public' ", starting_date_string, ending_date_string, numdays, "Calls to Public Hotline", "public.png", parts, styles)
        for disease in public_diseases:
            parts = addMultiSeriesChart(disease, starting_date_string, ending_date_string, numdays, parts, styles, cur)
        parts = addSingleSeriesChart("public", "hotline_menu='2'", starting_date_string, ending_date_string, numdays, "Public Disease Reports", "publicreports.png", parts, styles)
        parts = addSingleSeriesChart("public", "hotline_menu='3'", starting_date_string, ending_date_string, numdays, "Calls Requesting Additional Information", "moreinfo.png", parts, styles)
        parts = addSingleSeriesChart("public", "hotline_menu='4'", starting_date_string, ending_date_string, numdays, "Calls Requesting Ambulance Information", "ambulance.png", parts, styles)
        con.close()
        print('creating graphs pdf', file=sys.stderr)
        # Make PDF of all graphs
        makePdf("graphs", ["callsbytype.png", "publicbreakdown.png", "overview.png", "public.png"] +  [disease + ".png" for disease in public_diseases] +  ["publicreports.png", "moreinfo.png", "ambulance.png"])
        doc.build(parts)
        # Combine PDF with text (title page, qualitative, statistics) and PDF with graphs
        print('combining all pdfs', file=sys.stderr)
        output = PdfFileWriter()
        append_pdf(PdfFileReader(open("hello.pdf","rb")),output)
        append_pdf(PdfFileReader(open("graphs.pdf","rb")),output)
        output.write(open(filetitle,"wb"))
        # Send email
        sendEmail("Your 115 Hotline Report", "The PDF report you requested is attached to this email.", filetitle, to_email)
    # If there is an error while generating the report, notify the person who requested it via email
    #except:
        #sendEmail("115 Hotline Report - Error", "Unfortunately, there was an error while generating your 115 hotline report. Please try again later.", None, to_email)
    print('done!', file=sys.stderr)
    # Clean up working directory
    for f in os.listdir(os.getcwd()):
        if f.endswith(".png") or f.endswith(".pdf"):
            os.remove(f)