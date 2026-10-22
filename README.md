<div align="center">

# 🦾 Digital Goniometer - Edge AI Rehabilitation

[![CI/CD Pipeline](https://github.com/a-delavega/digital-goniometer/actions/workflows/ci.yml/badge.svg)](https://github.com/a-delavega/digital-goniometer/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands%200.10.9-FF6F00.svg?logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9%2B-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Vector%20Math-013243.svg?logo=numpy&logoColor=white)](https://numpy.org/)
[![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen.svg?logo=pytest&logoColor=white)](tests/)
[![Architecture](https://img.shields.io/badge/architecture-Clean%20%2F%20Decoupled-orange.svg)](#architecture)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An AI-powered, vision-based digital goniometer for hand rehabilitation and physical therapy. It measures real-world 3D Range of Motion (ROM), detects posture compensation (cheating) dynamically via normal vectors, applies adaptive jitter filtering (1€ Filter), and exports clinical exercise metrics in real time.

[Overview](#overview) • [Key Features](#key-features) • [Architecture](#architecture) • [Quickstart](#quickstart) • [Biomechanical Engine](#biomechanical-engine) • [Testing](#testing) • [Design Decisions](#design-decisions)

---

</div>

> [!WARNING]
> **Educational & Experimental Disclaimer:**
> Este proyecto es un **desarrollo estrictamente didáctico y de exploración técnica** diseñado para investigar la aplicación de visión artificial, matemáticas vectoriales 3D y Edge AI. **NO es un dispositivo médico, software clínico certificado ni herramienta de diagnóstico**. No debe utilizarse para evaluar, diagnosticar, tratar ni rehabilitar patologías reales ni sustituir el criterio de profesionales sanitarios o fisioterapeutas colegiados.

---

## Overview

Traditional rehabilitation assessment relies on manual plastic goniometers or expensive, intrusive wearable sensor gloves. This project delivers a **computer vision and edge-ready software instrument** that extracts spatial hand kinematics directly from a standard webcam without physical contact.

The platform is designed with clinical precision and clean software engineering:
- **Clean Decoupled Architecture:** Pure anatomical definitions and vector mathematics are isolated from the computer vision framework and UI rendering layers.
- **True 3D Spatial Kinematics:** Angles are computed in real-world meters ($x, y, z$) from MediaPipe World Landmarks, eliminating perspective foreshortening common in standard 2D image analysis.
- **Real-Time Biofeedback & Isometry:** Tracks holding periods under isometric contraction thresholds and alerts patients when compensating with wrist rotation.
- **Session Audit & Metric Export:** Auto-generates structured CSV session logs in `exports/` capturing angle trajectories, smoothing benchmarks, and postural flags.

---

## Key Features

- 🖐️ **Full Hand Topography (14 Joints):** Anatomical mapping across all 5 digits (MCP, PIP, DIP for fingers; CMC, MCP, IP for the thumb).
- 📐 **Vector-Based 3D Angle Calculation:** Computes true spatial vertex flexion using dot products, normalized vectors, and clamped cosine transforms.
- 🚨 **Articular Isolation & Cheat Detection:** Continuously computes the palm's normal vector via vector cross product ($\vec{v}_1 \times \vec{v}_2$), triggering real-time compensation warnings if the wrist rotates beyond clinical tolerances.
- 🎯 **1€ Filter Adaptive Signal Smoothing:** Dual-cutoff low-pass filter eliminates camera landmark jitter during static postures while preserving responsive zero-lag tracking during rapid flexions.
- ⏱️ **Isometric Hold Tracking:** Automatically detects when a patient maintains target joint flexion angles within tolerance thresholds for a required duration (e.g. 3.0s).
- 🧵 **Threaded Video Pipeline:** Dedicated `VideoStream` worker thread prevents blocking OpenCV I/O from stuttering the main inference and rendering loop.
- 📊 **Automated CSV Export:** Clinical audit log recording timestamp, elapsed time, raw vs. smoothed angles, deviation angles, and isometry flags.

---

## Architecture

The project adheres to Clean Architecture principles: business math and anatomical models have **zero dependencies** on OpenCV or MediaPipe.

```
┌────────────────────────────────────────────────────────┐
│                      UI / App Layer                    │
│      main.py (CLI Wizard, HUD Overlay, Event Loop)     │
└──────────────────────────┬─────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌─────────────────────────┐       ┌────────────────────────┐
│       Vision Layer      │       │     Core & Exporters   │
│   HandTracker (Adapter) │       │   RehabConfig Settings │
│   VideoStream (Thread)  │       │   SessionExporter(CSV) │
└────────────┬────────────┘       └───────────┬────────────┘
             │                                │
             └────────────────┬───────────────┘
                              ▼
┌────────────────────────────────────────────────────────┐
│                   Biomechanics Domain                  │
│       HandJoint (Enum Map) · BiomechanicsMath          │
│       OneEuroFilter · Palm Normal Cross-Product        │
└────────────────────────────────────────────────────────┘
```

### Directory Structure

```text
digital-goniometer/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI matrix (Python 3.10, 3.11)
├── exports/                     # Auto-generated patient session CSV reports
├── src/
│   ├── biomechanics/            # Pure domain logic (Framework agnostic)
│   │   ├── joints_map.py        # 14 anatomical joint landmark triples
│   │   └── math_utils.py        # 3D vector math & OneEuroFilter
│   ├── core/                    # System configuration & persistence
│   │   ├── config.py            # Clinical thresholds & paths
│   │   └── session_exporter.py  # Thread-safe CSV session logging
│   ├── vision/                  # Vision adapter layer
│   │   ├── stream.py            # Non-blocking threaded video acquisition
│   │   └── tracker.py           # Decoupled MediaPipe Hands adapter
│   └── main.py                  # CLI wizard & real-time visual orchestrator
├── tests/                       # Unit & integration test suite
│   ├── run_tests.py             # Global test suite runner
│   ├── test_config.py           # Threshold validation tests
│   ├── test_joints_map.py       # Landmark topology integrity tests
│   ├── test_main_cli.py         # Mocked CLI interface flow tests
│   ├── test_math_utils.py       # 3D vector angle & OneEuroFilter tests
│   ├── test_session_exporter.py # CSV export integrity tests
│   └── test_tracker.py          # Vision adapter & compatibility tests
├── pyproject.toml               # Modern PEP 518/621 package metadata
└── requirements.txt             # Locked production dependencies
```

---

## Quickstart

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/a-delavega/digital-goniometer.git
cd digital-goniometer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Application

```bash
python src/main.py
```

### 3. Controls & Interaction

| Control | Action |
|---|---|
| **CLI Wizard** | Select number of joints (1 to 3) and choose Finger & Phalanx |
| **`C` key** | Recalibrate palm baseline posture (accumulates 30 stable frames) |
| **`Q` key** | Gracefully quit session, release camera, and flush session CSV |

---

## Biomechanical Engine

### 1. Spatial Angle Formulation (3D)

Given three spatial points $\mathbf{P}_{\text{proximal}}$, $\mathbf{P}_{\text{vertex}}$, and $\mathbf{P}_{\text{distal}}$:

$$\vec{v}_1 = \mathbf{P}_{\text{proximal}} - \mathbf{P}_{\text{vertex}}, \quad \vec{v}_2 = \mathbf{P}_{\text{distal}} - \mathbf{P}_{\text{vertex}}$$

$$\theta = \arccos\left(\text{clip}\left(\frac{\vec{v}_1 \cdot \vec{v}_2}{\|\vec{v}_1\| \|\vec{v}_2\|}, -1.0, 1.0\right)\right) \times \frac{180}{\pi}$$

### 2. Postural Compensation (Cheat Detection)

The normal vector $\vec{n}_{\text{palm}}$ perpendicular to the coronal plane of the hand is defined by the cross product of vectors spanning from the wrist ($\mathbf{P}_0$) to the index MCP ($\mathbf{P}_5$) and pinky MCP ($\mathbf{P}_{17}$):

$$\vec{n}_{\text{palm}} = \frac{(\mathbf{P}_5 - \mathbf{P}_0) \times (\mathbf{P}_{17} - \mathbf{P}_0)}{\|(\mathbf{P}_5 - \mathbf{P}_0) \times (\mathbf{P}_{17} - \mathbf{P}_0)\|}$$

Angular deviation from baseline posture $\vec{n}_0$ is evaluated every frame. If $\Delta\phi > 15.0^\circ$, a compensation alert is rendered.

---

## Testing

The project includes an automated test suite verifying spatial mathematics, signal smoothing, topological bounds, CSV logging, and CLI resilience:

```bash
# Execute the full test suite
python tests/run_tests.py
```

```text
Ran 12 tests in 3.411s

OK
[SUCCESS] All tests passed. The system is stable.
```

---

## Design Decisions

| Decision | Implementation | Why |
|---|---|---|
| **True 3D Coordinates** | MediaPipe `world_landmarks` | 2D pixel coordinates distort angles depending on camera perspective and tilt. 3D coordinates in meters guarantee invariant angular measurement. |
| **1€ Filter Smoothing** | `OneEuroFilter` | Moving average filters introduce lag. 1€ filter dynamically adapts cutoff frequency based on velocity, giving rock-solid static stabilization and instant reaction on fast movements. |
| **Threaded Video Stream** | `VideoStream` (`threading.Thread`) | Hardware camera I/O (`cv2.VideoCapture.read()`) is blocking. Running capture on a dedicated thread maximizes frame delivery to inference. |
| **Defensive Version Shield** | Explicit checks in `tracker.py` | Detects mismatched global Python environments and provides actionable guidance on environment activation. |
| **Zero Heavy Frameworks** | Pure NumPy + OpenCV | Minimizes memory footprint and eliminates bloated UI dependencies, making the core deployable to Edge IoT targets (Raspberry Pi, Jetson Nano). |

---

## License

MIT License. Designed and developed by Alejandro de la Vega ([@a-delavega](https://github.com/a-delavega)).
