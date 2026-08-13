# 🦾 Digital Goniometer - Edge AI Rehabilitation

An AI-powered, vision-based digital goniometer for hand rehabilitation.

This project uses computer vision and 3D vector mathematics to measure the **Range of Motion (ROM)** of hand joints in real time, eliminating the need for physical wearable sensors.

> **Status:** Phase 1 (Local MVP) – Core Biomechanics & Vision Tracker completed.

---

## ✨ Key Features

- 🖐️ **Full Hand Topography:** Complete mapping of all **14 functional joints** across the five fingers (MCP, PIP, DIP, CMC, IP).
- 📐 **True 3D Spatial Angles:** Calculates Range of Motion (ROM) using real-world 3D coordinates (meters), making measurements immune to 2D camera perspective distortion.
- 🚨 **Articular Isolation (Cheat Detection):** Uses cross-product vector mathematics to dynamically calculate the palm's normal vector, detecting wrist compensation (unwanted rotation) and warning the patient in real time.
- 💻 **Interactive CLI Wizard:** Step-by-step console assistant to dynamically select and monitor up to **three joints simultaneously** without interface overlap.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Computer Vision:** OpenCV (`opencv-python`)
- **AI & Tracking:** Google MediaPipe Hands
- **Mathematics:** NumPy (Linear Algebra & 3D Vector Mathematics)

---

## 🏗️ Architecture (Clean Code)

The project follows a modular, decoupled architecture to ensure scalability for future IoT/Edge and Web integrations.

```text
src/
├── biomechanics/
│   ├── joints_map.py
│   └── math_utils.py
├── vision/
│   └── tracker.py
├── core/
│   └── config.py
└── main.py
```

### Module Description

- **`src/biomechanics/`**
  - Pure business logic.
  - Anatomical mapping (`joints_map.py`).
  - Framework-agnostic mathematical engine (`math_utils.py`).

- **`src/vision/`**
  - AI adapter layer.
  - Wraps MediaPipe Hands (`tracker.py`) to keep the application independent from the tracking framework.

- **`src/core/`**
  - Application configuration.
  - Medical thresholds (`config.py`).

- **`src/main.py`**
  - Main orchestrator.
  - Real-time rendering and visualization.

---

## 🧪 Testing

The project includes a comprehensive unit testing suite covering 3D vector math, data structures, and edge cases (e.g., hardware failures). 

To run the entire test suite, simply execute the global test runner:

```bash
python run_tests.py
```
---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/digital-goniometer.git
cd digital-goniometer
```

### 2. Create and activate a virtual environment

#### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install opencv-python==4.9.0.80 mediapipe==0.10.9 numpy==1.26.3
```

---

## 🎮 Usage

Run the main application:

```bash
python src/main.py
```

Then:

1. Select how many joints you want to monitor.
2. Choose the finger and specific joint (e.g., **PINKY → PIP**).
3. Position your hand in front of the webcam.
4. Perform the flexion exercises.
5. If wrist compensation is detected, the system will display a **CHEATING!** warning.
6. Press **Q** or close the window to exit.

---

Developed for **clinical rehabilitation** and **Edge AI research**.

---

# 🦾 Goniómetro Digital - Rehabilitación con Edge AI

Un goniómetro digital basado en visión artificial e Inteligencia Artificial para la rehabilitación de la mano.

Este proyecto utiliza visión por computador y matemáticas de vectores 3D para medir el **Rango de Movimiento (ROM)** de las articulaciones de la mano en tiempo real, eliminando la necesidad de sensores físicos o dispositivos wearables.

> **Estado:** Fase 1 (MVP Local) – Core de Biomecánica y Tracker de Visión completados.

---

## ✨ Características Principales

- 🖐️ **Topografía Completa de la Mano:** Mapeo anatómico de las **14 articulaciones funcionales** de los cinco dedos (MCP, PIP, DIP, CMC, IP).
- 📐 **Ángulos Espaciales 3D Reales:** Calcula el Rango de Movimiento (ROM) utilizando coordenadas 3D del mundo real (metros), haciendo que las mediciones sean inmunes a la distorsión de perspectiva de las cámaras 2D.
- 🚨 **Aislamiento Articular (Detección de Trampas):** Utiliza matemáticas de producto vectorial (*cross product*) para calcular dinámicamente el vector normal de la palma, detectando la compensación de la muñeca (rotación no deseada) y alertando al paciente en tiempo real.
- 💻 **Asistente Interactivo CLI:** Asistente de consola paso a paso para seleccionar y monitorizar dinámicamente hasta **tres articulaciones simultáneamente**, evitando el solapamiento en la interfaz.

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Visión Artificial:** OpenCV (`opencv-python`)
- **IA y Tracking:** Google MediaPipe Hands
- **Matemáticas:** NumPy (Álgebra Lineal y Vectores 3D)

---

## 🏗️ Arquitectura (Clean Code)

El proyecto sigue una arquitectura modular y desacoplada para garantizar su escalabilidad en futuras integraciones IoT/Edge y aplicaciones Web.

```text
src/
├── biomechanics/
│   ├── joints_map.py
│   └── math_utils.py
├── vision/
│   └── tracker.py
├── core/
│   └── config.py
└── main.py
```

### Descripción de los módulos

- **`src/biomechanics/`**
  - Lógica de negocio pura.
  - Mapeo anatómico (`joints_map.py`).
  - Motor matemático agnóstico (`math_utils.py`).

- **`src/vision/`**
  - Capa adaptadora de IA.
  - Envuelve MediaPipe Hands (`tracker.py`) para mantener la aplicación independiente del framework de seguimiento.

- **`src/core/`**
  - Configuración de la aplicación.
  - Umbrales médicos (`config.py`).

- **`src/main.py`**
  - Orquestador principal.
  - Renderizado y visualización en tiempo real.

---

## 🧪 Testing

El proyecto incluye una suite completa de pruebas unitarias que cubre matemáticas vectoriales 3D, estructuras de datos y casos límite (por ejemplo, fallos de hardware).

Para ejecutar toda la suite de pruebas, simplemente ejecuta el corredor de pruebas global:

```bash
python run_tests.py
```
--- 

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/digital-goniometer.git
cd digital-goniometer
```

### 2. Crear y activar un entorno virtual

#### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install opencv-python==4.9.0.80 mediapipe==0.10.9 numpy==1.26.3
```

---

## 🎮 Uso

Ejecuta la aplicación principal:

```bash
python src/main.py
```

Después:

1. Selecciona cuántas articulaciones deseas monitorizar.
2. Elige el dedo y la articulación específica (por ejemplo, **MEÑIQUE → PIP**).
3. Coloca la mano frente a la cámara web.
4. Realiza los ejercicios de flexión.
5. Si el sistema detecta compensación mediante rotación de la muñeca, mostrará una alerta **CHEATING!**.
6. Presiona **Q** o cierra la ventana para salir.

---

Desarrollado para **rehabilitación clínica** e **investigación en Edge AI**.