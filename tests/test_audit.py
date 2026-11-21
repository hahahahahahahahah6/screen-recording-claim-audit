import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from screen_recording_claim_audit.audit import audit, evidence, paragraphs, pattern
from screen_recording_claim_audit.phrases import SCREENRECORDING, NOSCREENRECORDING, GENERIC_NAMES
from screen_recording_claim_audit.__main__ import main

EXPECTED = (('record screen', 'records screen', 'recording screen', 'record screens', 'records screens', 'recording screens', 'screen recording', 'screen recordings', 'screen recorder', 'screen recorders', 'record the screen', 'records the screen', 'recording the screen', 'record your screen', 'records your screen', 'recording your screen', 'record desktop', 'records desktop', 'recording desktop', 'desktop recording', 'desktop recordings', 'desktop recorder', 'record display', 'records display', 'recording display', 'display recording', 'record monitor', 'records monitor', 'recording monitor', 'capture screen video', 'captures screen video', 'capturing screen video', 'record screen video', 'records screen video', 'recording screen video', 'screen video recording', 'screen video recorder', 'capture desktop video', 'captures desktop video', 'capturing desktop video', 'record screen activity', 'records screen activity', 'recording screen activity', 'screencast', 'screencasts', 'screencasting', 'record screencast', 'records screencast', 'recording screencast', 'screen capture video'), ('no screen recording', 'does not record screen', 'does not record screens', 'does not record the screen', 'does not record your screen', 'does not record desktop', 'does not record display', 'does not record monitor', 'does not capture screen video', 'does not capture desktop video', 'does not record screen video', 'no screen recordings', 'does not support screen recording', 'without screen recording', 'screen recording not supported', 'no screen recording support', 'screen recording not available', 'no screen recorder', 'does not record screen activity', 'does not support desktop recording', 'no desktop recording', 'does not screencast', 'no screencast', 'does not record screen as video'), ('record_screen', 'record_screens', 'record_the_screen', 'record_your_screen', 'record_desktop', 'record_display', 'record_monitor', 'record_screen_video', 'record_desktop_video', 'capture_screen_video', 'capture_desktop_video', 'record_screen_activity', 'start_screen_recording', 'stop_screen_recording', 'start_recording_screen', 'screen_record', 'screencast', 'start_screencast', 'stop_screencast', 'record_screencast', 'start_desktop_recording', 'stop_desktop_recording', 'record_screen_to_video', 'record_screen_to_file'))

