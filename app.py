###############################################################################
# Package Imports
import pandas as pd
from datetime import datetime, timedelta

import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
from dash import Dash, Input, Output, dash_table, dcc, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

import json

pio.templates.default = "plotly_dark"
###############################################################################
# Data Imports
df_emp = pd.read_csv("./data/Generated_Employee_Data.csv",
                     parse_dates=['DOB'])
df_PDR = pd.read_csv("./data/Generated_PDR_Data.csv")
df_time = pd.read_csv("./data/Generated_Timesheet_Data.csv",
                      parse_dates=['Wk_End'])

df_PDR['Role'] = pd.Categorical(df_PDR['Role'], ['Graduate Engineer', 
                                                 'Junior Engineer',
                                                 'Engineer',
                                                 'Senior Engineer',
                                                 'Lead Engineer',
                                                 'Principal Engineer'])
df_merge = df_emp.merge(df_PDR.drop(['Name', 'Dept', 'Role'], axis=1), on='EID')
df_merge['Selected'] = False
df_merge.set_index('EID', drop=False, inplace=True)



# PDR Skills for each Dept & Role
skills_dict = {'Stress' : ['FEA', 'Automation', 'Composite Analysis', 'Hand-Calcs', 'Manufacturing Awarness', 'Fatigue'],
               'Design' : ['CAD', 'Manufacturing', 'Composite Design', 'ALM Methods', 'Drawings', 'Tooling'], 
               'Systems' : ['Specifications', 'Stress Awarness', 'Piping', 'Cabling', 'DMU Design', 'Thermal Analysis'],
               'Lead Engineer': ['Leadership', 'Bidding', 'Client Handling'], 
               'Principal Engineer':['Leadership', 'Bidding', 'Client Handling', 'Training', 'R&D']}

clear_clicks = 0

local_df = pd.DataFrame(columns=['EID', 'Charge']).to_dict('records')


default_charge = {'Graduate Engineer':18, 
                    'Junior Engineer':24,
                    'Engineer':28,
                    'Senior Engineer':35,
                    'Lead Engineer':42,
                    'Principal Engineer':47}

###############################################################################
# App Layout

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])


app.layout = dbc.Container([
    # Local Data Storage
    dcc.Store(id='selected_data', data=[], storage_type='memory'),
    
    # Header 
    dbc.Row([
            dbc.Col([html.H1('Team Builder',className="fs-1 text"),
                     html.H6('Arrange a team based on required project skills',className="fs-5 text"),
                     ]),
            dbc.Col([html.Img(src=r'assets/Logo.png',
                              width='100%')],
                    width = 3)
            ],
            className="d-flex justify-content-between"),
    html.Hr(),
    # Dropdown Selectors
    html.H4('Talent Finder'),
    dbc.Row([
            dbc.Col([dcc.Dropdown( id = 'skill_cat_dd',
                                  options = [{'label':key, 
                                             'value':key} for key in skills_dict.keys()],
                                  placeholder = "Pick a Required Skill Category",
                                  value='Design',
                                  style={'color':'black'})],
                    width=4),
            dbc.Col([dcc.Dropdown( id = 'skill_dd',
                                  placeholder = "Pick a Required Skill...",
                                  style={'color':'black'},
                                  value='CAD')],
                                  
                    width=4)
            ]),
    html.Br(),

    # Plots
    dbc.Row([
             dbc.Col([dcc.Graph(id='skill_scatter',
                                className="h-100",
                                responsive=True)
                      ],
                    width=7,
                    ),
             dbc.Col(id='radar_col', children = [],
                    width=5),
            ]),
    html.Hr(),
    
    # Team Plots
    dbc.Row([
            dbc.Col([
                html.H3('Team Skills Plot'),
                dcc.RadioItems(id='team_radar_radio',
                               value='hide',
                               labelStyle = {'display': 'flex'}),
                ],
                width=8)
            ]),
    
    dbc.Row([
            dbc.Col([
                html.Div(id='team_radar', children=[])],
                width=8,
                )
            ],justify='center'),
    
    html.Hr(),
    
    dbc.Row([
            dbc.Col([
                html.H3('Team Summary'),
                html.Div(id='team_stats',
                         style={'padding-left': '20px'}),
                html.Br(),
                html.Div([dash_table.DataTable(id='data_table')],
                         id='team_table'),
                ],
                width=12)],
            ),
    html.Br(),
    html.Br(),
    html.Hr(),

    ])


###############################################################################
# App Callbacks

# Skills Dropdown
@app.callback(
            [Output('skill_dd', 'options'),
             Output('skill_dd', 'value')],
            Input('skill_cat_dd', 'value'))
