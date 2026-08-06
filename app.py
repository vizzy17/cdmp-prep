import json
import random
import streamlit as st

st.set_page_config(
    page_title="CDMP Master Trainer", page_icon="📊", layout="centered"
)


@st.cache_data
def load_questions():
  try:
    with open("questions.json", "r") as f:
      return json.load(f)
  except FileNotFoundError:
    return []


questions = load_questions()

st.title("🎯 CDMP Exam Mastery & Elimination Engine")
st.write(
    "Practice like the exam. Master roles, lifecycle traps, and structural"
    " logic."
)

if not questions:
  st.error(
      "No questions found. Make sure 'questions.json' is in your repository."
  )
else:
  if "score" not in st.session_state:
    st.session_state.score = 0
    st.session_state.q_index = 0
    st.session_state.submitted = False

  # Progress bar
  progress = st.session_state.q_index / len(questions)
  st.progress(progress)

  current_q = questions[st.session_state.q_index]

  st.subheader(f"Question {st.session_state.q_index + 1} of {len(questions)}")
  st.info(
      f"**Domain:** {current_q['domain']} | **Type:** {current_q['type']}"
  )
  st.write(f"### {current_q['question']}")

  selected_option = st.radio(
      "Choose your answer:", current_q["options"], key=f"q_{st.session_state.q_index}"
  )

  if not st.session_state.submitted:
    if st.button("Submit Answer & Check Elimination Logic"):
      st.session_state.submitted = True
      st.rerun()
  else:
    chosen_index = current_q["options"].index(selected_option)
    if chosen_index == current_q["correct"]:
      st.success("✅ Correct! Excellent application of DAMA logic.")
    else:
      st.error(
          f"❌ Incorrect. The correct answer was: **"
          f"{current_q['options'][current_q['correct']]}**"
      )

    st.markdown(f"> **DAMA Logic Breakdown:** {current_q['explanation']}")

    if st.button("Next Question ➡️"):
      st.session_state.q_index += 1
      st.session_state.submitted = False
      if st.session_state.q_index >= len(questions):
        st.balloons()
        st.success("Quiz Completed! You've finished this test block.")
        st.session_state.q_index = 0
      st.rerun()
