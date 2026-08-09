import json
import os
import random
import time
import streamlit as st

st.set_page_config(
    page_title="CDMP Master Engine - Passing Engine Suite",
    page_icon="📖",
    layout="wide",
)

if "initialized" not in st.session_state:
  st.session_state.initialized = True
  st.session_state.current_index = 0
  st.session_state.score = 0
  st.session_state.bookmarks = set()
  st.session_state.session_wrong_pool = []
  st.session_state.exam_active = False
  st.session_state.exam_start_time = None
  st.session_state.exam_submitted = False
  st.session_state.exam_questions = []
  st.session_state.exam_user_answers = {}


def auto_tag_question(q, idx):
  q_text = q.get("question", "")
  options = q.get("options", [])
  correct_idx = q.get("correct", 0)

  if options and 0 <= correct_idx < len(options):
    indexed_options = list(enumerate(options))
    random.shuffle(indexed_options)
    shuffled_options = [opt for _, opt in indexed_options]
    new_correct_idx = [
        new_i for new_i, (old_i, _) in enumerate(indexed_options) if old_i == correct_idx
    ][0]
  else:
    shuffled_options = options
    new_correct_idx = correct_idx

  raw_source = str(q.get("source", q.get("batch", "Standard"))).lower()
  lower_text = q_text.lower()

  if "dama" in raw_source or "official" in raw_source or "dmbook" in raw_source or "fundamental" in lower_text:
    source_batch = "⭐ Official DAMA-Core Priority"
  elif "pra" in raw_source or "new" in raw_source:
    source_batch = "New DMF PRA Batch"
  else:
    source_batch = "Legacy Bank Batch"

  if "who is" in lower_text or "responsible" in lower_text or "steward" in lower_text or "committee" in lower_text:
    tier = "Tier 1: Role & Responsibility"
  elif "not" in lower_text or "phase" in lower_text or "lifecycle" in lower_text or "step" in lower_text:
    tier = "Tier 2: Process & Lifecycle"
  elif "difference" in lower_text or "distinguish" in lower_text or "vs" in lower_text:
    tier = "Tier 3: Distinction & Definitions"
  else:
    tier = "Tier 4: Facts & Numerical Thresholds"

  # Clean domain names to eliminate duplicates caused by whitespace or minor casing differences
  raw_domain = q.get("domain", "General Data Management")
  clean_domain = " ".join(raw_domain.strip().title().split())

  return {
      "id": q.get("id", idx + 1),
      "domain": clean_domain,
      "source_batch": source_batch,
      "tier": tier,
      "question": q_text,
      "options": shuffled_options,
      "correct": new_correct_idx,
      "explanation": q.get("explanation", "Refer to DAMA-DMBoK guidelines for complete framework mapping."),
  }


def load_questions():
  paths = ["code/questions.json", "questions.json", "./code/questions.json", "./questions.json"]
  raw_data = None
  for path in paths:
    if os.path.exists(path):
      try:
        with open(path, "r", encoding="utf-8") as f:
          raw_data = json.load(f)
          break
      except Exception:
        pass

  if not raw_data:
    raw_data = [{
        "id": 1,
        "domain": "Data Governance",
        "source": "Official DAMA",
        "question": "What Organization Structure should set the overall direction for Data Governance?",
        "options": ["Data Governance Steering Committee", "Data Governance Office", "PMO", "IT Leadership Team", "Data Quality Board"],
        "correct": 0,
        "explanation": "The Steering Committee is the highest executive governing body."
    }]

  return [auto_tag_question(q, i) for i, q in enumerate(raw_data)]


all_questions = load_questions()

# Safe Navigation Check (Prompt user if leaving active mock exam)
st.sidebar.title("CDMP Master Engine")
st.sidebar.subheader("Passing Engine Suite")

requested_nav = st.sidebar.radio(
    "Navigation Suite",
    [
        "⚡ Tier & Batch Practice",
        "📝 90-Min Exam Simulation",
        "📊 Analytics Dashboard",
        "⭐ Bookmarked Flashcards",
        "📖 DMBoK Glossary Index",
    ],
)

