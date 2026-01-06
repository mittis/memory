# 📸 Image Library

Place your image files in this folder to use them in the memory game.

## Requirements

- **Minimum 15 images** for the 6×5 grid (largest board size)
- **Supported formats**: PNG, JPG, JPEG, GIF, WebP
- **Image quality**: At least 200×200 pixels recommended
- **Square or rectangular**: Both work! Non-square images are automatically cropped

## How It Works

1. **Add images**: Simply copy image files into this directory
2. **Game selection**: The game randomly picks images for each game
3. **Auto-processing**: 
   - Square images are automatically copied to the `squared/` folder
   - Non-square images trigger an interactive crop tool (one time only)
4. **Reuse**: Processed images are saved to `squared/` and never re-cropped

## Examples

```
img/
├── photo1.jpg         ← Your original images
├── photo2.png
├── vacation_pic.jpg
├── portrait.jpg       ← Non-square, crops once
├── landscape.png      ← Non-square, crops once
└── squared/           ← Auto-generated squared versions
    ├── photo1_square.jpg
    ├── portrait_square.jpg
    └── landscape_square.jpg
```

## Tips

- Use high-quality images for sharp display on game cards
- Mix square and rectangular images for variety
- Keep image filenames simple (no special characters)
- Once cropped, images won't trigger the crop tool again
- Works efficiently with 1000+ images!

Enjoy the game! 🎮
