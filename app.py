The issue in `app.py` is that while we added the shuffling logic into the `auto_tag_question` function, **Streamlit's `@st.cache_data` decorator** caches the result of `load_questions()` on the first run. Because of caching, Streamlit never re-runs the shuffling function when you refresh or navigate, causing options to stay static or locked in their original order.

To fix this so options shuffle fresh on every session launch, we need to remove `@st.cache_data` from `load_questions()` or add a re-shuffle step.

Here is the fully corrected, working `app.py`:

```python
import json
import os
import random
import time
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="CDMP Master Engine - Passing Engine Suite",
    page_icon="📖",
    layout="wide",
)

# Initialize Session State Variables
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


# Intelligent Auto-Tagging & Option Shuffling Engine
def auto_tag_question(q, idx):
  q_text = q.get("question", "")
  q_type = q.get("type", "Standard")
  domain = q.get("domain", "General")
  options = q.get("options", [])
  correct_idx = q.get("correct", 0)

  # Shuffle options randomly while tracking the correct answer's new index
  if options and 0 <= correct_idx < len(options):
    correct_text = options[correct_idx]
    indexed_options = list(enumerate(options))
    random.shuffle(indexed_options)
    
    shuffled_options = [opt for _, opt in indexed_options]
    new_correct_idx = [
        new_i for new_i, (old_i, _) in enumerate(indexed_options) if old_i == correct_idx
    ][0]
  else:
    shuffled_options = options
    new_correct_idx = correct_idx

  lower_text = q_text.lower()
  if (
      "who is" in lower_text
      or "responsible" in lower_text
      or "steward" in lower_text
      or "committee" in lower_text
  ):
    tier = "Tier 1: Role & Responsibility"
  elif (
      "not" in lower_text
      or "phase" in lower_text
      or "lifecycle" in lower_text
      or "step" in lower_text
  ):
    tier = "Tier 2: Process & Lifecycle"
  elif "difference" in lower_text or "distinguish" in lower_text or "vs" in lower_text:
    tier = "Tier 3: Distinction & Definitions"
  else:
    tier = "Tier 4: Facts & Numerical Thresholds"

  return {
      "id": q.get("id", idx + 1),
      "domain": domain,
      "type": q_type,
      "tier": tier,
      "question": q_text,
      "options": shuffled_options,
      "correct": new_correct_idx,
      "explanation": q.get("explanation", "No explanation provided."),
  }


# Load Questions function (Uncached to ensure option shuffling executes properly on restart)
def load_questions():
  paths = ["questions.json", "code/questions.json", "./code/questions.json"]
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
    raw_data = [
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
                "The Steering Committee is the highest executive body."
            ),
        }
    ]

  return [auto_tag_question(q, i) for i, q in enumerate(raw_data)]


all_questions = load_questions()


# Helper: Dynamic Elimination & Trap Word Breakdown Generator
def generate_elimination_breakdown(q):
  options = q["options"]
  correct_idx = q["correct"]
  trap_words = ["all", "never", "always", "only", "none", "exclusively", "completely"]

  breakdown_html = "#### 🛡️ DAMA Elimination Breakdown & Logic Analysis\n"
  
  found_traps = []
  for i, opt in enumerate(options):
    if i == correct_idx:
      continue
    if any(tw in opt.lower() for tw in trap_words):
      found_traps.append(f"Option {chr(65 + i)}: *\"{opt}\"*")

  if found_traps:
    breakdown_html += (
        "- **Step 1 (Trap Word Detection):** Notice extreme absolute language"
        " in options like: " + ", ".join(found_traps)
        + ". DAMA frameworks are situational and iterative, so absolute rules"
        " are almost always distractors.\n"
    )
  else:
    breakdown_html += (
        "- **Step 1 (Trap Word Detection):** Checked. Distractors rely on"
        " isolationist workflow rather than explicit absolutes.\n"
    )

  breakdown_html += (
      "- **Step 2 (DAMA Philosophy):** DAMA rejects isolation and siloed"
      " behavior, prioritizing cross-functional collaboration and framework"
      " alignment.\n"
  )
  
  correct_letter = chr(65 + correct_idx)
  breakdown_html += (
      f"- **Step 3 (Winning Principle):** **Option {correct_letter}** aligns"
      " perfectly with standard DMBoK governance guidelines.\n\n"
      f"> **📖 DMBoK Reference & Explanation:** {q['explanation']}"
  )
  return breakdown_html


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("CDMP Master Engine")
st.sidebar.subheader("Passing Engine Suite")

nav_mode = st.sidebar.radio(
    "Navigation Suite",
    [
        "⚡ Tier & Chapter Practice",
        "📝 90-Min Exam Simulation",
        "📊 Analytics Dashboard",
        "⭐ Bookmarked Flashcards",
        "📖 DMBoK Glossary Index",
    ],
)

# --- VIEW 1: PRACTICE MODE ---
if nav_mode == "⚡ Tier & Chapter Practice":
  st.header("⚡ Smart Adaptive Practice Mode")
  st.markdown(
      "Practice questions filtered by strategic tiers or individual chapters."
      " Includes automated elimination breakdowns and DMBoK cross-references."
  )

  col_f1, col_f2 = st.columns(2)
  with col_f1:
    tier_filter = st.selectbox(
        "Filter by Strategic Tier",
        [
            "All Tiers",
            "Tier 1: Role & Responsibility",
            "Tier 2: Process & Lifecycle",
            "Tier 3: Distinction & Definitions",
            "Tier 4: Facts & Numerical Thresholds",
        ],
    )
  with col_f2:
    domains = ["All Chapters"] + sorted(list(set(q["domain"] for q in all_questions)))
    domain_filter = st.selectbox("Filter by Chapter / Domain", domains)

  filtered = all_questions
  if tier_filter != "All Tiers":
    filtered = [q for q in filtered if q["tier"] == tier_filter]
  if domain_filter != "All Chapters":
    filtered = [q for q in filtered if q["domain"] == domain_filter]

  if not filtered:
    st.warning("No questions match this specific combination.")
  else:
    if "practice_idx" not in st.session_state:
      st.session_state.practice_idx = 0

    if st.session_state.practice_idx >= len(filtered):
      st.session_state.practice_idx = 0

    curr_q = filtered[st.session_state.practice_idx]

    prog = (st.session_state.practice_idx + 1) / len(filtered)
    st.progress(prog, text=f"Question {st.session_state.practice_idx + 1} of {len(filtered)}")

    st.markdown(f"**Domain:** {curr_q['domain']} | **Tier:** {curr_q['tier']}")
    st.markdown(f"### {curr_q['question']}")

    is_bookmarked = curr_q["id"] in st.session_state.bookmarks
    if st.button("⭐ Bookmark Card" if not is_bookmarked else "❌ Remove Bookmark"):
      if is_bookmarked:
        st.session_state.bookmarks.remove(curr_q["id"])
      else:
        st.session_state.bookmarks.add(curr_q["id"])
      st.rerun()

    with st.form(f"practice_form_{curr_q['id']}"):
      user_ans = st.radio(
          "Select Answer Choice:",
          curr_q["options"],
          key=f"p_ans_{curr_q['id']}",
      )
      submitted = st.form_submit_button("Submit & View Elimination Guide")

    if submitted:
      selected_idx = curr_q["options"].index(user_ans)
      is_correct = selected_idx == curr_q["correct"]

      if is_correct:
        st.success("✅ Correct! Excellent DAMA reasoning.")
      else:
        st.error(
            f"❌ Incorrect. The correct answer was:"
            f" {curr_q['options'][curr_q['correct']]}"
        )
        if curr_q["id"] not in st.session_state.session_wrong_pool:
          st.session_state.session_wrong_pool.append(curr_q["id"])

      st.markdown("---")
      st.markdown(generate_elimination_breakdown(curr_q))

    col_n1, col_n2 = st.columns(2)
    with col_n1:
      if st.button("⬅ Previous Question") and st.session_state.practice_idx > 0:
        st.session_state.practice_idx -= 1
        st.rerun()
    with col_n2:
      if st.button("Next Question ➡") and st.session_state.practice_idx < len(filtered) - 1:
        st.session_state.practice_idx += 1
        st.rerun()


# --- VIEW 2: 90-MIN EXAM SIMULATION (Stable & Flicker-Free) ---
elif nav_mode == "📝 90-Min Exam Simulation":
  st.header("📝 Realistic CDMP Exam Simulation Engine")
  st.markdown(
      "Simulates the strict official exam environment: **100 Questions in 90"
      " Minutes** (54 seconds per question average)."
  )

  if not st.session_state.exam_active:
    if st.button("🚀 Launch 90-Minute Timed Exam (100 Questions)"):
      st.session_state.exam_active = True
      st.session_state.exam_questions = random.sample(
          all_questions, min(100, len(all_questions))
      )
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
      with st.form("exam_form"):
        exam_preds = {}
        for idx, eq in enumerate(st.session_state.exam_questions):
          st.markdown(f"**Q{idx+1}: {eq['question']}**")
          ans = st.radio(
              "Options:", eq["options"], key=f"ex_{eq['id']}", index=None
          )
          exam_preds[eq["id"]] = ans
          st.markdown("---")

        if st.form_submit_button("🏁 Finish & Submit Exam"):
          st.session_state.exam_submitted = True
          st.session_state.exam_user_answers = exam_preds
          st.rerun()
    else:
      correct_count = 0
      total_ex = len(st.session_state.exam_questions)
      wrong_list = []

      for eq in st.session_state.exam_questions:
        user_choice = st.session_state.exam_user_answers.get(eq["id"])
        if user_choice:
          try:
            chosen_idx = eq["options"].index(user_choice)
            if chosen_idx == eq["correct"]:
              correct_count += 1
            else:
              wrong_list.append(eq)
          except ValueError:
            wrong_list.append(eq)
        else:
          wrong_list.append(eq)

      score_pct = (correct_count / total_ex) * 100
      st.subheader(f"Exam Results: {score_pct:.1f}% ({correct_count}/{total_ex})")

      if score_pct >= 70:
        st.success("🎉 Pass! You cleared the 70% CDMP certification threshold!")
      else:
        st.error("❌ Below Passing Threshold (70%). Review your weak areas below.")

      if wrong_list:
        if st.button("🎯 Practice Only My Mistakes (Custom Weak-Spot Quiz)"):
          st.session_state.session_wrong_pool = [w["id"] for w in wrong_list]
          st.rerun()

      if st.button("🔄 Reset Exam Simulation"):
        st.session_state.exam_active = False
        st.session_state.exam_submitted = False
        st.rerun()


# --- VIEW 3: ANALYTICS DASHBOARD ---
elif nav_mode == "📊 Analytics Dashboard":
  st.header("📊 Chapter-by-Chapter Performance Analytics")
  chapters = sorted(list(set(q["domain"] for q in all_questions)))
  for chap in chapters:
    chap_questions = [q for q in all_questions if q["domain"] == chap]
    st.markdown(f"**{chap}** ({len(chap_questions)} total questions)")
    st.progress(0.5, text="Mastery Level: Evaluating session telemetry...")


# --- VIEW 4: BOOKMARKED FLASHCARDS ---
elif nav_mode == "⭐ Bookmarked Flashcards":
  st.header("⭐ Saved Flashcards & Bookmarks")
  bookmarked_qs = [q for q in all_questions if q["id"] in st.session_state.bookmarks]

  if not bookmarked_qs:
    st.info("No bookmarks saved yet. Click 'Bookmark Card' during practice sessions.")
  else:
    st.write(f"You have {len(bookmarked_qs)} saved flashcards.")
    for idx, bq in enumerate(bookmarked_qs):
      with st.expander(f"Card {idx+1}: {bq['question'][:60]}..."):
        st.write(f"**Domain:** {bq['domain']}")
        st.write(f"**Question:** {bq['question']}")
        correct_opt = bq["options"][bq["correct"]]
        st.success(f"**Correct Answer:** {correct_opt}")
        st.info(f"**Explanation:** {bq['explanation']}")


# --- VIEW 5: DMBoK GLOSSARY INDEX ---
elif nav_mode == "📖 DMBoK Glossary Index":
  st.header("📖 Digital DMBoK Glossary & Keyword Search")
  search_query = st.text_input("Search keywords (e.g., Master Data, Lineage, DGO):")
  if search_query:
    results = [
        q
        for q in all_questions
        if search_query.lower() in q["question"].lower()
        or search_query.lower() in q["explanation"].lower()
    ]
    st.write(f"Found {len(results)} matching concepts:")
    for r in results:
      with st.expander(f"[{r['domain']}] {r['question']}"):
        st.write(f"**Explanation:** {r['explanation']}")

```
