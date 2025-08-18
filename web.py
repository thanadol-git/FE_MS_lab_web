import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px

# Split to separate filess
from sidebar import create_sidebar
from tabs.intro_tab import intro_detail
from tabs.plate_tab import plate_design_tab


# Sidebar
proj_name, organism, sample, plate_id, sample_name, machine, acq_tech = create_sidebar()


# Create three tabs
intro_tab, plate_tab, sample_order, sdrf_tab = st.tabs(["Intro", "Plate Design", "Sample Order", "SDRF"])

with intro_tab:
    intro_detail()

with plate_tab:
    plate_design_tab()


# Content for DIA
with sample_order:
    st.header(acq_tech + " Injection")
    

    # Choices Injection position with select boxes from red green and blue 
    injection_pos = st.selectbox("1.Select your Autosampler injection position", ["Red", "Green", "Blue"])

    # Determine the color based on the injection position
    load_color = 'red' if injection_pos == 'Red' else 'green' if injection_pos == 'Green' else 'blue'

    # Display the injection position with the corresponding color
    st.markdown(f"Selected injection position: <span style='color:{load_color}'>{injection_pos}</span>", unsafe_allow_html=True)
    
    # Lambda function to check the color and return the corresponding letter
    color_to_letter = lambda color: 'R' if color == 'Red' else 'B' if color == 'Blue' else 'G' if color == 'Green' else ''
    
    # Get the corresponding letter for the selected injection position
    injection_pos_letter = color_to_letter(injection_pos)
    st.write(f"The corresponding letter for {injection_pos} is {injection_pos_letter}")

    # Injection volumes
    injection_vol = 0.1

    injection_vol = st.slider("2.Select your injection volume", 0.01, 20.0, injection_vol, 0.01)
    cols = st.columns(2)
    with cols[0]:
        # Add suggestion volumn buttons     
        button1, button2, button3, button4, button5 = st.columns(5)
        if button1.button("0.01 ul", use_container_width=True):
            injection_vol = 0.01
        if button2.button("0.1 ul", use_container_width=True):
            injection_vol = .1
        if button3.button("5.0 ul", use_container_width=True):
            injection_vol = 5.0
        if button4.button("10.0 ul", use_container_width=True):
            injection_vol = 10.0
        if button5.button("15.0 ul", use_container_width=True):
            injection_vol = 15.0
    with cols[1]:
        injection_vol = st.text_input("Enter your injection volume (ul)", str(injection_vol))
    
    
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
    
    # Filter the plate_df_long to only include the samples
    plate_df_long = plate_df_long[plate_df_long['Sample'] != 'EMPTY']
    
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
    
    output_order_df = plate_df_long[['File Name', 'Path', 'Instrument Method', 'Position','Inj Vol']]
    # Remove 'EMPTY' wells from the output_order_df
    output_order_df = output_order_df[output_order_df['Position'] != 'EMPTY']
    # Randomize row order
    output_order_df_rand = output_order_df.sample(frac=1).reset_index(drop=True)
    
    # QC standard and washes 
    cols = st.columns(2)
    with cols[0]:
        
        st.markdown("### Wash")
        
        ## Wash parameters
        wash_path = st.text_input("Enter the path to the washes", "C:\\data\\wash")
        wash_method = st.text_input("Enter the method file for washes", "C:\\Xcalibur\\methods\\wash")
        wash_pos = st.text_input("Enter the position for washes", "G3")
        injection_vol_wash = st.text_input("Modify your 'Wash' injection volume (ul)", str(injection_vol))

        wash_df = pd.DataFrame({
            "File Name": ['wash'],
            "Path": [wash_path],
            "Instrument Method": [wash_method],
            "Position": [wash_pos],
            "Inj Vol": [injection_vol_wash] 
        })
        # st.write(wash_df, index=False)
    

    with cols[1]:
        ## QC standard parameters
        st.markdown("### QC Plasma standard")

        qc_path = st.text_input("Enter the path to the QC standard", "C:\\data\\QC")
        qc_method = st.text_input("Enter the method file for QC standard", "C:\\Xcalibur\\methods\\QC")
        qc_pos = st.text_input("Enter the position for QC standard", "GE1")
        injection_vol_qc = st.text_input("Modify your 'QC' injection volume (ul)", str(injection_vol))

        # qc_vol = st.text_input("Enter the volume for QC standard", "0.01")
        qc_df = pd.DataFrame({
            "File Name": ['QC_Plasma'],
            "Path": [qc_path],
            "Instrument Method": [qc_method],
            "Position": [qc_pos],
            "Inj Vol": [injection_vol_qc]
        })
        
        # Bind row from wash_df before and after qc_df
        qc_df = pd.concat([qc_df, wash_df], axis=0)
        qc_df = qc_df.reset_index(drop=True)
        
        # st.write(qc_df, index=False )

        

    # Download data

    ## export order sampel name 
    sample_order_name = "_".join([datetime.now().strftime("%Y%m%d%H%M"), proj_name, "Sample", "Order", plate_id]) + ".csv"

    ## export order sample
    ### DIA/DDA plate
    
    # Bind row from wash_df after every 8 rows in output_order_df
    chunks = [output_order_df_rand[i:i+8] for i in range(0, len(output_order_df_rand), 8)]
    # Add wash and qc standard after every 8 rows
    output_with_wash = pd.concat([pd.concat([chunk, wash_df], ignore_index=True) for chunk in chunks], ignore_index=True)
    
    ### SRM plate
    if acq_tech == "SRM":
        output_with_wash = output_order_df_rand
    
    # concat wash and qc dataframes
    output_with_wash = pd.concat([wash_df, qc_df, output_with_wash, qc_df], ignore_index=True)
    
        # Convert DataFrame to CSV
    csv_data = output_with_wash.to_csv(index=False)
    
    # Add 'Type=4,,,,' to the beginning of the CSV data
    csv_data = 'Bracket Type=4,,,,\n' + csv_data
    
    
    ## Download button for export file
    st.markdown("### Download data")
    
    st.markdown("The data below is an example for sample order in Xcalibur. The injection order will be randomized and added with wash and qc standard. Be sure with SRM injection")
    st.write(output_order_df)
    st.markdown("Click below to download the data.") 
    # Download button for output_order_df
    st.download_button(
        label="Download sample order",
        data=csv_data,
        file_name=sample_order_name,
        mime='csv'
    )
        

