import io
import os
import dash
import time
import base64
import datetime
import dash_table
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from cleaningmodule import Dclean, uniqueWords
from dash.dependencies import Input, Output, State


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server # the Flask app

colors = {
    'background': '#111111',
    'header': '#19627D',
    'subtext': '#5CB9DA'
}
image_filename = 'logo.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

UPLOAD_DIRECTORY = "app_uploaded_files"
DOWNLOAD_DIRECTORY = "annotated_data"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)


app.layout = html.Div([
    html.Img(
        src='data:image/png;base64,{}'.format(encoded_image.decode()),
                            id="project-logo",
                            style={
                                "height": "30px",
                                "width": "auto",
                                "margin-bottom": "10px",
                                "margin-top": "10px",
                                "margin-left": "10px",
                            },
                ),
    html.Div([
                html.H1(children='Automated Data Cleaning', style={
                                                                'textAlign': 'center',
                                                                'color': colors['header'],
                                                                "margin-top": "25px"
                                                                })
            ],className="app-header",
    ),
    dcc.Tabs(
        id="tabs-with-classes",
        value='tab-4',
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            dcc.Tab(
                label='Detect Phrase',
                value='tab-4',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Hr(),
                    html.Label("Type your statment below"),
                    dcc.Textarea(
                    id='textarea-example',
                    value='Clear this area then write not less than 100 words',
                    style={'width': '100%', 'height': 200},
                    ),
                    html.Div(id="some_output"),
                    html.Button('Detect', id='detect_button', n_clicks=0),
                    #html.Div(id="output2"),
                    dcc.Loading(
                                id="loading-detection",
                                children=[html.Div(id='detection_output'),],
                                type="graph",
                                fullscreen=False
                                ),
                    html.Hr(),
                ]
            ),
            dcc.Tab(
                label='Phase1: Preprocessing',
                value='tab-1',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Hr(),
                    dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select Files')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                # Allow multiple files to be uploaded
                                multiple=True
                            ),
                    dcc.Loading(
                                id="loading-2",
                                children=[html.Div(id='upload_data-to-table'),],
                                type="circle",
                                fullscreen=True
                                ),
                            
                ]
            ),
            dcc.Tab(
                label='Phase2: Detection',
                value='tab-2',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Hr(),
                    html.H5("1- Process the file and select your target column: "),
                    html.Div(id="output1"),
                    html.Br(),
                    html.Button('Process', id='process_button', n_clicks =0, style={
                                            'textAlign': 'right',
                                            'color': '#c92023'}),
                    html.Br(),
                    dcc.Loading(
                                id="loading-3",
                                children=[html.Br(), dcc.RadioItems(
                                id ='column_radioption',
                                # options=options_list, 
                                labelStyle={'display': 'inline-block'}
                                ),
                                html.Br(),
                                html.Div("Please make sure your target column selected is correct before your press Detect",
                                style={
                                            'textAlign': 'left',
                                            'color': '#c92023'}),
                                html.Br()],
                                type="graph",
                                fullscreen=False
                                ),
                    html.Br(),
                    html.H5(id="indicate-column-selection"),
                    html.Button('Detect', id='Detect_button', n_clicks =0),
                    dcc.Loading(
                                id="loading-4",
                                children=[html.Br(), 
                                html.Br(),
                                html.Div(id="file-detection-confirmation", style={
                                            'textAlign': 'left',
                                            'color': '#10913d'}),
                                ],
                                type="graph",
                                fullscreen=False
                                ),
                    html.Hr(),
                ]
            ),
            dcc.Tab(
                label='Phase3: Clean Data',
                value='tab-3', className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Hr(),
                    html.H5('Get the annotated file: '),
                    html.Br(),
                    html.Button('Prepare annotated file', id='get_annotated_file', n_clicks =0),
                    html.Br(),
                    dcc.Loading(children = [
                                html.Div(id='annotated_link'),
                                ],
                                type="default",
                                fullscreen=False
                                ),
                    html.Hr(),
                    html.H5('Get the file after removal of dirty data: '),
                    html.Br(),
                    html.Button('Get clean file', id='get_clean_file', n_clicks =0),
                    html.Br(),
                    dcc.Loading(children = [
                                html.Div(id='clean_link'),
                                ],
                                type="default",
                                fullscreen=False
                                )
                ]
            ),
        ]),
])

def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([

        html.H5('Table view (table name= {}):'.format(filename)),
        html.H5(content_type),
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            fixed_rows={ 'headers': True, 'data': 0 },
            style_table={
                        'overflowX': 'scroll',
                        'maxHeight': '300px',
                        'overflowY': 'scroll'
                        },
            style_cell={
                        'height': 'auto',
                        # all three widths are needed
                        'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                        'whiteSpace': 'normal'
                       }
        ),

        html.Hr(),  # horizontal line
    ])

