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
  "description": "This questionnaire measures how regularly a person conducts weekly planning sessions and how successfully they achieve the goals set during those sessions.",
  "questions": [
    {
      "id": 1,
      "text": "How often do you hold a dedicated weekly planning session?",
      "options": [
        { "label": "Every week without exception", "score": 0 },
        { "label": "Most weeks (3 out of 4)", "score": 1 },
        { "label": "Occasionally (1–2 times per month)", "score": 2 },
        { "label": "Rarely (a few times per year)", "score": 3 },
        { "label": "Never", "score": 4 }
      ]
    },
    {
      "id": 2,
      "text": "What proportion of the goals you set at the start of a week do you typically complete by the end of it?",
      "options": [
        { "label": "Nearly all of them (90% or more)", "score": 0 },
        { "label": "Most of them (around 70–89%)", "score": 1 },
        { "label": "About half (50–69%)", "score": 2 },
        { "label": "Fewer than half (below 50%)", "score": 3 },
        { "label": "Rarely any (less than 20%)", "score": 4 }
      ]
    },
    {
      "id": 3,
      "text": "How long is your typical weekly planning session?",
      "options": [
        { "label": "More than 30 minutes with structured thinking", "score": 0 },
        { "label": "Around 15–30 minutes", "score": 1 },
        { "label": "Under 10 minutes, mostly informal", "score": 2 },
        { "label": "I do not set aside dedicated planning time", "score": 3 }
      ]
    },
    {
      "id": 4,
      "text": "How do you document the goals you plan to achieve each week?",
      "options": [
        { "label": "I write them in a dedicated planner or digital tool every week", "score": 0 },
        { "label": "I write them down most weeks", "score": 1 },
        { "label": "I occasionally write them down but not consistently", "score": 2 },
        { "label": "I do not record goals — I rely on memory or set none", "score": 3 }
      ]
    },
    {
      "id": 5,
      "text": "How clearly do you define each goal at the start of the week?",
      "options": [
        { "label": "Always clearly, with specific steps and a target date", "score": 0 },
        { "label": "Mostly clear, though some details are missing", "score": 1 },
        { "label": "Usually vague — I know the goal but not the steps", "score": 2 },
        { "label": "I do not define goals in advance", "score": 3 }
      ]
    },
    {
      "id": 6,
      "text": "How consistently do you conduct an end-of-week review to assess which goals were achieved?",
      "options": [
        { "label": "Every week as a fixed habit", "score": 0 },
        { "label": "Most weeks", "score": 1 },
        { "label": "Occasionally", "score": 2 },
        { "label": "Rarely", "score": 3 },
        { "label": "Never", "score": 4 }
      ]
    },
    {
      "id": 7,
      "text": "How well do you prioritise your weekly goals by importance and urgency?",
      "options": [
        { "label": "Very well — I always rank tasks before starting the week", "score": 0 },
        { "label": "Fairly well — I prioritise most of the time", "score": 1 },
        { "label": "Inconsistently — I sometimes treat all tasks as equally important", "score": 2 },
        { "label": "I do not prioritise at all", "score": 3 }
      ]
    },
    {
      "id": 8,
      "text": "How realistic are the goals you typically set for a single week?",
      "options": [
        { "label": "Always realistic — I consistently achieve what I plan", "score": 0 },
        { "label": "Mostly realistic — I occasionally overestimate", "score": 1 },
        { "label": "Sometimes unrealistic — goals frequently carry over", "score": 2 },
        { "label": "Usually too ambitious — most goals carry over to the next week", "score": 3 },
        { "label": "Always unrealistic — I rarely complete what I planned", "score": 4 }
      ]
    },
    {
      "id": 9,
      "text": "When you do not achieve a planned weekly goal, how do you typically respond?",
      "options": [
        { "label": "I analyse what went wrong and adjust my approach for next week", "score": 0 },
        { "label": "I reschedule the goal with a revised plan", "score": 1 },
        { "label": "I carry it over without making any changes", "score": 2 },
        { "label": "I tend to drop the goal entirely", "score": 3 }
      ]
    },
    {
      "id": 10,
      "text": "How often do you break large weekly goals into smaller, actionable steps during planning?",
      "options": [
        { "label": "Always — I map out sub-tasks for every major goal", "score": 0 },
        { "label": "Often — for most goals", "score": 1 },
        { "label": "Rarely — only for very complex goals", "score": 2 },
        { "label": "Never", "score": 3 }
      ]
    },
    {
      "id": 11,
      "text": "How often do unexpected events completely derail your weekly plan?",
      "options": [
        { "label": "Rarely — I build buffer time and adapt well", "score": 0 },
        { "label": "Occasionally — perhaps once or twice a month", "score": 1 },
        { "label": "Very often — almost every week", "score": 2 }
      ]
    },
    {
      "id": 12,
      "text": "How consistent has your weekly planning habit been over the past three months?",
      "options": [
        { "label": "Very consistent — I planned every single week", "score": 0 },
        { "label": "Mostly consistent — I missed only a few weeks", "score": 1 },
        { "label": "Inconsistent — I planned roughly half the weeks or fewer", "score": 2 },
        { "label": "I have not held a single planning session in the past three months", "score": 3 }
      ]
    },
    {
      "id": 13,
      "text": "How confident do you feel at the start of each week that you will achieve your planned goals?",
      "options": [
        { "label": "Very confident — I trust my planning process", "score": 0 },
        { "label": "Moderately confident", "score": 1 },
        { "label": "Mostly doubtful", "score": 2 },
        { "label": "Not confident at all", "score": 3 }
      ]
    },
    {
      "id": 14,
      "text": "How often do you connect your weekly goals to longer-term personal or professional objectives?",
      "options": [
        { "label": "Always — each weekly goal links to a broader plan", "score": 0 },
        { "label": "Sometimes", "score": 1 },
        { "label": "Never — my weekly goals are set independently of any longer plan", "score": 2 }
      ]
    },
    {
      "id": 15,
      "text": "How often do you postpone a planned weekly task even after scheduling it?",
      "options": [
        { "label": "Almost never — I follow through on scheduled tasks", "score": 0 },
        { "label": "Occasionally", "score": 1 },
        { "label": "About half the time", "score": 2 },
        { "label": "Often", "score": 3 },
        { "label": "Almost always — tasks routinely carry over to the next week", "score": 4 }
      ]
    },
    {
      "id": 16,
      "text": "How promptly do you revise your weekly plan when circumstances change?",
      "options": [
        { "label": "Immediately — I update the plan the same day", "score": 0 },
        { "label": "Usually within a day or two", "score": 1 },
        { "label": "Rarely — I usually continue with the original plan even if it no longer fits", "score": 2 },
        { "label": "I never adjust — I either complete the goals or abandon them", "score": 3 }
      ]
    },
    {
      "id": 17,
      "text": "How often do you reflect on what made your successfully completed goals achievable?",
      "options": [
        { "label": "Regularly — I identify what worked and build on it", "score": 0 },
        { "label": "Occasionally", "score": 1 },
        { "label": "Never — I move on without reflection", "score": 2 }
      ]
    },
    {
      "id": 18,
      "text": "How effectively does the tool or system you use support your weekly planning?",
      "options": [
        { "label": "Very effectively — it is structured, reliable, and easy to follow", "score": 0 },
        { "label": "Somewhat — it works but is often inconsistently used", "score": 1 },
        { "label": "I use no planning tool or system at all", "score": 2 }
      ]
    },
    {
      "id": 19,
      "text": "How often do you begin each week knowing clearly which goal is the single highest priority?",
      "options": [
        { "label": "Always — I identify my top priority during planning", "score": 0 },
        { "label": "Usually", "score": 1 },
        { "label": "Sometimes", "score": 2 },
        { "label": "Never — I start the week without a clear priority", "score": 3 }
      ]
    },
    {
      "id": 20,
      "text": "Overall, how satisfied are you with your personal rate of weekly goal achievement?",
      "options": [
        { "label": "Satisfied — I consistently achieve what I plan", "score": 0 },
        { "label": "Somewhat satisfied — achievement is hit or miss", "score": 1 },
        { "label": "Dissatisfied — I rarely achieve what I set out to do", "score": 2 }
      ]
    }
  ],
  "states": [
    {
      "min_score": 0,
      "max_score": 10,
      "label": "Highly Effective Planner",
      "summary": "Excellent planning frequency with outstanding goal achievement.",
      "description": "Weekly sessions are held consistently, goals are clearly defined, and the vast majority are completed each week. No changes are needed; this level of self-regulation and commitment should be maintained and built upon."
    },
    {
      "min_score": 11,
      "max_score": 20,
      "label": "Effective Planner",
      "summary": "Good planning consistency and solid goal achievement rate.",
      "description": "Planning sessions occur regularly and most goals are completed on time. Minor refinements to prioritisation, goal clarity, or end-of-week review habits could push performance to the highest level."
    },
    {
      "min_score": 21,
      "max_score": 30,
      "label": "Moderate Planner",
      "summary": "Planning sessions occur but goal achievement is inconsistent.",
      "description": "Some weeks are productive while others fall short. Improving how goals are defined, breaking tasks into smaller steps, and conducting a brief weekly review would likely close the gap between planning and achievement."
    },
    {
      "min_score": 31,
      "max_score": 40,
      "label": "Inconsistent Planner",
      "summary": "Planning sessions are irregular and fewer than half of goals are typically achieved.",
      "description": "Goal achievement suffers primarily because planning is unpredictable. Committing to a fixed weekly planning time, reducing the number of goals set each week, and introducing a simple accountability method are strongly advisable."
    },
    {
      "min_score": 41,
      "max_score": 50,
      "label": "Low-Engagement Planner",
      "summary": "Planning rarely occurs and goal achievement is very low.",
      "description": "Without a reliable planning structure, most goals are left to chance. Establishing a simple, repeatable weekly routine, writing down at least one goal per week, and using a basic tracking tool would provide a meaningful starting point."
    },
    {
      "min_score": 51,
      "max_score": 60,
      "label": "Disengaged Planner",
      "summary": "There is no structured weekly planning and goals are almost never achieved.",
      "description": "Significant support around self-regulation, goal-setting fundamentals, and time management is strongly recommended. Beginning with one small, clearly defined goal per week and reviewing it at the end of the week can help build initial momentum."
    }
  ]
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
