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
# from tabs.plate_tab import plate_design_tab
# from tabs.sdrf_tab import sdrf_tab

# Sidebar
proj_name, organism, sample, plate_id, sample_name, machine, acq_tech = create_sidebar()


# Create three tabs
intro_tab, plate_tab, sample_order, sdrf_tab = st.tabs(["Intro", "Plate Design", "Sample Order", "SDRF"])

with intro_tab:
    intro_detail()


def create_plate_df_long(plate_df): 
    long_format = plate_df.stack().reset_index()
    long_format.columns = ['Row', 'Column', 'Sample']
    return long_format

def plate_dfplot(plate_df, plate_id): 
    
    # format plate_df in a long format
    plate_df_long = create_plate_df_long(plate_df)
    
    # Get unique labels sorted alphabetically
    unique_labels = sorted(plate_df_long['Sample'].unique())

    # Create a custom palette with colors mapped to labels alphabetically
    custom_palette = dict(zip(unique_labels, sns.color_palette("colorblind", len(unique_labels))))

    
    fig, ax = plt.subplots()
    # Create a color palette for discrete text

    # Plot the heatmap with discrete text colors
    sns.heatmap(plate_df.isnull(), cbar=False, cmap="coolwarm", ax=ax, linewidths=1, linecolor='darkgrey', alpha=0.1)
    ax.xaxis.tick_top()  # Move the x-axis labels to the top
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)  # Fix label rotation on y-axis
    ax.set_title(plate_id)  # Add title on top

    # Add text annotations and circles with custom colors
    for i in range(plate_df.shape[0]):
        for j in range(plate_df.shape[1]):
            value = plate_df.iloc[i, j]
            color = custom_palette.get(value, (1, 1, 1))  # Use custom_palette for colors
            ax.add_patch(plt.Circle((j + 0.5, i + 0.5), 0.4, color=color, fill=True))
            ax.text(j + 0.5, i + 0.5, f'{value}', ha='center', va='center', color='white', fontsize=4)

    ax.set_yticklabels(plate_df.index, rotation=0)

    # Display the plot
    st.pyplot(fig)
    
    # Plot barplot from labels of plate_df_long['Sample']
    fig2, ax2 = plt.subplots()
    sns.countplot(
        data=plate_df_long, 
        x='Sample', 
        ax=ax2, 
        order=plate_df_long['Sample'].value_counts().index,  # Reorder by count
        palette=custom_palette  # Apply the custom palette
    )
    ax2.set_title(f"Sample count in plate {plate_id}")
    ax2.set_xlabel(None)
    ax2.set_ylabel("Count")

    # Add count numbers on top of the bars
    for p in ax2.patches:
        ax2.text(
            p.get_x() + p.get_width() / 2.,  # X-coordinate (center of the bar)
            p.get_height() + 1,           # Y-coordinate (slightly above the bar)
            int(p.get_height()),            # Text (bar height)
            ha='center', va='center', fontsize=10, color='black'  # Text alignment and styling
        )

    # Display the plot
    st.pyplot(fig2)
    
    # Return the plate_df_long for use in other parts
    return plate_df_long

with plate_tab:
    st.header("Plate layout new")
    
    # Sample types 
    st.subheader("A. Cohort name")
    
    st.markdown(f"The main cohort samples will be: <span style='color:red'>{sample_name}</span>", unsafe_allow_html=True)
    st.markdown(f"Plate ID: <span style='color:red'>{plate_id}</span>", unsafe_allow_html=True)

    # Adding pool or control
    st.subheader("B. Control or Pool")
    st.write("This is a list of control or pool. Important! The 'EMPTY' will be removed in the later steps.")
    
    example_text = "Pool;A7\nControl;G12\nControl;H12\nCohort_2;C8\nEMPTY;A1\nCohort_2;RowD\nCohort_2;RowE\nCohort_2;Col9\nCohort_2;Col8"
    replace_pos = st.text_area("Example Control, Pool or another cohort", example_text).split('\n')
    # Filter row in text that contain 'Col' or 'Row' in replace_pos
    colrow_label = [item for item in replace_pos if ('Col' in item or 'Row' in item)]
        # Remove row with 'Col' or 'Row in replace_pos
    replace_pos = [item for item in replace_pos if not ('Col' in item or 'Row' in item)]
    
    # Check Col and Row then append to replace pos each well
    for item in colrow_label:
        if ';' in item:
            text, pos = item.split(';')
            # Check if pos is Row and followed by A-H or Col and followed by 1-12
            if pos.startswith('Row') and len(pos) == 4 and pos[-1] in 'ABCDEFGH':
                for number in range(1,13):
                    replace_pos.append(text + ';' + pos[-1] + str(number))
            elif pos.startswith('Col') and 4 <=len(pos) <= 5 and pos[3:].isdigit() and 1 <= int(pos[3:]) <= 12:
                for letter in 'ABCDEFGH':
                    replace_pos.append(text + ';' + letter + pos[3:])
            else:
                st.warning(f"Invalid position format: {item}. It should be like 'Cohort_2;C8'.")
        else:
            st.warning(f"Invalid format: {item}. It should be like 'Cohort_2;Col8'.")

