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
    
    return proj_name, organism, sample, plate_id, sample_name
    
def ms_info():
    # Instrument
    machine = st.sidebar.selectbox("Select your instrument", ["Q Exactive HF", "TSQ Altis", "LIT Stellar"])
    ms_options = {
        "Q Exactive HF": ["DIA", "DDA","PRM"],
        "TSQ Altis": ["SRM"],
        "LIT Stellar": ["DIA", "DDA", "PRM", "SRM"]
    }
    # Acquisition technique 
    acq_tech = st.sidebar.selectbox("Select your acquisition",ms_options[machine])

    # Initialize srm_lot with default value
    srm_lot = None
    
    # Add SRM/Proteomedge panel
    if 'SRM' in acq_tech: # If SRM  do 
        # acq_tech = "SRM"
        srm_lot = st.sidebar.text_input('ProteomeEdge Lot number: Lot ', "23233")
        if srm_lot: 
            st.sidebar.markdown(f"The ProteomEdge Lot <span style='color:red'>{srm_lot}</span>", unsafe_allow_html=True)

    return machine, acq_tech, srm_lot

def create_sidebar():
    # Create a sidebar
    st.sidebar.header("Sample information")
    st.sidebar.write("This part is needed for every file that we are creating.")

    proj_name, organism, sample, plate_id, sample_name = sample_info()

    # MS content
    st.sidebar.header("MS setup")

    machine, acq_tech, srm_lot = ms_info()

    return proj_name, organism, sample, plate_id, sample_name, machine, acq_tech