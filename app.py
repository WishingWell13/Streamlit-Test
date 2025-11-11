import streamlit as st
import random
import time

st.set_page_config(page_title="Toy Page Number App", layout="centered")

# Use session state for fast, synced updates
def set_random_page():
    st.session_state.page_number = random.randint(1, 10)

if "page_number" not in st.session_state:
    st.session_state.page_number = 1

st.title("Toy Page Number App")

# Number input for page number
page_input = st.number_input(
    "Set page number:", min_value=1, max_value=10, value=st.session_state.page_number,
    key="page_input",
    on_change=lambda: st.session_state.update({"page_number": st.session_state.page_input})
)

if st.button("Set to random page (1-10)"):
    set_random_page()
    st.rerun()
    
with st.spinner("Loading..."):
        time.sleep(1)

# Display current page number
st.markdown(f"### Current Page Number: {st.session_state.page_number}")
