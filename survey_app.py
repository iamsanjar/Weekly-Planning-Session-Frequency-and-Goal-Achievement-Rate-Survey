from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

ALLOWED_NAME_PUNCTUATION = frozenset({"-", "'", " "})   
SUPPORTED_EXTENSIONS: set = {"txt", "csv", "json"}       

_DEMO_INT:   int   = 0                       
_DEMO_STR:   str   = "survey"                   
_DEMO_FLOAT: float = 0.0                        
_DEMO_LIST:  list  = []                         
_DEMO_TUPLE: tuple = (0, 100)                 
_DEMO_RANGE: range = range(15, 26)              
_DEMO_BOOL:  bool  = True                       
_DEMO_DICT:  dict  = {}                      

FALLBACK_QUESTION_BANK: dict = {
    "survey_id": "weekly-planning-goal-achievement",
    "title": "Weekly Planning Session Frequency and Goal Achievement Rate Survey",
    "description": (
        "This questionnaire measures how regularly a person plans their week "
        "and how effectively they achieve planned goals."
    ),
    "questions": [
        {"id": 1,
         "text": "How often do you dedicate time to holding a structured weekly planning session?",
         "options": [
             {"label": "Every week without exception",  "score": 0},
             {"label": "Most weeks",                    "score": 1},
             {"label": "Occasionally",                  "score": 2},
             {"label": "Almost never or never",         "score": 3}]},
        {"id": 2,
         "text": "When you set goals at the start of a week, how many do you typically achieve by the end of it?",
         "options": [
             {"label": "Nearly all of them",            "score": 0},
             {"label": "More than half",                "score": 1},
             {"label": "About half or fewer",           "score": 2},
             {"label": "Rarely any",                    "score": 3}]},
        {"id": 3,
         "text": "How clearly do you define your goals before beginning a planning session?",
         "options": [
             {"label": "Always clearly, with specific steps and deadlines", "score": 0},
             {"label": "Usually clear, though sometimes vague",             "score": 1},
             {"label": "Often vague or loosely defined",                    "score": 2},
             {"label": "I do not define goals in advance",                  "score": 3}]},
        {"id": 4,
         "text": "How consistently do you review what you planned at the end of each week to assess your progress?",
         "options": [
             {"label": "Every week",                    "score": 0},
             {"label": "Often, but not every week",     "score": 1},
             {"label": "Rarely",                        "score": 2},
             {"label": "Never",                         "score": 3}]},
        {"id": 5,
         "text": "When you do not achieve a planned goal, how do you typically respond?",
         "options": [
             {"label": "I analyse what went wrong and adjust my approach", "score": 0},
             {"label": "I reschedule the goal for next week",              "score": 1},
             {"label": "I feel frustrated but do not take specific action","score": 2},
             {"label": "I tend to abandon the goal altogether",            "score": 3}]},
        {"id": 6,
         "text": "How well do you prioritise your goals during a planning session?",
         "options": [
             {"label": "Very well, I always rank tasks by importance and urgency",          "score": 0},
             {"label": "Fairly well, I consider priority most of the time",                 "score": 1},
             {"label": "Inconsistently, I sometimes treat all tasks as equally important",  "score": 2},
             {"label": "I do not prioritise and proceed without a clear order",             "score": 3}]},
        {"id": 7,
         "text": "How often do you break large goals into smaller, manageable steps during planning?",
         "options": [
             {"label": "Always",   "score": 0},
             {"label": "Often",    "score": 1},
             {"label": "Rarely",   "score": 2},
             {"label": "Never",    "score": 3}]},
        {"id": 8,
         "text": "How realistic are the goals you usually set for a single week?",
         "options": [
             {"label": "Very realistic and achievable",      "score": 0},
             {"label": "Mostly realistic",                   "score": 1},
             {"label": "Sometimes unrealistic",              "score": 2},
             {"label": "Usually too ambitious or unclear",   "score": 3}]},
        {"id": 9,
         "text": "How often do unexpected events completely derail your weekly plans?",
         "options": [
             {"label": "Almost never because I adapt well",  "score": 0},
             {"label": "Occasionally",                       "score": 1},
             {"label": "Often",                              "score": 2},
             {"label": "Almost every week",                  "score": 3}]},
        {"id": 10,
         "text": "How much time do you usually spend preparing your weekly plan?",
         "options": [
             {"label": "Enough time to think through tasks carefully", "score": 0},
             {"label": "A reasonable amount of time",                  "score": 1},
             {"label": "Very little time",                             "score": 2},
             {"label": "I do not set aside planning time",             "score": 3}]},
        {"id": 11,
         "text": "How often do you write your weekly goals down in a planner, notebook, or digital tool?",
         "options": [
             {"label": "Every week",   "score": 0},
             {"label": "Most weeks",   "score": 1},
             {"label": "Rarely",       "score": 2},
             {"label": "Never",        "score": 3}]},
        {"id": 12,
         "text": "How confident do you feel that you will complete your goals after a planning session?",
         "options": [
             {"label": "Very confident",         "score": 0},
             {"label": "Moderately confident",   "score": 1},
             {"label": "Slightly confident",     "score": 2},
             {"label": "Not confident at all",   "score": 3}]},
        {"id": 13,
         "text": "When planning your week, how often do you consider deadlines in advance?",
         "options": [
             {"label": "Always",           "score": 0},
             {"label": "Usually",          "score": 1},
             {"label": "Sometimes",        "score": 2},
             {"label": "Rarely or never",  "score": 3}]},
        {"id": 14,
         "text": "How often do you include time for rest or recovery when making your weekly plan?",
         "options": [
             {"label": "Always",   "score": 0},
             {"label": "Often",    "score": 1},
             {"label": "Rarely",   "score": 2},
             {"label": "Never",    "score": 3}]},
        {"id": 15,
         "text": "How likely are you to postpone an important task even after planning it?",
         "options": [
             {"label": "Very unlikely",      "score": 0},
             {"label": "Somewhat unlikely",  "score": 1},
             {"label": "Quite likely",       "score": 2},
             {"label": "Very likely",        "score": 3}]},
        {"id": 16,
         "text": "How often do you adjust your weekly goals when you notice they are no longer realistic?",
         "options": [
             {"label": "Promptly and effectively",                           "score": 0},
             {"label": "Sometimes",                                          "score": 1},
             {"label": "Rarely",                                             "score": 2},
             {"label": "I usually continue without adjusting anything",      "score": 3}]},
        {"id": 17,
         "text": "How organized are the tools or systems you use for weekly planning?",
         "options": [
             {"label": "Very organized and easy to follow",  "score": 0},
             {"label": "Mostly organized",                   "score": 1},
             {"label": "Somewhat disorganized",              "score": 2},
             {"label": "I do not use any consistent system", "score": 3}]},
        {"id": 18,
         "text": "How often do you begin your week knowing exactly which goals are the top priority?",
         "options": [
             {"label": "Always",           "score": 0},
             {"label": "Usually",          "score": 1},
             {"label": "Sometimes",        "score": 2},
             {"label": "Rarely or never",  "score": 3}]},
        {"id": 19,
         "text": "How often do you reflect on why certain goals were completed successfully?",
         "options": [
             {"label": "Every week",   "score": 0},
             {"label": "Often",        "score": 1},
             {"label": "Rarely",       "score": 2},
             {"label": "Never",        "score": 3}]},
        {"id": 20,
         "text": "Overall, how effective do you believe your weekly planning process is?",
         "options": [
             {"label": "Highly effective",      "score": 0},
             {"label": "Mostly effective",      "score": 1},
             {"label": "Somewhat ineffective",  "score": 2},
             {"label": "Very ineffective",      "score": 3}]},
    ],
    "states": [
        {"min_score": 0,  "max_score": 12,
         "label":   "Highly Effective Planner",
         "summary": "Exceptional planning frequency and goal achievement.",
         "description": "Strong self-regulatory habits are visible in the answers, so no immediate intervention is needed."},
        {"min_score": 13, "max_score": 24,
         "label":   "Effective Planner",
         "summary": "Good planning consistency with solid goal achievement.",
         "description": "Current habits are working well, and only minor improvements are likely to be needed."},
        {"min_score": 25, "max_score": 36,
         "label":   "Moderate Planner",
         "summary": "Planning is present, but goal achievement is inconsistent.",
         "description": "Refining goal structure, planning detail, and weekly review habits would likely improve results."},
        {"min_score": 37, "max_score": 48,
         "label":   "Inconsistent Planner",
         "summary": "Planning sessions are irregular and goal achievement is low.",
         "description": "Increasing planning frequency and adding stronger accountability would be advisable."},
        {"min_score": 49, "max_score": 60,
         "label":   "Disengaged Planner",
         "summary": "There is little structured planning and planned goals are rarely achieved.",
         "description": "A more supportive structure around self-regulation and goal setting is strongly recommended."},
    ],
}


