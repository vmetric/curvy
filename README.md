# Curvy for DaVinci Resolve

An interactive, visual easing curve editor for DaVinci Resolve's Fusion page. This tool allows you to visually drag and adjust cubic-bezier curves (just like CSS or After Effects) and apply them directly to your Fusion keyframes.

## Prerequisites

Since this plugin provides a rich graphical interface using Python, you will need the following installed on your computer:

1. **Python 3.6 or newer**
   * Download from [python.org](https://www.python.org/downloads/)
   * **IMPORTANT (Windows):** During installation, make sure to check the box that says **"Add Python to PATH"**.

2. **PySide6**
   * This is the UI framework used to draw the interactive curve editor.
   * Open your Terminal or Command Prompt and run the following command:
     ```bash
     pip install PySide6
     # OR
     python3.exe -m pip install PySide6
     ```

## Installation

You can install this script by dragging and dropping `Curvy.py` into your DaVinci Resolve Scripts folder. 

1. Close DaVinci Resolve if it is currently open.
2. Copy the `Curvy.py` file.
3. Paste it into the appropriate `Comp` scripts folder for your operating system:

* **Windows:**
  `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Comp`
  *(You can paste this path directly into the File Explorer address bar)*

* **macOS:**
  `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Comp`

* **Linux:**
  `~/.local/share/DaVinciResolve/Fusion/Scripts/Comp`

## Usage

1. Open DaVinci Resolve and navigate to the **Fusion Page**.
2. Select a node/tool that already has at least two keyframes animated.
3. From the top menu bar, go to:
   **Workspace** > **Scripts** > **Comp** > **Curvy**
4. The Curvy UI will pop up!
5. Click a visual preset from the grid on the left, or drag the large curve handles on the right to create your custom easing.
   * *Tip: If you want to make an extreme "bounce" or "overshoot" curve and the handles go outside the box, use the **Zoom Graph Out** slider!*
6. Click **"Apply to Selected Tool in Fusion"**.

### Managing Custom Presets

* **Save:** Drag the curve handles to your liking, then click the **💾 Save** button below the presets grid. Enter a name for your preset. It will appear at the bottom of the grid with an orange diamond marker. To update an existing custom preset, just save again with the same name and confirm the overwrite.
* **Overwrite:** Right-click a custom preset and choose **"Overwrite Preset"** to replace its curve with the current one. (You can also use Save with the same name.)
* **Delete:** Right-click a custom preset and choose **"Delete Preset"**. Built-in presets cannot be deleted.

Custom presets are saved to `Curvy_presets.json` in the same folder as the script, so they persist across sessions.

## Troubleshooting

* **The script doesn't show up in the menu:** Ensure you placed it inside the `Comp` folder, not just the root `Scripts` folder.
* **"PySide6 is not installed" error:** Open your command prompt and run `pip install PySide6`. If it says it's already installed, Resolve might be looking at a different Python environment. You can explicitly set your Python executable path in DaVinci Resolve's Preferences > System > General.
* **The curve isn't applying:** Make sure you are on the Fusion page, you have a node actively selected (it has a red border), and that node actually has animated keyframes on it.

Enjoy your smooth, beautiful animations! ❤️

> 💰 **Support this tool**
> This tool cost $8 to make. Donations appreciated to offset the cost! 🙂
> DOGE: DPx2Rxouq7Xc4AJnLB7Dg4hnyYcAYLkGTJ

## Features

* **Visual Presets Grid:** Clickable, dynamically-rendered thumbnails showing exactly what each preset curve looks like.
* **Custom Presets:** Save your own curves as custom presets, edit them later, or delete ones you no longer need. Custom presets are marked with an orange diamond indicator and persist between sessions in a `Curvy_presets.json` file next to the script.
* **Interactive Zoom:** A zoom slider prevents handles from clipping off-screen when creating extreme overshoot effects.
* **Selected Keyframes:** If you drag a selection box over specific keyframes in the Spline Editor, the script will strictly apply the easing between those keyframes. If nothing is selected, it applies to all keyframes on the node.
* **Undo Support:** Fully integrated with DaVinci Resolve's Undo history (`Ctrl+Z`).
* **Resolve Free Support:** Includes robust environment scanning to work reliably within DaVinci Resolve Free's internal scripting engine.
