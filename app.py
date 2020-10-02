import plotly
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as ddt
from dash.dependencies import Input, Output, State
import base64
import os
import io
from urllib.parse import quote as urlquote
from flask import Flask, send_from_directory
import urllib


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

UPLOAD_DIRECTORY = "./app_uploaded_files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=external_stylesheets)
app.scripts.config.serve_locally = True


@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)

colors = {
    'background': '',
    'text': '#7FDBFF'
}

# fnameDict = {'chriddy': ['opt1_c', 'opt2_c', 'opt3_c'], 'jackp': ['opt1_j', 'opt2_j']}
# names = list(fnameDict.keys())
# nestedOptions = fnameDict[names[0]]


app.layout = html.Div(style={'backgroundColor': colors['background'], 'height' : "100vh"}, children=[
    html.H1(
        children='Analyse de séries temporelles en hydrologie',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    html.Div(children='', style={
        'textAlign': 'center',
        'color': colors['text']
    }),
    html.Div(
        [
        html.Div(
            [
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(
                        ["Importer .csv ou .xlsx "]
                    ),
                    className= 'button',
                    style={
                        "width": "100%",
                        "height": "30px",
                        "lineHeight": "30px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "0px",
                        "color": "#ffffff",
                        "background-color": "#7FDBFF"
                    },
                    multiple=True,
                ),
            ],
            className='four columns',
            style={}
        ),
        html.Div(
            className='four columns',
            # style={
            #     "width": "33.6666666667%%",
            #     "height": "30px",
            #     "lineHeight": "60px",
            #     "textAlign": "center",
            #     "margin": "0px",
            # },
        ),
        html.Div(
            [
                html.Button(
                    id="export-data",
                    children= html.A(
                            children='  Exporter (.csv)...',
                            id='download-link',
                            download="donnees_points.csv",
                            href="",
                        )
                    ,
                    className='',
                    style={
                        "width": "100%",
                        "height": "30px",
                        "lineHeight": "30px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "0px",
                        "background-color": "#151a42"
                    },
                ),
            ],
            className='four columns',
            style={'float': 'right',
                   'position': 'relative'}
        ),
        ],
        className='row'),

    html.Div(
        [html.Div(
            dcc.Graph(
            id='example-graph-2',
            style={'height' : "80vh"},
            figure={
                    # 'data': [
                    #     {'x': df.Date, 'y': df.iloc[:,2] , 'type': 'scatter', 'name': 'SF'},
                    #     {'x': df.Date[[50,100]], 'y': [100,100], 'name': 'SF2','mode': 'markers','marker': {'size': 12}},
                    # ],
                    'layout': {
                        'clickmode': 'event+select',
                        'xaxis' : {'rangeslider' : {'visible': True } },
                        'plot_bgcolor': colors['background'],
                        'paper_bgcolor': colors['background'],
                        'font': {
                            'color': colors['text']
                        }
                    }
                }
            ),
            className='eight columns')
        ,
        html.Div(
            ddt.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in ['Dates','Débits', 'Dérivée','Volume Cumulatif']],
            editable=True,
            sort_action="native",
            sort_mode="multi",
            row_deletable=True,
            style_table={
                'maxHeight': '70vh',
                'overflowY': 'scroll',
                'margin-top': '40px'
            },
            ),
            className='four columns')
        ],
        className='row'
    )

 ,
    html.Div(className='row', children=html.Div([
            html.Pre(id='click-data'),
        ], className='three columns')),

    html.Div(id='intermediate-value', style={'display': 'none'})
])


@app.callback(
    Output('table', 'data'),
    [Input('example-graph-2', 'clickData')],
    [State('table', 'data'),
     State('table', 'columns')])
def display_click_data(clickData, rows,columns):
    if not clickData is None:
        value = [clickData['points'][0]['x']]
        [value.append(str(round(float(i['y']),2))) for i in clickData['points']]
        zipped = zip(columns,value)
        add_row = {c['id']: d for c,d in zipped}
        if rows is None:
            rows = [add_row]
        else:
            rows.append(add_row)
        return rows


def read_files(file_contents, uploaded_files ):
    fig = None
    df = None
    if uploaded_files is not None :
        filename = uploaded_files[0]
        print(filename)
        contents = file_contents[0]
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
                # Assume that the user uploaded a CSV file
                df = pd.read_csv(
                    io.StringIO(decoded.decode('latin-1')))
            elif 'xls' in filename:
                # Assume that the user uploaded an excel file
                df = pd.read_excel(io.BytesIO(decoded))
            print(df)
        except Exception as e:
            print(e)
            return html.Div([
                'There was an error processing this file.'
            ])
    return df


@app.callback(dash.dependencies.Output('example-graph-2', 'figure'),
    [Input("upload-data", "contents")],[State("upload-data", "filename")],
)
def update_graph_scatter(uploaded_file_contents, uploaded_filenames ):
    df = read_files(uploaded_file_contents, uploaded_filenames)
    traces = []
    fig = plotly.tools.make_subplots(rows=1, cols=1, vertical_spacing=0.2)
    if df is not None:
        trace1 = dict(x= df.iloc[:,1],
                      y= df.iloc[:,2],
                      name= 'Débit',
                      type= 'scatter')

        trace2 = dict(x= df.iloc[:,1],
                      y= df.iloc[:,2].diff(),
                      name= 'Dérivée',
                      type= 'scatter')

        trace3 = dict(x= df.iloc[:,1],
                      y= df.iloc[:,2].cumsum(),
                      name= 'Volume cumulatif',
                      type= 'scatter',
                      yaxis= 'y2')


        layout = dict(hovermode='x',
                      xaxis=dict(title='Date',
                                 rangeslider=dict(Visible=True)
                                 ),
                      yaxis=dict(  # left yaxis
                                 showgrid=True,
                                 title='Débit/Dérivée'
                                 ),
                      yaxis2=dict(overlaying='y',
                                  anchor='x',
                                  side='right',
                                  showgrid=False,
                                  title='Volume cumulatif'
                                  )
                      )
        fig = dict(data=[trace1, trace2, trace3], layout=layout)
    return fig


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


@app.callback(Output('download-link', 'href'),
             [Input('table', 'data')],
             [State('download-link', 'href')]
              )
def save_current_table(tablerows,href1):
    table_df = pd.DataFrame(tablerows) #convert current rows into df
    csv_string = table_df.to_csv(index=False,encoding='latin-1')
    csv_string = "data:text/csv;charset=latin-1," + urllib.parse.quote(csv_string.encode('latin-1'))
    return csv_string


# @app.callback(
#     dash.dependencies.Output("file-list", "children"),
#     [dash.dependencies.Input("upload-data", "filename"), dash.dependencies.Input("upload-data", "contents")],
# )
# def update_output(uploaded_filenames, uploaded_file_contents):
#     """Save uploaded files and regenerate the file list."""
#
#     if uploaded_filenames is not None and uploaded_file_contents is not None:
#         for name, data in zip(uploaded_filenames, uploaded_file_contents):
#             save_file(name, data)

    # files = uploaded_files()
    # if len(files) == 0:
    #     return [html.Li("No files yet!")]
    # else:
    #     return [html.Li(file_download_link(filename)) for filename in files]

if __name__ == '__main__':
    app.run()
    # app.run_server(host='127.0.0.1', port=8020, debug=True)
