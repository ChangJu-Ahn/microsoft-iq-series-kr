"""노트북 코드를 실행하지 않고 실제 retrieve 호출의 질문만 읽습니다."""

import ast
import json
import os
from pathlib import Path

NOTEBOOK = (Path(__file__).resolve().parent / "../../05-foundry-iq/kb_retrieve_test.ipynb").resolve()


def load_questions(path: Path = NOTEBOOK) -> list[dict[str, str]]:
    if path == NOTEBOOK and os.getenv("QUESTION_SET_PATH"):
        questions = json.loads(Path(os.environ["QUESTION_SET_PATH"]).read_text(encoding="utf-8"))
        if not isinstance(questions, list) or not questions or any(
            not isinstance(item, dict) or set(item) != {"kb", "question"}
            or item["kb"] not in ("process", "quality")
            or not isinstance(item["question"], str) or not item["question"].strip()
            for item in questions
        ):
            raise ValueError("패키징된 노트북 질문 파일이 올바르지 않습니다.")
        return questions
    values: dict[str, str] = {}
    questions = []
    for cell in json.loads(path.read_text(encoding="utf-8"))["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if source.lstrip().startswith("%"):
            continue
        for node in ast.parse(source).body:
            if not isinstance(node, ast.Assign):
                continue
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        values[target.id] = node.value.value
            call = node.value
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "retrieve_v2_trace"):
                continue
            kb = {"PROCESS_KB_NAME": "process", "QUALITY_KB_NAME": "quality"}[call.args[0].id]
            question = values[call.args[1].id]
            questions.append({"kb": kb, "question": question})
    if not questions:
        raise ValueError("노트북에서 retrieve_v2_trace 질문을 찾지 못했습니다.")
    return questions
