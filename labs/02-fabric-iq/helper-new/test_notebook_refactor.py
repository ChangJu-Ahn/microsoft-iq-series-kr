"""외부 서비스 없이 현재 노트북과 보관본의 요청·생성 결과를 비교합니다."""

import copy
from dataclasses import asdict
import datetime as dt
import io
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch
import urllib.error


LAB = Path(__file__).resolve().parent


def load_cells(path, indices, name):
    module = ModuleType(name)
    module.MES_BASE_URL = "https://example.test"
    sys.modules[name] = module
    cells = json.loads(path.read_text())["cells"]
    for index in indices:
        exec(compile("".join(cells[index]["source"]), f"{path.name}:{index}", "exec"),
             module.__dict__)
    return module


def mes_fixture(module):
    """테스트 전용 입력이며 워크숍 데이터나 API 응답을 대체하지 않습니다."""
    product = next(iter(module.PRODUCT_CD_SCALE))
    steps = list(module.STEP_CHARACTERISTICS)
    route = [{"step_code": step, "step_name": step, "seq": i + 1,
              "eqp_type": "Polisher" if step == "CMP" else "CVD"}
             for i, step in enumerate(steps)]
    lots = [{"lot_id": f"TEST-LOT-{i}", "product_code": product,
             "product_name": product, "status": "Done" if i < 2 else "Running",
             "current_step": steps[-1], "wafer_qty": 25} for i in range(4)]
    start = dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
    results = []
    for i in range(40):
        step = steps[i % len(steps)]
        results.append({
            "id": i + 1, "lot_id": lots[i % len(lots)]["lot_id"],
            "step_code": step, "step_name": step, "eqp_id": f"TEST-{step}",
            "in_time": (start + dt.timedelta(minutes=10 * i)).isoformat(),
            "out_time": (start + dt.timedelta(minutes=10 * i + 5)).isoformat(),
            "result": "Fail" if i < 3 else "Rework" if i < 5 else "Pass",
            "defect_code": "Scratch" if i < 20 else None,
            "in_qty": 25, "out_qty": 23, "scrap_qty": 2,
        })
    return {
        "products": [{"product_code": code, "product_name": code}
                     for code in module.PRODUCT_CD_SCALE],
        "materials": [{"material_code": "TEST-MATERIAL", "material_name": "Test",
                       "category": "Raw Wafer", "uom": "EA"}],
        "bom": [{"product_code": product, "step_code": step,
                 "material_code": "TEST-MATERIAL"} for step in steps],
        "lots": lots, "process_results": results, "route": route,
        "equipment": module.derive_equipment(results, route),
    }


class MesTransport:
    def __init__(self, snapshot, failure=None, sse=False):
        self.snapshot = snapshot
        self.failure = failure
        self.sse = sse
        self.calls = []
        self.responses = []

    def open(self, request, timeout):
        body = json.loads(request.data) if request.data else None
        self.calls.append((request.full_url, request.method, dict(request.headers), body, timeout))
        if body is None:
            key = request.full_url.rsplit("/", 1)[-1]
            result = self.snapshot[key]
        elif body["method"] == "notifications/initialized":
            result = None
        elif body["method"] == "initialize":
            result = {"jsonrpc": "2.0", "id": body["id"], "result": {}}
        else:
            key = {"list_process_results": "process_results", "get_process_route": "route",
                   "list_lots": "lots"}[body["params"]["name"]]
            result = {"jsonrpc": "2.0", "id": body["id"], "result": {
                "structuredContent": {"result": self.snapshot[key]},
            }}
            if self.failure == "empty":
                result = None
            elif self.failure == "rpc":
                result = {"jsonrpc": "2.0", "id": body["id"], "error": {"code": -1}}
            elif self.failure == "missing":
                result = {"jsonrpc": "2.0", "id": body["id"]}
            elif self.failure == "tool":
                result["result"] = {"isError": True, "content": []}
            elif self.failure == "shape":
                result["result"] = {"structuredContent": {}}
            elif self.failure == "id":
                result["id"] = 999
            elif self.failure == "drift" and body["id"] > 4:
                result["result"]["structuredContent"]["result"] = copy.deepcopy(self.snapshot[key])
                if key == "lots":
                    result["result"]["structuredContent"]["result"][0]["product_code"] = "CHANGED"
        text = "" if result is None else json.dumps(result)
        if self.sse and text and body is not None:
            text = f"event: message\ndata: {text}\n\n"
        response = io.BytesIO(text.encode())
        self.responses.append(response)
        return response


class NotebookRefactorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qms = load_cells(LAB / "01_factory_lakehouse.ipynb", range(2, 14), "current_qms")
        cls.old_qms = load_cells(
            LAB.parent / "helper-old/1.qms-lakehouse/qms_lakehouse_seed.ipynb",
            range(2, 11), "archived_qms",
        )
        cls.fdc = load_cells(LAB / "02_fdc_eventhouse.ipynb", range(2, 9), "current_fdc")
        cls.old_fdc = load_cells(
            LAB.parent / "helper-old/2.fdc-eventhouse/fdc_eventhouse_stream.ipynb",
            range(2, 9), "archived_fdc",
        )
        cls.snapshot = mes_fixture(cls.old_qms)

    def invoke(self, function, transport):
        with patch("urllib.request.urlopen", transport.open):
            try:
                return function()
            finally:
                self.assertTrue(all(response.closed for response in transport.responses))

    def test_qms_snapshot_requests_and_result_match_archive(self):
        for sse in (False, True):
            with self.subTest(sse=sse):
                old = MesTransport(self.snapshot, sse=sse)
                new = MesTransport(self.snapshot, sse=sse)
                expected = self.invoke(lambda: self.old_qms.MesClient(
                    "https://example.test/", "test-key").fetch_snapshot(), old)
                actual = self.invoke(lambda: self.qms.fetch_mes_snapshot(
                    "https://example.test/", "test-key"), new)
                self.assertEqual(asdict(actual), asdict(expected))
                self.assertEqual(new.calls, old.calls)

    def test_fdc_facts_requests_and_result_match_archive(self):
        for sse in (False, True):
            with self.subTest(sse=sse):
                old = MesTransport(self.snapshot, sse=sse)
                new = MesTransport(self.snapshot, sse=sse)
                expected = self.invoke(lambda: self.old_fdc.MesProbe(
                    "https://example.test/", "test-key").fetch_facts(), old)
                actual = self.invoke(lambda: self.fdc.fetch_mes_facts(
                    "https://example.test/", "test-key"), new)
                self.assertEqual(asdict(actual), asdict(expected))
                self.assertEqual(new.calls, old.calls)

    def test_mcp_failure_messages_and_requests_match_archive(self):
        for current, archived, fetch, client, method in [
            (self.qms, self.old_qms, "fetch_mes_snapshot", "MesClient", "fetch_snapshot"),
            (self.fdc, self.old_fdc, "fetch_mes_facts", "MesProbe", "fetch_facts"),
        ]:
            for failure in ("empty", "rpc", "missing", "tool", "shape"):
                with self.subTest(fetch=fetch, failure=failure):
                    old, new = MesTransport(self.snapshot, failure), MesTransport(self.snapshot, failure)
                    with self.assertRaises(RuntimeError) as expected:
                        self.invoke(lambda: getattr(getattr(archived, client)(
                            "https://example.test", "test-key"), method)(), old)
                    with self.assertRaises(RuntimeError) as actual:
                        self.invoke(lambda: getattr(current, fetch)(
                            "https://example.test", "test-key"), new)
                    self.assertEqual(str(actual.exception), str(expected.exception))
                    self.assertEqual(new.calls, old.calls)

    def test_qms_all_generated_rows_and_schema_match_archive(self):
        expected = self.old_qms.build_all_tables(self.old_qms.MesSnapshot(**self.snapshot))
        actual = self.qms.build_all_tables(self.qms.MesSnapshot(**self.snapshot))
        self.assertEqual(actual, expected)
        self.assertEqual(self.qms.TABLE_DDL, self.old_qms.TABLE_DDL)
        for name in expected:
            self.assertEqual(self.qms.to_rows(name, actual[name]),
                             self.old_qms.to_rows(name, expected[name]))
        self.assertEqual(
            self.qms.format_report(self.qms.validate(self.qms.MesSnapshot(**self.snapshot), actual)),
            self.old_qms.format_report(self.old_qms.validate(
                self.old_qms.MesSnapshot(**self.snapshot), expected)),
        )

    def test_fdc_readings_and_schema_match_archive(self):
        facts = {"process_results": self.snapshot["process_results"], "route": self.snapshot["route"]}
        start = dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc)
        end = start + dt.timedelta(hours=7)
        expected = self.old_fdc.build_readings(self.old_fdc.MesFacts(**facts), start, end)
        actual = self.fdc.build_readings(self.fdc.MesFacts(**facts), start, end)
        self.assertEqual(actual, expected)
        self.assertEqual(self.fdc.TABLE_DDL, self.old_fdc.TABLE_DDL)
        self.assertEqual(self.fdc.build_sensor_spec_rows(), self.old_fdc.build_sensor_spec_rows())

    def test_context_checks_two_snapshots(self):
        transport = MesTransport(self.snapshot, sse=True)
        actual = self.invoke(lambda: self.qms.fetch_mes_context(
            "https://example.test", "test-key"), transport)
        self.assertEqual(actual, self.qms.project_snapshot(self.snapshot))
        bodies = [call[3] for call in transport.calls]
        self.assertEqual([body.get("id") for body in bodies], [1, None, 2, 3, 4, 5, 6, 7])
        self.assertEqual([body["params"]["name"] for body in bodies[2:]],
                         ["list_process_results", "list_lots", "get_process_route"] * 2)

    def test_context_rejects_untrusted_url_mismatched_response_and_drift(self):
        for url in ("http://example.test", "https://user:pass@example.test", "https://example.test?q=1"):
            with self.subTest(url=url):
                with patch("urllib.request.urlopen") as open_url:
                    with self.assertRaises(self.qms.MesContextError):
                        self.qms.fetch_mes_context(url, "test-key")
                    open_url.assert_not_called()
        for failure, message in [("id", "request ID"), ("drift", "changed during extraction")]:
            with self.subTest(failure=failure):
                with self.assertRaisesRegex(self.qms.MesContextError, message):
                    self.invoke(lambda: self.qms.fetch_mes_context(
                        "https://example.test", "test-key"), MesTransport(self.snapshot, failure))

    def test_context_refuses_truncated_result(self):
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["process_results"] = [snapshot["process_results"][0]] * 500
        with self.assertRaisesRegex(self.qms.MesContextError, "500-row limit"):
            self.invoke(lambda: self.qms.fetch_mes_context(
                "https://example.test", "test-key"), MesTransport(snapshot))

    def test_fetch_failures_clear_local_key(self):
        for module, name in [(self.qms, "fetch_mes_snapshot"),
                             (self.qms, "fetch_mes_context"),
                             (self.fdc, "fetch_mes_facts")]:
            with self.subTest(fetch=name):
                try:
                    self.invoke(lambda: getattr(module, name)(
                        "https://example.test", "test-key"), MesTransport(self.snapshot, "tool"))
                except RuntimeError as error:
                    traceback = error.__traceback__
                    checked = False
                    while traceback:
                        if traceback.tb_frame.f_code.co_name == name:
                            self.assertEqual(traceback.tb_frame.f_locals["api_key"], "")
                            checked = True
                        traceback = traceback.tb_next
                    self.assertTrue(checked)
                else:
                    self.fail("MCP tool failure must stop the fetch.")

    def test_context_http_error_closes_response_and_does_not_retry(self):
        response = io.BytesIO(b"forbidden")
        error = urllib.error.HTTPError("https://example.test/mcp", 403, "Forbidden", {}, response)
        with patch("urllib.request.urlopen", side_effect=error) as open_url:
            with self.assertRaisesRegex(self.qms.MesContextError, "HTTP 403"):
                self.qms.fetch_mes_context("https://example.test", "test-key")
            open_url.assert_called_once()
        self.assertTrue(response.closed)

    def test_context_transport_error_does_not_retry_or_return_data(self):
        for error in (urllib.error.URLError("offline"), TimeoutError("slow")):
            with self.subTest(error=type(error).__name__):
                with patch("urllib.request.urlopen", side_effect=error) as open_url:
                    with self.assertRaisesRegex(self.qms.MesContextError, "No fallback data"):
                        self.qms.fetch_mes_context("https://example.test", "test-key")
                    open_url.assert_called_once()


if __name__ == "__main__":
    unittest.main()
