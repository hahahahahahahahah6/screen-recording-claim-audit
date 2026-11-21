# Documentation claim auditor

This offline static auditor compares documented claims about the checked capability with Python source evidence. It never executes inspected code.

## Usage

```sh
python3 -m pip install .
screen-recording-claim-audit audit . --json
python3 -m screen_recording_claim_audit audit . --verbose
```

The optional repository path defaults to the current directory. Use `--ignore PREFIX` repeatedly to exclude paths and `--fail-on medium` to include test-only findings in the failure threshold. Exit status is 0 for PASS, 2 for findings at the selected threshold, and 1 for usage or I/O errors. Use `--version` to show the version.

The finding identifiers are:

```text
documented-screen-recording-claim-false
documented-no-screen-recording-claim-false
```

## Differentiation

The checked operation differs from still-image capture, webcam capture, synthetic video creation, video stabilization, live broadcast and audio-only capture. The phrase lists also exclude spreadsheet reading and generation, word-document reading and generation, presentation reading and generation, PDF extraction, generation, merging, splitting, encryption, rotation, form-filling, watermarking, redaction, compression and annotation, table extraction, OCR, document extraction, e-signature and payment-processing claims. Other claim-audit families address those capabilities.

## Limitations

This phrase may refer only to a roadmap:

```text
screen recording
```

This phrase may refer to a live broadcast or playback:

```text
screencast
```

This phrase may refer to audio or a recording made on a desktop:

```text
desktop recording
```

This phrase may refer to desktop audio or another operation:

```text
record desktop
```

This phrase may refer to a still-image gallery or a setting:

```text
record display
```

This phrase may refer to monitoring a record or a sensor device:

```text
record monitor
```

This phrase may refer loosely to one frame from a video:

```text
screen capture video
```

This phrase may refer to a user interface or one still image:

```text
record screen
```

- An unrelated `.run()` call can complete the ffmpeg pair.
- An mss import and an unrelated shot or grab method can complete the writer pair.
- The writer pair does not trace whether frames flow to the writer.
- An unrelated `.start()` call can complete the gear pair.
- An unrelated `.start_recording()` call can complete the recorder pair.
- An unrelated `.start_record()` call can complete the OBS pair.
- A variable holding an ffmpeg input format is missed.
- Passing both format keywords can count even though the library rejects the call.
- A bare library import is not evidence.
- A roadmap, changelog or TODO claim is still treated as a claim.
- A denial outside the listed phrases may be missed.
- Claims outside the root README and docs directories are invisible.
- Evidence split across modules is missed.
- A locally defined route name shadows the imported route, even for a wrapper.
- Dead code counts as evidence.
- External recorder commands invoked through subprocess are not evidence.
- A still capture without a writer is not evidence, even inside a loop.
- A webcam read is not evidence, even if its frames are written.
- Audio-only capture is not evidence, even alongside a capture in another module.
- A locally defined generic name is shadowed even when it implements the capability.
- Alias chains the tracer cannot follow are missed.
- Exact phrases do not establish meaning and paraphrases can be missed.
- Implementations in languages other than Python are invisible.
- Runtime-only routes and dynamically loaded plugins are invisible.
- The OBS client and its starting call must occur in the same module.
- A format built by concatenation or read from configuration is missed.
- The gear construction and its starting call must occur in the same module.
- The recorder construction and its starting call must occur in the same module.
- The writer construction and its frame source must occur in the same module.
- A lone writer construction is not evidence.
- A bare screenshot call is not evidence.
- A bare grab call is not evidence.
- A lone recorder construction is not evidence.
- A lone gear construction is not evidence.
- A lone client construction is not evidence.
- A lone input call is not evidence.
- A lone output or run call is not evidence.
- A lone `.start()` call is not evidence.
- A lone `.start_recording()` call is not evidence.
- A lone `.start_record()` call is not evidence.
- Static matching cannot judge whether a detected operation works correctly.