if st.session_state.exam_active and not st.session_state.exam_submitted and requested_nav != "📝 90-Min Exam Simulation":
  st.sidebar.warning("⚠️ Active Exam Session Running!")
  if st.sidebar.button("🚨 End Exam & Switch View"):
    st.session_state.exam_active = False
    st.session_state.exam_start_time = None
    st.session_state.exam_submitted = False
    st.rerun()
  else:
    nav_mode = "📝 90-Min Exam Simulation"
else:
  nav_mode = requested_nav


if nav_mode == "⚡ Tier & Batch Practice":
  st.header("⚡ Smart Adaptive Practice Mode (DAMA Priority Focus)")
  st.markdown("Filter questions by **Official DAMA Priority batches**, strategic tiers, or specific chapters. Modifying filters instantly refreshes the active pool.")

  col_f1, col_f2, col_f3 = st.columns(3)
  with col_f1:
    batch_filter = st.selectbox(
        "Source / Priority Filter",
        ["All Batches", "⭐ Official DAMA-Core Priority", "New DMF PRA Batch", "Legacy Bank Batch"],
        key="sb_batch",
        on_change=lambda: st.session_state.update({"practice_idx": 0})
    )
  with col_f2:
    tier_filter = st.selectbox(
        "Strategic Tier",
        ["All Tiers", "Tier 1: Role & Responsibility", "Tier 2: Process & Lifecycle", "Tier 3: Distinction & Definitions", "Tier 4: Facts & Numerical Thresholds"],
        key="sb_tier",
        on_change=lambda: st.session_state.update({"practice_idx": 0})
    )
  with col_f3:
    # Use sorted unique deduplicated list
    unique_domains = sorted(list(set(q["domain"] for q in all_questions)))
    domains = ["All Chapters"] + unique_domains
    domain_filter = st.selectbox(
        "Chapter / Domain",
        domains,
        key="sb_domain",
        on_change=lambda: st.session_state.update({"practice_idx": 0})
    )

  filtered = all_questions
  if batch_filter != "All Batches":
    filtered = [q for q in filtered if q["source_batch"] == batch_filter]
  if tier_filter != "All Tiers":
    filtered = [q for q in filtered if q["tier"] == tier_filter]
  if domain_filter != "All Chapters":
    filtered = [q for q in filtered if q["domain"] == domain_filter]

  st.info(f"Active Pool Size: **{len(filtered)} questions** loaded matching current filters.")

  if not filtered:
    st.warning("No questions match this specific filter selection.")
  else:
    if "practice_idx" not in st.session_state:
      st.session_state.practice_idx = 0
    if st.session_state.practice_idx >= len(filtered):
      st.session_state.practice_idx = 0

    curr_q = filtered[st.session_state.practice_idx]

    st.progress((st.session_state.practice_idx + 1) / len(filtered), text=f"Question {st.session_state.practice_idx + 1} of {len(filtered)}")
    st.markdown(f"**Batch:** `{curr_q['source_batch']}` | **Domain:** {curr_q['domain']} | **Tier:** {curr_q['tier']}")
    st.markdown(f"### {curr_q['question']}")

    is_bookmarked = curr_q["id"] in st.session_state.bookmarks
    if st.button("⭐ Bookmark Card" if not is_bookmarked else "❌ Remove Bookmark"):
      if is_bookmarked:
        st.session_state.bookmarks.remove(curr_q["id"])
      else:
        st.session_state.bookmarks.add(curr_q["id"])
      st.rerun()

    with st.form(f"practice_form_{curr_q['id']}"):
      user_ans = st.radio("Select Answer Choice:", curr_q["options"], key=f"p_ans_{curr_q['id']}")
      submitted = st.form_submit_button("Submit & View DAMA Elimination Breakdown")

    if submitted:
      selected_idx = curr_q["options"].index(user_ans)
      if selected_idx == curr_q["correct"]:
        st.success("✅ Correct! Excellent DAMA exam reasoning.")
      else:
        st.error(f"❌ Incorrect. The correct answer was: {curr_q['options'][curr_q['correct']]}")

      st.markdown("---")
      st.markdown("#### 🛡️ DAMA Elimination Breakdown & Logic Analysis")
      st.markdown(f"> **📖 DMBoK Reference & Explanation:** {curr_q['explanation']}")

    col_n1, col_n2 = st.columns(2)
    with col_n1:
      if st.button("⬅ Previous Question") and st.session_state.practice_idx > 0:
        st.session_state.practice_idx -= 1
        st.rerun()
    with col_n2:
      if st.button("Next Question ➡") and st.session_state.practice_idx < len(filtered) - 1:
        st.session_state.practice_idx += 1
        st.rerun()

