from streamlit.testing.v1 import AppTest
from pathlib import Path

APP = str(Path(__file__).resolve().parents[1] / "app.py")

def test_all_phase3_pages_render_without_exception():
    pages = ["总览", "AI 智能采集", "候选人管理", "招聘流程看板", "提醒中心", "招聘分析", "数据管理"]
    for page in pages:
        app = AppTest.from_file(APP).run(timeout=30)
        app.sidebar.radio[0].set_value(page).run(timeout=30)
        assert not app.exception, page

def test_ai_intake_exposes_engine_entrypoint():
    app = AppTest.from_file(APP).run(timeout=30)
    app.sidebar.radio[0].set_value("AI 智能采集").run(timeout=30)
    assert any("AI 智能采集中心" in title.value for title in app.title)
    assert len(app.button) >= 2
