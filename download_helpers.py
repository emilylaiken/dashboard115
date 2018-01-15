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

def appendStats(parts, styles, total, avg, label):
    parts.append(Paragraph("Total " + label + ": " + str(total), styles['paragraph']))
    parts.append(Spacer(1, 0.1*inch))
    parts.append(Paragraph("Average: " + label + " (by day): " + str(avg), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    return parts

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

# Sends email given subject line, text, distination email, and optional filetitle
def sendEmail(subject, body_text, filetitle, to_email, cc, bcc):
    print('sending email', file=sys.stderr)
    fromaddr = "emily.aiken@instedd.org"
    toaddr = to_email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    if cc is not None and filetitle is not None:
        msg['cc'] = cc
    if bcc is not None and filetitle is not None:
        msg['bcc'] = bcc
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

def genReport(starting_date_string, ending_date_string, qualitative, to_emails, cc, bcc, target_url, numdays, chosenfigures):
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
        duration_string, title_addon = ghelpers.parseDuration('0', 'end')
        _, public_diseases, _, _ = helpers.getDiseases()
        chartid = 0
        # Breakdown pie charts
        ghelpers.hotlineBreakdown(cur, 'all', ["Public Callers", "HC Workers"], [" type='public' ", " type='hc_worker' "], starting_date_string, ending_date_string, duration_string, "Hotline Breakdown", str(chartid) + "hotlinebreakdown.png")
        chartid = chartid + 1
        ghelpers.hotlineBreakdown(cur, 'public', ["Visit " + disease + " Information" for disease in public_diseases] + ['Make a Report', 'Request More Information', 'Request Ambulance Information'], [disease + "_menu IS NOT NULL" for disease in public_diseases] + ["hotline_menu='2'", "hotline_menu='3'", "hotline_menu='4'"], starting_date_string, ending_date_string, duration_string, "Public Hotline Breakdown", str(chartid) + "publicbreakdown.png")
        chartid = chartid + 1
        # Line charts and statistics
        total, avg = ghelpers.publicLineChart(cur, "all", ["call_id != ''"], starting_date_string, ending_date_string, duration_string, ["Calls to Hotline"], "Calls to Hotline by Day", False, str(chartid) + "overview.png")
        chartid = chartid + 1
        parts = appendStats(parts, styles, total, avg, "calls to entire hotline")
        total, avg = ghelpers.publicLineChart(cur, "all", [" type='public' "], starting_date_string, ending_date_string, duration_string, ["Calls to Public Hotline"], "Calls to Public Hotline by Day", False, str(chartid) + "public.png")
        chartid = chartid + 1
        parts = appendStats(parts, styles, total, avg, "calls to public hotline")
        for disease in public_diseases:
            total, avg = ghelpers.publicLineChart(cur, "public", [disease + "_menu IS NOT NULL", disease + "_menu=1", disease + "_menu=2"], starting_date_string, ending_date_string, duration_string, ["Visit Menu", "Listen to Overview Info", "Listen to Prevention Info"], "Calls to " + disease.title() + " Menu by Day", False, str(chartid) + disease + ".png")
            chartid = chartid + 1
            parts = appendStats(parts, styles, total, avg, "visitors to " + disease.title() + " menu")
        total, avg = ghelpers.publicLineChart(cur, "public", ["hotline_menu='2'"], starting_date_string, ending_date_string, duration_string, ["Public Disease Reports"], "Public Disease Reports by Day", False, str(chartid) + "publicreports.png")
        chartid = chartid + 1
        parts = appendStats(parts, styles, total, avg, "public disease reports")
        total, avg = ghelpers.publicLineChart(cur, "public", ["hotline_menu='3'"], starting_date_string, ending_date_string, duration_string, ["Calls Requesting Additional Information"], "Cals Requesting Additional Information by Day", False, str(chartid) + "moreinfo.png")
        chartid = chartid + 1
        parts = appendStats(parts, styles, total, avg, "calls requesting additional information")
        total, avg = ghelpers.publicLineChart(cur, "public", ["hotline_menu='4'"], starting_date_string, ending_date_string, duration_string, ["Calls Requesting Ambulance Information"], "Cals Requesting Ambulance Information by Day", False, str(chartid) + "ambulance.png")
        parts = appendStats(parts, styles, total, avg, "calls requesting ambulance information")
        con.close()
        print('creating graphs pdf', file=sys.stderr)
        # Make PDF of all graphs
        print(chosenfigures)
        makePdf("graphs", list(sorted([figure + ".png" for figure in chosenfigures])))
        doc.build(parts)
        # Combine PDF with text (title page, qualitative, statistics) and PDF with graphs
        print('combining all pdfs', file=sys.stderr)
        output = PdfFileWriter()
        append_pdf(PdfFileReader(open("hello.pdf","rb")),output)
        append_pdf(PdfFileReader(open("graphs.pdf","rb")),output)
        output.write(open(filetitle,"wb"))
        # Send email
        sendEmail("Your 115 Hotline Report", "The PDF report you requested is attached to this email.", filetitle, to_emails, cc, bcc)
    # If there is an error while generating the report, notify the person who requested it via email
    #except:
        #sendEmail("115 Hotline Report - Error", "Unfortunately, there was an error while generating your 115 hotline report. Please try again later.", None, to_email)
    print('done!', file=sys.stderr)
    # Clean up working directory
    for f in os.listdir(os.getcwd()):
        if f.endswith(".png") or f.endswith(".pdf"):
            os.remove(f)