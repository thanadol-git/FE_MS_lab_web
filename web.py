import asyncio
import json
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

import pandas as pd
import streamlit as st
try:
    from hypha_rpc import connect_to_server
    from hypha_rpc.utils.schema import schema_function
except Exception:
    # hypha_rpc is an optional dependency used for the OpenAI/Hypha agent integration.
    # If it's missing, provide safe fallbacks so the app continues to run.
    connect_to_server = None
    def schema_function(fn=None, **kwargs):
        # Allow use as @schema_function or @schema_function(...)
        if fn is None:
            def decorator(f):
                return f
            return decorator
        return fn

from func.plate_plot import plate_dfplot, process_plate_positions

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

SERVER_URL = "https://hypha.aicell.io"

INJECTION_POS_COLORS = {"Red": "red", "Green": "green", "Blue": "blue"}
INJECTION_POS_LETTERS = {"Red": "R", "Green": "G", "Blue": "B"}
EMPTY_WELL_LABEL = "EMPTY"


def _ensure_bom(text: str) -> str:
    if text.startswith("\ufeff"):
        return text
    return "\ufeff" + text


def _safe_run(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)


def _init_plate_replace_text(example_text: str) -> None:
    if "pending_plate_update" in st.session_state:
        st.session_state.replace_pos_text = st.session_state.pending_plate_update
        del st.session_state.pending_plate_update
    if "replace_pos_text" not in st.session_state:
        st.session_state.replace_pos_text = example_text


def _build_file_name(row, ms_info, sample_info, date_injection: str) -> str:
    parts = [
        ms_info["acq_tech"],
        date_injection,
        sample_info["proj_name"],
        sample_info["plate_id"],
        row["Position"],
    ]
    return "_".join(parts)


def _build_download_name(parts, suffix: str) -> str:
    return "_".join(parts) + suffix


def _chunk_df(df, size: int):
    return [df[i : i + size] for i in range(0, len(df), size)]


def _insert_wash_after_chunks(df, wash_df, size: int):
    chunks = _chunk_df(df, size)
    return pd.concat(
        [pd.concat([chunk, wash_df], ignore_index=True) for chunk in chunks],
        ignore_index=True,
    )