with sdrf_tab:
    st.header("SDRF")
    ms_file = st.selectbox("MS file output", ["RAW", "mzML"])

    # CE = st.markup("Collision Energy (CE) is set to 27 NCE. If you want to change it, please edit the code in the web.py file.")
    
    # Create a DataFrame for the SDRF
    sdrf_df = pd.DataFrame({
        # "source name": [f"{proj_name}_{sample_name}"],
        # "characteristics[organism]": ["Homo sapiens"],
        # "characteristics[organism part]": ["plasma"], 
        # "characteristics[age]" : ["not available"], 
        # "characteristics[developmental stage]" : ["not available"], 
        # "characteristics[sex]" : ["not available"], ["not available"], 
        # "characteristics[ancestry category]" : ["not available"], 
        # "characteristics[cell type]" : ["not available"], 
        # "characteristics[cell line]" : ["not available"], 
        # "characteristics[disease]" : ["not available"], 
        # "characteristics[individual]" : ["not available"], 
        # "characteristics[biological replicate]" : ["1"]
        # "material type" : ["plasma"],
        "assay name" : [f"run {i}" for i in range(1, output_order_df.shape[0] + 1)],
        # "technology type" : ["proteomic profiling by mass spectrometry"]
        "comment[data file]" : output_order_df["File Name"]+ "." + ms_file,
        "comment[file uri]"	: output_order_df["File Name"] + "." + ms_file #,
        # "comment[proteomics data acquisition method]" : ["NT=Data-Independent Acquisition;AC=NCIT:C161786"],
        # "comment[fractionation method]"	: ["NT=High-performance liquid chromatography;AC=PRIDE:0000565"],
        # "comment[fraction identifier]" :	["1"],
        # "comment[label]" : ["AC=MS:1002038;NT=label free sample"],	
        # "comment[technical replicate]" : ["1"],	
        # "comment[cleavage agent details]" : ["NT=Trypsin;AC=MS:1001251"],	
        # "comment[cleavage agent details]" : ["NT=Lys-C;AC=MS:1001309"],	
        # "comment[ms2 mass analyzer]" : ["not available"], 	
        # "comment[instrument]" : ["NT=Q Exactive HF;AC=MS:1002523"]
        # "comment[modification parameters]" :	["not available"]
        # "comment[dissociation method]" : ["AC=MS:1000422;NT=HCD"], 
        # "comment[collision energy]" :	["27 NCE"],
        # "comment[precursor mass tolerance]" :	["not available"]
        # "comment[fragment mass tolerance]" : ["not available"]


    })
    # Create empty pandas DataFrame 
    # comment_df = pd.DataFrame(columns=[
    #     "source name",
    sdrf_df["comment[proteomics data acquisition method]"] = "T=Data-Independent Acquisition;AC=NCIT:C161786"
    sdrf_df["comment[fractionation method]"] = "NT=High-performance liquid chromatography;AC=PRIDE:0000565"
    sdrf_df["comment[fraction identifier]"] = "1"
    sdrf_df["comment[label]"] = "AC=MS:1002038;NT=label free sample"
    sdrf_df["comment[technical replicate]"] = "1"
    # sdrf_df["comment[cleavage agent details]"] = "not available"
    sdrf_df["comment[ms2 mass analyzer]"] = "NT=Trypsin;AC=MS:1001251"
    sdrf_df["comment[instrument]"] = "not available"
    sdrf_df["comment[modification parameters]"] = "not available"
    sdrf_df["comment[dissociation method]"] = "AC=MS:1000422;NT=HCD"
    sdrf_df["comment[collision energy]"] = "27 NCE"
    sdrf_df["comment[precursor mass tolerance]"] = "not available"
    sdrf_df["comment[fragment mass tolerance]"] = "not available"

    st.write(sdrf_df)
    
    # Add link to website github.com/thanadol-git/quantms_example/
    url = "https://www.github.com/thanadol-git/quantms_example/"
    st.markdown("check out this [link](%s)" % url)

    # # Convert DataFrame to CSV
    # csv_data = sdrf_df.to_csv(index=False)
    
    # # Add 'Type=4,,,,' to the beginning of the CSV data
    # csv_data = 'Bracket Type=4,,,,\n' + csv_data
    
    # # Download button for SDRF
    # st.markdown("Click below to download the SDRF data.") 
    # st.download_button(
    #     label="Download SDRF",
    #     data=csv_data,
    #     file_name=f"{proj_name}_SDRF.csv",
    #     mime='csv'