@dataclass
class SurveyOption:
    label: str
    score: int


@dataclass
class SurveyQuestion:
    question_id: int
    text: str
    options: List[SurveyOption]


@dataclass
class SurveyState:
    min_score: int
    max_score: int
    label: str
    summary: str
    description: str


@dataclass
class SurveyResult:
    survey_title: str
    survey_id: str
    surname: str
    given_name: str
    date_of_birth: str
    student_id: str
    submitted_at: str
    total_score: int
    max_score: int
    score_percentage: float
    state_label: str
    state_summary: str
    state_description: str
    answers: List[Dict[str, Any]]



def clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def validate_name(value: str, field_label: str) -> str:
    cleaned_value = clean_text(value)
    if not cleaned_value:
        raise ValueError(f"{field_label} cannot be empty.")
    contains_letter: bool = False          # ← bool
    for character in cleaned_value:
        if character.isalpha() and character.isascii():
            contains_letter = True
            continue
        if character not in ALLOWED_NAME_PUNCTUATION:
            raise ValueError(
                f"{field_label} can contain only letters, spaces, hyphens, and apostrophes."
            )
    if not contains_letter:
        raise ValueError(f"{field_label} must contain at least one letter.")
    return cleaned_value


def validate_date_of_birth(value: str) -> str:
    cleaned_value = clean_text(value)
    if not cleaned_value:
        raise ValueError("Date of birth cannot be empty.")
    try:
        parsed_date = datetime.strptime(cleaned_value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("Date of birth must use the YYYY-MM-DD format.") from error
    today = date.today()
    if parsed_date > today:
        raise ValueError("Date of birth cannot be in the future.")
    if parsed_date.year < today.year - 120:
        raise ValueError("Date of birth appears to be outside a valid range.")
    return parsed_date.isoformat()


def validate_student_id(value: str) -> str:
    cleaned_value = clean_text(value)
    if not cleaned_value:
        raise ValueError("Student ID cannot be empty.")
    idx = 0                                          # ← while loop for input validation
    while idx < len(cleaned_value):
        if not cleaned_value[idx].isdigit():
            raise ValueError("Student ID must contain digits only.")
        idx += 1
    return cleaned_value



def parse_question_bank(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a raw dict (from JSON file or the embedded fallback) into typed objects."""
    raw_questions: list = raw_data.get("questions", [])   # list
    raw_states:    list = raw_data.get("states",    [])   # list

    if len(raw_questions) not in range(15, 26):
        raise ValueError("The question bank must contain between 15 and 25 questions.")
    if len(raw_states) not in range(5, 8):
        raise ValueError("The survey must contain between 5 and 7 result states.")

    questions: List[SurveyQuestion] = []
    for expected_id, question_data in zip(range(1, len(raw_questions) + 1), raw_questions):
        if question_data.get("id") != expected_id:
            raise ValueError("Question IDs must be sequential and start from 1.")
        raw_options: list = question_data.get("options", [])   # list
        if len(raw_options) not in range(3, 6):
            raise ValueError("Each question must have between 3 and 5 answer options.")
        options = [
            SurveyOption(label=str(o["label"]), score=int(o["score"]))
            for o in raw_options
        ]
        questions.append(
            SurveyQuestion(
                question_id=int(question_data["id"]),
                text=str(question_data["text"]),
                options=options,
            )
        )

    states = [
        SurveyState(
            min_score=int(s["min_score"]),
            max_score=int(s["max_score"]),
            label=str(s["label"]),
            summary=str(s["summary"]),
            description=str(s["description"]),
        )
        for s in raw_states
    ]

    return {
        "survey_id": str(raw_data["survey_id"]),
        "title": str(raw_data["title"]),
        "description": str(raw_data["description"]),
        "questions": questions,
        "states": states,
    }


def load_question_bank(file_path: Path) -> Dict[str, Any]:
    """Load and parse a question bank from an external JSON file."""
    with file_path.open("r", encoding="utf-8") as f:
        raw_data: dict = json.load(f)   # dict
    return parse_question_bank(raw_data)


def load_fallback_question_bank() -> Dict[str, Any]:
    """Return the question bank embedded directly in this source file (fallback)."""
    return parse_question_bank(FALLBACK_QUESTION_BANK)



def calculate_max_score(questions: List[SurveyQuestion]) -> int:
    return sum(max(o.score for o in q.options) for q in questions)


def resolve_state(total_score: int, states: List[SurveyState]) -> SurveyState:
    for state in states:
        if state.min_score <= total_score <= state.max_score:
            return state
    raise ValueError("The final score does not match any configured result state.")


def build_result(
    respondent_info: Dict[str, str],
    answers: List[int],
    questions: List[SurveyQuestion],
    states: List[SurveyState],
    survey_title: str,
    survey_id: str,
) -> SurveyResult:
    total_score = 0
    answer_details: List[Dict[str, Any]] = []
    for q_idx, a_idx in enumerate(answers):
        question = questions[q_idx]
        chosen = question.options[a_idx]
        total_score += chosen.score
        answer_details.append(
            {
                "question_id": question.question_id,
                "question": question.text,
                "selected_answer": chosen.label,
                "score": chosen.score,
            }
        )
    max_score = calculate_max_score(questions)
    state = resolve_state(total_score, states)
    score_pct = round((total_score / float(max_score)) * 100, 2) if max_score else 0.0

    return SurveyResult(
        survey_title=survey_title,
        survey_id=survey_id,
        surname=respondent_info["surname"],
        given_name=respondent_info["given_name"],
        date_of_birth=respondent_info["date_of_birth"],
        student_id=respondent_info["student_id"],
        submitted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_score=total_score,
        max_score=max_score,
        score_percentage=score_pct,
        state_label=state.label,
        state_summary=state.summary,
        state_description=state.description,
        answers=answer_details,
    )


def result_to_txt(result: SurveyResult) -> bytes:
    lines = [
        "[METADATA]",
        f"survey_title: {result.survey_title}",
        f"survey_id: {result.survey_id}",
        f"surname: {result.surname}",
        f"given_name: {result.given_name}",
        f"date_of_birth: {result.date_of_birth}",
        f"student_id: {result.student_id}",
        f"submitted_at: {result.submitted_at}",
        f"total_score: {result.total_score}",
        f"max_score: {result.max_score}",
        f"score_percentage: {result.score_percentage}",
        f"state_label: {result.state_label}",
        f"state_summary: {result.state_summary}",
        f"state_description: {result.state_description}",
        "",
        "[ANSWERS]",
    ]
    for a in result.answers:
        lines.append(
            f"{a['question_id']} | {a['question']} | {a['selected_answer']} | {a['score']}"
        )
    return "\n".join(lines).encode("utf-8")


def result_to_csv(result: SurveyResult) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=("section", "key", "value", "question_id", "question", "selected_answer", "score"),
    )
    writer.writeheader()
    metadata = {
        "survey_title": result.survey_title,
        "survey_id": result.survey_id,
        "surname": result.surname,
        "given_name": result.given_name,
        "date_of_birth": result.date_of_birth,
        "student_id": result.student_id,
        "submitted_at": result.submitted_at,
        "total_score": result.total_score,
        "max_score": result.max_score,
        "score_percentage": result.score_percentage,
        "state_label": result.state_label,
        "state_summary": result.state_summary,
        "state_description": result.state_description,
    }
    for key, value in metadata.items():
        writer.writerow({"section": "meta", "key": key, "value": value})
    for a in result.answers:
        writer.writerow(
            {
                "section": "answer",
                "question_id": a["question_id"],
                "question": a["question"],
                "selected_answer": a["selected_answer"],
                "score": a["score"],
            }
        )
    return buf.getvalue().encode("utf-8")


def result_to_json(result: SurveyResult) -> bytes:
    return json.dumps(asdict(result), indent=2, ensure_ascii=False).encode("utf-8")



def load_from_txt_bytes(raw: bytes) -> SurveyResult:
    metadata: Dict[str, str] = {}
    answers: List[Dict[str, Any]] = []
    section = ""
    for raw_line in raw.decode("utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "[METADATA]":
            section = "metadata"
            continue
        if line == "[ANSWERS]":
            section = "answers"
            continue
        if section == "metadata":
            if ":" not in line:
                raise ValueError("Invalid TXT metadata format.")
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        elif section == "answers":
            parts = [p.strip() for p in line.split(" | ", 3)]
            if len(parts) != 4:
                raise ValueError("Invalid TXT answer format.")
            answers.append(
                {
                    "question_id": int(parts[0]),
                    "question": parts[1],
                    "selected_answer": parts[2],
                    "score": int(parts[3]),
                }
            )
    return build_result_from_data(metadata, answers)


def load_from_csv_bytes(raw: bytes) -> SurveyResult:
    metadata: Dict[str, str] = {}
    answers: List[Dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    for row in reader:
        section = (row.get("section") or "").strip().lower()
        if section == "meta":
            key = (row.get("key") or "").strip()
            metadata[key] = (row.get("value") or "").strip()
        elif section == "answer":
            answers.append(
                {
                    "question_id": int(row["question_id"]),
                    "question": row["question"],
                    "selected_answer": row["selected_answer"],
                    "score": int(row["score"]),
                }
            )
    return build_result_from_data(metadata, answers)


def load_from_json_bytes(raw: bytes) -> SurveyResult:
    d = json.loads(raw.decode("utf-8"))
    return SurveyResult(
        survey_title=str(d["survey_title"]),
        survey_id=str(d["survey_id"]),
        surname=str(d["surname"]),
        given_name=str(d["given_name"]),
        date_of_birth=str(d["date_of_birth"]),
        student_id=str(d["student_id"]),
        submitted_at=str(d["submitted_at"]),
        total_score=int(d["total_score"]),
        max_score=int(d["max_score"]),
        score_percentage=float(d["score_percentage"]),
        state_label=str(d["state_label"]),
        state_summary=str(d["state_summary"]),
        state_description=str(d["state_description"]),
        answers=list(d["answers"]),
    )


def build_result_from_data(
    metadata: Dict[str, str], answers: List[Dict[str, Any]]
) -> SurveyResult:
    required = {
        "survey_title", "survey_id", "surname", "given_name",
        "date_of_birth", "student_id", "submitted_at",
        "total_score", "max_score", "score_percentage",
        "state_label", "state_summary", "state_description",
    }
    if not required.issubset(set(metadata.keys())):
        raise ValueError("The selected file does not contain a complete survey result.")
    return SurveyResult(
        survey_title=metadata["survey_title"],
        survey_id=metadata["survey_id"],
        surname=metadata["surname"],
        given_name=metadata["given_name"],
        date_of_birth=metadata["date_of_birth"],
        student_id=metadata["student_id"],
        submitted_at=metadata["submitted_at"],
        total_score=int(metadata["total_score"]),
        max_score=int(metadata["max_score"]),
        score_percentage=float(metadata["score_percentage"]),
        state_label=metadata["state_label"],
        state_summary=metadata["state_summary"],
        state_description=metadata["state_description"],
        answers=answers,
    )


def init_state(bank: Dict[str, Any]) -> None:
    defaults = {
        "screen": "home",
        "respondent": {},
        "answers": [None] * len(bank["questions"]),
        "current_q": 0,
        "result": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val



def render_home(bank: Dict[str, Any]) -> None:
    max_score = calculate_max_score(bank["questions"])
    score_range: Tuple[int, int] = (0, max_score)   # ← tuple

    st.title(bank["title"])
    st.caption(bank["description"])

    st.info(
        f"Question bank loaded: **{len(bank['questions'])} questions**, "
        f"score range **{score_range[0]} – {score_range[1]}**.  \n"
        "Supported save / load formats: **TXT, CSV, JSON**."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("▶ Start New Survey", use_container_width=True, type="primary"):
            st.session_state.screen = "info"
            st.session_state.answers = [None] * len(bank["questions"])
            st.session_state.current_q = 0
            st.session_state.result = None
            st.rerun()

    with col2:
        st.markdown("**Load a saved result file**")
        uploaded = st.file_uploader(
            "Upload TXT / CSV / JSON", type=["txt", "csv", "json"], label_visibility="collapsed"
        )
        if uploaded is not None:
            ext = uploaded.name.rsplit(".", 1)[-1].lower()
            try:
                raw = uploaded.read()
                if ext == "txt":
                    loaded = load_from_txt_bytes(raw)
                elif ext == "csv":
                    loaded = load_from_csv_bytes(raw)
                else:
                    loaded = load_from_json_bytes(raw)
                st.session_state.result = loaded
                st.session_state.screen = "result"
                st.rerun()
            except Exception as exc:
                st.error(f"Could not load file: {exc}")


def render_info() -> None:
    st.title("Respondent Details")
    st.write("Enter participant information before starting the survey. Date of birth must use **YYYY-MM-DD** format.")

    with st.form("info_form"):
        surname = st.text_input("Surname")
        given_name = st.text_input("Given Name")
        dob = st.text_input("Date of Birth (YYYY-MM-DD)")
        student_id = st.text_input("Student ID")

        col1, col2 = st.columns([1, 5])
        with col1:
            submitted = st.form_submit_button("Continue →", type="primary")
        with col2:
            back = st.form_submit_button("← Back")

    if back:
        st.session_state.screen = "home"
        st.rerun()

    if submitted:
        try:
            st.session_state.respondent = {
                "surname": validate_name(surname, "Surname"),
                "given_name": validate_name(given_name, "Given Name"),
                "date_of_birth": validate_date_of_birth(dob),
                "student_id": validate_student_id(student_id),
            }
            st.session_state.screen = "question"
            st.session_state.current_q = 0
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def render_question(bank: Dict[str, Any]) -> None:
    questions = bank["questions"]
    idx = st.session_state.current_q
    question = questions[idx]
    total_q = len(questions)
    answered = sum(1 for a in st.session_state.answers if a is not None)

    st.title(bank["title"])
    st.progress((idx) / total_q, text=f"Question {idx + 1} of {total_q}")
    st.caption(f"Answered so far: {answered} / {total_q}")

    st.subheader(question.text)

    option_labels = [o.label for o in question.options]
    current_answer = st.session_state.answers[idx]
    default_index = current_answer if current_answer is not None else 0

    chosen = st.radio(
        "Select your answer:",
        options=range(len(option_labels)),
        format_func=lambda i: option_labels[i],
        index=default_index,
        key=f"q_{idx}",
    )

    st.divider()
    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button("← Previous", disabled=(idx == 0)):
            st.session_state.answers[idx] = chosen
            st.session_state.current_q -= 1
            st.rerun()

    is_last: bool = idx == total_q - 1   # ← bool
    with col2:
        label = "Finish Survey ✓" if is_last else "Next →"
        if st.button(label, type="primary"):
            st.session_state.answers[idx] = chosen
            if is_last:
                try:
                    result = build_result(
                        respondent_info=st.session_state.respondent,
                        answers=st.session_state.answers,
                        questions=bank["questions"],
                        states=bank["states"],
                        survey_title=bank["title"],
                        survey_id=bank["survey_id"],
                    )
                    st.session_state.result = result
                    st.session_state.screen = "result"
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            else:
                st.session_state.current_q += 1
                st.rerun()

    with col3:
        if st.button("✕ Cancel"):
            st.session_state.screen = "home"
            st.rerun()


def render_result() -> None:
    result: SurveyResult = st.session_state.result

    st.title("Survey Result")

    st.subheader("Respondent")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {result.given_name} {result.surname}")
        st.markdown(f"**Date of birth:** {result.date_of_birth}")
    with col2:
        st.markdown(f"**Student ID:** {result.student_id}")
        st.markdown(f"**Recorded on:** {result.submitted_at}")

    st.divider()

    st.subheader("Score")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total score", f"{result.total_score} / {result.max_score}")
    col2.metric("Percentage", f"{result.score_percentage}%")
    col3.metric("State", result.state_label)

    st.markdown(f"**Summary:** {result.state_summary}")
    st.markdown(f"**Interpretation:** {result.state_description}")

    st.divider()

    st.subheader("Answer Breakdown")
    for a in result.answers:
        with st.expander(f"Q{a['question_id']}. {a['question']}"):
            st.markdown(f"**Selected answer:** {a['selected_answer']}")
            st.markdown(f"**Score:** {a['score']}")

    st.divider()

    st.subheader("Download Result")
    filename_base = f"{result.student_id}" #_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "⬇ Download TXT",
            data=result_to_txt(result),
            file_name=f"{filename_base}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇ Download CSV",
            data=result_to_csv(result),
            file_name=f"{filename_base}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "⬇ Download JSON",
            data=result_to_json(result),
            file_name=f"{filename_base}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.divider()
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Start Another Survey", type="primary"):
            bank, _ = get_bank()
            st.session_state.screen = "info"
            st.session_state.answers = [None] * len(bank["questions"])
            st.session_state.result = None
            st.rerun()
    with col2:
        if st.button("Home"):
            st.session_state.screen = "home"
            st.rerun()

@st.cache_resource
def get_bank() -> tuple[Dict[str, Any], bool]:
        base_dir: Path = Path(__file__).resolve().parent
        json_path: Path = base_dir / "survey_questions.json"

        if json_path.exists():
            return load_question_bank(json_path), False
        else:
            return load_fallback_question_bank(), True

def main() -> None:
    st.set_page_config(page_title="Survey App", layout="centered")
    try:
        bank, using_fallback = get_bank()
    except (ValueError, json.JSONDecodeError) as exc:
        st.error(f"**Could not load question bank:** {exc}")
        st.stop()

    if using_fallback:
        st.info(
            "\u2139\ufe0f **Using built-in fallback survey** \u2014 "
            "`survey_questions.json` was not found in the app directory. "
            "Place your JSON file next to `survey_app.py` to load your own survey."
        )

    init_state(bank)

    screen = st.session_state.screen
    if screen == "home":
        render_home(bank)
    elif screen == "info":
        render_info()
    elif screen == "question":
        render_question(bank)
    elif screen == "result":
        render_result()


if __name__ == "__main__":
    main()
