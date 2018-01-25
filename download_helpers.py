## TODO: BETTER ERROR CATCHING ON THIS PAGE

from __future__ import print_function
import sys
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
from flask import Flask, redirect, render_template, request, url_for, send_file, session, json
import smtplib
import graph_helpers as ghelpers
import chartmaker
import helpers
import base64

# Append PDFs (input files) to a PDF file writer (output)
def append_pdf(input,output):
    [output.addPage(input.getPage(page_num)) for page_num in range(input.numPages)]

# Sends email given subject line, text, distination email, and optional filetitle
def sendEmail(subject, body_text, filetitle, to_email, cc, bcc):
    print('sending email', file=sys.stderr)
    with open('s.json') as infile:
        s  = json.load(infile)
    fromaddr = base64.b64decode(s["emu"])
    toaddr = to_email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    if cc != None and filetitle != None:
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
    server.login(fromaddr, base64.b64decode(s["emp"]))
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def genReport(starting_date_string, ending_date_string, qualitative, to_emails, cc, bcc, chosenfigures, target):
    # File title includes current timestamp for unique identification
    now = datetime.datetime.now()
    filetitle = "report" + now.strftime("%d-%m-%y-%H-%M-%S") + ".pdf"
    print('writing qualitative', file=sys.stderr)
    #Set up PDF document and styles
    if True:
        doc = SimpleDocTemplate("hello.pdf", pagesize=letter)
        parts = []
        styles = {
            'paragraph': ParagraphStyle('paragraph', fontName='Helvetica', fontSize=10, alignment=TA_LEFT),
            'title': ParagraphStyle('title', fontName='Helvetica', fontSize=20, alignment=TA_CENTER),
            'report_title': ParagraphStyle('report_title', fontName='Helvetica', fontSize=30, alignment=TA_CENTER),
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
        doc.build(parts)
        #Rest of report: statistics and graphs
        con = sqlite3.connect("logs115.db")
        cur = con.cursor()
        print('making sql queries and generating pngs', file=sys.stderr)
        duration_string, title_addon = ghelpers.parseDuration('0', 'end')
        _, public_diseases, _, _ = helpers.getDiseases()
        chartid = 0
        ghelpers.publicLineChart(cur, "all", ["call_id != ''"], starting_date_string, ending_date_string, duration_string, ["Calls to Hotline"], "Calls to Hotline by Day", False, str(chartid).zfill(2) + "overview.pdf")
        chartid = chartid + 1
        # Breakdown pie charts
        ghelpers.hotlineBreakdown(cur, 'all', ["Public Callers", "HC Workers"], [" type='public' ", " type='hc_worker' "], starting_date_string, ending_date_string, duration_string, "Hotline Breakdown", str(chartid).zfill(2) + "hotlinebreakdown.pdf")
        chartid = chartid + 1
        ghelpers.hotlineBreakdown(cur, 'public', ["Visit " + disease + " Information" for disease in public_diseases] + ['Make a Report', 'Request More Information', 'Request Ambulance Information'], [disease + "_menu IS NOT NULL" for disease in public_diseases] + ["hotline_menu='2'", "hotline_menu='3'", "hotline_menu='4'"], starting_date_string, ending_date_string, duration_string, "Public Hotline Breakdown", str(chartid).zfill(2) + "publicbreakdown.pdf")
        chartid = chartid + 1
        # Status chart
        ghelpers.statusChart(cur,"public", starting_date_string, ending_date_string, duration_string, str(chartid).zfill(2) + "statuspublic.pdf")
        chartid = chartid + 1
        ghelpers.statusChart(cur,"healthcare workers", starting_date_string, ending_date_string, duration_string, str(chartid).zfill(2) + "statushc.pdf")
        chartid = chartid + 1
        # Line charts and statistics
        ghelpers.publicLineChart(cur, "all", [" type='public' "], starting_date_string, ending_date_string, duration_string, ["Calls to Public Hotline"], "Calls to Public Hotline by Day", False, str(chartid).zfill(2) + "public.pdf")
        chartid = chartid + 1
        for disease in public_diseases:
            ghelpers.publicLineChart(cur, "public", [disease + "_menu IS NOT NULL", disease + "_menu=1", disease + "_menu=2"], starting_date_string, ending_date_string, duration_string, ["Visit Menu", "Listen to Overview Info", "Listen to Prevention Info"], "Calls to " + disease.title() + " Menu by Day", False, str(chartid).zfill(2) + disease + ".pdf")
            chartid = chartid + 1
        ghelpers.publicLineChart(cur, "public", ["hotline_menu='2'"], starting_date_string, ending_date_string, duration_string, ["Public Disease Reports"], "Public Disease Reports by Day", False, str(chartid).zfill(2) + "publicreports.pdf")
        chartid = chartid + 1
        ghelpers.publicLineChart(cur, "public", ["hotline_menu='3'"], starting_date_string, ending_date_string, duration_string, ["Calls Requesting Additional Information"], "Cals Requesting Additional Information by Day", False, str(chartid).zfill(2) + "moreinfo.pdf")
        chartid = chartid + 1
        ghelpers.publicLineChart(cur, "public", ["hotline_menu='4'"], starting_date_string, ending_date_string, duration_string, ["Calls Requesting Ambulance Information"], "Cals Requesting Ambulance Information by Day", False, str(chartid).zfill(2) + "ambulance.pdf")
        chartid = chartid + 1
        ghelpers.hcOntimeChart(cur, starting_date_string, ending_date_string, str(chartid).zfill(2) + "hcontime.pdf")
        for addon in ['_case', '_death']:
            chartid = chartid + 1
            ghelpers.hcDiseaseChart(cur, starting_date_string, ending_date_string, addon, str(chartid).zfill(2) + "hc" + addon[1:] + ".pdf")
        con.close()
        # Combine PDF with text (title page, qualitative, statistics) and PDF with graphs
        print('combining all pdfs', file=sys.stderr)
        output = PdfFileWriter()
        append_pdf(PdfFileReader(open("hello.pdf","rb")),output)
        for graph in list(sorted([figure + ".pdf" for figure in chosenfigures])):
            append_pdf(PdfFileReader(open(graph,"rb")),output)
        output.write(open(filetitle,"wb"))
        if target == 'email':
            # Send email
            sendEmail("Your 115 Hotline Report", "The PDF report you requested is attached to this email.", filetitle, to_emails, cc, bcc)
            print('done!', file=sys.stderr)
            helpers.cleanUp()
            return
        else:
            return filetitle
    # If there is an error while generating the report, notify the person who requested it via email
    #except:
        #sendEmail("115 Hotline Report - Error", "Unfortunately, there was an error while generating your 115 hotline report. Please try again later.", None, to_email)

    # Clean up working directory
