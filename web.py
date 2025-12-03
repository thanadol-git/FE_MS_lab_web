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
intro_tab, plate_tab, sample_order, evo_tab, sdrf_tab = st.tabs(["Intro", "Plate Design", "Xcalibur", "Chronos", "SDRF"])

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
    st.markdown("### Download data")

    # Add randomized sample order tickbox
    randomize_checkbox_xcalibur = st.checkbox("Randomize sample order", key="randomize_xcalibur")
    
    if randomize_checkbox_xcalibur == True:
        st.success("Sample order randomized!")
        output_order_df_rand = output_order_df.sample(frac=1).reset_index(drop=True)
    else:
        output_order_df_rand = output_order_df.copy()

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
    
    st.markdown("The data below is an example for sample order in Xcalibur. The injection order will be randomized and added with wash and qc standard. Be sure with SRM injection")
    st.write(output_order_df_rand)
    st.markdown("Click below to download the data.") 
    # Download button for output_order_df
    st.download_button(
        label="Download sample order",
        data=csv_data.encode('utf-8-sig'),
        file_name=sample_order_name,
        mime='text/csv; charset=utf-8'
    )



with evo_tab:
    if ms_info_output['machine'] == "LIT Stellar":
        # Evosep method
        st.header("Evosep method for " + ms_info_output['acq_tech']) 
        
        # Output location
        evosep_output = st.text_input("Enter the directory path to save Evosep method file", uploaded_dir)
        
        # Evosep method file
        evosep_method = st.text_input("Enter the Evosep experiment machine file", "C:\\data\\Evosep\\method.cam")
        st.markdown(f"The Evosep method file is from: <span style='color:red'>{evosep_method}</span>", unsafe_allow_html=True)  
        
        # Create a tick box for randomizing sample order
        randomize_checkbox_chronos = st.checkbox("Randomize sample order")

        cols = st.columns(3)
        with cols[0]:
            st.markdown("### Xcalibur methods")
            # Xcalibur iRT method 
            xcalibur_irt_method = st.text_input("Enter the Xcalibur iRT method file", "C:\\Xcalibur\\methods\\iRT.meth")
            # st.markdown(f"The Xcalibur iRT method file is from: <span style='color:red'>{xcalibur_irt_method}</span>", unsafe_allow_html=True)
            
            # Xcalibur sample SRM/PRM method
            xcalibur_sample_method = st.text_input("Enter the Xcalibur SRM/PRM method file", "C:\\Xcalibur\\methods\\SRM_PRM.meth")
            # st.markdown(f"The Xcalibur SRM/PRM method file is from: <span style='color:red'>{xcalibur_sample_method}</span>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown("### Standby and Prepare Commands")
            # Standby command location
            standby_command = st.text_input("Enter the standby command", "C:\\Xcalibur MS standby.cam")
            # st.markdown(f"The standby command file is from: <span style='color:red'>{standby_command}</span>", unsafe_allow_html=True)
            
            # Prepare command file location for 
            prepare_command = st.text_input("Enter the prepare command", "C:\\Xcalibur MS prepare.cam")
            # st.markdown(f"The prepare command file is from: <span style='color:red'>{prepare_command}</span>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown("### Evosep slot and comment")
            # Dropdown evosep_slot 1 to 9
            evosep_slot = st.selectbox("Select Evosep slot", list(range(1, 6)))
            # st.markdown(f"The Evosep slot is: <span style='color:red'>{evosep_slot}</span>", unsafe_allow_html=True)
            # Append EvoLot to evosep_slot
            evosep_slot = "EvoSlot " + str(evosep_slot)
            # Comment 
            evosep_comment = st.text_input("Enter comment for Evosep", ms_info_output['srm_lot'])

            # st.markdown(f"The Evosep comment is: <span style='color:red'>{evosep_comment}</span>", unsafe_allow_html=True)
        
        ## Create Evosep method file

        evosep_sample_df = plate_df_long.copy()
        
        
        # Add 'Xcalibur Method' column
        evosep_sample_df['Xcalibur Method'] = [xcalibur_sample_method] * evosep_sample_df.shape[0]
        # Rename File Name to Sample Name
        evosep_sample_df = evosep_sample_df.rename(columns={"File Name": "Sample Name"})

        # Filter EMPTY wells
        evosep_sample_df = evosep_sample_df[evosep_sample_df['Sample'] != 'EMPTY']

        # Select only column Sample Name, Xcalibur Method, Source Vial
        evosep_sample_df = evosep_sample_df[['Source Vial', 'Sample Name', 'Xcalibur Method']]

        ## Create Evosep iRT table
        # Select total numbers of iRT samples
        iRT_samples = st.selectbox("Select iRT samples", list(range(0, 10 + 1)), index=2)
        
                
        
        
        if randomize_checkbox_chronos == True:
            evosep_sample_final = evosep_sample_df.sample(frac=1).reset_index(drop=True)
            st.success("Sample order randomized!")
        else:
            evosep_sample_final = evosep_sample_df.copy()
        
        # evosep_sample_final = evosep_sample_df.copy()
        # iRT sample name 
        if iRT_samples != 0:
            iRT_sample_name = st.text_input("Enter iRT sample name", "iRT_Tag_unscheduled")
            
            # Create iRT df
            evosep_irt_df = pd.DataFrame({
                # Column Source vial is list from 1 to iRT_samples
                "Source Vial": list(range(1, iRT_samples + 1)),
                "Sample Name": [iRT_sample_name] * iRT_samples,
                "Xcalibur Method": [xcalibur_irt_method] * iRT_samples
            })
            
             # Append source vial to Sample Name
            evosep_irt_df['Sample Name'] = evosep_irt_df['Sample Name'] + '_' + evosep_irt_df['Source Vial'].astype(str)
            # Final Evosep df
            evosep_final_df = pd.concat([evosep_irt_df, evosep_sample_final], ignore_index=True)
        else:
            evosep_final_df = evosep_sample_final

        st.markdown("### Download Chronos File")


        # Add first and second column name Analysis Method and Srouce Tray, they are evosep_method and evosep_slot
        evosep_final_df.insert(0, 'Analysis Method', [evosep_method] * evosep_final_df.shape[0])
        evosep_final_df.insert(1, 'Source Tray', [evosep_slot] * evosep_final_df.shape[0])
        
        # Add prefix to Sample Name with ms_info_output['acq_tech']
        # evosep_final_df['Sample Name'] = ms_info_output['acq_tech'] + '_' + evosep_final_df['Sample Name']
        
        # Add Xcalibur file name column with is File Name 
        evosep_final_df['Xcalibur Filename'] = evosep_final_df['Sample Name']
        # Add empty column call Xcalibur Post Acquisition Program
        evosep_final_df['Xcalibur Post Acquisition Program'] = ""
        
        # Add Xcalibur output dir called Xcalibur Output Dir
        evosep_final_df['Xcalibur Output Dir'] = [evosep_output] * evosep_final_df.shape[0]
        
        # Add comment 
        evosep_final_df['Comment'] = [evosep_comment] * evosep_final_df.shape[0]
        # Add 3 empty columns called  Pump preparation	Align solvents	Flow to column / idle flow
        evosep_final_df['Pump preparation'] = ""
        evosep_final_df['Align solvents'] = ""
        evosep_final_df['Flow to column / idle flow'] = ""
        
        # Copy evosep_final_df to evo_Standby_df and remove all contents
        
        evo_standby_df = evosep_final_df.copy()
        evo_standby_df.loc[:, :] = ""
        # Add standby_command to first row and first column
        evo_standby_df.iloc[0, 0] = standby_command
        evo_standby_df.iloc[1, 0] = prepare_command
        # Add the last three columns of the second row to be "none", "False", "Idle flow (250 nl/min)"
        evo_standby_df.iloc[1, -3] = "none"
        evo_standby_df.iloc[1, -2] = "False"
        evo_standby_df.iloc[1, -1] = "Idle flow (250 nl/min)"
        # Ensure that evo_Standby_df has two row and 12 columns
        evo_standby_df = evo_standby_df.iloc[:2, :12]
        # Rowbind evo_standby_df after evosep_final_df
        evosep_final_df = pd.concat([ evosep_final_df, evo_standby_df], ignore_index=True)

        st.write(evosep_final_df)
        
        # Add download buttons for evosep_final_df
        evosep_csv_name = "_".join([datetime.now().strftime("%Y%m%d%H%M"), sample_info_output['proj_name'], "Evosep", "Order", sample_info_output['plate_id']]) + ".csv"
        csv_evosep_data = evosep_final_df.to_csv(index=True, sep=';', encoding='utf-8-sig')
        
        # Ensure UTF-8 BOM is present
        if not csv_evosep_data.startswith('\ufeff'):
            csv_evosep_data = '\ufeff' + csv_evosep_data
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_evosep_data.encode('utf-8-sig'),
                file_name=evosep_csv_name,
                mime='text/csv; charset=utf-8; separator=semicolon'
            )
        
        with col2:
            # Add download button for evosep_final_df as XML
            # Replace invalid XML tag characters in column names
            evosep_xml_df = evosep_final_df.copy()
            evosep_xml_df.columns = [col.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '') for col in evosep_xml_df.columns]
            
            evosep_xml_name = "_".join([datetime.now().strftime("%Y%m%d%H%M"), sample_info_output['proj_name'], "Evosep", "Order", sample_info_output['plate_id']]) + ".xml"
            xml_evosep_data = evosep_xml_df.to_xml(index=True)
            
            st.download_button(
                label="⬇️ Download XML",
                data=xml_evosep_data.encode('utf-8'),
                file_name=evosep_xml_name,
                mime='application/xml'
            )
        
        with col3:
            # Add copy to clipboard button for XML data
            if st.button("📋 Copy XML to Clipboard"):
                st.write("""
                <script>
                navigator.clipboard.writeText(`""" + xml_evosep_data.replace('`', '\\`') + """`);
                </script>
                """, unsafe_allow_html=True)
                st.success("XML copied to clipboard!")
            
        
        # Display XML results
        st.markdown("### XML Preview")
        # Show expandable XML preview
        with st.expander("View XML (click to expand)"):
            # Show only first 2000 characters of XML
            xml_preview = xml_evosep_data 
            st.code(xml_preview, language="xml")
            
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

    