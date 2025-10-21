import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px


# Import functions from other modules
from sidebar import create_sidebar
from tabs.intro_tab import intro_detail
from func.plate_plot import plate_dfplot, process_plate_positions


# Results from Sidebar script
ms_info_output, sample_info_output = create_sidebar()


# Create three tabs
intro_tab, plate_tab, sample_order, sdrf_tab = st.tabs(["Intro", "Plate Design", "Xcalibur",  "SDRF"])

with intro_tab:
    intro_detail()



with plate_tab:
    st.header("Plate layout new")
    
    # Sample types 
    st.subheader("A. Cohort name")
    
    st.markdown(f"The main cohort samples will be: <span style='color:red'>{sample_info_output['sample_name']}</span>", unsafe_allow_html=True)
    st.markdown(f"Plate ID: <span style='color:red'>{sample_info_output['plate_id']}</span>", unsafe_allow_html=True)

    # Adding pool or control
    st.subheader("B. Control or Pool")
    st.write("Please annotate samples with other cohort besides the main cohort in your plate for example pool samples or control samples. Importantly, The 'EMPTY' wells will be removed in the later steps.")

    example_text = "Pool;A7\nControl;G12\nControl;H12\nCohort_2;C8\nEMPTY;A1\nCohort_2;RowD\nCohort_2;RowE\nCohort_2;Col9\nCohort_2;Col8"
    # Text area for input with example_text 8 rows
    text_input = st.text_area("Example Control, Pool or another cohort", example_text, height=200)
    
    # Process plate positions using the function
    plate_df, replace_pos = process_plate_positions(text_input, sample_info_output['sample_name'])

    # header 
    st.subheader("C. Layout of plate")
    plate_df_long = plate_dfplot(plate_df, sample_info_output['plate_id'])
    
    # Store in session state for use in other tabs
    st.session_state.plate_df_long = plate_df_long

with sample_order:
    st.header(ms_info_output['acq_tech'] + " Injection")

    # Get plate_df_long from session state
    if 'plate_df_long' in st.session_state:
        plate_df_long = st.session_state.plate_df_long.copy()
    else:
        st.warning("Please go to the 'Plate Design' tab first to create the plate layout.")
        st.stop()

    plate_df_long['Source Vial'] = list(range(1, plate_df_long.shape[0] + 1))
    # Filter the plate_df_long to only include the samples
    plate_df_long = plate_df_long[plate_df_long['Sample'] != 'EMPTY']

    # Choices Injection position with select boxes from red green and blue 
    injection_pos = st.selectbox("1.Select your Autosampler injection position", ["Red", "Green", "Blue"])

    # Determine the color based on the injection position
    load_color = 'red' if injection_pos == 'Red' else 'green' if injection_pos == 'Green' else 'blue'
    
    # Lambda function to check the color and return the corresponding letter
    color_to_letter = lambda color: 'R' if color == 'Red' else 'B' if color == 'Blue' else 'G' if color == 'Green' else ''
    
    # Get the corresponding letter for the selected injection position
    injection_pos_letter = color_to_letter(injection_pos)
    # Add color for both injection position and letter
    st.write(f"The selected injection position is <span style='color:{load_color}'>{injection_pos}</span> with corresponding letter <span style='color:{load_color}'>{injection_pos_letter}</span>.", unsafe_allow_html=True)

    # Injection volumes (default)
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
    
    # Sample order column 
    plate_df_long['Position'] =  plate_df_long['Row'] + plate_df_long['Column'].astype(str)
    # Injection volume column
    plate_df_long['Inj Vol'] = injection_vol
    # Instrument method column
    plate_df_long['Instrument Method'] = method_file
    # Path column 
    plate_df_long['Path'] = uploaded_dir
    # File name 
    plate_df_long['File Name'] = plate_df_long.apply(lambda row: "_".join([ms_info_output['acq_tech'], date_injection, sample_info_output['proj_name'], sample_info_output['plate_id'], row['Position']]), axis=1)
    plate_df_long['Position'] =  injection_pos_letter + plate_df_long['Position'] 
    
    output_order_df = plate_df_long.copy()
    output_order_df = output_order_df[['File Name', 'Path', 'Instrument Method', 'Position','Inj Vol']]
 
    # Randomize row order
    output_order_df_rand = output_order_df.sample(frac=1).reset_index(drop=True)
    
    # QC standard and washes 
    cols = st.columns(3)
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
        st.markdown("### QC Plasma")

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
        
    with cols[2]:
        ## QC between samples
        st.markdown("### QC between samples")
        qc_between_path = st.text_input("Enter the path to the between QC standard", "C:\\data\\QC_between")
        qc_between_method = st.text_input("Enter the method file for between QC standard", "C:\\Xcalibur\\methods\\QC_between")
        qc_between_pos = st.text_input("Enter the position for between QC standard", "GE2")
        injection_vol_qc_between = st.text_input("Modify your 'QC between' injection volume (ul)", str(injection_vol))
        # Tickbox for including QC between samples
        include_qc_between = st.checkbox("Include QC between samples", value=True)

        qc_between_df = pd.DataFrame({
            "File Name": ['QC_' + date_injection],
            "Path": [qc_between_path],
            "Instrument Method": [qc_between_method],
            "Position": [qc_between_pos],
            "Inj Vol": [injection_vol_qc_between]
        })
        
        qc_between_df_pre = pd.concat([wash_df, qc_between_df], axis=0)
        # append File Name in qc_between_df_pre with _1
        qc_between_df_pre['File Name'] = qc_between_df_pre['File Name'] + '_1'
        qc_between_df_pre = qc_between_df_pre.reset_index(drop=True)

        qc_between_df_post = pd.concat([qc_between_df, wash_df], axis=0)
        qc_between_df_post['File Name'] = qc_between_df_post['File Name'] + '_2'
        qc_between_df_post = qc_between_df_post.reset_index(drop=True)

    # Download data

    ## export order sample name
    sample_order_name = "_".join([ datetime.now().strftime("%Y%m%d%H%M"), sample_info_output['proj_name'], "Sample", "Order", sample_info_output['plate_id']]) + ".csv"

    ## export order sample
    ### DIA/DDA plate
    
    # Bind row from wash_df after every 8 rows in output_order_df
    chunks = [output_order_df_rand[i:i+8] for i in range(0, len(output_order_df_rand), 8)]
    # Add wash and qc standard after every 8 rows
    output_with_wash = pd.concat([pd.concat([chunk, wash_df], ignore_index=True) for chunk in chunks], ignore_index=True)
    
    ### SRM plate
    if ms_info_output['acq_tech'] == "SRM":
        output_with_wash = output_order_df_rand
    
    # concat wash and qc dataframes
    output_with_wash = pd.concat([wash_df, qc_df, output_with_wash, qc_df], ignore_index=True)
    
    if qc_between_df.shape[0] > 0 and include_qc_between:
        output_with_wash = pd.concat([qc_between_df_pre, output_with_wash, qc_between_df_post], ignore_index=True)
    
    # Store output_order_df in session state for SDRF tab
    st.session_state.output_order_df = output_order_df
    
    # Convert DataFrame to CSV with UTF-8 encoding
    csv_data = output_with_wash.to_csv(index=False, encoding='utf-8-sig')
    
    # Add 'Type=4,,,,' to the beginning of the CSV data with proper encoding
    csv_data = '\ufeff' + 'Bracket Type=4,,,,\n' + csv_data
    
    
    ## Download button for export file
    st.markdown("### Download data")
    
    st.markdown("The data below is an example for sample order in Xcalibur. The injection order will be randomized and added with wash and qc standard. Be sure with SRM injection")
    st.write(output_order_df)
    st.markdown("Click below to download the data.") 
    # Download button for output_order_df
    st.download_button(
        label="Download sample order",
        data=csv_data.encode('utf-8-sig'),
        file_name=sample_order_name,
        mime='text/csv; charset=utf-8'
    )

        
        
