import pandas as pd
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
