"""공개 시나리오 문서와 배포에 포함할 기존 도식의 위치입니다."""

import os
from pathlib import Path

SOURCE_DIR = (Path(__file__).resolve().parent / "../../00-getting-started").resolve()
DIAGRAMS = ("customer-problem.svg", "problem-solving-workshop.svg")


def content_directory() -> Path:
    return Path(os.getenv("SCENARIO_CONTENT_DIR", str(SOURCE_DIR))).resolve()
