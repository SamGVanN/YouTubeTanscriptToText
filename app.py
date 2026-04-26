import streamlit as st
import traceback

# Import the core logic from our existing CLI tool
from extractor import get_transcript_pairs, format_transcript

st.set_page_config(page_title="YouTube Transcript Extractor", page_icon="🎬", layout="centered")

st.title("🎬 YouTube Transcript Extractor")
st.markdown("Extract timestamps and text from YouTube videos or transcript HTML files.")

# Mode selection
mode = st.radio("Choose Input Method", ["YouTube URL", "HTML File Upload"], horizontal=True)

# Input area based on mode
input_data = None
is_url = False

if mode == "YouTube URL":
    is_url = True
    input_data = st.text_input("Enter YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
else:
    is_url = False
    uploaded_file = st.file_uploader("Upload HTML Transcript File", type=["txt", "html"])
    if uploaded_file is not None:
        try:
            input_data = uploaded_file.read().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# Options
st.markdown("### Options")
col1, col2 = st.columns(2)
with col1:
    include_ts = st.checkbox("Include Timestamps", value=True)
with col2:
    fmt_display = st.selectbox("Output Format", ["TSV (Tab-separated)", "Plain Text", "Markdown Table"])
    # Map display names to the internal format identifiers
    fmt_map = {"TSV (Tab-separated)": "tsv", "Plain Text": "txt", "Markdown Table": "md"}
    fmt = fmt_map[fmt_display]

# Action button
if st.button("Extract Transcript", type="primary"):
    if not input_data:
        st.warning("Please provide an input (URL or file) first.")
    else:
        with st.spinner("Processing transcript..."):
            try:
                # 1. Fetch pairs
                pairs = get_transcript_pairs(input_data, is_url=is_url)
                
                if not pairs:
                    st.warning("No transcript found or extracted from the provided input.")
                else:
                    # 2. Format
                    output_text = format_transcript(pairs, include_ts=include_ts, fmt=fmt)
                    
                    st.success(f"Successfully extracted {len(pairs)} segments!")
                    
                    # 3. Output
                    st.markdown("### Preview")
                    # Use a text area for copy-pasting
                    st.text_area("Result", value=output_text, height=300, label_visibility="collapsed")
                    
                    # Provide download button
                    file_extension = fmt
                    st.download_button(
                        label="Download File",
                        data=output_text,
                        file_name=f"transcript.{file_extension}",
                        mime="text/plain"
                    )
            except RuntimeError as e:
                st.error(f"Runtime Error: {e}")
                st.info("Make sure you have installed 'youtube-transcript-api' if you are using YouTube URLs.")
            except Exception as e:
                st.error("An unexpected error occurred:")
                st.code(traceback.format_exc())
