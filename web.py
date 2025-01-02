import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Create two tabs
dia_tab, dda_tab = st.tabs(["DIA", "DDA"])

# Content for Tab 1
with dia_tab:
    st.header("FE DIA")
    st.write("This is the content of the first tab.")

# Content for Tab 2
with dda_tab:
    st.header("FE DDA")
    st.write("This is the content of the second tab.")

