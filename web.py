import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Create a sidebar
st.sidebar.header("Sample information")
st.sidebar.write("This part is needed for every file that we are creating..")

# Inputs
plate_name = st.sidebar.text_input("Enter your plate name", "Type Here")
organism = st.sidebar.text_input("Enter your organism", "Type Here")
# Change organism to be a dropdown
organism = st.sidebar.selectbox("Select your organism", ["Human", "Rat","Other"])
sample = st.sidebar.text_input("Enter your sample", "Type Here")



# Create three tabs
plate_tab, dia_tab, dda_tab, srm_tab = st.tabs(["Plate", "DIA", "DDA", "SRM"])


# content for Plate 
with plate_tab:
    st.header("Plate layout")
    
    # Sample types 
    st.subheader("A. Cohort name")
    sample_name = st.text_input("1.Main cohort name/abbreviation", "Cohort_1")
    st.markdown(f"The main cohort samples will be: <span style='color:red'>{sample_name}</span>", unsafe_allow_html=True)

    # plate id 
    plate_id = st.text_input("2.Enter your plate ID", "")
    if not plate_id:
        plate_id = sample_name
    st.markdown(f"Plate ID: <span style='color:red'>{plate_id}</span>", unsafe_allow_html=True)



    st.subheader("2. Control or Pool")
    st.write("This is a list of control or pool.")
    replace_pos = st.text_area("Example Ctrl, Pool or another cohort", "Pool;A7\nCtrl;G12\nCtrl;H12\nCohort_2;C8").split('\n')
    # Write a  warning message if the position is mentioned more than one time in text area
    # Check if the position is mentioned more than one time
    pos_list = []
    for item in replace_pos:
        if ';' in item:
            text, pos = item.split(';')
            pos_list.append(pos)
    if len(pos_list) != len(set(pos_list)):
        st.warning("Position is mentioned more than one time")


    # Ensure the dataframe has 12 columns and 8 rows
    data = np.resize(sample_name, (8, 12))
    plate_df = pd.DataFrame(data, columns=[str(i) for i in range(1, 13)], index=list('ABCDEFGH'))
    
        # Replace text in the dataframe based on replace_pos
    for item in replace_pos:
        if ';' in item:
            text, pos = item.split(';')
            row = pos[0]
            col = int(pos[1:]) - 1
            plate_df.at[row, str(col + 1)] = text

    
    st.write(plate_df)

    # header 
    st.subheader("3. Layout of plate")
    
    # Heatmap of plate location 
    # from plate_df to heatmap
    fig, ax = plt.subplots()
    # Create a color palette for discrete text
    unique_texts = plate_df.stack().unique()
    palette = sns.color_palette("viridis", len(unique_texts))
    color_mapping = {text: palette[i] for i, text in enumerate(unique_texts)}

    # Create a new DataFrame for the colors
    color_df = plate_df.applymap(lambda x: color_mapping.get(x, (1, 1, 1)))

    # Plot the heatmap with discrete text colors
    sns.heatmap(plate_df.isnull(), cbar=False, cmap='viridis', ax=ax, linewidths=1, linecolor='darkgrey', alpha=0.1)
    ax.xaxis.tick_top()  # Move the x-axis labels to the top
    # fix label rotation on y to be straight
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    # Plot the heatmap with discrete text colors
    sns.heatmap(plate_df.isnull(), cbar=False, cmap='magma', ax=ax, linewidths=0.5, linecolor='darkgrey', alpha = 0.0)
    for i in range(plate_df.shape[0]):
        for j in range(plate_df.shape[1]):
            value = plate_df.iloc[i, j]
            color = color_mapping.get(value, (1, 1, 1))
            ax.add_patch(plt.Circle((j + 0.5, i + 0.5), 0.4, color=color, fill=True))
            ax.text(j + 0.5, i + 0.5, f'{value}', ha='center', va='center', color='white', fontsize=4)

    # Overlay ticks and labels
    # ax.set_xticks(np.arange(len(plate_df.columns)) + 0.5)
    # ax.set_yticks(np.arange(len(plate_df.index)) + 0.5)
    # ax.set_xticklabels(plate_df.columns)
    ax.set_yticklabels(plate_df.index, rotation=0)

    st.pyplot(fig)

# Content for DIA 
with dia_tab:
    st.header("DIA")
    st.write("This is the content of the first tab.")
    # Interactive plot
    df = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    fig = px.scatter(df, x='x', y='y', title="Interactive Scatter Plot")
    st.plotly_chart(fig)


# Content for DDA
with dda_tab:
    st.header("DDA")
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
    st.header("SRM or Targeted proteomics")
    st.write("This is the content of the third tab.")
    # Another interactive plot
    df = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    fig = px.histogram(df, x='x', title="Interactive Histogram")
    st.plotly_chart(fig)

