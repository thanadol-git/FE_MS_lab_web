import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Create a sidebar
st.sidebar.header("Sidebar")
st.sidebar.write("This is the sidebar content.")

# Create three tabs
dia_tab, dda_tab, srm_tab = st.tabs(["DIA", "DDA", "SRM"])

# Content for Tab 1
with dia_tab:
    st.header("FE DIA")
    st.write("This is the content of the first tab.")
    # Interactive plot
    df = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    fig = px.scatter(df, x='x', y='y', title="Interactive Scatter Plot")
    st.plotly_chart(fig)

# Content for Tab 2
with dda_tab:
    st.header("FE DDA")
    st.write("This is the content of the second tab.")
    # Editable plot
    df = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    fig = px.line(df, x='x', y='y', title="Editable Line Plot")
    st.plotly_chart(fig)

# Content for Tab 3
with srm_tab:
    st.header("FE SRM")
    st.write("This is the content of the third tab.")
    # Another interactive plot
    df = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    fig = px.histogram(df, x='x', title="Interactive Histogram")
    st.plotly_chart(fig)