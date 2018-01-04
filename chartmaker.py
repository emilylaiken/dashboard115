import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import helpers

# Calls by type pie chart: HC workers vs. public--ONLINE
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

# Pie charts for download--used for summary pie chart for entire hotline (calls by type) and summary pie chart for public hotline--OFFLINE
def pie_offline(values, labels, fname, title):
    py.sign_in('emilylaiken', 'csrDX5SAFtnDVouV2f18') 
    trace = go.Pie(labels=labels, values=values, textinfo='value')
    layout = go.Layout(title=title, width=800, height=640)
    fig = go.Figure(data=[trace], layout=layout)
    py.image.save_as(fig, filename=fname)
    return

# Single-series by day (used for total calls, calls requesting more info, etc.)--OFFLINE
def calls_by_day_offline(dates, call_totals, thetitle, fname, daterange):
    py.sign_in('emilylaiken', 'csrDX5SAFtnDVouV2f18') 
    trace = go.Scatter(x=dates, y= call_totals)
    data = [trace]
    layout = go.Layout(title=thetitle, width=800, height=640, xaxis={'range': daterange})
    fig = go.Figure(data=data, layout=layout)
    py.image.save_as(fig, filename=fname)
    return 

# Single-series by day (used for total calls, calls requesting more info, etc.)--ONLINE
def calls_by_day(dates, call_totals, title, daterange):
    figure = {
        "data": [{
            'x': dates,
            'y': call_totals
        }],
        "layout": {
            "title": title,
            "showlegend": False,
            "xaxis": {'range': daterange}
        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False, image='jpeg', image_filename='test')

# Multi-series by day (used for overview/prevention charts for public hotine)--OFFLINE
def overview_and_prevention_by_day_download(dates, overview, prevention, all, title, fname, daterange):
    py.sign_in('emilylaiken', 'csrDX5SAFtnDVouV2f18') # Replace the username, and API key with your credentials.
    trace1 = go.Scatter(x=dates, y= overview, name='Overview information')
    trace2 = go.Scatter(x=dates, y=prevention, name='Prevention information')
    trace3 = go.Scatter(x=dates, y=all, name='All Visits')
    data = [trace1, trace2, trace3]
    layout = go.Layout(title="Visits to Prevention/Overview Information by Day - " + title, width=800, height=640, xaxis={'range': daterange})
    fig = go.Figure(data=data, layout=layout)
    py.image.save_as(fig, filename=fname)

# Multi-series by day (used for overview/prevention charts for public hotine)--ONLINE
def overview_and_prevention_by_day(dates, all, overview, prevention, title, daterange):
    figure = {
        "data": [
            {'x': dates, 'y': overview, 'name': "Overview Information"},
            {'x': dates, 'y': prevention, 'name': "Prevention Information"},
            {'x': dates, 'y': all, 'name': "Total Visits"}
        ],
        "layout": {
            "title": "Visits to Prevention/Overview Information by Day - " + title,
            "showlegend": True,
            "xaxis": {'range': daterange}
        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

# Two subplots: 1) call-by-status pie for HC workers, 2) call-by-status pie for public (used on Overview page)--ONLINE
def calls_by_status(labels, data_public, data_hc, title):
    figure = {
    'data': [
        {
            'labels':  labels,
            'values': data_public,
            'type': 'pie',
            'name': 'Public',
            'domain': {'x': [0, .5],
                       'y': [.4, .9]},
            'hoverinfo':'label+percent+name',
            'textinfo':'none'
        },
        {
            'labels': labels,
            'values': data_hc,
            'type': 'pie',
            'name': 'HC Workers',
            'domain': {'x': [.5, 1],
                       'y': [.4, .9]},
            'hoverinfo':'label+percent+name',
            'textinfo':'none'

        }
    ],
    'layout': {'title': title,
               'showlegend': True,
               'annotations': [
                    {
                        'xref': 'paper',
                        'yref': 'paper',
                        'x': .27,
                        'xanchor': 'right',
                        'y': .94,
                        'yanchor': 'bottom',
                        'text': 'Public',
                        'showarrow': False
                    },
                    {
                        'xref': 'paper',
                        'yref': 'paper',
                        'x': .78,
                        'xanchor': 'right',
                        'y': .94,
                        'yanchor': 'bottom',
                        'text': 'HC Workers',
                        'showarrow': False
                    }
                ]
            }
    }

    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

# Double-series by week, only for completed vs. attempted calls by HC workers--ONLINE, NOT CURRENTLY IN USE
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

# Double-series by week: reports by week for HC workers, divided into two series (completed vs. attempted, on-time vs. late, etc.)--ONLINE
def case_reports_by_week(diseases, dates, series, title):
    data = []
    for i in range (0, len(diseases)):
        data.append({'x': dates, 'y': series[i], 'name': str.title(diseases[i].split("_")[1] + " " + diseases[i].split("_")[2] + "s")})
    figure = {
        "data": data,
        "layout": {
            "title": title,
            "showlegend": True,
        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)


