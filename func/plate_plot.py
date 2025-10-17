import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st


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

def process_plate_positions(text_input, sample_name):
    """
    Process plate positions from text input and create a plate DataFrame.
    
    Args:
        text_input (str): Text area input with position specifications
        sample_name (str): Default sample name to fill the plate
    
    Returns:
        tuple: (plate_df, replace_pos) - DataFrame and processed position list
    """

    
    # Split text and clean empty lines
    replace_pos = text_input.split('\n')
    replace_pos = [item for item in replace_pos if item.strip() != '']
    
    # Write warning message if replace_pos does not have ; as one special character
    for item in replace_pos:
        if ';' not in item or item.count(';') != 1 or any(char in item for char in ['?', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=', '{', '}', '[', ']', '|', '\\', ':', '"', "'", '<', '>', ',', '.', '/', '~','`']):
            st.warning(f"Invalid format: {item}. It should be like 'Cohort_2;Col8'.")
            break
    
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
                    # Change replace_pos by prepend text + ';' + pos[-1] + str(number) before replace_pos
                    replace_pos.insert(0, text + ';' + pos[-1] + str(number))
            elif pos.startswith('Col') and 4 <=len(pos) <= 5 and pos[3:].isdigit() and 1 <= int(pos[3:]) <= 12:
                for letter in 'ABCDEFGH':
                    replace_pos.insert(0, text + ';' + letter + pos[3:])
            else:
                st.warning(f"Invalid position format: {item}. It should be like 'Cohort_2;RowA' or 'Cohort_2;Col8'.")
        else:
            st.warning(f"Invalid format: {item}. It should be like 'Cohort_2;Col8'.")

    # Write a warning message if the position is mentioned more than one time in text area
    if len(replace_pos) != len(set(replace_pos)):
        st.warning("Some positions are mentioned more than once. Please check your input.")

    # Check if the position is mentioned more than one time
    pos_list = []
    for item in list(set(replace_pos)):
        if ';' in item:
            text, pos = item.split(';')
            pos_list.append(pos)
    if len(pos_list) != len(set(pos_list)):
        st.warning("Position is mentioned more than one time with different labels. Possibly, using Row or Col. Please check your input.")

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
    
    return plate_df, replace_pos