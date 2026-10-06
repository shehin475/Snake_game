# Nokia Snake with Gesture Control

A desktop Snake game controlled with hand movements through a webcam. The game uses Pygame for its window and MediaPipe/OpenCV for gesture detection.

## Requirements

- Windows
- Python 3.11 (recommended; the pinned MediaPipe version has been verified with this version)
- A working webcam

The exact Python package versions are pinned in [`requirements.txt`](requirements.txt).

## Setup

Open PowerShell in the project folder and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you already have a broken `.venv`, remove that environment before recreating it:

```powershell
Remove-Item -Recurse -Force .venv
```

If PowerShell blocks virtual-environment activation, you can install and run with the environment's Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

To verify that the installed MediaPipe package includes the API used by the game:

```powershell
python -c "import mediapipe as mp; print(mp.__version__, hasattr(mp, 'solutions'))"
```

The expected output is `0.10.21 True`.

## Run

With the virtual environment activated:

```powershell
python main.py
```

The game opens a Pygame window and a separate webcam window showing hand tracking.

## Download a Windows release

Windows builds are published on the [GitHub Releases page](https://github.com/shehin475/Snake_game/releases).
Download and extract `NokiaSnake-Windows.zip`, then run `NokiaSnake.exe`. The game
still requires a working webcam and permission to use it.

To publish a new release, push a version tag such as `v1.0.0`. GitHub Actions
builds the Windows executable and attaches it to a GitHub Release automatically.

## Controls

- Move your hand to swipe up, down, left, or right to steer the snake.
- Pinch your thumb and index finger to activate the speed boost.
- The game filters small tracking jitters; if the hand leaves the frame, direction tracking resets until it is detected again.
- After game over, swipe your hand upward to restart. Move the hand clearly in the camera view; a held-up hand pose is not enough.
- Press **Esc** in the game window or **Q** in the webcam window to quit.

## Webcam permissions and troubleshooting

- If the camera cannot be opened, close other apps using it and check Windows **Settings > Privacy & security > Camera**. Allow camera access and access for desktop apps.
- Make sure the intended Python environment is active before installing dependencies or starting the game. Check with `python --version`; it should report Python 3.11.
- If you see `module 'mediapipe' has no attribute 'solutions'`, confirm the environment uses `mediapipe==0.10.21` and reinstall from the pinned requirements:

  ```powershell
  python -m pip install --force-reinstall -r requirements.txt
  ```

- If NumPy reports incompatible or missing compiled files, recreate the virtual environment using the Python 3.11 commands in the Setup section, then reinstall the requirements.