@app.callback(
    Output('detection_output', 'children'),
    [Input('detect_button', 'n_clicks')],
    [State('textarea-example', 'value')]
)
def classify_phrase(value, n_clicks):
    '''
    For some reason parameters here has swapped content and have no time
    to check why is this happening or what causes it.
    '''
    if value == 0:
        raise PreventUpdate #return 'didnt start yet bro'
    else:
        try:
            cleaner = Dclean('statmet cleaner')
            classification_result = cleaner.classify_statement(n_clicks)
            return 'You have entered: \n{}'.format(classification_result)
        except Exception as e:
            return 'Sorry we ran into an error \n{}'.format(e)


# @app.callback(
#     Output("output1", "children"),
#     [Input("input1", "value")],
# )
# def get_column_name(input1):
#     return u'Input 1 {}'.format(input1)

@app.callback(
    Output("column_radioption", "options"),
    [Input(component_id='process_button', component_property='n_clicks')],
    [State('upload-data', 'filename')]
)
def get_text_column(n_clicks, list_of_names):
    if n_clicks == 0:
        raise PreventUpdate #return 'didnt start yet bro'
    else:
        try:
            c = Dclean('cleaner')
            filepath = '{}/{}'.format(UPLOAD_DIRECTORY,list_of_names[0])
            # print(list_of_names[0])
            # print(filepath)
            dataf = pd.read_csv(filepath)
            options_list = list()
            for column in dataf.columns:
                options_list.append({'label': column, 'value': column})
            # print(options_list)
            return options_list
        except Exception as e:
            return u'We face an error\n{}'.format(e)

@app.callback(
    Output('indicate-column-selection', 'children'),
    [Input('column_radioption', 'value')]
)
def radio_option(radio_items_value):
    return '2- Go on to detect column {}'.format(radio_items_value)

@app.callback(
    Output('file-detection-confirmation', 'children'),
    [Input(component_id = 'Detect_button', component_property = 'n_clicks')],
    [State('column_radioption', 'value'), State('upload-data', 'filename')]
)
def detect_column(n_clicks, radio_items_value, list_of_names):
    if n_clicks == 0:
        raise PreventUpdate #return 'didnt start yet bro'
    else:
        try:
            # getting the file to iterate column rows
            filepath = '{}/{}'.format(UPLOAD_DIRECTORY,list_of_names[0])
            dataf = pd.read_csv(filepath)
            print(type(dataf[radio_items_value]))
            print(dataf[radio_items_value][0])
            print(len(dataf[radio_items_value]))
            
            # the following list will hold the result of the prediction
            predictions_list = list()

            # classifier object instantiation
            cleaner = Dclean('column cleaner')

            for row in range(len(dataf[radio_items_value])):
                classification_result = cleaner.classify_statement(dataf[radio_items_value][row])
                predictions_list.append(classification_result)
            dataf['prediction'] = predictions_list
            print('{}/{}'.format(DOWNLOAD_DIRECTORY,list_of_names[0]))
            dataf.to_csv('{}/{}'.format(DOWNLOAD_DIRECTORY,list_of_names[0]))
            time.sleep(1.5)
            return 'Detection completed for column {}'.format(radio_items_value)
        except Exception as e:
            return str(e)


@app.callback(
    Output('annotated_link', 'children'),
    [Input(component_id = 'get_annotated_file', component_property = 'n_clicks')],
    [State('upload-data', 'filename')]
)
def download_annot(n_clicks, list_of_names):
    if n_clicks == 0:
        raise PreventUpdate #return 'didnt start yet bro'
    else:
        try:
            # getting the file to iterate column rows
            filepath = '{}/{}'.format(DOWNLOAD_DIRECTORY, list_of_names[0])
            df_name = pd.read_csv(filepath)
            time.sleep(1)
            return html.Div([html.A("Download annotated file"
                            ,id='Download_link'
                            ,download=filepath
                            ,href=''
                            ,target='_blank'),
            ])
        except Exception as e:
            return str(e)


@app.callback(
    Output('clean_link', 'children'),
    [Input(component_id = 'get_clean_file', component_property = 'n_clicks')],
    [State('upload-data', 'filename')]
)
def download_annot(n_clicks, list_of_names):
    if n_clicks == 0:
        raise PreventUpdate #return 'didnt start yet bro'
    else:
        try:
            filepath = '{}/{}'.format(DOWNLOAD_DIRECTORY, list_of_names[0])
            df_name = pd.read_csv(filepath)
            df_name[(df_name['prediction'] == "Dirty text")].to_csv('{}/cleaned {}'.format(DOWNLOAD_DIRECTORY, list_of_names[0]))
            time.sleep(1)
            return html.Div([html.A("Download clean file"
                            ,id='Download_clean'
                            ,download='{}/cleaned {}'.format(DOWNLOAD_DIRECTORY, list_of_names[0])
                            ,href=''
                            ,target='_blank'),
            ])
        except Exception as e:
            return str(e)


@app.callback(Output('upload_data-to-table', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        save_file(list_of_names[0], list_of_contents[0])
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


if __name__ == '__main__':
    # app.run_server(debug=True, host = '0.0.0.0', port = '8080')
    app.run_server(debug=True)