from requests import options
import streamlit as st

def sample_info():
    
    # Organism accession
    organism_species = {
        "Human": "Homo sapiens",
        "Rat": "Rattus norvegicus",
        "Mouse": "Mus musculus",
        "Cyanobacteria": "Cyanobacteria",
        "E.coli": "Escherichia coli",
    }
    
    # Project
    proj_name = st.sidebar.text_input("Enter your project name", "Project X")
    # Organism
    organism = st.sidebar.selectbox("Select your organism", list(organism_species.keys()), index=0)
    # Sample type
    sample = st.sidebar.selectbox("Select your sample type", ["Plasma", "Serum", "Tissue", "Cell line", "Cell culture"], index=0)
    # Plate id 
    plate_id = st.sidebar.text_input("Enter your plate ID", "")
    # Samplee/ cohort name
    sample_name = st.sidebar.text_input("Main cohort name/abbreviation", "Cohort_1")
    
        # plate id 
    if not plate_id:
        plate_id = sample_name



    # return all values
    sample_info_output = {
        "proj_name": proj_name,
        "organism_species": organism_species[organism],
        "sample": sample,
        "plate_id": plate_id,
        "sample_name": sample_name
    }

    return sample_info_output

def ms_info():
    # MS content
    st.sidebar.header("MS setup")
    
    # Instrument
    machine = st.sidebar.selectbox("Select your instrument", ["Q Exactive HF", "TSQ Altis", "LIT Stellar"])
    ms_options = {
        "Q Exactive HF": ["DIA", "DDA","PRM"],
        "TSQ Altis": ["SRM"],
        "LIT Stellar": ["DIA", "DDA", "PRM", "SRM"]
    }
    
    ms_analyzers = {
        "Q Exactive HF": ["DIA", "DDA", "PRM"],
        "TSQ Altis": ["SRM"],
        "LIT Stellar": ["DIA", "DDA", "PRM", "SRM"]
    }

    # Acquisition technique accession
    ms_acquisition = {
        "DIA": "NT=Data Independent Acquisition;AC=MS:1002804",
        "DDA": "NT=Data-Dependent Acquisition;AC=NCIT:C161785",
        "PRM": "NT=Parallel Reaction Monitoring;AC=MS:1002956",
        "SRM": "NT=Selected Reaction Monitoring;AC=MS:1000423"
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

    # sdrf ms acquisition
    sdrf_acquisition = ms_acquisition[acq_tech]
    
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
        "Trypsin": "AC=MS:1001251;NT=Trypsin",
        "Lys-C": "AC=MS:1001309;NT=Lys-C",
        "Chymotrypsin": "AC=MS:1001306;NT=Chymotrypsin"
    }
    
    # Get the accession from the selected enzymes in list
    enz_accession_list = [enz_accession[enz] for enz in digestion_enz]
    
     # Dissociation method accession
    dissociation_accession = {
        "ETD": "NT=Electron Transfer Dissociation;AC=MS:1002592",
        "CID": "NT=Collision-Induced Dissociation;AC=MS:1000132",
        "HCD": "NT=Higher-energy Collisional Dissociation;AC=MS:1000422"
    }
    
    # Dissociation
    dissociation_method = st.sidebar.selectbox("Select your dissociation method", list(dissociation_accession.keys()), index=2)
    
    
   
    
    # create dict for all of returns values
    ms_info_output = {
        "machine": machine,
        "srm_lot": srm_lot,
        "sdrf_ms": sdrf_ms,
        "acq_tech": acq_tech,
        "digestion_enz": digestion_enz,
        "dissociation_method": dissociation_method,
        "dissociation_accession": dissociation_accession[dissociation_method],
        "enz_accession_list": enz_accession_list,
        "sdrf_acquisition": sdrf_acquisition
    }

    return ms_info_output

def create_sidebar():
    # Create a sidebar
    st.sidebar.header("Sample information")
    st.sidebar.write("This part is needed for every file that we are creating.")

    # Pass the values from sample_info
    sample_info_output = sample_info()

    # Pass the values from ms_info
    ms_info_output = ms_info()

    


    return ms_info_output, sample_info_output