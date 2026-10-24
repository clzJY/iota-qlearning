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


def main(export_pdf=False, preview_directory=None):
    if not shutil.which("geckodriver") or not shutil.which("firefox"):
        raise SystemExit("Optional browser check requires installed firefox and geckodriver")
    preview_temp = tempfile.TemporaryDirectory(prefix="iota-preview-") if preview_directory is None else None
    preview = Path(preview_temp.name) if preview_temp else preview_directory
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
        assert script("return document.querySelectorAll('#route-scene .route-track').length") == 3
        assert script("return document.querySelectorAll('#fixed-robot image, #fixed-destination image').length") == 2
        assert script("return !document.querySelector('#update-form') && document.getElementById('worked-example').textContent.includes('0.009')"), "Worked example must explain reward propagation without sliders"
        motion = script("const svg=document.getElementById('route-scene');const robot=document.getElementById('fixed-robot');const dock=document.getElementById('fixed-destination');const echo=document.querySelector('.route-echo');function position(element){const r=element.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}const before=[position(robot),position(dock)];svg.pauseAnimations();svg.setCurrentTime(1);const first=[echo.getCTM().e,echo.getCTM().f,Number(getComputedStyle(echo).opacity)];svg.setCurrentTime(7.9);const last=[echo.getCTM().e,echo.getCTM().f,Number(getComputedStyle(echo).opacity)];const after=[position(robot),position(dock)];svg.unpauseAnimations();return {before,after,first,last}")
        assert motion["before"] == motion["after"], "Robot or destination moved"
        assert motion["first"][:2] != motion["last"][:2], "Route echo did not move"
        assert motion["last"][2] < motion["first"][2] / 10, motion
        script("document.getElementById('route-motion').click()")
        assert script("return document.getElementById('route-scene').animationsPaused()")
        script("document.getElementById('route-motion').click()")
        assert not script("return document.getElementById('route-scene').animationsPaused()")
        ai_target = command("POST", "/execute/async", {"script": "const done=arguments[arguments.length-1];window.addEventListener('hashchange',()=>done(location.hash),{once:true});document.querySelector('nav a[href=\"#ai-use\"]').click()", "args": []})
        assert ai_target == "#ai-use", ai_target
        assert script("const links=[...document.querySelectorAll('nav[aria-label=\"Report sections\"] a')];return links.findIndex(a=>a.hash==='#ai-use')<links.findIndex(a=>a.hash==='#reproduce')"), "AI use must precede Report & files"
        assert script("return document.querySelectorAll('#report-guide .requirement-link').length===5 && [...document.querySelectorAll('#report-guide a')].every(a=>document.getElementById(a.hash.slice(1)))"), "Every report requirement needs a valid direct link"
        assert script("const ids=['method','setup','results','required-comparison','takeaways'];const titles=['Motivation and method','Environment and experimental setup','Results for both configurations','Comparison and critical analysis','Takeaways and references'];return ids.every((id,i)=>document.querySelector('#'+id+' h2').textContent===titles[i]) && document.getElementById('takeaways').contains(document.getElementById('references')) && document.getElementById('takeaways').contains(document.getElementById('ai-use'))"), "Five main headings and their contents must match the brief"
        assert script("return !document.querySelector('.requirement-cards') && document.getElementById('report-guide').parentElement.id==='question' && document.querySelectorAll('#report-guide .requirement-link').length===5 && document.querySelectorAll('.jump-subsections a').length===12"), "Keep main links and direct subsection links at the bottom of The Problem"
        assert script("return [...document.querySelectorAll('#setup details,#results details,#comparison details')].every(panel=>panel.open)"), "Supporting explanations, tables and figures must be visible by default"
        assert script("return [...document.querySelectorAll('#comparison .chart,#comparison table')].every(element=>!element.closest('details:not([open])'))"), "Additional evidence must be visible without opening a panel"
        assert script("const sizes=[...document.querySelectorAll('#comparison>details>summary')].map(element=>getComputedStyle(element).fontSize);return sizes.length===3 && new Set(sizes).size===1"), "Three Part 4 panel titles must have identical font size"
        reading_checks = []
        for target,part in [("method","1"),("setup","2"),("results","3"),("case-original","3"),("case-modified","3"),("required-comparison","4"),("comparison","4"),("takeaways","5"),("references","5"),("ai-use","5")]:
            script(f"document.getElementById({json.dumps(target)}).scrollIntoView({{behavior:'instant'}})")
            command("POST", "/execute/async", {"script": "const done=arguments[arguments.length-1];requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>done(true))))", "args": []})
            state = script("return {caption:document.getElementById('reading-caption').textContent,title:document.getElementById('reading-current').textContent,subphase:document.getElementById('reading-subphase').textContent,active:[...document.querySelectorAll('.reading-steps a[aria-current]')].map(a=>a.textContent),top:document.getElementById('reading-position').getBoundingClientRect().top}")
            assert state["active"] == [part], (target,state)
            assert state["caption"].startswith(f"PART {part} OF 5"), (target,state)
            assert abs(state["top"]) < 1, (target,state)
            if target == "case-modified": assert "Experiment 2" in state["subphase"]
            reading_checks.append({"target":target,"part":part,"checked":True})
        script("document.getElementById('report-guide').scrollIntoView({behavior:'instant'});document.documentElement.style.scrollBehavior='auto'")
        quick_target = command("POST", "/execute/async", {"script": "const done=arguments[arguments.length-1];window.addEventListener('hashchange',()=>requestAnimationFrame(()=>requestAnimationFrame(()=>done({hash:location.hash,part:document.getElementById('reading-caption').textContent}))),{once:true});document.querySelector('#report-guide a[href=\"#setup\"]').click()", "args": []})
        assert quick_target["hash"] == "#setup" and quick_target["part"].startswith("PART 2 OF 5"), quick_target
        script("document.documentElement.style.scrollBehavior=''")
        assert script("return document.querySelectorAll('.extension-answers article').length===2 && !document.querySelector('.extension-answers').closest('details') && document.getElementById('equal-routes-conclusion').textContent.includes('No,') && document.getElementById('route-accuracy-conclusion').textContent.includes('Yes.')"), "Both additional questions need explicit visible answers"
        assert script("const scene=document.getElementById('modified-route-scene');return scene.closest('#case-modified') && scene.querySelectorAll('.route-track').length===3 && document.getElementById('modified-fixed-robot').dataset.room==='A' && document.getElementById('modified-fixed-destination').dataset.room==='C'"), "Experiment 2 needs the A-to-C figure"
        modified_motion = script("const svg=document.getElementById('modified-route-scene');const robot=document.getElementById('modified-fixed-robot');const dock=document.getElementById('modified-fixed-destination');const echo=svg.querySelector('.route-echo');function position(element){const r=element.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}const before=[position(robot),position(dock)];svg.pauseAnimations();svg.setCurrentTime(1);const first=[echo.getCTM().e,echo.getCTM().f,Number(getComputedStyle(echo).opacity)];svg.setCurrentTime(7.9);const last=[echo.getCTM().e,echo.getCTM().f,Number(getComputedStyle(echo).opacity)];const after=[position(robot),position(dock)];svg.unpauseAnimations();return {before,after,first,last}")
        assert modified_motion["before"] == modified_motion["after"]
        assert modified_motion["first"][:2] != modified_motion["last"][:2]
        assert modified_motion["last"][2] < modified_motion["first"][2] / 10
        script("document.getElementById('modified-route-motion').click()")
        assert script("return document.getElementById('modified-route-scene').animationsPaused() && !document.getElementById('route-scene').animationsPaused()"), "Figure controls must be independent"
        script("document.getElementById('modified-route-motion').click()")
        assert not script("return document.getElementById('modified-route-scene').animationsPaused()")
        script("document.getElementById('equal-routes-evidence').open=false")
        evidence_target = command("POST", "/execute/async", {"script": "const done=arguments[arguments.length-1];window.addEventListener('hashchange',()=>done(document.getElementById('equal-routes-evidence').open),{once:true});document.querySelector('#equal-routes-conclusion>a').click()", "args": []})
        assert evidence_target, "Evidence link must open the correct panel"
        subsection_checks = []
        for target in ["implementation-choices","original-tables","original-convergence","modified-tables","modified-convergence","reference-calculation","saved-qtables","equal-routes-evidence","insight","pilot-settings"]:
            script(f"document.documentElement.style.scrollBehavior='auto';for(const panel of document.querySelectorAll('#setup details,#results details,#comparison details'))panel.open=false;location.hash='report-guide';document.getElementById('report-guide').scrollIntoView({{behavior:'instant'}})")
            command("POST", "/execute/async", {"script": "const done=arguments[arguments.length-1];requestAnimationFrame(()=>requestAnimationFrame(()=>done(true)))", "args": []})
            state = command("POST", "/execute/async", {"script": "const done=arguments[arguments.length-1];const id="+json.dumps(target)+";window.addEventListener('hashchange',()=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>{const target=document.getElementById(id);done({hash:location.hash,subphase:document.getElementById('reading-subphase').getAttribute('href'),visible:!target.closest('details:not([open])'),top:target.getBoundingClientRect().top,barBottom:document.getElementById('reading-position').getBoundingClientRect().bottom})}))),{once:true});document.querySelector('.jump-subsections a[href=\"#'+id+'\"]').click()", "args": []})
            assert state["hash"] == "#"+target and state["visible"], (target,state)
            assert state["subphase"] == "#"+target, (target,state)
            assert state["top"] >= state["barBottom"]-1, (target,state)
            subsection_checks.append({"target":target,"opens_and_tracks":True})
        script("document.documentElement.style.scrollBehavior='';document.querySelectorAll('#setup details,#results details,#comparison details').forEach(panel=>panel.open=true)")
        result = script("document.querySelector('.snapshot-details').open=true; document.getElementById('snapshot-case').value='modified'; document.getElementById('snapshot-case').dispatchEvent(new Event('change')); document.getElementById('snapshot-episode').value='20000'; document.getElementById('snapshot-episode').dispatchEvent(new Event('change')); return document.querySelector('#snapshot-table caption').textContent")
        assert "A → C" in result and "20000" in result
        assert script("return document.querySelectorAll('#snapshot-table tbody tr').length") == 6
        command("POST", "/url", {"url": local_url})
        screenshot("desktop.png")
        script("document.getElementById('case-original').scrollIntoView({behavior:'instant'})")
        screenshot("results-desktop.png")
        script("document.getElementById('case-modified').scrollIntoView({behavior:'instant'})")
        screenshot("experiment2-desktop.png")
        script("document.getElementById('report-guide').scrollIntoView({behavior:'instant'})")
        screenshot("report-guide-desktop.png")
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
            offline_ok = script("return document.title.includes('Q-learning') && document.getElementById('worked-example').textContent.includes('0.009') && document.querySelectorAll('.route-scene').length===2 && document.querySelectorAll('#modified-route-scene .route-track').length===3 && document.querySelectorAll('#report-guide .requirement-link').length===5 && !document.getElementById('reading-position').hidden && [...document.images].every(i=>i.complete && i.naturalWidth>0)")
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
                  "annotated_reward_propagation_without_sliders": True, "saved_snapshot_control_checked": True,
                  "fixed_robot_and_destination_checked": True, "three_route_echoes_move_and_fade": True,
                  "route_pause_button_checked": True, "ai_use_menu_checked": True,
                  "modified_a_to_c_figure_checked": True, "both_figure_controls_independent": True,
                  "five_required_report_parts_linked": True, "extension_answers_visible": True,
                  "ai_use_before_report_files": True,
                  "five_named_report_parts": True, "single_row_quick_links": True,
                  "sticky_reading_position": reading_checks, "quick_link_updates_position": True,
                  "direct_subsection_links": subsection_checks, "supporting_evidence_open_by_default": True,
                  "matching_part4_panel_title_sizes": True, "subsection_middle_main_part_right": True,
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
        if preview_temp:
            preview_temp.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-pdf", action="store_true")
    parser.add_argument("--preview-dir", type=Path, help="Optionally retain QA screenshots; omitted by default")
    args = parser.parse_args()
    main(args.export_pdf, args.preview_dir)
