# app.py
import streamlit as st
from mock_scorer import score_essay   # потом заменим на: from scorer import score_essay
# расскомментить когда будет scorer а не mock_scorer !!!!!!

# @st.cache_resource
# def get_scorer():
#     from scorer import score_essay
#     return score_essay

# ---------- Настройка страницы ----------
st.set_page_config(
    page_title="write&check",
    page_icon="🎓",
    layout="wide"
)

# ---------- Инициализация истории ----------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Заголовок ----------
st.title("🎓 Проверь свое IELTS эссе")
st.caption("Автоматическая проверка эссе по 4 критериям IELTS Writing Task 2")

# ---------- Форма ввода ----------
with st.form("essay_form"):
    task = st.text_area(
        "Task (задание)",
        height=120,
        placeholder="Some people believe that... Discuss both views and give your opinion."
    )
    essay = st.text_area(
        "Essay (текст эссе)",
        height=300,
        placeholder="Введите эссе студента сюда..."
    )
    submitted = st.form_submit_button("Проверить", type="primary")

# ---------- Обработка ----------
if submitted:
    if not task.strip() or not essay.strip():
        st.warning("Заполните оба поля.")
    else:
        with st.spinner("Модель оценивает эссе..."):
            result = score_essay(task, essay)

        if result["status"] == "error":
            st.error(f"Ошибка: {result['error']}")
        else:
            # Сохраняем в историю
            st.session_state.history.append({
                "task": task[:80] + "..." if len(task) > 80 else task,
                "result": result
            })

            scores = result["scores"]

            # ---------- Общая оценка ----------
            st.subheader("Результат по критериям")
            st.metric("Overall Band Score", scores["total"])

            # ---------- 4 критерия в колонках ----------
            col1, col2, col3, col4 = st.columns(4)
            criteria = [
                ("TR",  "Task Response",          col1),
                ("CC",  "Coherence & Cohesion",   col2),
                ("LR",  "Lexical Resource",       col3),
                ("GRA", "Grammar & Accuracy",     col4),
            ]
            for key, full_name, col in criteria:
                with col:
                    st.metric(full_name, scores[key]["score"])
                    st.caption(scores[key]["comment"])

            # ---------- Общий фидбек ----------
            st.subheader("Общий фидбек")
            st.markdown(result["overall_feedback"])

# ---------- Сайдбар с историей ----------
with st.sidebar:
    st.header("История проверок")
    if not st.session_state.history:
        st.write("Пока ничего не проверено.")
    else:
        for i, item in enumerate(reversed(st.session_state.history), 1):
            st.markdown(
                f"{i}. Band: {item['result']['scores']['total']}  \n"
                f"_{item['task']}_"
            )
        if st.button("Очистить историю"):
            st.session_state.history = []
            st.rerun()