class AuditTests(unittest.TestCase):
    def test_oracle(self):
        self.assertEqual((SCREENRECORDING, NOSCREENRECORDING, GENERIC_NAMES), EXPECTED)
        self.assertEqual(tuple(map(len, EXPECTED)), (50, 24, 24))

    def test_routes(self):
        sources = ['import ffmpeg; ffmpeg.input("x", f="%s"); ffmpeg.output()' % f for f in ('x11grab','gdigrab','avfoundation','dshow','decklink','kmsgrab')]
        sources += ['from ffmpeg import input as i, run as r; i("x", format="X11GRAB"); r()', 'import ffmpeg as f; f.input("x", f="x11grab"); stream.run()', 'import cv2, pyautogui; cv2.VideoWriter(); pyautogui.screenshot()', 'from cv2 import VideoWriter as W; from PIL.ImageGrab import grab as g; W(); g()', 'import cv2; from PIL import ImageGrab as G; cv2.VideoWriter(); G.grab()', 'import cv2, mss; cv2.VideoWriter(); x.shot()', 'import cv2; from mss import mss; cv2.VideoWriter(); x.grab()', 'import pyscreenrec as p; p.ScreenRecorder(); x.start_recording()', 'from pyscreenrec import ScreenRecorder as R; R(); x.start_recording()', 'import vidgear.gears as v; v.ScreenGear(); x.start()', 'from vidgear.gears import ScreenGear as G; G(); x.start()', 'import obsws_python as o; o.ReqClient(); x.start_record()', 'from obsws_python import ReqClient as C; C(); x.start_record()']
        sources += ['x.%s()' % n for n in GENERIC_NAMES] + ['from lib import %s as f; f()' % n for n in GENERIC_NAMES]
        for source in sources:
            with self.subTest(source=source): self.assertTrue(evidence(source))

    def test_non_routes(self):
        sources = ['import '+x for x in ('ffmpeg','cv2','pyscreenrec','vidgear','obsws_python','pyautogui','PIL','mss','imageio')]
        sources += ['import ffmpeg; ffmpeg.input("x", f="x11grab")', 'import ffmpeg; ffmpeg.output()', 'x.run()', 'import cv2; cv2.VideoWriter()', 'import pyautogui; pyautogui.screenshot()', 'x.grab()', 'x.shot()', 'import pyscreenrec; pyscreenrec.ScreenRecorder()', 'x.start_recording()', 'import vidgear; vidgear.ScreenGear()', 'x.start()', 'import obsws_python; obsws_python.ReqClient()', 'x.start_record()', 'import obsws_python; obsws_python.ReqClient(); x.stop_record()', 'cv2.VideoCapture().read()', 'imageio.get_writer()', 'matplotlib.animation()', 'sounddevice.rec()', 'pyaudio.open()', 'soundfile.write()', '"screen recording"', 'subprocess.run(["ffmpeg"])', 'subprocess.run(["obs"])', 'record_screen()', 'x.record_screen', 'def record_screen(): pass\nx.record_screen()', 'import cv2\nwith obj as cv2: pass\ncv2.VideoWriter(); x.grab()', 'invalid syntax !!!']
        sources += ['import ffmpeg; ffmpeg.input("x", f="%s"); ffmpeg.output()' % f for f in ('mp4','mp3','v4l2','image2')]
        sources += ['import ffmpeg; ffmpeg.input("x"); ffmpeg.output()', 'import cv2; cv2.VideoWriter(); x.grab()', 'import pyscreenshot; pyscreenshot.grab()', 'av.open("camera")', 'x.stabilize()', 'x.publish()']
        for source in sources:
            with self.subTest(source=source): self.assertFalse(evidence(source))

    def test_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); doc=root/'README.md'; src=root/'app.py'
            for phrase in SCREENRECORDING:
                doc.write_text(phrase); self.assertEqual(audit(root)['verdict'], 'FAIL', phrase)
            for phrase in NOSCREENRECORDING:
                doc.write_text(phrase); self.assertEqual(audit(root)['verdict'], 'PASS', phrase)
                src.write_text('x.record_screen()'); self.assertEqual(audit(root)['findings'][0]['rule'], 'documented-no-screen-recording-claim-false'); src.unlink()
            doc.write_text('```\nrecord screen\n```'); self.assertEqual(audit(root)['verdict'], 'PASS')
            doc.write_text('`record-screen`'); self.assertEqual(audit(root)['verdict'], 'FAIL')
            (root/'tests').mkdir(); (root/'tests/test_x.py').write_text('x.record_screen()')
            self.assertEqual(audit(root)['findings'][0]['severity'], 'MEDIUM'); self.assertEqual(audit(root)['verdict'], 'PASS'); self.assertEqual(audit(root, fail_on='medium')['verdict'], 'FAIL')

    def test_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'README.md').write_text('record screen'); (root/'a.py').write_text('import ffmpeg; ffmpeg.input("x",f="x11grab")'); (root/'b.py').write_text('x.run()')
            self.assertEqual(audit(root)['verdict'], 'FAIL')
            (root/'b.py').write_text('x.record_screen()'); (root/'link.py').symlink_to(root/'b.py'); self.assertEqual(audit(root, ignore=['b.py'])['verdict'], 'FAIL')
            (root/'docs').mkdir(); (root/'docs/a.md').write_text('no screen recording'); self.assertEqual(audit(root)['verdict'], 'FAIL')

    def test_cli(self):
        self.assertEqual(subprocess.run([sys.executable, '-m', 'screen_recording_claim_audit', '--version'], capture_output=True, text=True).stdout.strip(), '0.1.0')
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'README.md').write_text('record screen')
            p=subprocess.run([sys.executable, '-m', 'screen_recording_claim_audit', 'audit', tmp, '--json'], capture_output=True, text=True)
            self.assertEqual(p.returncode,2); self.assertEqual(json.loads(p.stdout)['verdict'],'FAIL'); self.assertEqual(main(['audit',tmp]),2)
            self.assertEqual(subprocess.run([sys.executable, '-m', 'screen_recording_claim_audit', 'audit', '/missing-path'], capture_output=True).returncode,1)

if __name__ == '__main__': unittest.main()