def callback_skill_dd(value):
    options = []
    if value:
        options = [{'label':skill, 
                   'value':skill} for skill in skills_dict[value]]
        
        value = skills_dict[value][0]
    return options, value


# Skills Scatter
@app.callback(
            Output('skill_scatter', 'figure'),
            Input('skill_dd', 'value'))
def callback_scatter_update(value):
    
    fig = {'data':[], 'layout':go.Layout()}
    
    if value:
        # Filter PDR df
        df_filtered = df_merge[df_merge[value]>0]
        
        # Figure Data
        fig = px.scatter(df_filtered,
                            ['Pay Rate'],
                              value,
                              opacity=0.7,
                              hover_data=['Name', 'EID'],
                              color = 'Role'
                                )
        fig.update_layout(showlegend=False, 
                          xaxis_title='Pay Rate (£/hr)',
                          yaxis_title=f'{value} PDR Scores'
                          )
        fig.update_traces(hovertemplate="%{customdata[0]}<br>£%{x}/hr<br>")
    
    return fig


# Hover Data Radar Chart
@app.callback(
            Output('radar_col', 'children'),
            Input('skill_scatter', 'hoverData'))
def callback_radar_update(hoverData):
    
    fig = {}
    
    if hoverData:
        
        # Filter PDR df
        EID = hoverData['points'][0]['customdata'][1]
        df_filtered = df_merge.loc[df_merge['EID']==EID]
        
        # Filter Skills
        role = df_filtered['Role'].values[0]
        dept = df_filtered['Dept'].values[0]
        
        skill_cols = skills_dict.get(dept)
        if skills_dict.get(role):
           skill_cols = skill_cols + skills_dict.get(role)

        # Radar Plot
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
              r=[df_filtered[skill].values[0] for skill in skill_cols],
              theta=skill_cols,
              fill='toself',
              name=df_filtered['Name'].values[0]
        ))
        
        fig.update_layout(
          polar=dict(
                  radialaxis=dict(
                  visible=True,
                  range=[0, 10]
                  )),
          showlegend=False,
          title = f"{df_filtered['Name'].values[0]}"
          )
        
        # Hours plot
        df_hours_6m_mean = df_time[(df_time['Wk_End']>(datetime.today()-timedelta(days=365/2))) &
                                      (df_time['EID']==EID)]['Hours'].mean()
                                      
        
        
        
        return  [dcc.Markdown(f"{df_filtered['Name'].values[0]}"),
                 dcc.Markdown(f"{df_filtered['Dept'].values[0]} | {df_filtered['Role'].values[0]} | *£{df_filtered['Pay Rate'].values[0]}/hr*"),
                 dcc.Markdown(f"Average {df_hours_6m_mean:.1f} hrs/wk"),
                 dcc.Graph(id='radar_plot', 
                           figure=fig),
                 ]
        
    return []


# Add Selected Data
@app.callback(
            [Output('selected_data', 'data')],
            [Input('skill_scatter', 'clickData'),
             Input('selected_data', 'data'),
             Input('data_table', 'data'),
             Input('data_table', 'columns')],
            prevent_initial_call=True)
def callback_team_table_update(clickData, selected_data, rows, columns):

    if selected_data is None:
        raise PreventUpdate
    if clickData is None:
        raise PreventUpdate        
    
        
    if clickData:
        EID = clickData['points'][0]['customdata'][1]
        EID_list = [x['EID'] for x in selected_data]
        if EID not in EID_list:
            role = df_merge.loc[df_merge['EID']==EID]['Role'].values[0]
            selected_data = selected_data + [{'EID':EID, 'Charge':default_charge[role]}]
            selected_data = list({v['EID']:v for v in selected_data}.values())
            
            return [selected_data]
    
        else:
            selected_data = [{'EID':x['EID'], 'Charge':float(x['Charge'])} for x in rows]
            return [selected_data]


# Update Selected Data Table
@app.callback(
            [Output('team_table', 'children')],
            [Input('selected_data', 'data')],
            prevent_initial_call=True)
