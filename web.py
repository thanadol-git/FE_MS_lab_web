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
plate_tab, dia_tab, dda_tab, srm_tab = st.tabs(["Plate", "DIA", "DDA", "SRM"])


# content for Plate 
with plate_tab:
    st.header("Plate layout")
    # Sample types 
    # Add text area here 
    st.subheader("Sample types")
    st.write("This is a list of sample types.")
    sample_types = st.text_area("Sample types", "Sample\nPool\nCtrl").split('\n')

    # Ensure the dataframe has 12 columns and 8 rows
    data = np.resize(sample_types, (8, 12))
    df = pd.DataFrame(data, columns=[str(i) for i in range(1, 13)], index=list('ABCDEFGH'))
    st.write(df)

    # header 
    st.subheader("Heatmap")
    # Show a heatmap
    # set size to be 127x85

    fig, ax = plt.subplots(figsize=(12.7, 8.5))
    ax.xaxis.tick_top()  # Move the x-axis labels to the top
    sns.heatmap(df, ax=ax, cbar=False, annot=False, xticklabels=True, yticklabels=True, alpha=0, linewidths=0.5, linecolor='darkgrey')
    ax.tick_params(axis='y', rotation=0)  # Keep y-axis ticks straight


    # Add circular cells with color
    norm = plt.Normalize(df.min().min(), df.max().max())
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            value = df.iloc[i, j]
            color = plt.cm.viridis(norm(value))
            ax.add_patch(plt.Circle((j + 0.5, i + 0.5), 0.3, color=color, fill=True))
            ax.text(j + 0.5, i + 0.5, f'{value:.2f}', ha='center', va='center', color='white', fontsize=8)

    st.pyplot(fig)

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