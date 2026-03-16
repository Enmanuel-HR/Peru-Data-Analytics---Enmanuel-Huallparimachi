import plotly.express as px

def create_impact_bar_chart(df, x_col, y_col, title):
    fig = px.bar(df, x=x_col, y=y_col, color=y_col, color_continuous_scale="Viridis")
    fig.update_layout(title=title)
    return fig

def create_industry_pie_chart(counts, values, names):
    fig = px.pie(values=values, names=names, hole=.3)
    return fig