def _sanitize_xml_columns(columns):
    return [
        col.replace(" ", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        for col in columns
    ]


def _create_xml_from_dataframe(df: pd.DataFrame) -> str:
    root = ET.Element("data")
    for _, row in df.iterrows():
        row_elem = ET.SubElement(root, "row")
        for col_name, value in row.items():
            col_elem = ET.SubElement(row_elem, col_name)
            col_elem.text = str(value)
    return minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")


@schema_function
def design_plate(plate_design_str: str) -> str:
    """Design a plate by setting the replacement positions text.

    The input string should be formatted as 'Label;Location' separated by newlines.
    Example: 'Pool;A7\nControl;G12\nControl;H12\nCohort_2;C8\nEMPTY;A1\nCohort_2;RowD\nCohort_2;RowE\nCohort_2;Col9\nCohort_2;Col8'
    """
    st.session_state["pending_plate_update"] = plate_design_str
    return "Successfully updated plate design."


async def run_open_ai_agent(prompt, api_key):
    """Run the OpenAI agent with MCP tools."""
    if not AsyncOpenAI:
        st.error("OpenAI library not installed.")
        return

    client = AsyncOpenAI(api_key=api_key)

    # Define tool directly to avoid MCP fetch issues
    openai_tools = [
        {
            "type": "function",
            "function": {
                "name": "design_plate",
                "description": "Design a plate by setting the replacement positions text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plate_design_str": {
                            "type": "string",
                            "description": "The input string formatted as 'Label;Location' separated by newlines.",
                        }
                    },
                    "required": ["plate_design_str"],
                },
            },
        }
    ]

    # Call OpenAI
    messages = [
        {
            "role": "system",
            "content": f"You are a helpful assistant that can modify plate designs. The current plate design replace_pos text is:\n{st.session_state.replace_pos_text}",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=openai_tools, tool_choice="auto"
        )
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return

    message = completion.choices[0].message

    # Handle Tool Calls
    if message.tool_calls:
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            st.info(f"Agent calling tool: `{function_name}` with args: `{arguments}`")
            if function_name == "design_plate":
                result = design_plate(**arguments)
                st.success(result)
                st.rerun()
    else:
        st.write(message.content)


def create_agent_chat():
    """Create an agent chat interface."""

    api_key = st.text_input("OpenAI API Key", type="password")
    prompt = st.text_input(
        "Prompt", "Set the plate to have Control at A1 and Pool at B2"
    )

    if st.button("Run Agent"):
        if not api_key:
            st.warning("Please enter an OpenAI API Key.")
            return

        # If hypha_rpc is not installed, disable the agent functionality with a clear message.
        if connect_to_server is None:
            st.error(
                "Hypha RPC client is not available. Agent features are disabled. "
                "Install the optional dependency 'hypha-rpc' to enable this."
            )
            return

        async def start_and_chat():
            # Connect to Hypha
            client_id = f"ms-experiment-{uuid.uuid4().hex[:8]}"
            st.session_state.service_id = client_id

            with st.spinner("Connecting to Hypha..."):
                async with connect_to_server({"server_url": SERVER_URL}) as server:

                    # Register Service
                    await server.register_service(
                        {
                            "id": client_id,
                            "description": "Plate Design Service",
                            "config": {"visibility": "public"},
                            "design_plate": design_plate,
                        }
                    )

                    serve_task = asyncio.create_task(server.serve())

                    # Run Agent
                    await run_open_ai_agent(prompt, api_key)

                    serve_task.cancel()
                    try:
                        await serve_task
                    except asyncio.CancelledError:
                        pass

        # Run the async loop
        _safe_run(start_and_chat())


# Import functions from other modules
from sidebar import create_sidebar
from tabs.intro_tab import intro_detail

# Results from Sidebar script
ms_info_output, sample_info_output = create_sidebar()


# Create three tabs
intro_tab, plate_tab, sample_order, evo_tab, sdrf_tab, skyline_tab = st.tabs(
    ["Intro", "Plate Design", "Xcalibur", "Chronos", "SDRF", "Skyline"]
)

with intro_tab:
    intro_detail()


with plate_tab:
    st.header("Plate layout")

    # Sample types
    st.subheader("A. Cohort name")

    st.markdown(
        f"The main cohort samples will be: <span style='color:red'>{sample_info_output['sample_name']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"Plate ID: <span style='color:red'>{sample_info_output['plate_id']}</span>",
        unsafe_allow_html=True,
    )

    # Adding pool or control
    st.subheader("B. Sample annotation")
    st.write(
        "Please annotate samples with other cohort besides the main cohort in your plate, for example pool samples or control samples. Importantly, The 'EMPTY' wells will be removed in the later steps."
    )
    # Add disclaimer on sensitive information
    st.markdown(
        "<span style='color:red'>⚠️ **Disclaimer:** Please ensure that the information you provide does not contain any sensitive or personally identifiable information.</span>",
        unsafe_allow_html=True,
    )

    # Text area for input with example_text 8 rows
    example_text = "Pool;A7\nControl;G12\nControl;H12\nCohort_2;C8\nEMPTY;A1\nCohort_2;RowD\nCohort_2;RowE\nCohort_2;Col9\nCohort_2;Col8"

    _init_plate_replace_text(example_text)

    text_input = st.text_area(
        "Example: Control, Pool or another cohort", key="replace_pos_text", height=200
    )

    # Process plate positions using the function
    plate_df, replace_pos = process_plate_positions(
        text_input, sample_info_output["sample_name"]
    )

    # header
    st.subheader("C. Layout of plate")
    plate_df_long = plate_dfplot(plate_df, sample_info_output["plate_id"])

    # Store in session state for use in other tabs
    st.session_state.plate_df_long = plate_df_long

    create_agent_chat()

with sample_order:
    st.header(ms_info_output["acq_tech"] + " Injection")

    # Get plate_df_long from session state
    if "plate_df_long" in st.session_state:
        plate_df_long = st.session_state.plate_df_long.copy()
    else:
        st.warning(
            "Please go to the 'Plate Design' tab first to create the plate layout."
        )
        st.stop()

    plate_df_long["Source Vial"] = list(range(1, plate_df_long.shape[0] + 1))
    # Filter the plate_df_long to only include the samples
    plate_df_long = plate_df_long[plate_df_long["Sample"] != EMPTY_WELL_LABEL]

    # Choices Injection position with select boxes from red green and blue
    injection_pos = st.selectbox(
        "1.Select your Autosampler injection position", ["Red", "Green", "Blue"]
    )

    # Determine the color based on the injection position
    load_color = INJECTION_POS_COLORS.get(injection_pos, "blue")
    injection_pos_letter = INJECTION_POS_LETTERS.get(injection_pos, "")
    # Add color for both injection position and letter
    st.write(
        f"The selected injection position is <span style='color:{load_color}'>{injection_pos}</span> with corresponding letter <span style='color:{load_color}'>{injection_pos_letter}</span>.",
        unsafe_allow_html=True,
    )

    # Injection volumes (default)
    injection_vol = 0.1

    injection_vol = st.slider(
        "2.Select your injection volume", 0.01, 20.0, injection_vol, 0.01
    )
    cols = st.columns(2)
    with cols[0]:
        # Add suggestion volumn buttons
        button1, button2, button3, button4, button5 = st.columns(5)
        if button1.button("0.01 ul", use_container_width=True):
            injection_vol = 0.01
        if button2.button("0.1 ul", use_container_width=True):
            injection_vol = 0.1
        if button3.button("5.0 ul", use_container_width=True):
            injection_vol = 5.0
        if button4.button("10.0 ul", use_container_width=True):
            injection_vol = 10.0
        if button5.button("15.0 ul", use_container_width=True):
            injection_vol = 15.0
    with cols[1]:
        injection_vol = st.text_input(
            "Enter your injection volume (ul)", str(injection_vol)
        )

    st.markdown(
        f"Selected injection volume (ul): <span style='color:red'>{injection_vol}</span>",
        unsafe_allow_html=True,
    )

    # Path to the data
    uploaded_dir = st.text_input(
        "3.Enter the directory path to the data", "C:\data\yourdir"
    )
    st.markdown(
        f"The data will be saved at: <span style='color:red'>{uploaded_dir}</span>",
        unsafe_allow_html=True,
    )

    # Path to method file
    method_file = st.text_input(
        "4.Enter the directory path to the method file", "C:\Xcalibur\methods\method1"
    )
    st.markdown(
        f"The method file for MS is from: <span style='color:red'>{method_file}</span>",
        unsafe_allow_html=True,
    )

    # Date of injection
    date_injection = st.date_input("5.Date of injection", pd.Timestamp("today"))
    # format date_injection to YYYYMMDD as text
    date_injection = date_injection.strftime("%Y%m%d")
    st.markdown(
        f"Date of injection: <span style='color:red'>{date_injection}</span>",
        unsafe_allow_html=True,
    )

    # Sample order column
    plate_df_long["Position"] = plate_df_long["Row"] + plate_df_long["Column"].astype(
        str
    )
    # Injection volume column
    plate_df_long["Inj Vol"] = injection_vol
    # Instrument method column
    plate_df_long["Instrument Method"] = method_file
    # Path column
    plate_df_long["Path"] = uploaded_dir
    # File name
    plate_df_long["File Name"] = plate_df_long.apply(
        _build_file_name,
        axis=1,
        ms_info=ms_info_output,
        sample_info=sample_info_output,
        date_injection=date_injection,
    )
    plate_df_long["Position"] = injection_pos_letter + plate_df_long["Position"]

    output_order_df = plate_df_long.copy()
    output_order_df = output_order_df[
        ["File Name", "Path", "Instrument Method", "Position", "Inj Vol"]
    ]

    # QC standard and washes
    cols = st.columns(3)
    with cols[0]:

        st.markdown("### Wash")

        ## Wash parameters
        wash_path = st.text_input("Enter the path to the washes", "C:\\data\\wash")
        wash_method = st.text_input(
            "Enter the method file for washes", "C:\\Xcalibur\\methods\\wash"
        )
        wash_pos = st.text_input("Enter the position for washes", "G3")
        injection_vol_wash = st.text_input(
            "Modify your 'Wash' injection volume (ul)", str(injection_vol)
        )

        wash_df = pd.DataFrame(
            {
                "File Name": ["wash"],
                "Path": [wash_path],
                "Instrument Method": [wash_method],
                "Position": [wash_pos],
                "Inj Vol": [injection_vol_wash],
            }
        )
        # st.write(wash_df, index=False)

    with cols[1]:
        ## QC standard parameters
        st.markdown("### QC Plasma")

        qc_path = st.text_input("Enter the path to the QC standard", "C:\\data\\QC")
        qc_method = st.text_input(
            "Enter the method file for QC standard", "C:\\Xcalibur\\methods\\QC"
        )
        qc_pos = st.text_input("Enter the position for QC standard", "GE1")
        injection_vol_qc = st.text_input(
            "Modify your 'QC' injection volume (ul)", str(injection_vol)
        )

        # qc_vol = st.text_input("Enter the volume for QC standard", "0.01")
        qc_df = pd.DataFrame(
            {
                "File Name": ["QC_Plasma"],
                "Path": [qc_path],
                "Instrument Method": [qc_method],
                "Position": [qc_pos],
                "Inj Vol": [injection_vol_qc],
            }
        )

        # Bind row from wash_df before and after qc_df
        qc_df = pd.concat([qc_df, wash_df], axis=0)
        qc_df = qc_df.reset_index(drop=True)

    with cols[2]:
        ## QC between samples
        st.markdown("### QC between samples")
        qc_between_path = st.text_input(
            "Enter the path to the between QC standard", "C:\\data\\QC_between"
        )
        qc_between_method = st.text_input(
            "Enter the method file for between QC standard",
            "C:\\Xcalibur\\methods\\QC_between",
        )
        qc_between_pos = st.text_input(
            "Enter the position for between QC standard", "GE2"
        )
        injection_vol_qc_between = st.text_input(
            "Modify your 'QC between' injection volume (ul)", str(injection_vol)
        )
        # Tickbox for including QC between samples
        include_qc_between = st.checkbox("Include QC between samples", value=True)

        qc_between_df = pd.DataFrame(
            {
                "File Name": ["QC_" + date_injection],
                "Path": [qc_between_path],
                "Instrument Method": [qc_between_method],
                "Position": [qc_between_pos],
                "Inj Vol": [injection_vol_qc_between],
            }
        )

        qc_between_df_pre = pd.concat([wash_df, qc_between_df], axis=0)
        # append File Name in qc_between_df_pre with _1
        qc_between_df_pre["File Name"] = qc_between_df_pre["File Name"] + "_1"
        qc_between_df_pre = qc_between_df_pre.reset_index(drop=True)

        qc_between_df_post = pd.concat([qc_between_df, wash_df], axis=0)
        qc_between_df_post["File Name"] = qc_between_df_post["File Name"] + "_2"
        qc_between_df_post = qc_between_df_post.reset_index(drop=True)

    # Download data
    st.markdown("### Download data")

    # Add randomized sample order tickbox
    randomize_checkbox_xcalibur = st.checkbox(
        "Randomize sample order", key="randomize_xcalibur"
    )

    if randomize_checkbox_xcalibur:
        st.success("Sample order randomized!")
        output_order_df_rand = output_order_df.sample(frac=1).reset_index(drop=True)
    else:
        output_order_df_rand = output_order_df.copy()

    ## export order sample name
    sample_order_name = _build_download_name(
        [
            datetime.now().strftime("%Y%m%d%H%M"),
            sample_info_output["proj_name"],
            "Sample",
            "Order",
            sample_info_output["plate_id"],
        ],
        ".csv",
    )

    ## export order sample
    ### DIA/DDA plate

    # Bind row from wash_df after every 8 rows in output_order_df
    # Add wash and qc standard after every 8 rows
    output_with_wash = _insert_wash_after_chunks(output_order_df_rand, wash_df, 8)

    ### SRM/PRM plate
    if ms_info_output["acq_tech"] in ["SRM", "PRM"]:
        output_with_wash = output_order_df_rand

    # concat wash and qc dataframes
    output_with_wash = pd.concat(
        [wash_df, qc_df, output_with_wash, qc_df], ignore_index=True
    )

    if qc_between_df.shape[0] > 0 and include_qc_between:
        output_with_wash = pd.concat(
            [qc_between_df_pre, output_with_wash, qc_between_df_post], ignore_index=True
        )

    # Store output_order_df in session state for SDRF tab
    st.session_state.output_order_df = output_order_df

    # Convert DataFrame to CSV with UTF-8 encoding
    csv_data = output_with_wash.to_csv(index=False, encoding="utf-8-sig")
    csv_data = _ensure_bom("Bracket Type=4,,,,\n" + csv_data)

    ## Download button for export file

    st.markdown(
        "The data below is an example for sample order in Xcalibur. The injection order will be randomized and added with wash and qc standard. Be sure with SRM injection"
    )
    st.write(output_order_df_rand)
    st.markdown("Click below to download the data.")
    # Download button for output_order_df
    st.download_button(
        label="Download sample order",
        data=csv_data.encode("utf-8-sig"),
        file_name=sample_order_name,
        mime="text/csv; charset=utf-8",
    )


with evo_tab:
    # (Removed conditional: unindented the block below)
        evosep_sample_df = plate_df_long.copy()

        # Evosep method
        st.header("Evosep method for " + ms_info_output["acq_tech"])

        # Output location
        evosep_output = st.text_input(
            "Enter the directory path to save Evosep method file", uploaded_dir
        )
        st.markdown(
            f"The data will be saved at: <span style='color:red'>{evosep_output}</span>",
            unsafe_allow_html=True,
        )

        # Evosep method file
        evosep_method = st.text_input(
            "Enter the Evosep experiment machine file (.cam)",
            "C:\\data\\Evosep\\method.cam",
        )
        st.markdown(
            f"The Evosep method file is from: <span style='color:red'>{evosep_method}</span>",
            unsafe_allow_html=True,
        )

        # Xcalibur sample SRM/PRM method
        xcalibur_sample_method = st.text_input(
            "Enter the Xcalibur method file (.meth)", "C:\\Xcalibur\\methods.meth"
        )
        st.markdown(
            f"The Xcalibur method file is from: <span style='color:red'>{xcalibur_sample_method}</span>",
            unsafe_allow_html=True,
        )

        # Dropdown evosep_slot 1 to 6
        evosep_slot = st.selectbox("Select Evosep slot", list(range(1, 7)))
        # st.markdown(f"The Evosep slot is: <span style='color:red'>{evosep_slot}</span>", unsafe_allow_html=True)
        # Append EvoLot to evosep_slot
        evosep_slot = "EvoSlot " + str(evosep_slot)

        # Comment
        evosep_comment = st.text_input(
            "Enter comment for Evosep", ms_info_output["srm_lot"]
        )
        # st.markdown(f"The Evosep comment is: <span style='color:red'>{evosep_comment}</span>", unsafe_allow_html=True)

        # Add Source Tray column
        evosep_sample_df["Source Tray"] = [evosep_slot] * evosep_sample_df.shape[0]
        # Add 'Xcalibur Method' column
        evosep_sample_df["Xcalibur Method"] = [
            xcalibur_sample_method
        ] * evosep_sample_df.shape[0]
        # Rename File Name to Sample Name
        evosep_sample_df = evosep_sample_df.rename(columns={"File Name": "Sample Name"})

        # Filter EMPTY wells
        evosep_sample_df = evosep_sample_df[
            evosep_sample_df["Sample"] != EMPTY_WELL_LABEL
        ]

        # Select only column Sample Name, Xcalibur Method, Source Vial
        evosep_sample_df = evosep_sample_df[
            ["Source Tray", "Source Vial", "Sample Name", "Xcalibur Method"]
        ]

        # Create a tick box for randomizing sample order
        randomize_checkbox_chronos = st.checkbox("Randomize sample order")
        if randomize_checkbox_chronos:
            evosep_sample_final = evosep_sample_df.sample(frac=1).reset_index(drop=True)
            st.success("Sample order randomized!")
        else:
            evosep_sample_final = evosep_sample_df.copy()

        cols = st.columns(2)
        with cols[0]:
            st.markdown("### Pre-run: iRT calibration")

            # Tickbox for including iRT method
            include_irt_method = st.checkbox("Include iRT standards", value=False)

            if include_irt_method:
                # Dropdown evosep_slot 1 to 6
                iRT_slot = st.selectbox(
                    "Number of pre-run iRT sample to add", list(range(1, 7))
                )
                iRT_slot = "EvoSlot " + str(iRT_slot)
                # Select total numbers of iRT samples
                iRT_samples = st.number_input(
                    "Select iRT samples", min_value=1, max_value=10, value=2, step=1
                )

                # Xcalibur iRT method
                xcalibur_irt_method = st.text_input(
                    "Enter the Xcalibur iRT method file",
                    "C:\\Xcalibur\\methods\\iRT.meth",
                )
                st.markdown(
                    f"The Xcalibur iRT method file is from: <span style='color:red'>{xcalibur_irt_method}</span>",
                    unsafe_allow_html=True,
                )
                # iRT sample name
                iRT_sample_name = st.text_input(
                    "Enter iRT sample name", "iRT_Tag_unscheduled"
                )
            else:
                iRT_samples = 0
                xcalibur_irt_method = ""

        with cols[1]:
            st.markdown("### Post-run: Standby and Prepare Commands")

            # Tickbox for including standby and prepare commands
            include_standby_prepare = st.checkbox(
                "Include Standby and Prepare commands", value=False
            )

            if include_standby_prepare:
                # Standby command location
                standby_command = st.text_input(
                    "Enter the standby command", "C:\\Xcalibur MS standby.cam"
                )
                # st.markdown(f"The standby command file is from: <span style='color:red'>{standby_command}</span>", unsafe_allow_html=True)

                # Prepare command file location for
                prepare_command = st.text_input(
                    "Enter the prepare command", "C:\\Xcalibur MS prepare.cam"
                )
                # st.markdown(f"The prepare command file is from: <span style='color:red'>{prepare_command}</span>", unsafe_allow_html=True)
            else:
                standby_command = ""
                prepare_command = ""

        ## Create Evosep iRT table

        # evosep_sample_final = evosep_sample_df.copy()
        # iRT sample name
        if iRT_samples != 0:
            # Create iRT df
            evosep_irt_df = pd.DataFrame(
                {
                    # Column Source vial is list from 1 to iRT_samples
                    "Source Vial": list(range(1, iRT_samples + 1)),
                    "Sample Name": [iRT_sample_name] * iRT_samples,
                    "Xcalibur Method": [xcalibur_irt_method] * iRT_samples,
                }
            )

            # Append source vial to Sample Name and add Source Tray column
            evosep_irt_df["Sample Name"] = (
                evosep_irt_df["Sample Name"]
                + "_"
                + evosep_irt_df["Source Vial"].astype(str)
            )

            evosep_irt_df.insert(0, "Source Tray", iRT_slot)

            # Final Evosep df
            evosep_final_df = pd.concat(
                [evosep_irt_df, evosep_sample_final], ignore_index=True
            )

        else:
            evosep_final_df = evosep_sample_final

        # Download Chronos file

        # Add first
        evosep_final_df.insert(
            0, "Analysis Method", [evosep_method] * evosep_final_df.shape[0]
        )

        # Add prefix to Sample Name with ms_info_output['acq_tech']
        # evosep_final_df['Sample Name'] = ms_info_output['acq_tech'] + '_' + evosep_final_df['Sample Name']

        # Add Xcalibur file name column with is File Name
        evosep_final_df["Xcalibur Filename"] = evosep_final_df["Sample Name"]
        # Add empty column call Xcalibur Post Acquisition Program
        evosep_final_df["Xcalibur Post Acquisition Program"] = ""

        # Add Xcalibur output dir called Xcalibur Output Dir
        evosep_final_df["Xcalibur Output Dir"] = [
            evosep_output
        ] * evosep_final_df.shape[0]

        # Add comment
        evosep_final_df["Comment"] = [evosep_comment] * evosep_final_df.shape[0]

        # Add 3 empty columns called  Pump preparation	Align solvents	Flow to column / idle flow
        evosep_final_df["Pump preparation"] = ""
        evosep_final_df["Align solvents"] = ""
        evosep_final_df["Flow to column / idle flow"] = ""

        if include_standby_prepare:
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
            evosep_final_df = pd.concat(
                [evosep_final_df, evo_standby_df], ignore_index=True
            )

        # Use Streamlit's data editor for interactive dataframe editing
        st.subheader("Edit your data here:")
        evosep_final_df = st.data_editor(evosep_final_df, use_container_width=True)

        # Add download buttons for evosep_final_df
        evosep_csv_name = _build_download_name(
            [
                datetime.now().strftime("%Y%m%d%H%M"),
                sample_info_output["proj_name"],
                "Evosep",
                "Order",
                sample_info_output["plate_id"],
            ],
            ".csv",
        )
        csv_evosep_data = evosep_final_df.to_csv(
            index=True, sep=",", encoding="utf-8-sig"
        )

        # Ensure UTF-8 BOM is present
        csv_evosep_data = _ensure_bom(csv_evosep_data)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_evosep_data.encode("utf-8-sig"),
                file_name=evosep_csv_name,
                mime="text/csv; charset=utf-8; separator=semicolon",
            )

        with col2:
            # Add download button for evosep_final_df as XML
            # Replace invalid XML tag characters in column names
            evosep_xml_df = evosep_final_df.copy()
            evosep_xml_df.columns = _sanitize_xml_columns(evosep_xml_df.columns)

            evosep_xml_name = _build_download_name(
                [
                    datetime.now().strftime("%Y%m%d%H%M"),
                    sample_info_output["proj_name"],
                    "Evosep",
                    "Order",
                    sample_info_output["plate_id"],
                ],
                ".xml",
            )

            # Generate XML using ElementTree and minidom
            xml_evosep_data = _create_xml_from_dataframe(evosep_xml_df)

            st.download_button(
                label="⬇️ Download XML",
                data=xml_evosep_data.encode("utf-8"),
                file_name=evosep_xml_name,
                mime="application/xml",
            )

        with col3:
            # Add copy to clipboard button for XML data
            if st.button("📋 Copy XML to Clipboard"):
                st.write(
                    """
                <script>
                navigator.clipboard.writeText(`"""
                    + xml_evosep_data.replace("`", "\\`")
                    + """`);
                </script>
                """,
                    unsafe_allow_html=True,
                )
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
    if "output_order_df" in st.session_state:
        output_order_df = st.session_state.output_order_df
    else:
        st.warning(
            "Please go to the 'Sample Order' tab first to create the sample order."
        )
        st.stop()

    # Create sample properties from Thermo injection table
    sample_prop = plate_df_long.copy()
    # Organism column
    sample_prop["organism"] = [
        sample_info_output["organism_species"]
    ] * sample_prop.shape[0]
    # Organism part
    sample_prop["organism part"] = [sample_info_output["sample"]] * sample_prop.shape[0]
    # Plate
    sample_prop["plate"] = [sample_info_output["plate_id"]] * sample_prop.shape[0]
    # Project
    sample_prop["project"] = [sample_info_output["proj_name"]] * sample_prop.shape[0]
    # age
    sample_prop["age"] = ["not available"] * sample_prop.shape[0]
    # developmental stage
    sample_prop["developmental stage"] = ["not available"] * sample_prop.shape[0]
    # sex
    sample_prop["sex"] = ["not available"] * sample_prop.shape[0]
    # ancestry category
    sample_prop["ancestry category"] = ["not available"] * sample_prop.shape[0]
    # cell type
    sample_prop["cell type"] = ["not available"] * sample_prop.shape[0]
    # cell line
    sample_prop["cell line"] = ["not available"] * sample_prop.shape[0]
    # disease
    sample_prop["disease"] = ["not available"] * sample_prop.shape[0]
    # individual
    sample_prop["individual"] = ["not available"] * sample_prop.shape[0]
    # biological replicate
    sample_prop["biological replicate"] = ["1"] * sample_prop.shape[0]

    # Export column names for factor value
    sample_prop_columns = sample_prop.columns.tolist()

    # Rename all columns with characteristics[]
    sample_prop.columns = "characteristics[" + sample_prop.columns + "]"

    # Adding three columns and first column is source name
    sample_prop.insert(0, "source name", output_order_df["File Name"])
    sample_prop["Material type"] = ["AC=EFO:0009656;NT=plasma"] * sample_prop.shape[0]
    sample_prop["assay name"] = [
        "run " + str(i) for i in range(1, sample_prop.shape[0] + 1)
    ]
    sample_prop["technology type"] = "proteomics profiling by mass spectrometry"

    # Data file properties (MS)
    data_file_prop = pd.DataFrame(
        {
            "data file": output_order_df["File Name"] + "." + ms_file,
            "file uri": output_order_df["File Name"] + "." + ms_file,
            "proteomics data acquisition method": [ms_info_output["sdrf_acquisition"]]
            * len(output_order_df),
            "label": ["AC=MS:1002038;NT=label free sample"] * len(output_order_df),
            "fraction identifier": ["1"] * len(output_order_df),
            "fractionation method": [
                "NT=High-performance liquid chromatography;AC=PRIDE:0000565"
            ]
            * len(output_order_df),
            "technical replicate": ["1"] * len(output_order_df),
            # Add column cleaveage agent details later outside
            "ms2 mass analyzer": ["not available"] * len(output_order_df),
            "instrument": [ms_info_output["sdrf_ms"]] * len(output_order_df),
            "modification parameters": ["NT=Carbamidomethyl;AC=UNIMOD:4;TA=C;MT=Fixed"]
            * len(output_order_df),
            "dissociation method": [ms_info_output["dissociation_accession"]]
            * len(output_order_df),
            "collision energy": [collision_energy + " NCE"] * len(output_order_df),
            "precursor mass tolerance": ["40 ppm"] * len(output_order_df),
            "fragment mass tolerance": ["0.05 Da"] * len(output_order_df),
        }
    )

    # Add enzyme columns with suffix
    if len(ms_info_output["enz_accession_list"]) > 0:
        for i in range(len(ms_info_output["enz_accession_list"])):
            column_name = "cleavage agent details" + str(i)
            data_file_prop[column_name] = [
                ms_info_output["enz_accession_list"][i]
            ] * len(output_order_df)

    # Move all cleavage agent details columns to be after technical replicate
    cleavage_cols = [
        col
        for col in data_file_prop.columns
        if col.startswith("cleavage agent details")
    ]
    other_cols = [
        col
        for col in data_file_prop.columns
        if not col.startswith("cleavage agent details")
    ]

    # Find the index of "technical replicate" column
    tech_rep_index = (
        other_cols.index("technical replicate")
        if "technical replicate" in other_cols
        else 6
    )

    # Reorder: columns before tech replicate + tech replicate + cleavage columns + remaining columns
    new_column_order = (
        other_cols[: tech_rep_index + 1]
        + cleavage_cols
        + other_cols[tech_rep_index + 1 :]
    )
    data_file_prop = data_file_prop[new_column_order]

    # For DIA add MS1 and MS2 scan range
    if ms_info_output["acq_tech"] == "DIA":
        data_file_prop["MS1 scan range"] = ["400-1250 m/z"] * data_file_prop.shape[0]
        data_file_prop["MS2 scan range"] = ["100-2000 m/z"] * data_file_prop.shape[0]

    # For SRM/PRM add ProteomeEdge lot
    if ms_info_output["acq_tech"] in ["SRM", "PRM"]:
        data_file_prop["ProteomeEdge"] = [
            ms_info_output["srm_lot"]
        ] * data_file_prop.shape[0]

    # rename
    data_file_prop.columns = "comment[" + data_file_prop.columns + "]"

    # Colbind sample_prop and data_file_prop
    sdrf_df = pd.concat([sample_prop, data_file_prop], axis=1)

    factor_value_col = st.selectbox(
        "Select column for factor value", sample_prop_columns
    )

    # Add factor values based on selected columns
    # Select box

    sdrf_df[f"factor value[{factor_value_col}]"] = sdrf_df[
        f"characteristics[{factor_value_col}]"
    ]

    # Use Streamlit's data editor for interactive dataframe editing
    st.subheader("Edit your SDRF data here:")
    sdrf_df = st.data_editor(sdrf_df, use_container_width=True)

    # Download SDRF file
    # fix datetime to YYMMDD
    sdrf_filename = _build_download_name(
        [
            datetime.now().strftime("%Y%m%d"),
            sample_info_output["proj_name"],
            sample_info_output["plate_id"],
        ],
        ".sdrf.tsv",
    )
    sdrf_tsv = sdrf_df.to_csv(sep="\t", index=False, encoding="utf-8-sig")

    # Ensure UTF-8 BOM is present
    sdrf_tsv = _ensure_bom(sdrf_tsv)

    # In sdrf_tsv replace first row where comment[cleavage agent details] with any numbers to just comment[cleavage agent details]
    for i in range(len(ms_info_output["enz_accession_list"])):
        sdrf_tsv = sdrf_tsv.replace(
            f"comment[cleavage agent details{i}]", "comment[cleavage agent details]"
        )

    # Download button
    st.download_button(
        label="Download SDRF",
        data=sdrf_tsv.encode("utf-8"),
        file_name=sdrf_filename,
        mime="text/tab-separated-values; charset=utf-8",
    )

    # Add link to website github.com/thanadol-git/quantms_example/
    url = "https://www.github.com/thanadol-git/quantms_example/"
    st.markdown(
        "comment[cleavage agent details'] will be fixed with the downloaded file. Pandas cannot handle two columns with the same name. check out this [link](%s)"
        % url
    )

