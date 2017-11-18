import plotly
import plotly.plotly as py
import plotly.graph_objs as go


def calls_by_type(hc_workers, public):
    figure = {
        "data": [
            {
                "labels": ["HC workers", "Public"],
                "hoverinfo": "none",
                "marker": {
                    "colors": [
                        "rgb(0,255,00)",
                        "rgb(255,0,0)",
                    ]
                },
                "type": "pie",
                "values": [hc_workers, public]
            }
        ],
        "layout": {
            "title": "Calls by Type (HC Worker vs Public)",
            "showlegend": True
            }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def calls_by_day_offline(dates, call_totals, thetitle, fname):
    py.sign_in('emilylaiken', 'csrDX5SAFtnDVouV2f18') # Replace the username, and API key with your credentials.
    trace = go.Scatter(x=dates, y= call_totals)
    data = [trace]
    layout = go.Layout(title=thetitle, width=800, height=640)
    fig = go.Figure(data=data, layout=layout)
    py.image.save_as(fig, filename=fname)
    return 


def calls_by_day(dates, call_totals, title):
    figure = {
        "data": [{
            'x': dates,
            'y': call_totals
        }],
        "layout": {
            "title": title,
            "showlegend": False
        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False, image='jpeg', image_filename='test')

def menu_visits_by_day(dates, h5n1, mers, zika):
    figure = {
        "data": [
            {'x': dates, 'y': h5n1, 'name': "H5N1"},
            {'x': dates, 'y': mers, 'name': "Mers"},
            {'x': dates, 'y': zika, 'name': "Zika"}
        ],
        "layout": {
            "title": "Visits to Each Public Disease Menu by Day",
            "showlegend": True,

        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def overview_and_prevention_by_day_download(dates, overview, prevention, title, fname):
    py.sign_in('emilylaiken', 'csrDX5SAFtnDVouV2f18') # Replace the username, and API key with your credentials.
    trace1 = go.Scatter(x=dates, y= overview, name='Overview information')
    trace2 = go.Scatter(x=dates, y=prevention, name='Prevention information')
    data = [trace1, trace2]
    layout = go.Layout(title="Visits to Prevention/Overview Information by Day - " + title, width=800, height=640)
    fig = go.Figure(data=data, layout=layout)
    py.image.save_as(fig, filename=fname)

def overview_and_prevention_by_day(dates, overview, prevention, title):
    figure = {
        "data": [
            {'x': dates, 'y': overview, 'name': "Overview Information"},
            {'x': dates, 'y': prevention, 'name': "Prevention Information"},
        ],
        "layout": {
            "title": "Visits to Prevention/Overview Information by Day - " + title,
            "showlegend": True,

        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def calls_by_status(labels, data):
    figure = {
        "data": [
            {
                "labels": labels,
                "type": "pie",
                "values": [data[0], data[1], data[2], data[3]]
            }
        ],
        "layout": {
            "title": "Public calls by Status",
            "showlegend": True
        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)


def reports_by_week(dates, completed, attempted, title):
    figure = {
        "data": [
            {'x': dates, 'y': completed, 'name': "On-time reports"},
            {'x': dates, 'y': attempted, 'name': "Late reports"},
        ],
        "layout": {
            "title": title,
            "showlegend": True,

        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def case_reports_by_week(dates, series, title):
    figure = {
        "data": [
            {'x': dates, 'y': series[0], 'name': "Diarrhea"},
            {'x': dates, 'y': series[1], 'name': "Fever"},
            {'x': dates, 'y': series[2], 'name': "Flaccid"},
            {'x': dates, 'y': series[3], 'name': "Respiratory"},
            {'x': dates, 'y': series[4], 'name': "Dengue"},
            {'x': dates, 'y': series[5], 'name': "Meningitis"},
            {'x': dates, 'y': series[6], 'name': "Jaundice"},
            {'x': dates, 'y': series[7], 'name': "Diphteria"},
            {'x': dates, 'y': series[8], 'name': "Rabies"},
            {'x': dates, 'y': series[9], 'name': "Neonatal"}
        ],
        "layout": {
            "title": title,
            "showlegend": True,

        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)


