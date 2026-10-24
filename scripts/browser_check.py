"""Optional real-browser checks and PDF export with Firefox + geckodriver.

Uses the standard WebDriver HTTP protocol through Python's standard library;
no Selenium package, browser download, or website build is required.
"""
import argparse
import base64
import json
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main(export_pdf=False):
    if not shutil.which("geckodriver") or not shutil.which("firefox"):
        raise SystemExit("Optional browser check requires installed firefox and geckodriver")
    preview = ROOT / "docs/preview"
    preview.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "report")))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    driver_port = free_port()
    log = tempfile.TemporaryFile()
    process = subprocess.Popen(["geckodriver", "--host", "127.0.0.1", "--port", str(driver_port)], stdout=log, stderr=log)
    base = f"http://127.0.0.1:{driver_port}"
    session_id = None

    def call(method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(base + path, method=method, data=data, headers={"Content-Type": "application/json"})
        # Loopback QA must not be sent through an inherited proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=60) as response:
                return json.load(response)["value"]
        except urllib.error.HTTPError as exc:
            raise RuntimeError(exc.read().decode()) from exc

    def command(method, path, payload=None):
        return call(method, f"/session/{session_id}" + path, payload)

    def script(source):
        return command("POST", "/execute/sync", {"script": source, "args": []})

    def screenshot(name):
        (preview / name).write_bytes(base64.b64decode(command("GET", "/screenshot")))

    try:
        for _ in range(100):
            try:
                call("GET", "/status")
                break
            except (urllib.error.URLError, ConnectionError):
                time.sleep(.1)
        else:
            raise RuntimeError("geckodriver did not become ready")
        session = call("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "firefox", "webSocketUrl": True, "moz:firefoxOptions": {"args": ["-headless"]}}}})
        session_id = session["sessionId"]
        command("POST", "/timeouts", {"pageLoad": 30000, "script": 15000})
        local_url = f"http://127.0.0.1:{server.server_port}/"
        command("POST", "/window/rect", {"width": 1440, "height": 1000})
        command("POST", "/url", {"url": local_url})
        ready = script("return document.readyState === 'complete' && [...document.images].every(i => i.complete && i.naturalWidth > 0)")
        assert ready, "Some local figures failed to render"
        assert script("return document.querySelectorAll('.q-tables .q-table').length") == 4
        assert script("return [...document.querySelectorAll('.q-tables')].every(table => !table.closest('details'))"), "Required tables must remain visible without interaction"
        assert script("return !document.querySelector('.stat-strip') && document.querySelector('h1').textContent.includes('goal')"), "Opening must describe the problem without a statistics strip"
        assert script("return Boolean(document.querySelector('.hero-illustration img').naturalWidth)"), "Opening illustration failed to load"
        assert script("return document.getElementById('calc-value').textContent") == "0.234"
        result = script("document.getElementById('transition').value='terminal'; document.getElementById('transition').dispatchEvent(new Event('change',{bubbles:true})); return document.getElementById('calc-value').textContent")
        assert result == "0.280", result
        assert script("return document.getElementById('next-q').disabled")
        result = script("document.querySelector('.snapshot-details').open=true; document.getElementById('snapshot-case').value='modified'; document.getElementById('snapshot-case').dispatchEvent(new Event('change')); document.getElementById('snapshot-episode').value='20000'; document.getElementById('snapshot-episode').dispatchEvent(new Event('change')); return document.querySelector('#snapshot-table caption').textContent")
        assert "A → C" in result and "20000" in result
        assert script("return document.querySelectorAll('#snapshot-table tbody tr').length") == 6
        command("POST", "/url", {"url": local_url})
        screenshot("desktop.png")
        script("document.getElementById('case-original').scrollIntoView({behavior:'instant'})")
        screenshot("results-desktop.png")
        # Native window resize has a minimum width in Firefox. BiDi overrides the
        # actual CSS viewport, so a requested 390px test really tests 390px.
        viewport_input = {"webSocketUrl": session["capabilities"]["webSocketUrl"],
                          "webdriverBase": base, "sessionId": session_id,
                          "previewDirectory": str(preview)}
        completed = subprocess.run(["node", str(ROOT / "scripts/check_viewports.cjs")],
                                   input=json.dumps(viewport_input), text=True, capture_output=True, timeout=45)
        if completed.returncode:
            raise RuntimeError(completed.stderr)
        viewport_checks = json.loads(completed.stdout)
        # Snap Firefox cannot see /data/private. Test a byte-identical standalone
        # copy in its permitted directory instead; keep submitted files here.
        permitted = Path.home() / "snap/firefox/common"
        copy_parent = permitted if permitted.is_dir() else None
        with tempfile.TemporaryDirectory(prefix="iota-offline-", dir=copy_parent) as temporary:
            offline_report = Path(temporary) / "report"
            shutil.copytree(ROOT / "report", offline_report)
            command("POST", "/url", {"url": (offline_report / "index.html").as_uri()})
            offline_ok = script("return document.title.includes('Q-learning') && document.getElementById('calc-value').textContent==='0.234' && [...document.images].every(i=>i.complete && i.naturalWidth>0)")
            assert offline_ok, "Direct file opening failed"
        if export_pdf:
            command("POST", "/url", {"url": local_url})
            # Extensions and exact methodology are expandable on screen. Include
            # their full text and figures in the printable companion report.
            script("document.querySelectorAll('details').forEach(section=>section.open=true)")
            loaded = command("POST", "/execute/async", {"script": "const done=arguments[arguments.length-1];Promise.all([...document.images].map(image=>image.complete?Promise.resolve(image.naturalWidth>0):new Promise(resolve=>{image.onload=()=>resolve(true);image.onerror=()=>resolve(false)}))).then(results=>done(results.every(Boolean)))", "args": []})
            assert loaded, "A figure failed to load before PDF export"
            # Preserve useful PDF download links after the temporary QA server
            # stops. Only link destinations change; local figure sources do not.
            script("for(const a of document.querySelectorAll('a[href]')){const raw=a.getAttribute('href');if(raw && !raw.startsWith('#') && !/^[a-z][a-z0-9+.-]*:/i.test(raw)){a.href=new URL(raw,'https://clzJY.github.io/iota-qlearning/').href}}")
            pdf = command("POST", "/print", {"background": True, "orientation": "portrait", "page": {"width": 21.0, "height": 29.7}, "margin": {"top": 1.6, "bottom": 1.6, "left": 1.4, "right": 1.4}, "shrinkToFit": True})
            pdf_path = ROOT / "report/Qlearning_Report_Chenglong_Zhang_50068179.pdf"
            pdf_path.write_bytes(base64.b64decode(pdf))
            assert pdf_path.read_bytes().startswith(b"%PDF")
            print(f"Exported {pdf_path.name}", flush=True)
        record = {"browser": "Firefox", "version": session["capabilities"]["browserVersion"],
                  "figures_loaded": True, "four_required_static_qtables": True,
                  "problem_first_opening_without_statistics_strip": True,
                  "required_qtables_outside_collapsible_sections": True,
                  "conceptual_opening_illustration_loaded": True,
                  "update_calculator_checked": True, "saved_snapshot_control_checked": True,
                  "viewports": viewport_checks, "direct_file_opening_checked": bool(offline_ok),
                  "direct_file_opening_method": "byte-identical temporary copy, compatible with Firefox Snap confinement",
                  "pdf_exported": export_pdf}
        (ROOT / "docs/browser-verification.json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record, indent=2))
    finally:
        if session_id:
            try: command("DELETE", "")
            except Exception: pass
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill()
        server.shutdown()
        server.server_close()
        log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-pdf", action="store_true")
    main(parser.parse_args().export_pdf)
