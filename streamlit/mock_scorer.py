import random
import time


def score_essay(task: str, essay: str) -> dict:
    """
    Заглушка для разработки UI.
    Возвращает фейковые оценки в том же формате, что и реальная модель.
    """
    # Имитируем время инференса
    time.sleep(1.5)

    # Защита от пустого ввода
    if not task.strip() or not essay.strip():
        return {
            "status": "error",
            "scores": None,
            "overall_feedback": None,
            "error": "Task и Essay не должны быть пустыми."
        }

    # Генерируем правдоподобные оценки
    tr = random.randint(5, 8)
    cc = random.randint(5, 8)
    lr = random.randint(5, 8)
    gra = random.randint(5, 8)
    total = round((tr + cc + lr + gra) / 4, 1)

    return {
        "status": "ok",
        "scores": {
            "TR":  {"score": tr,  "comment": "The essay addresses the task but lacks depth in some arguments."},
            "CC":  {"score": cc,  "comment": "Ideas are logically organized, though transitions could be smoother."},
            "LR":  {"score": lr,  "comment": "Good range of vocabulary with occasional inaccuracies."},
            "GRA": {"score": gra, "comment": "Mix of simple and complex structures; minor grammatical errors."},
            "total": total
        },
        "overall_feedback": (
            "Overall, this is a competent response that demonstrates a good grasp of the topic. "
            "To improve, focus on developing arguments more fully and using a wider range of cohesive devices. "
            "Pay attention to article usage and subject-verb agreement."
        ),
        "error": None
    }