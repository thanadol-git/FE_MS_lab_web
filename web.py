import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
with open('../config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create a sidebar
st.sidebar.header("Sample information")
st.sidebar.write("This part is needed for every file that we are creating..")

# Project
proj_name = st.sidebar.text_input("Enter your project name", "Project X")
# Organism
organism = st.sidebar.text_input("Select your organism", "Human")
# Sample type
sample = st.sidebar.text_input("Enter your sample", "Plasma")
# Plate id 
plate_id = st.sidebar.text_input("2.Enter your plate ID", "")
# Samplee/ cohort name
sample_name = st.sidebar.text_input("1.Main cohort name/abbreviation", "Cohort_1")



# Create three tabs
plate_tab, dia_tab, dda_tab, srm_tab = st.tabs(["Plate Design", "DIA", "DDA", "SRM"])


# content for Plate 
with plate_tab:
    st.header("Plate layout")
    
    # Sample types 
    st.subheader("A. Cohort name")
    st.markdown(f"The main cohort samples will be: <span style='color:red'>{sample_name}</span>", unsafe_allow_html=True)

    # plate id 
    if not plate_id:
        plate_id = sample_name
    st.markdown(f"Plate ID: <span style='color:red'>{plate_id}</span>", unsafe_allow_html=True)



    st.subheader("2. Control or Pool")
    st.write("This is a list of control or pool.")
    replace_pos = st.text_area("Example Control, Pool or another cohort", "Pool;A7\nControl;G12\nControl;H12\nCohort_2;C8").split('\n')
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
    
    # format plate_df in a long for mat
    plate_df_long = plate_df.stack().reset_index()
    plate_df_long.columns = ['Row', 'Column', 'Sample']
    
    #Add Position column to plate_df_long


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
    st.header("DIA Injection")

    # Choices Injection position with select boxes from red green and blue 
    injection_pos = st.selectbox("1.Select your injection position", ["Red", "Green", "Blue"])

    st.markdown(f"Selected injection position: <span style='color:red'>{injection_pos}</span>", unsafe_allow_html=True)
    
    # Lambda function to check the color and return the corresponding letter
    color_to_letter = lambda color: 'R' if color == 'Red' else 'B' if color == 'Blue' else 'G' if color == 'Green' else ''
    
    # Get the corresponding letter for the selected injection position
    injection_pos_letter = color_to_letter(injection_pos)
    st.write(f"The corresponding letter for {injection_pos} is {injection_pos_letter}")

    # Injection volumes
    injection_vol = st.slider("2.Select your injection volume", 0.01, 0.1, 0.01, 0.01)
    st.markdown(f"Selected injection volume (ul): <span style='color:red'>{injection_vol}</span>", unsafe_allow_html=True)
    
    # Path to the data
    uploaded_dir = st.text_input("3.Enter the directory path to the data", "C:\data\yourdir")
    st.markdown(f"The data will be saved at: <span style='color:red'>{uploaded_dir}</span>", unsafe_allow_html=True)
    
    # Path to method file 
    method_file = st.text_input("4.Enter the directory path to the method file", "C:\Xcalibur\methods\method1")
    st.markdown(f"The method file for MS is from: <span style='color:red'>{method_file}</span>", unsafe_allow_html=True)

    # Date of injection
    date_injection = st.date_input("5.Date of injection", pd.Timestamp("today"))
    # format date_injection to YYYYMMDD as text
    date_injection = date_injection.strftime("%Y%m%d")
    st.markdown(f"Date of injection: <span style='color:red'>{date_injection}</span>", unsafe_allow_html=True)
    
    # Sample order column 
    plate_df_long['Position'] =  plate_df_long['Row'] + plate_df_long['Column'].astype(str)
    # Injection volume column
    plate_df_long['Inj Vol'] = injection_vol
    # Instrument method column
    plate_df_long['Instrument Method'] = method_file
    # Path column 
    plate_df_long['Path'] = uploaded_dir
    # File name 
    plate_df_long['File Name'] = date_injection + "_" + proj_name + "_" + plate_id + "_" + plate_df_long['Position']
    plate_df_long['Position'] =  injection_pos_letter + plate_df_long['Position'] 
    
    output_order_df = plate_df_long[['File name', 'Path', 'Instrument Method', 'Position','Inj Vol']]
    # Randomize row order
    output_order_df_rand = output_order_df.sample(frac=1).reset_index(drop=True)
    
    # QC standard and washes 
    st.markdown("### Wash")
    
    ## Wash parameters
    wash_path = st.text_input("Enter the path to the washes", "C:\\data\\wash")
    wash_method = st.text_input("Enter the method file for washes", "C:\\Xcalibur\\methods\\wash")
    wash_pos = st.text_input("Enter the position for washes", "G3")
    wash_df = pd.DataFrame({
        "File Name": ['wash'],
        "Path": [wash_path],
        "Instrument Method": [wash_method],
        "Position": [wash_pos],
        "Inj Vol": [str(injection_vol)] 
    })
    # st.write(wash_df, index=False)
    
    ## QC standard parameters
    st.markdown("### QC Plasma standard")

    qc_path = st.text_input("Enter the path to the QC standard", "C:\\data\\QC")
    qc_method = st.text_input("Enter the method file for QC standard", "C:\\Xcalibur\\methods\\QC")
    qc_pos = st.text_input("Enter the position for QC standard", "GE1")
    # qc_vol = st.text_input("Enter the volume for QC standard", "0.01")
    qc_df = pd.DataFrame({
        "File Name": ['QC_Plasma'],
        "Path": [qc_path],
        "Instrument Method": [qc_method],
        "Position": [qc_pos],
        "Inj Vol": [str(injection_vol)]
    })
    
    # Bind row from wash_df before and after qc_df
    qc_df = pd.concat([qc_df, wash_df], axis=0)
    qc_df = qc_df.reset_index(drop=True)
    
    # st.write(qc_df, index=False )

    # Download data

    ## export order sampel name 
    sample_order_name = "_".join([proj_name, "Sample", "Order", plate_id]) + ".csv"

    ## export order sample
    # Bind row from wash_df after every 8 rows in output_order_df
    chunks = [output_order_df_rand[i:i+8] for i in range(0, len(output_order_df_rand), 8)]
    output_with_wash = pd.concat([pd.concat([chunk, wash_df], ignore_index=True) for chunk in chunks], ignore_index=True)
    
    # concat wash and qc dataframes
    output_with_wash = pd.concat([wash_df, qc_df, output_with_wash, qc_df], ignore_index=True)
    
        # Convert DataFrame to CSV
    csv_data = output_with_wash.to_csv(index=False)
    
    # Add 'Type=4,,,,' to the beginning of the CSV data
    csv_data = 'Bracket Type=4,,,,\n' + csv_data
    
    # st.write(output_with_wash)
    
    ## Download button for export file
    st.markdown("### Download data")
    st.markdown("The data below is an example for sample order in Xcalibur. The injection order will be randomized and added with wash and qc standard.")
    st.write(output_order_df)
    st.markdown("Click below to download the data.") 
    # Download button for output_order_df
    st.download_button(
        label="Download sample order",
        data=csv_data,
        file_name=sample_order_name,
        mime='csv'
    )
        


# Content for DDA
# with dda_tab:
    # st.header("DDA")
    # st.write("This is the content of the second tab.")
    # # Editable plot
    # df = pd.DataFrame({
    #     'x': np.random.randn(100),
    #     'y': np.random.randn(100)
    # })
    # fig = px.line(df, x='x', y='y', title="Editable Line Plot")
    # st.plotly_chart(fig)

# Content for Tab 3
# with srm_tab:
    # st.header("SRM or Targeted proteomics")
    # st.write("This is the content of the third tab.")
    # # Another interactive plot
    # df = pd.DataFrame({
    #     'x': np.random.randn(100),
    #     'y': np.random.randn(100)
    # })
    # fig = px.histogram(df, x='x', title="Interactive Histogram")
    # st.plotly_chart(fig)

