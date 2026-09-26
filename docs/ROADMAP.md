# Roadmap

This roadmap is directional rather than a commitment to dates.

## Completed foundations

- personal neutral-posture calibration
- torso/slouch detection using shoulders, hips and relative depth
- per-module tracking confidence with LOW_CONFIDENCE gating
- guided camera framing and runtime camera selection
- confidence-weighted temporal exposure and postural drift
- personalized EAR baseline and blink-state tracking
- closed-loop correction alerts with verified recovery
- explicit signal-readiness states for tracking and baselines
- live posture trends and local browser session history
- configurable reminders and desktop notifications
- installable macOS launcher and Windows shortcuts
- automated macOS + Windows release bundles
- professional CI and contribution workflow

## Near term

- exportable **derived** session summaries for research/evaluation
- reproducible benchmark script and labelled evaluation protocol
- confidence-calibration analysis and reliability plots
- additional frontend/component tests
- accessibility audit, reduced-motion support and non-colour-only states
- signed/notarized release packaging

## Product maturity

- persistent local session database with explicit retention controls
- configurable ergonomic thresholds and saved profiles
- optional side-view posture mode
- research-session export with schema/version metadata
- richer intervention analytics without overstating long-term behaviour change

## Research and architecture

- evaluation dataset for threshold tuning and subgroup analysis
- reference comparison for slouch / forward-head proxies
- event-level blink validation across eyewear and lighting conditions
- longitudinal validation of the prototype exposure indicator
- controlled evaluation of intervention effectiveness
- browser-native capture/inference for a truly hosted version

See [Research gaps and validation plan](RESEARCH_GAPS.md) for the evidence plan and claims boundaries.

## Explicit non-goals for the current version

- medical diagnosis
- clinical posture assessment
- exact spinal-curvature measurement
- exact webcam-to-user distance measurement
- hidden background recording
- cloud video storage
- multi-person monitoring
