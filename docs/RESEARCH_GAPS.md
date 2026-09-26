# Research gaps and validation plan

ErgoVision is a local-first ergonomic coaching prototype. Its current signals are designed for real-time feedback, but they are **ergonomic heuristics rather than clinically validated measurements**.

This document makes the main research gaps explicit and turns them into a reproducible validation plan. The intent is to make uncertainty visible instead of hiding it behind a single score.

## What the current system already does

ErgoVision reduces several known weaknesses of webcam-only posture estimation by combining:

- personal neutral-posture calibration
- face, shoulder and hip geometry
- relative MediaPipe depth cues
- temporal smoothing and persistence
- per-module tracking confidence
- a LOW_CONFIDENCE state that prevents weak tracking from becoming false GOOD posture
- confidence-weighted temporal exposure
- a personalized eye-aspect-ratio baseline
- closed-loop intervention verification

These are useful engineering mitigations. They are not substitutes for external validation.

## Research gaps

| Gap | Current mitigation | Evidence still needed |
| --- | --- | --- |
| Front-facing 2D posture approximation | Personal calibration, torso geometry and relative depth | Comparison with expert annotation, side-view reference or motion-capture measurements |
| Heuristic posture thresholds | Transparent thresholds and bounded ErgoVision Index | Threshold tuning on a labelled evaluation set with class-level metrics |
| Confidence modelling | Landmark visibility/presence, module confidence and LOW_CONFIDENCE gating | Reliability calibration showing whether confidence predicts usable observations |
| Slouch / forward-head proxy validity | Multiple geometric cues instead of one landmark | Agreement study across body types, camera positions and desk setups |
| Visual ergonomics | Personalized EAR baseline, blink state machine and relative proximity drift | Longer recordings across lighting, glasses, gaze angles and natural blink behaviour |
| Temporal exposure | Confidence-weighted risk-seconds with recovery | Longitudinal study against an independently labelled ergonomic-exposure reference |
| Generalization | Per-user calibration and local processing | Evaluation across participant diversity, clothing, cameras, lighting and occlusion |
| Intervention effectiveness | Verified correction and before/after risk | Controlled study of correction rate, time-to-correction and sustained behaviour change |
| Hosted deployment | Local Python process owns the webcam | Browser-native capture/inference architecture before claiming a true hosted version |

## Signal readiness

The dashboard exposes readiness separately from the ergonomic result.

### Tracking readiness

A posture score is only treated as reliable when the required head and shoulder landmarks are visible and the combined tracking confidence clears the reliability threshold. Weak tracking produces LOW_CONFIDENCE rather than a reassuring score.

### Personal posture calibration

Calibration establishes a neutral geometry for the individual user and camera setup. It improves interpretation of slouch and relative proximity drift. Changing cameras invalidates this geometry and clears calibration.

### Exposure baseline

Postural drift is withheld until the engine has accumulated the configured amount of **reliable observation time**. Time spent in LOW_CONFIDENCE does not complete the baseline.

### Visual baseline

The eye baseline is built from valid eye observations only. Interruptions in eye confidence do not count as baseline time. Blink-rate and visual-load outputs remain in warm-up until both the personal eye baseline and a longer observation window are ready.

## Validation priorities

### 1. Build a consented evaluation dataset

Use a fixed capture protocol containing:

1. neutral upright posture
2. forward-head posture
3. shoulder asymmetry
4. torso lean
5. slouch / hunch
6. partial occlusion
7. low or uneven lighting
8. no-person frames
9. natural blink sequences
10. recovery after an ErgoVision intervention

Prefer storing derived landmarks and labels instead of raw video whenever the research question allows it. If video is required for annotation, it should be opt-in, access-controlled and kept separate from the normal application data path.

Suggested metadata:

- pseudonymous participant/session ID
- camera model and resolution
- camera height and approximate view angle
- lighting category
- eyewear condition
- reference posture label
- ErgoVision status and ErgoVision Index
- component measurements
- module confidence
- calibration/readiness state
- timestamp

### 2. Report metrics by task

Do not collapse validation into a single "accuracy" number.

For posture classification, report a confusion matrix plus precision, recall and F1 for GOOD / WARNING / BAD. Report LOW_CONFIDENCE coverage separately.

For continuous posture proxies, report error and association against the selected reference with confidence intervals.

For confidence, use reliability diagrams or calibration error so confidence is evaluated as confidence rather than as classification accuracy.

For blink detection, use event-level precision/recall with a documented temporal matching tolerance.

For interventions, report correction success rate, time-to-correction and immediate risk reduction. Treat sustained behaviour change as a separate longitudinal outcome.

### 3. Stress-test failure modes

Evaluate performance separately for:

- low and uneven lighting
- glasses and reflective lenses
- partial face/shoulder occlusion
- off-axis head pose
- camera above or below eye level
- different desk distances
- loose or dark clothing
- brief tracking dropouts
- different webcam qualities
- a second person entering frame

## Claims discipline

Use:

- **ErgoVision Index** rather than a clinical score
- **prototype ergonomic exposure indicator** or **risk-seconds**
- **visual ergonomic indicator** rather than eye-strain diagnosis
- **relative proximity drift** rather than distance in centimetres
- **confidence-aware posture estimate** rather than anatomical measurement

Do not claim clinical validation, medical diagnosis, exact spinal curvature, exact viewing distance, RULA/REBA equivalence, or a universal accuracy percentage until a suitable study supports that claim.

## Research-ready product direction

The next research-oriented extensions are:

1. an exportable derived-session format for evaluation
2. a reproducible benchmark script and labelled test protocol
3. calibration plots for tracking/module confidence
4. an optional side-view mode for sagittal posture cues
5. accessibility and reduced-motion options
6. explicit local data-retention controls
7. browser-native capture/inference for hosted deployment

The target is not to make ErgoVision sound more certain. The target is to make uncertainty measurable, visible and progressively reducible through evidence.
