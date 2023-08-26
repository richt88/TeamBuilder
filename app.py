###############################################################################
# Package Imports
import pandas as pd
from datetime import datetime, timedelta

import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
from dash import Dash, Input, Output, dash_table, dcc, html
import dash_bootstrap_components as dbc

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
###############################################################################
# App Layout
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])


app.layout = dbc.Container([
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
    html.H3('Team', id='team_title'),
    dbc.Row([
            dbc.Col([
                html.Div(id='team_stats'),
                html.Div(id='team_table'),
                html.Button('Clear List', id='clear_button', n_clicks=0)],
                width=7),
            dbc.Col([
                html.H5('Team Skills Plot'),
                dcc.RadioItems(id='team_radar_radio',
                               labelStyle = {'display': 'flex'}),
                html.Div(id='team_radar', children=[])],
                width=5)
            ]),
                
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
                                      
        
        
        
        return  [dcc.Markdown(f"#### {df_filtered['Name'].values[0]}"),
                 dcc.Markdown(f"###### {df_filtered['Dept'].values[0]} | {df_filtered['Role'].values[0]} | *£{df_filtered['Pay Rate'].values[0]}/hr*"),
                 dcc.Markdown(f"###### Average {df_hours_6m_mean:.1f} hrs/wk"),
                 dcc.Graph(id='radar_plot', 
                           figure=fig),
                 ]
        
    return []


# Add to Team list
@app.callback(
            [Output('team_table', 'children'),
             Output('team_stats', 'children'),
             Output('team_radar_radio', 'options')],
            [Input('skill_scatter', 'clickData'),
             Input('clear_button', 'n_clicks')])
def callback_team_table_update(clickData, n_clicks):
    global df_merge
    global clear_clicks
    
    if clickData:
        ##### Update Table #####
        # Filter PDR df
        EID = clickData['points'][0]['customdata'][1]
        df_merge.loc[EID,'Selected'] = True    
    
    
    if n_clicks > clear_clicks:
        clear_clicks =  n_clicks
        df_merge['Selected'] = False
    
    
    if clickData:
        show_cols = ['Name', 'Dept', 'Role', 'Pay Rate']
        
        df_filtered = df_merge.loc[df_merge['Selected']]  
        
        table = dbc.Table.from_dataframe(df_filtered[show_cols].sort_values(['Dept', 'Pay Rate'], ascending=False),
                                         id='data_table', 
                                         striped=True, 
                                         bordered=True,
                                         responsive=True)
        
        
        ##### Update Team Stats #####
        avg_pay = df_filtered['Pay Rate'].mean()
        stats = dcc.Markdown(f'###### Team Average Rate - £{avg_pay:.2f}/hr')
        
        options = [{'label':dept,
                    'value': dept} for dept in df_filtered['Dept'].unique() ]
        
        return [table], [stats], options
    
    else: 
        return [], [], []
    
# Team Radar Charts
@app.callback(
            [Output('team_radar', 'children')],
            [Input('team_radar_radio', 'value'),
             Input('skill_scatter', 'clickData'),
             Input('clear_button', 'n_clicks')])
def callback_team_radar_update(value, click_data, n_clicks):
    global df_merge
    
    if value:
        # Filter data
        df_filtered = df_merge.loc[(df_merge['Dept'] == value) & (df_merge['Selected']==True)]
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
    app.run_server(debug=True, port=8002)





