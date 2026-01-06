# 🎮 Memory Game

A vibrant, kid-friendly memory matching game built with Flask and vanilla JavaScript. Play with a friend and test your memory skills!

## Features

- 👥 **Two-Player Gameplay**: Take turns matching pairs
- ✏️ **Editable Player Names**: Customize player names by double-clicking
- 🎨 **Smooth Animations**: Polished card flip, match reveal, and zoom effects
- 📱 **Responsive Grid**: Multiple board sizes (2×2, 4×3, 6×5)
- 🏆 **Score Tracking**: Real-time pair count and winner announcement
- 🎭 **Vibrant UI**: Colorful design optimized for younger players

## How to Play

1. **Start the Game**: Open the application in your web browser
2. **Name Your Players** (Optional): Double-click on "Spieler 1" or "Spieler 2" to edit custom names
3. **Take Turns**: Players alternate clicking on cards to reveal images
4. **Match Pairs**: When you flip two cards:
   - If they match: Both cards vanish with a smooth animation, and you score a point
   - If they don't match: A magnifying glass zoom effect highlights the mismatch, then cards flip back
5. **Win**: Continue playing until all pairs are matched. The player with the most matched pairs wins!

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. **Clone/Download** the repository:
   ```bash
   cd memory
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv myenvwin
   ```

3. **Activate Virtual Environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\myenvwin\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     myenvwin\Scripts\activate.bat
     ```
   - **macOS/Linux**:
     ```bash
     source myenvwin/bin/activate
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

1. **Start the Flask Server**:
   ```bash
   python src/app.py
   ```

2. **Open in Browser**: Navigate to `http://localhost:8080`

3. **Play**: Start matching pairs with your opponent!

## Game Configuration

Edit `config.json` to customize board sizes:

```json
{
  "grid": "2x2",
  "gridOptions": {
    "2x2": {"width": 2, "height": 2},
    "4x3": {"width": 4, "height": 3},
    "6x5": {"width": 6, "height": 5}
  }
}
```

Select a grid option by changing the `"grid"` value. Board sizes adjust dynamically.

## Adding Images

Place image files in the `img/` folder. 

**Requirements:**
- **Minimum 15 images**: To support the largest board size (6×5 grid = 15 pairs)
- **Any format**: Images can be square or rectangular
- **Supported formats**: PNG, JPG, JPEG, GIF, WebP

**Image Processing:**
- Images are randomly selected for each game (k = board_width × board_height ÷ 2)
- **Already square images**: If an image is already square (width = height), it's copied directly to `img/squared/` without cropping. This preserves image quality and avoids unnecessary processing.
- **_square.jpg versions**: When you crop a non-square image, a "_square.jpg" version is saved to the `img/squared/` subfolder. Original images remain untouched.
- **Smart selection**: Game prefers using existing "_square.jpg" versions to avoid re-cropping the same image
- **Non-square images without _square versions**: When detected, the game opens an interactive crop tool before gameplay starts
- **Crop Tool**: Displays the largest possible square within the image and lets you drag it to choose the best crop region
- **Caching**: Images are cached after initial load to minimize filesystem access

Example: After cropping `photo.jpg`, a `photo_square.jpg` is created in the `img/squared/` folder for future use. If you add a square image like `portrait.jpg`, it's automatically copied to `img/squared/portrait_square.jpg`.

The game selects images randomly (sorted alphabetically as tie-breaker). For example:
- 2×2 grid: Randomly chooses 2 images
- 4×3 grid: Randomly chooses 6 images
- 6×5 grid: Randomly chooses 15 images

**Tip**: Use high-quality images at least 200×200 pixels for sharp display on cards. The game will scale them appropriately.

## Image Management & Cropping

### Automatic Processing
The game intelligently processes images to ensure they display correctly as square cards:

1. **Square images** (width = height):
   - Automatically copied to `img/squared/` folder on first selection
   - No cropping needed, preserves full image quality
   - Crop tool **never appears** for these images

2. **Non-square images** (width ≠ height):
   - Trigger the interactive crop tool when first selected
   - Player chooses the desired crop area
   - Cropped version saved to `img/squared/` with `_square.jpg` suffix

### No Re-cropping on Restart
Once an image is processed and saved to `img/squared/`:
- ✅ **Future games** reuse the squared version automatically
- ✅ **Server restarts** don't re-trigger cropping
- ✅ **New game sessions** skip already-processed images
- The crop tool only appears for genuinely new (non-squared) images

### File Organization Example
```
img/
├── vacation.jpg           (original, non-square)
├── portrait.jpg           (original, already square)
├── landscape.png          (original, non-square)
└── squared/
    ├── vacation_square.jpg    (player cropped)
    ├── portrait_square.jpg    (auto-copied)
    └── landscape_square.jpg   (player cropped)
```

### Performance with Large Libraries
- Efficiently handles 1000+ images
- Only selected k images are checked for processing (not all n)
- Squared images are cached to avoid redundant checks
- Optimized random selection ensures fast game initialization

## Project Structure

```
memory/
├── src/
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Configuration management
│   ├── crop_service.py        # Image cropping and validation
│   ├── routes/
│   │   └── game.py            # Game API endpoints
│   ├── templates/
│   │   ├── game.html          # Main game template
│   │   └── crop_tool.html     # Interactive crop tool
│   └── static/
│       ├── css/
│       │   └── style.css      # Styling and animations
│       └── js/
│           └── game.js        # Client-side game logic
├── img/                       # Original and cropped images
├── config.json                # Game configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: Vanilla JavaScript, CSS3
- **Animations**: CSS Keyframes
- **State Management**: Server-side session management

## Customization

### Player Names
Double-click any player name in the scoreboard to edit it. Names persist during the current game session.

### Colors & Styling
Edit `src/static/css/style.css` to customize:
- Card colors and borders
- Animation timing
- Player indicator colors
- Button styles

### Animation Timing
Adjust timing constants in `src/static/js/game.js`:
- `REVEAL_TIME`: How long matched pairs stay visible (5000ms)
- `FLIP_TIME`: Card flip animation duration (600ms)
- `EXPAND_DELAY`: Delay before showing expanded view (1000ms)
- `ZOOM_HOLD_TIME`: How long to zoom on mismatch (2500ms)

## Troubleshooting

**Game not loading?**
- Ensure Flask server is running on `localhost:8080`
- Check that no other application is using port 8080
- Clear browser cache if styling looks incorrect

**Images not showing?**
- Verify image files are in the `img/` folder
- Ensure filenames contain only standard characters
- Check that image formats are supported (PNG, JPG, GIF, WebP)

**Names not appearing?**
- Names reset when starting a new game
- Double-click player names to ensure changes are saved

**Crop tool not appearing?**
- Ensure Pillow is installed: `pip install -r requirements.txt`
- Check that non-square images are in the `img/` folder
- Reload the page if the crop tool doesn't display

## Disclaimer

This project was **entirely generated by GitHub Copilot** to showcase its capabilities in code generation and software development. While functional, it is provided as-is without warranty. Users assume all responsibility for its use. This is an educational and demonstration project, not production-ready software.

## License

Personal use only. Designed for educational and recreational purposes.

## Author

**Gerhard Mitterlechner**

Generated with GitHub Copilot to showcase AI-assisted development capabilities.