# Skyline tab
with skyline_tab:
    st.header("Skyline")

    # Upload SDRF file
    st.markdown(
        "Use SDRF file or Upload your SDRF file here to generate Skyline annotation file."
    )
    sdrf_upload = st.file_uploader(
        "Upload SDRF file",
        type=[
            "sdrf.tsv",
            "tsv",
        ],
    )

    # Add dropdown for selecting file to process
    anno_file = st.selectbox(
        "Select SDRF file to process",
        ["Use generated SDRF", "Upload SDRF file"],
        key="sdrf_choice",
    )

    if anno_file == "Upload SDRF file":
        if sdrf_upload is not None:
            upload_sdrf_df = pd.read_csv(sdrf_upload, sep="\t", dtype=str)
            st.success("SDRF file uploaded successfully!")
        else:
            st.warning("Please upload an SDRF file.")
            st.stop()
    else:
        st.info("Using generated SDRF file from previous section.")
        # Use the sdrf_df from previous section
        if "sdrf_df" not in locals():
            st.warning("Please generate the SDRF file in the SDRF section first.")
            st.stop()
        else:
            upload_sdrf_df = sdrf_df.copy()

    # Take columns with charactersistics[] from sdrf_df and also comment[data file]
    char_cols = [
        col for col in upload_sdrf_df.columns if col.startswith("characteristics[")
    ]
    # data_file_col = [col for col in sdrf_df.columns if col == 'comment[data file]']
    skyline_anno = upload_sdrf_df[char_cols]
    # skyline_anno = sdrf_df[char_cols + data_file_col]

    # Rename all colnames to remove characteristics[]
    skyline_anno.columns = [
        col.replace("characteristics[", "").replace("]", "")
        for col in skyline_anno.columns
    ]

    st.subheader("Sample Annotations for Skyline")

    # Display skyline_anno with data editor
    skyline_anno = st.data_editor(skyline_anno, use_container_width=True)

    # Download skyline_anno as csv
    skyline_anno_filename = _build_download_name(
        [
            datetime.now().strftime("%Y%m%d%H%M"),
            sample_info_output["proj_name"],
            "Skyline",
            "Annotations",
            sample_info_output["plate_id"],
        ],
        ".csv",
    )
    skyline_anno_csv = skyline_anno.to_csv(index=False, encoding="utf-8")

    st.download_button(
        label="Download Skyline Annotation",
        data=skyline_anno_csv.encode("utf-8"),
        file_name=skyline_anno_filename,
        mime="text/csv; charset=utf-8",
    )
