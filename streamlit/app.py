# app.py

import streamlit as st
from mock_scorer import score_essay
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# ---------- Настройка страницы ----------
st.set_page_config(
    page_title="Essay Checker",
    page_icon="📝",
    layout="wide"
)

# ---------- Session State ----------
if "history" not in st.session_state:
    st.session_state.history = []

if "selected_check" not in st.session_state:
    st.session_state.selected_check = None

if "current_essay_index" not in st.session_state:
    st.session_state.current_essay_index = None

# ---------- Функция анализа слов ----------
def analyze_word_count(word_count):

    if word_count < 250:
        return (
            "❌ Слишком мало слов",
            "IELTS Task 2 требует минимум 250 слов."
        )

    elif 250 <= word_count <= 320:
        return (
            "✅ Оптимальный объём",
            "Очень хороший диапазон для IELTS Writing Task 2."
        )

    elif 321 <= word_count <= 380:
        return (
            "⚠️ Немного длинное",
            "Допустимо, но может снижать качество из-за ошибок."
        )

    else:
        return (
            "❌ Слишком длинное эссе",
            "Слишком длинные эссе часто содержат больше ошибок."
        )


# ---------- Генерация PDF ----------
def generate_pdf(item):

    # ---------- Перевод статусов ----------
    status_translations = {
        "❌ Слишком мало слов": "Too few words",
        "✅ Оптимальный объём": "Optimal length",
        "⚠️ Немного длинное": "Slightly long",
        "❌ Слишком длинное эссе": "Too long essay"
    }

    comment_translations = {
        "IELTS Task 2 требует минимум 250 слов.":
            "IELTS Task 2 requires at least 250 words.",

        "Очень хороший диапазон для IELTS Writing Task 2.":
            "Very good range for IELTS Writing Task 2.",

        "Допустимо, но может снижать качество из-за ошибок.":
            "Acceptable, but may reduce quality because of mistakes.",

        "Слишком длинные эссе часто содержат больше ошибок.":
            "Very long essays often contain more mistakes."
    }

    # ---------- Английские версии ----------
    word_status_en = status_translations.get(
        item["word_status"],
        item["word_status"]
    )

    word_comment_en = comment_translations.get(
        item["word_comment"],
        item["word_comment"]
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    result = item["result"]
    scores = result["scores"]

    # ---------- Заголовок ----------
    elements.append(
        Paragraph(
            "IELTS Essay Report",
            styles['Title']
        )
    )

    elements.append(Spacer(1, 12))

    # ---------- Task ----------
    elements.append(
        Paragraph(
            f"<b>Task:</b><br/>{item['task']}",
            styles['BodyText']
        )
    )

    elements.append(Spacer(1, 12))

    # ---------- Essay ----------
    elements.append(
        Paragraph(
            f"<b>Essay:</b><br/>{item['essay']}",
            styles['BodyText']
        )
    )

    elements.append(Spacer(1, 12))

    # ---------- Word Count ----------
    elements.append(
        Paragraph(
            (
                f"<b>Word Count:</b> "
                f"{item['word_count']}<br/>"
                f"{word_status_en}<br/>"
                f"{word_comment_en}"
            ),
            styles['BodyText']
        )
    )

    elements.append(Spacer(1, 12))

    # ---------- Overall ----------
    elements.append(
        Paragraph(
            (
                f"<b>Overall Band:</b> "
                f"{scores['total']}"
            ),
            styles['Heading2']
        )
    )

    elements.append(Spacer(1, 12))

    # ---------- Scores ----------
    criteria = [
        ("TR", "Task Response"),
        ("CC", "Coherence & Cohesion"),
        ("LR", "Lexical Resource"),
        ("GRA", "Grammar & Accuracy")
    ]

    for key, name in criteria:

        elements.append(
            Paragraph(
                (
                    f"<b>{name}</b><br/>"
                    f"Score: {scores[key]['score']}<br/>"
                    f"Comment: {scores[key]['comment']}"
                ),
                styles['BodyText']
            )
        )

        elements.append(Spacer(1, 10))

    # ---------- Feedback ----------
    elements.append(
        Paragraph(
            (
                f"<b>Overall Feedback</b><br/>"
                f"{result['overall_feedback']}"
            ),
            styles['BodyText']
        )
    )

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return pdf


# ---------- Sidebar ----------
with st.sidebar:

    st.header("История проверок")

    # ---------- Новое эссе ----------
    if st.button("➕ Новое эссе"):

        st.session_state.current_essay_index = None
        st.session_state.selected_check = None

        st.rerun()

    st.divider()

    # ---------- История ----------
    if not st.session_state.history:
        st.write("Пока ничего не проверено.")

    else:
        for idx, item in enumerate(st.session_state.history):

            button_text = (
                f"Band {item['result']['scores']['total']} | "
                f"{item['word_count']} words"
            )

            if st.button(button_text, key=f"history_{idx}"):

                st.session_state.selected_check = idx
                st.session_state.current_essay_index = idx

                st.rerun()

            st.caption(item["task"])

        st.divider()

        # ---------- Очистить историю ----------
        if st.button("Очистить историю"):

            st.session_state.history = []
            st.session_state.selected_check = None
            st.session_state.current_essay_index = None

            st.rerun()

# ---------- Заголовок ----------
st.title("📝 IELTS Essay Checker")
st.caption("Автоматическая проверка эссе по 4 критериям IELTS Writing Task 2")

# ---------- Значения формы ----------
default_task = ""
default_essay = ""

if st.session_state.current_essay_index is not None:

    current_item = st.session_state.history[
        st.session_state.current_essay_index
    ]

    default_task = current_item["task"]
    default_essay = current_item["essay"]

# ---------- Форма ----------
with st.form("essay_form"):

    task = st.text_area(
        "Task (задание)",
        value=default_task,
        height=120,
        placeholder="Some people believe that... Discuss both views and give your opinion."
    )

    essay = st.text_area(
        "Essay (текст эссе)",
        value=default_essay,
        height=300,
        placeholder="Введите эссе студента сюда..."
    )

    # ---------- Кнопки ----------
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        show_words = st.form_submit_button("Посмотреть количество слов")

    with col_btn2:
        submitted = st.form_submit_button(
            "Проверить",
            type="primary"
        )

# ---------- Просмотр количества слов ----------
if show_words:

    live_word_count = len(essay.split())

    st.subheader("Количество слов")

    progress = min(live_word_count / 250, 1.0)

    st.progress(progress)

    word_status, word_comment = analyze_word_count(
        live_word_count
    )

    if "✅" in word_status:
        st.success(f"{word_status} ({live_word_count} слов)")

    elif "⚠️" in word_status:
        st.warning(f"{word_status} ({live_word_count} слов)")

    else:
        st.error(f"{word_status} ({live_word_count} слов)")

    st.caption(word_comment)

# ---------- Проверка эссе ----------
if submitted:

    if not task.strip() or not essay.strip():

        st.warning("Заполните оба поля.")

    else:

        with st.spinner("Модель оценивает эссе..."):

            result = score_essay(task, essay)

        if result["status"] == "error":

            st.error(f"Ошибка: {result['error']}")

        else:

            # ---------- Количество слов ----------
            word_count = len(essay.split())

            word_status, word_comment = analyze_word_count(
                word_count
            )

            # ---------- Данные вкладки ----------
            history_item = {
                "task": (
                    task[:80] + "..."
                    if len(task) > 80
                    else task
                ),
                "essay": essay,
                "result": result,
                "word_count": word_count,
                "word_status": word_status,
                "word_comment": word_comment
            }

            # ---------- Обновление текущей вкладки ----------
            if st.session_state.current_essay_index is not None:

                st.session_state.history[
                    st.session_state.current_essay_index
                ] = history_item

                st.session_state.selected_check = (
                    st.session_state.current_essay_index
                )

            # ---------- Создание новой ----------
            else:

                st.session_state.history.append(history_item)

                new_index = len(st.session_state.history) - 1

                st.session_state.selected_check = new_index
                st.session_state.current_essay_index = new_index

            st.rerun()

# ---------- Отображение результатов ----------
selected_idx = st.session_state.selected_check

if selected_idx is not None:

    item = st.session_state.history[selected_idx]

    result = item["result"]
    scores = result["scores"]

    # ---------- Общая оценка ----------
    st.subheader("Результат")

    st.metric(
        "Overall Band Score",
        scores["total"]
    )

    # ---------- Предупреждение ----------
    st.info(
        "Результаты проверки не сохраняются после закрытия страницы. "
        "Вы можете скачать отчёт проверки."
    )

    # ---------- PDF ----------
    pdf_data = generate_pdf(item)

    st.download_button(
        label="📄 Сохранить результаты проверки",
        data=pdf_data,
        file_name="ielts_essay_report.pdf",
        mime="application/pdf"
    )

    # ---------- Информация о словах ----------
    st.subheader("Количество слов")

    progress = min(item["word_count"] / 250, 1.0)

    st.progress(progress)

    if "✅" in item["word_status"]:
        st.success(
            f"{item['word_status']} "
            f"({item['word_count']} слов)"
        )

    elif "⚠️" in item["word_status"]:
        st.warning(
            f"{item['word_status']} "
            f"({item['word_count']} слов)"
        )

    else:
        st.error(
            f"{item['word_status']} "
            f"({item['word_count']} слов)"
        )

    st.caption(item["word_comment"])

    # ---------- Критерии ----------
    col1, col2, col3, col4 = st.columns(4)

    criteria = [
        ("TR", "Task Response", col1),
        ("CC", "Coherence & Cohesion", col2),
        ("LR", "Lexical Resource", col3),
        ("GRA", "Grammar & Accuracy", col4),
    ]

    for key, full_name, col in criteria:

        with col:

            st.metric(
                full_name,
                scores[key]["score"]
            )

            st.caption(
                scores[key]["comment"]
            )

    # ---------- Общий фидбек ----------
    st.subheader("Общий фидбек")

    st.markdown(
        result["overall_feedback"]
    )

    # ---------- Текст эссе ----------
    with st.expander("Показать текст эссе"):

        st.write(item["essay"])