elif nav_mode == "📝 90-Min Exam Simulation":
  st.header("📝 Realistic CDMP Exam Simulation Engine")
  if not st.session_state.exam_active:
    if st.button("🚀 Launch 90-Minute Timed Exam (100 Questions)"):
      st.session_state.exam_active = True
      st.session_state.exam_questions = random.sample(all_questions, min(100, len(all_questions)))
      st.session_state.exam_start_time = time.time()
      st.session_state.exam_submitted = False
      st.session_state.exam_user_answers = {}
      st.rerun()
  else:
    elapsed = time.time() - st.session_state.exam_start_time
    remaining = max(0, 5400 - int(elapsed))
    mins, secs = divmod(remaining, 60)
    st.sidebar.markdown(f"### ⏱️ Time Remaining: {mins:02d}:{secs:02d}")
    if remaining == 0 and not st.session_state.exam_submitted:
      st.session_state.exam_submitted = True
      st.rerun()

    if not st.session_state.exam_submitted:
      if st.button("🛑 Abort & Discard Exam Session"):
        st.session_state.exam_active = False
        st.session_state.exam_start_time = None
        st.rerun()

      with st.form("exam_form"):
        exam_preds = {}
        for idx, eq in enumerate(st.session_state.exam_questions):
          st.markdown(f"**Q{idx+1}: {eq['question']}**")
          ans = st.radio("Options:", eq["options"], key=f"ex_{eq['id']}", index=None)
          exam_preds[eq["id"]] = ans
          st.markdown("---")
        if st.form_submit_button("🏁 Finish & Submit Exam"):
          st.session_state.exam_submitted = True
          st.session_state.exam_user_answers = exam_preds
          st.rerun()
    else:
      correct_count = sum(1 for eq in st.session_state.exam_questions if st.session_state.exam_user_answers.get(eq["id"]) and eq["options"].index(st.session_state.exam_user_answers[eq["id"]]) == eq["correct"])
      score_pct = (correct_count / len(st.session_state.exam_questions)) * 100
      st.subheader(f"Exam Results: {score_pct:.1f}% ({correct_count}/100)")
      if score_pct >= 70:
        st.success("🎉 Pass! You cleared the official 70% CDMP threshold!")
      else:
        st.error("❌ Below Passing Threshold (70%).")
      if st.button("🔄 Reset Exam Simulation"):
        st.session_state.exam_active = False
        st.session_state.exam_submitted = False
        st.session_state.exam_start_time = None
        st.rerun()

elif nav_mode == "📊 Analytics Dashboard":
  st.header("📊 Chapter & Batch Analytics")
  for batch in ["⭐ Official DAMA-Core Priority", "New DMF PRA Batch", "Legacy Bank Batch"]:
      b_count = len([q for q in all_questions if q["source_batch"] == batch])
      st.write(f"- **{batch}**: {b_count} questions loaded.")

elif nav_mode == "⭐ Bookmarked Flashcards":
  st.header("⭐ Saved Flashcards")
  for bq in [q for q in all_questions if q["id"] in st.session_state.bookmarks]:
    st.write(f"- {bq['question']}")

elif nav_mode == "📖 DMBoK Glossary Index":
  st.header("📖 DMBoK Glossary Index")
  sq = st.text_input("Search keywords:")
  if sq:
    for r in [q for q in all_questions if sq.lower() in q["question"].lower()]:
      st.write(f"💡 {r['question']}")