def callback_team_table_update(select_data):
    
    if select_data:
        show_cols = ['Name', 'EID', 'Dept', 'Role', 'Pay Rate', 'Charge', 'PM']
        
        selected_df = pd.DataFrame(select_data).set_index('EID',  
                                                          drop=False)
        df_filtered = df_merge.loc[df_merge['EID'].isin(selected_df['EID'])]
        #df_filtered.loc[:,'Charge Rate'] = [selected_df.loc[e]['Charge'] for e in df_filtered['EID']]
        df_filtered = df_filtered.merge(selected_df[['Charge']], left_index = True, right_index=True) 
        df_filtered.loc[:,'PM'] = (((df_filtered['Charge'] / df_filtered['Pay Rate'])-1)*100).round(2)

        
        columns = [{'name': 'Name', 'id' :  'Name'},
                   {'name': 'EID', 'id' :  'EID'},
                    {'name': 'Dept', 'id' :  'Dept'},
                    {'name': 'Role', 'id' : 'Role' },
                    {'name': 'Cost (£/hr)', 'id' :'Pay Rate'  },
                    {'name': 'Set Charge (£/hr)', 'id' : 'Charge', 'editable': True},
                    {'name': 'PM (%)', 'id' : 'PM' },]
        
        table = dash_table.DataTable(data=df_filtered[show_cols].to_dict('records'),
                                      columns = columns,
                                      id='data_table',
                                      style_header={'backgroundColor': 'rgb(30, 30, 30)',
                                                    'color': 'white',
                                                    'textAlign':'left'},
                                      style_data={'backgroundColor': 'rgb(50, 50, 50)',
                                                  'color': 'white',
                                                  'textAlign':'left'},
                                      style_table={'overflowX': 'auto',
                                                   },
                                      row_deletable=False,
                                      style_data_conditional=[
                                                                {
                                                                    'if': {
                                                                        'column_id': 'Charge',
                                                                    },
                                                                    'backgroundColor': 'dodgerblue',
                                                                    'color': 'white'
                                                                }])
        
        return [table]
    
    else: 
         return []

# Update Selected Team Stats
@app.callback(
            [Output('team_stats', 'children')],
            [Input('selected_data', 'data')],
            prevent_initial_call=True)
def callback_team_stats_update(select_data):
    
    if select_data:
        selected_df = pd.DataFrame(select_data).set_index('EID',  
                                                          drop=False)
        df_filtered = df_merge.loc[df_merge['EID'].isin(selected_df['EID'])]

        total_cost = df_filtered['Pay Rate'].sum()
        total_charge = sum([x['Charge'] for x in select_data])
        GP = (total_charge - total_cost)
        
        stats = [dcc.Markdown(f'###### Total Team Cost :   £{total_cost:.2f} /hr'),
                 dcc.Markdown(f'###### Total Team Charge : £{total_charge:.2f} /hr'),
                 dcc.Markdown(f'###### Profit :            £{GP:.2f} /hr     ({((GP/total_cost))*100:.2f}%)'),
                 ]
        
        return  [stats]
    else: 
         return []
    
    
# Update Team Plots radio
@app.callback(
            [Output('team_radar_radio', 'options')],
            [Input('selected_data', 'data')],
            prevent_initial_call=True)
def callback_team_radio_update(select_data):
    
    if select_data:
        selected_df = pd.DataFrame(select_data).set_index('EID',  
                                                          drop=False)
        df_filtered = df_merge.loc[df_merge['EID'].isin(selected_df['EID'])]

        options = [{'label':'Hide','value': 'hide'}] +  [{'label':dept,
                    'value': dept} for dept in df_filtered['Dept'].unique() ]
        
        return  [options]
    else: 
         return []    
    
    
# Team Radar Charts
@app.callback(
            [Output('team_radar', 'children')],
            [Input('team_radar_radio', 'value'),
             Input('selected_data', 'data')],
            prevent_initial_call=True)
def callback_team_radar_update(value, select_data):
    
    if value:
        
        if value == 'hide':
            return [" "]
        
        # Filter data
        selected_df = pd.DataFrame(select_data).set_index('EID',  
                                                          drop=False)
        df_filtered = df_merge.loc[(df_merge['Dept'] == value) & (df_merge['EID'].isin(selected_df['EID']))]
        skill_cols = skills_dict.get(value) + ['Leadership', 'Bidding', 'Client Handling', 'Training', 'R&D']
        
        fig = go.Figure()

        for idx, row in df_filtered.sort_values('Pay Rate', ascending=False).iterrows():
            fig.add_trace(go.Scatterpolar(
                  r=[row[skill] for skill in skill_cols],
                  theta=skill_cols,
                  fill='toself',
                  name=row['Name'],
                  mode='lines'
            ))
            
        fig.update_layout(
          polar=dict(
                  radialaxis=dict(
                  visible=True,
                  range=[0, 10]
                  )),
          showlegend=False,
          title = f"{value}"
          )
        
        return [dcc.Graph(figure=fig)]
    else:
        return [" "]



    

###############################################################################
# Run Server
if __name__ == "__main__":
    app.run_server(debug=False, port=8002)

 



