import streamlit as st

def plate_design_tab(): 
    st.header("Plate layout new")
    
    # Sample types 
    st.subheader("A. Cohort name")
    st.markdown(f"The main cohort samples will be: <span style='color:red'>{sample_name}</span>", unsafe_allow_html=True)

    # plate id 
    if not plate_id:
        plate_id = sample_name
    st.markdown(f"Plate ID: <span style='color:red'>{plate_id}</span>", unsafe_allow_html=True)


    st.subheader("B. Control or Pool")
    st.write("This is a list of control or pool. Important! The 'EMPTY' will be removed in the later steps.")
    replace_pos = st.text_area("Example Control, Pool or another cohort", "Pool;A7\nControl;G12\nControl;H12\nCohort_2;C8\nEMPTY;A1\nCohort_2;RowD\nCohort_2;RowE\nCohort_2;Col9\nCohort_2;Col8").split('\n')
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
    
    # format plate_df in a long for mat
    plate_df_long = plate_df.stack().reset_index()
    plate_df_long.columns = ['Row', 'Column', 'Sample']
    
        # Get unique labels sorted alphabetically
    unique_labels = sorted(plate_df_long['Sample'].unique())

    # Create a custom palette with colors mapped to labels alphabetically
    custom_palette = dict(zip(unique_labels, sns.color_palette("colorblind", len(unique_labels))))

        
    # header 
    st.subheader("C. Layout of plate")
    
    
    
    # Heatmap of plate location 
    # from plate_df to heatmap
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