with sdrf_tab:
    st.header("SDRF")
    ms_file = st.selectbox("MS file output", ["RAW", "mzML"])
    # Collision energy
    collision_energy = st.text_input("Collision Energy (NCE)", "27")


    # Get output_order_df from session state
    if 'output_order_df' in st.session_state:
        output_order_df = st.session_state.output_order_df
    else:
        st.warning("Please go to the 'Sample Order' tab first to create the sample order.")
        st.stop()

    # Create sample properties from Thermo injection table 
    sample_prop = plate_df_long.copy()
    # Organism column
    sample_prop['organism'] = [sample_info_output['organism_species']] * sample_prop.shape[0]
    # Organism part
    sample_prop['organism part'] = [sample_info_output["sample"]] * sample_prop.shape[0]
    # Plate
    sample_prop['plate'] = [sample_info_output['plate_id']] * sample_prop.shape[0]
    # Project
    sample_prop['project'] = [sample_info_output['proj_name']] * sample_prop.shape[0]
    # age
    sample_prop['age'] = ["not available"] * sample_prop.shape[0]
    # developmental stage
    sample_prop['developmental stage'] = ["not available"] * sample_prop.shape[0]
    # sex
    sample_prop['sex'] = ["not available"] * sample_prop.shape[0]
    # ancestry category
    sample_prop['ancestry category'] = ["not available"] * sample_prop.shape[0]
    # cell type
    sample_prop['cell type'] = ["not available"] * sample_prop.shape[0]
    # cell line
    sample_prop['cell line'] = ["not available"] * sample_prop.shape[0]
    # disease
    sample_prop['disease'] = ["not available"] * sample_prop.shape[0]
    # individual
    sample_prop['individual'] = ["not available"] * sample_prop.shape[0]
    # biological replicate
    sample_prop['biological replicate'] = ["1"] * sample_prop.shape[0]

    # Export column names for factor value
    sample_prop_columns = sample_prop.columns.tolist()


    # Rename all columns with characteristics[]
    sample_prop.columns = 'characteristics[' + sample_prop.columns + ']'
    
    # Adding three columns and first column is source name
    sample_prop.insert(0, 'source name', output_order_df['File Name'])
    sample_prop['Material type'] = ["AC=EFO:0009656;NT=plasma"] * sample_prop.shape[0]
    sample_prop['assay name'] = ['run ' + str(i) for i in range(1, sample_prop.shape[0] + 1)]
    sample_prop['technology type'] = 'proteomics profiling by mass spectrometry'


    # Data file properties (MS)
    data_file_prop = pd.DataFrame({
        "data file": output_order_df["File Name"] + "." + ms_file,
        "file uri": output_order_df["File Name"] + "." + ms_file,
        "proteomics data acquisition method": [ms_info_output['sdrf_acquisition']] * len(output_order_df),
        "label": ["AC=MS:1002038;NT=label free sample"] * len(output_order_df),
        "fraction identifier": ["1"] * len(output_order_df),
        "fractionation method": ["NT=High-performance liquid chromatography;AC=PRIDE:0000565"] * len(output_order_df),
        "technical replicate": ["1"] * len(output_order_df),
        # Add column cleaveage agent details later outside
        "ms2 mass analyzer": ["not available"] * len(output_order_df),
        "instrument": [ms_info_output['sdrf_ms']] * len(output_order_df),
        "modification parameters": ["NT=Carbamidomethyl;AC=UNIMOD:4;TA=C;MT=Fixed"] * len(output_order_df),
        "dissociation method": [ms_info_output['dissociation_accession']] * len(output_order_df),
        "collision energy": [collision_energy + ' NCE'] * len(output_order_df),
        "precursor mass tolerance": ["40 ppm"] * len(output_order_df),
        "fragment mass tolerance": ["0.05 Da"] * len(output_order_df),

    })

    # Add enzyme columns with suffix 
    if len(ms_info_output['enz_accession_list']) > 0:
        for i in range(len(ms_info_output['enz_accession_list'])):
                column_name = "cleavage agent details" + str(i)
                data_file_prop[column_name] = [ms_info_output['enz_accession_list'][i]] * len(output_order_df)

    # Move all cleavage agent details columns to be after technical replicate
    cleavage_cols = [col for col in data_file_prop.columns if col.startswith("cleavage agent details")]
    other_cols = [col for col in data_file_prop.columns if not col.startswith("cleavage agent details")]
    
    # Find the index of "technical replicate" column
    tech_rep_index = other_cols.index("technical replicate") if "technical replicate" in other_cols else 6
    
    # Reorder: columns before tech replicate + tech replicate + cleavage columns + remaining columns
    new_column_order = other_cols[:tech_rep_index+1] + cleavage_cols + other_cols[tech_rep_index+1:]
    data_file_prop = data_file_prop[new_column_order]

    # For DIA add MS1 and MS2 scan range
    if ms_info_output['acq_tech'] == "DIA":
        data_file_prop["MS1 scan range"] = ["400-1250 m/z"] * data_file_prop.shape[0]
        data_file_prop["MS2 scan range"] = ["100-2000 m/z"] * data_file_prop.shape[0]

    # For SRM add ProteomeEdge lot
    if ms_info_output['acq_tech'] == "SRM":
        data_file_prop['ProteomeEdge'] = [ms_info_output['srm_lot']] * data_file_prop.shape[0]

    # rename
    data_file_prop.columns = 'comment[' + data_file_prop.columns + ']'

    # Colbind sample_prop and data_file_prop
    sdrf_df = pd.concat([sample_prop, data_file_prop], axis=1)

    factor_value_col = st.selectbox("Select column for factor value", sample_prop_columns)

    # Add factor values based on selected columns
    # Select box 

    sdrf_df[f'factor value[{factor_value_col}]'] = sdrf_df[f'characteristics[{factor_value_col}]']

    st.write(sdrf_df)
    
    # Download SDRF file
    # fix datetime to YYMMDD
    sdrf_filename = "_".join([datetime.now().strftime("%Y%m%d"), sample_info_output['proj_name'], sample_info_output['plate_id']]) + ".sdrf.tsv"
    sdrf_tsv = sdrf_df.to_csv(sep='\t', index=False, encoding='utf-8-sig')
    
    # Ensure UTF-8 BOM is present
    if not sdrf_tsv.startswith('\ufeff'):
        sdrf_tsv = '\ufeff' + sdrf_tsv

    # In sdrf_tsv replace first row where comment[cleavage agent details] with any numbers to just comment[cleavage agent details]
    for i in range(len(ms_info_output['enz_accession_list'])):
        sdrf_tsv = sdrf_tsv.replace(f'comment[cleavage agent details{i}]', 'comment[cleavage agent details]')

    st.download_button(
        label="Download SDRF",
        data=sdrf_tsv.encode('utf-8-sig'),
        file_name=sdrf_filename,
        mime='text/tab-separated-values; charset=utf-8'
    )

    # Add link to website github.com/thanadol-git/quantms_example/
    url = "https://www.github.com/thanadol-git/quantms_example/"
    st.markdown("comment[cleavage agent details'] will be fixed with the downloaded file. Pandas cannot handle two columns with the same name. check out this [link](%s)" % url)

    