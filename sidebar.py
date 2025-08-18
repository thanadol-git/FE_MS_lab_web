from requests import options
import streamlit as st

def sample_info():
    # Project
    proj_name = st.sidebar.text_input("Enter your project name", "Project X")
    # Organism
    organism = st.sidebar.text_input("Select your organism", "Human")
    # Sample type
    sample = st.sidebar.text_input("Enter your sample", "Plasma")
    # Plate id 
    plate_id = st.sidebar.text_input("Enter your plate ID", "")
    # Samplee/ cohort name
    sample_name = st.sidebar.text_input("Main cohort name/abbreviation", "Cohort_1")
    
        # plate id 
    if not plate_id:
        plate_id = sample_name

    
    return proj_name, organism, sample, plate_id, sample_name
    
def ms_info():
    # Instrument
    machine = st.sidebar.selectbox("Select your instrument", ["Q Exactive HF", "TSQ Altis", "LIT Stellar"])
    ms_options = {
        "Q Exactive HF": ["DIA", "DDA","PRM"],
        "TSQ Altis": ["SRM"],
        "LIT Stellar": ["DIA", "DDA", "PRM", "SRM"]
    }
    
    ms_accession = {
        "Q Exactive HF": "NT=Q Exactive HF;AC=MS:1002523",
        "TSQ Altis": "NT=TSQ Altis;AC=MS:1002874",
        "LIT Stellar": "NT=Stellar;AC=MS:1003409"
    }
    
    # Acquisition technique 
    acq_tech = st.sidebar.selectbox("Select your acquisition",ms_options[machine])

    # sdrf ms 
    sdrf_ms = ms_accession[machine]
    
    # Initialize srm_lot with default value
    srm_lot = None
    
    # Add SRM/Proteomedge panel
    if 'SRM' in acq_tech: # If SRM  do 
        # acq_tech = "SRM"
        srm_lot = st.sidebar.text_input('ProteomeEdge Lot number: Lot ', "23233")
        if srm_lot: 
            st.sidebar.markdown(f"The ProteomEdge Lot <span style='color:red'>{srm_lot}</span>", unsafe_allow_html=True)

    # Digestion 
    digestion_enz = st.sidebar.multiselect("Select your tryptic enzyme", ["Trypsin", "Lys-C", "Chymotrypsin"], default=["Trypsin"])

    # Digestion enzyme accession
    enz_accession = {
        "Trypsin": "NT=Trypsin;AC=MS:1001251",
        "Lys-C": "NT=Lys-C;AC=MS:1001309",
        "Chymotrypsin": "NT=Chymotrypsin;AC=MS:1001306"
    }
    
    # Get the accession list for selected enzymes
    sdrf_enz = [enz_accession.get(enzyme, f"NT={enzyme};AC=unknown") for enzyme in digestion_enz]

    st.sidebar.write("You selected:", digestion_enz)

    return machine, acq_tech, srm_lot, sdrf_ms, sdrf_enz

def create_sidebar():
    # Create a sidebar
    st.sidebar.header("Sample information")
    st.sidebar.write("This part is needed for every file that we are creating.")

    proj_name, organism, sample, plate_id, sample_name = sample_info()

    # MS content
    st.sidebar.header("MS setup")

    machine, acq_tech, srm_lot, sdrf_ms, sdrf_enz = ms_info()

    return proj_name, organism, sample, plate_id, sample_name, machine, acq_tech