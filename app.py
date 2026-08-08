import json
import os
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="CDMP Master Engine - Passing Engine Suite",
    page_icon="📖",
    layout="centered",
)

st.title("CDMP Master Engine")
st.subheader("Passing Engine Suite")


# Load Questions function with safe local fallback
@st.cache_data
def load_questions():
  # Check paths relative to typical repo structures
  paths = ["questions.json", "code/questions.json", "./code/questions.json"]
  data = None

  for path in paths:
    if os.path.exists(path):
      try:
        with open(path, "r", encoding="utf-8") as f:
          data = json.load(f)
          break
      except Exception as e:
        print(f"Error reading {path}: {e}")

  # Fallback data if JSON file isn't found or fails parsing, ensuring app always works
  if not data:
    data = [
        {
            "id": 1,
            "domain": "Data Governance",
            "type": "Role & Responsibility",
            "question": (
                "What Organization Structure should set the overall direction"
                " for Data Governance?"
            ),
            "options": [
                "Data Governance Steering Committee",
                "Data Governance Office",
                "PMO",
                "IT Leadership Team",
                "Data Quality Board",
            ],
            "correct": 0,
            "explanation": (
                "The Steering Committee / Council is the highest executive body"
                " that sets direction, while the DGO handles day-to-day"
                " operations."
            ),
        },
        {
            "id": 2,
            "domain": "Data Governance",
            "type": "Process & Lifecycle",
            "question": (
                "Which of the following is NOT a primary responsibility of a"
                " Data Steward?"
            ),
            "options": [
                "Defining business glossaries and data definitions",
                "Writing physical database tables and indexes",
                "Identifying data quality rules and issues",
                "Ensuring compliance with data policies",
            ],
            "correct": 1,
            "explanation": (
                "Data Stewards manage business metadata, definitions, and"
                " quality rules. Writing physical database objects is an IT /"
                " DBA implementation task."
            ),
        },
    ]

  # Normalize properties
  formatted_data = []
  for idx, q in enumerate(data):
    formatted_data.append({
        "id": q.get("id", idx + 1),
        "domain": q.get("domain", "General"),
        "type": q.get("type", "Standard"),
        "question": q.get("question", "No question provided."),
        "options": q.get("options", []),
        "correct": q.get("correct", 0),
        "explanation": q.get("explanation", "No explanation provided."),
    })
  return formatted_data


questions = load_questions()

# Sidebar Filters / Navigation
st.sidebar.header("Strategic Tier/Chapter")
filter_option = st.sidebar.selectbox(
    "Select View Mode",
    [
        "All Tiers & Chapters",
        "Tier 1: Role & Responsibility",
        "Tier 2: Process & Lifecycle",
        "Tier 3: Distinction & Definitions",
        "Tier 4: Facts & Numerical Thresholds",
        "Chapter 2: Data Governance",
        "Chapter 3: Data Handling Ethics",
        "Chapter 4: Data Architecture",
        "Chapter 5: Data Modeling & Design",
        "Chapter 6: Data Storage & Operations",
        "Chapter 7: Data Security",
        "Chapter 8: Data Integration",
        "Chapter 10: Reference & Master Data",
        "Chapter 11: Data Warehousing & BI",
        "Chapter 12: Metadata Management",
        "Chapter 13: Data Quality",
    ],
)

# Filter logic
if filter_option == "All Tiers & Chapters":
  filtered_q = questions
elif filter_option.startswith("Tier"):
  filtered_q = [q for q in questions if q["type"] == filter_option.split(": ")[1]]
else:
  filtered_q = [
      q for q in questions if filter_option.lower() in q["domain"].lower()
  ]

if not filtered_q:
  filtered_q = questions  # Fallback if filter returns empty

# Initialize Session State for Pagination
if "index" not in st.session_state:
  st.session_state.index = 0

if st.session_state.index >= len(filtered_q):
  st.session_state.index = 0

current_q = filtered_q[st.session_state.index]

# Main Card UI Display
st.markdown(f"**Domain:** {current_q['domain']} | **Type:** {current_q['type']}")
st.markdown(f"### Question {st.session_state.index + 1} of {len(filtered_q)}")

st.write(f"**{current_q['question']}**")

# Options Form / Radio Selection
user_choice = st.radio(
    "Select your answer:", current_q["options"], key=f"q_{current_q['id']}"
)

# Check Answer Button
if st.button("Submit / Flip Answer"):
  selected_index = current_q["options"].index(user_choice)
  if selected_index == current_q["correct"]:
    st.success("Correct!")
  else:
    st.error(
        f"Incorrect. The correct answer is:"
        f" {current_q['options'][current_q['correct']]}"
    )
  st.info(f"**Explanation:** {current_q['explanation']}")

# Navigation Controls
col1, col2 = st.columns(2)
with col1:
  if st.button("Previous Question") and st.session_state.index > 0:
    st.session_state.index -= 1
    st.rerun()
with col2:
  if (
      st.button("Next Question")
      and st.session_state.index < len(filtered_q) - 1
  ):
    st.session_state.index += 1
    st.rerun()
