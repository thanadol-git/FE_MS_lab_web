import streamlit as st

def intro_detail():
    st.header("Introduction")
    st.write("This is a web application to help you design your plate layout and sample order for mass spectrometry.")
    st.write("The application will help you design the plate layout, injection order, and SDRF file.")
    st.write("Please fill in the necessary information in the sidebar to get started.")
    st.subheader("Related links")
    st.markdown("1. [Xcalibur](https://www.thermofisher.com/order/catalog/product/OPTON-30900)")
    