#    replace_pos =  pd.Series(replace_pos).unique().tolist()

    # Write a  warning message if the position is mentioned more than one time in text area
    # Check if the position is mentioned more than one time
    pos_list = []
    for item in list(set(replace_pos)):
        if ';' in item:
            text, pos = item.split(';')
            pos_list.append(pos)
    if len(pos_list) != len(set(pos_list)):
        st.warning("Position is mentioned more than one time with different labels. Please check your input.")


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

    ## Comments for checking
    # st.write(replace_pos)
    

        
    # header 
    st.subheader("C. Layout of plate")
    plate_df_long = plate_dfplot(plate_df, plate_id)
    
    # Store in session state for use in other tabs
    st.session_state.plate_df_long = plate_df_long

with sample_order:
    st.header(acq_tech + " Injection")
    
    # Get plate_df_long from session state
    if 'plate_df_long' in st.session_state:
        plate_df_long = st.session_state.plate_df_long.copy()
    else:
        st.warning("Please go to the 'Plate Design' tab first to create the plate layout.")
        st.stop()
    
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
    st.write(f"The selected injection position is: <span style='color:{load_color}'>{injection_pos}</span> with corresponding letter: <span style='color:{load_color}'>{injection_pos_letter}</span>", unsafe_allow_html=True)

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
    plate_df_long['File Name'] = date_injection + "_" + proj_name + "_" + plate_id + "_" + plate_df_long['Position']
    plate_df_long['Position'] =  injection_pos_letter + plate_df_long['Position'] 
    
    output_order_df = plate_df_long[['File Name', 'Path', 'Instrument Method', 'Position','Inj Vol']]
    # Remove 'EMPTY' wells from the output_order_df
    output_order_df = output_order_df[output_order_df['Position'] != 'EMPTY']
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
    
    if qc_between_df.shape[0] > 0 and include_qc_between:
        output_with_wash = pd.concat([qc_between_df_pre, output_with_wash, qc_between_df_post], ignore_index=True)
    
    # Store output_order_df in session state for SDRF tab
    st.session_state.output_order_df = output_order_df
    
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

    # Get output_order_df from session state
    if 'output_order_df' in st.session_state:
        output_order_df = st.session_state.output_order_df
    else:
        st.warning("Please go to the 'Sample Order' tab first to create the sample order.")
        st.stop()

    # Create sample properties from Thermo injection table 
    sample_prop = plate_df_long.copy()
    # Organism column
    sample_prop['organism'] = ["Homo sapiens"] * sample_prop.shape[0]
    # Organism part
    sample_prop['organism part'] = ["plasma"] * sample_prop.shape[0]
    # age
    sample_prop['age'] = ["no available"] * sample_prop.shape[0]
    # developmental stage
    sample_prop['developmental stage'] = ["no available"] * sample_prop.shape[0]
    # sex
    sample_prop['sex'] = ["no available"] * sample_prop.shape[0]
    # ancestry category
    sample_prop['ancestry category'] = ["no available"] * sample_prop.shape[0]
    # cell type
    sample_prop['cell type'] = ["no available"] * sample_prop.shape[0]
    # cell line
    sample_prop['cell line'] = ["no available"] * sample_prop.shape[0]
    # disease
    sample_prop['disease'] = ["no available"] * sample_prop.shape[0]
    # individual
    sample_prop['individual'] = ["no available"] * sample_prop.shape[0]
    # biological replicate
    sample_prop['biological replicate'] = ["1"] * sample_prop.shape[0]

    # Rename all columns with characteristics[]
    sample_prop.columns = 'characteristics[' + sample_prop.columns + ']'
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

    st.write(sample_prop)
    
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