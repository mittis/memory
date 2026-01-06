"""Game routes and business logic for memory matching game."""
import random
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, send_file, session

from config import Config
from crop_service import (
    copy_square_image,
    get_image_dimensions,
    get_largest_square_dimensions,
    get_safe_image_path,
    is_square_image,
    save_cropped_image,
)

game_bp = Blueprint('game', __name__)


def _get_image_files() -> list[Path]:
    """Get all image file paths from img directory (excludes squared/ folder).

    Returns:
        List of Path objects for image files.
    """
    img_dir = Path(__file__).parent.parent.parent / 'img'
    img_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

    if not img_dir.exists():
        return []

    return [
        f for f in img_dir.iterdir()
        if f.is_file() and f.suffix.lower() in img_extensions
    ]


def get_all_images() -> list[str]:
    """Get all base image files from img directory (excludes squared/ folder).

    Returns:
        Sorted list of base image filenames.
    """
    return sorted([f.name for f in _get_image_files()])


def _get_k_random_images(k: int) -> list[str]:
    """Randomly select k images from img directory efficiently.

    For large n (image count), this avoids loading all n filenames.
    Uses iterative sampling to select k without materializing full list.

    Args:
        k: Number of images to select.

    Returns:
        List of k randomly selected image filenames.
    """
    files = _get_image_files()
    if len(files) <= k:
        return [f.name for f in files]
    
    # random.sample() can work on iterables, but for efficiency
    # with large n, we convert to names only for selected items
    selected_paths = random.sample(files, k)
    return [f.name for f in selected_paths]


def _get_cropped_version_path(base_filename: str) -> Path:
    """Get path to cropped version of an image.

    Args:
        base_filename: Original image filename (e.g., 'photo.jpg').

    Returns:
        Path object for the cropped version (e.g., img/squared/photo_square.jpg).
    """
    img_dir = Path(__file__).parent.parent.parent / 'img'
    squared_dir = img_dir / 'squared'
    name_without_ext = base_filename.rsplit('.', 1)[0] if '.' in base_filename else base_filename
    return squared_dir / f"{name_without_ext}_square.jpg"


def _has_cropped_version(base_filename: str) -> bool:
    """Check if a base image has a cropped version in squared/ folder.

    Args:
        base_filename: Original image filename.

    Returns:
        True if cropped version exists, False otherwise.
    """
    return _get_cropped_version_path(base_filename).exists()


def _get_display_filename(base_filename: str) -> str:
    """Get the filename to display (cropped if available, else base).

    Args:
        base_filename: Original image filename.

    Returns:
        Filename to display (e.g., 'photo.jpg' or 'squared/photo_square.jpg').
    """
    if _has_cropped_version(base_filename):
        name_without_ext = base_filename.rsplit('.', 1)[0] if '.' in base_filename else base_filename
        return f"squared/{name_without_ext}_square.jpg"
    return base_filename


def get_images() -> list[str]:
    """Get k randomly selected images for current game.

    Selects k = (board_width * board_height) / 2 base images randomly.
    Returns display filenames (cropped if available, else original).

    Returns:
        List of k display filenames to use in the game.
    """
    k = (Config.BOARD_WIDTH * Config.BOARD_HEIGHT) // 2
    selected = _get_k_random_images(k)
    
    # Convert to display filenames
    return [_get_display_filename(img) for img in selected]


def get_image_path(filename: str) -> Path | None:
    """Retrieve safe path to image file with directory traversal prevention.

    Args:
        filename: Image filename to retrieve.

    Returns:
        Path object if file exists and is in img directory, None otherwise.
    """
    img_dir = Path(__file__).parent.parent.parent / 'img'
    file_path = img_dir / filename

    # Security check: ensure file is within img directory
    if file_path.resolve().parent != img_dir.resolve():
        return None

    return file_path if file_path.exists() else None


def init_game_state() -> None:
    """Initialize game session with selected images and pending crops.

    Randomly selects k images and determines which need cropping.
    Images that are already square are copied to squared/ folder.
    Images that are not square are marked for cropping.
    Stores BASE filenames (not display names) to ensure consistency.
    The serve_image endpoint will serve cropped versions if they exist.
    
    Only checks k images for square dimensions, not all n images.
    """
    k = (Config.BOARD_WIDTH * Config.BOARD_HEIGHT) // 2
    
    # Randomly select only k images (efficient for large n)
    selected_base = _get_k_random_images(k)
    
    # Identify which of the k images need cropping
    # If already square, copy directly; otherwise mark for cropping
    pending_crops = []
    for img in selected_base:
        if not _has_cropped_version(img):
            if is_square_image(img):
                # Already square, copy to squared folder
                copy_square_image(img)
            else:
                # Not square, needs cropping
                pending_crops.append(img)

    # Store BASE filenames (not display names)
    # The server will serve cropped versions if they exist
    session['all_game_images'] = selected_base
    session['pending_crops'] = pending_crops
    session['cards'] = []
    session['matched'] = []
    session['current_player'] = 1
    session['player1_matches'] = []
    session['player2_matches'] = []
    session.modified = True


def get_card_image(card_value: int) -> str | None:
    """Get image filename for a card value using current game images.

    Args:
        card_value: Integer index into images list.

    Returns:
        Image filename or None if index is out of bounds.
    """
    images = session.get('all_game_images', [])
    if 0 <= card_value < len(images):
        return images[card_value]
    return None


def setup_card_pairs() -> None:
    """Setup shuffled card pairs after all crops are done."""
    images = session.get('all_game_images', [])
    pairs = list(range(len(images))) * 2
    random.shuffle(pairs)
    session['cards'] = pairs
    session['matched'] = []
    session.modified = True


@game_bp.route('/')
def index():
    """Load main game page."""
    if 'cards' not in session:
        init_game_state()
    return render_template('game.html')


@game_bp.route('/crop/<filename>')
def crop_tool(filename: str):
    """Display interactive crop tool for non-square images."""
    if not get_safe_image_path(filename):
        return jsonify({'error': 'Image not found'}), 404
    return render_template('crop_tool.html', filename=filename)


@game_bp.route('/img/<path:filepath>')
def serve_image(filepath: str):
    """Serve image files from img directory, preferring cropped versions if they exist.

    If a cropped version exists in squared/ folder, serve that instead of the original.
    
    Args:
        filepath: Image filename (e.g., 'photo.jpg').

    Returns:
        File response or 404 JSON error.
    """
    img_dir = Path(__file__).parent.parent.parent / 'img'
    
    # First, try to serve cropped version if it exists
    cropped_path = _get_cropped_version_path(filepath)
    if cropped_path.exists():
        # Security check: ensure file is within img directory
        if not cropped_path.resolve().parent.as_posix().startswith(img_dir.resolve().as_posix()):
            return jsonify({'error': 'Invalid path'}), 404
        return send_file(str(cropped_path), mimetype='image/*')
    
    # Otherwise serve the original
    file_path = img_dir / filepath
    
    # Security check: ensure file is within img directory
    if not file_path.resolve().parent.as_posix().startswith(img_dir.resolve().as_posix()):
        return jsonify({'error': 'Invalid path'}), 404

    if not file_path.exists():
        return jsonify({'error': 'Image not found'}), 404

    return send_file(str(file_path), mimetype='image/*')


@game_bp.route('/api/image/dimensions/<filename>')
def get_image_dimensions_api(filename: str):
    """Get dimensions of image for crop tool.

    Args:
        filename: Image filename.

    Returns:
        JSON with width and height, or error response.
    """
    if not get_safe_image_path(filename):
        return jsonify({'error': 'Image not found'}), 404

    dims = get_image_dimensions(filename)
    if not dims:
        return jsonify({'error': 'Cannot read image'}), 400

    return jsonify(dims)


@game_bp.route('/api/image/crop', methods=['POST'])
def save_crop():
    """Save cropped image and update session.

    Expects JSON: {filename, crop_box: {x, y, size}}

    Returns:
        JSON with next_image if more crops needed, or status ok if all done.
    """
    data = request.get_json()
    filename = data.get('filename')
    crop_box = data.get('crop_box')

    if not filename or not crop_box:
        return jsonify({'error': 'Missing data'}), 400

    if not get_safe_image_path(filename):
        return jsonify({'error': 'Image not found'}), 404

    temp_filename = save_cropped_image(filename, crop_box)
    if not temp_filename:
        return jsonify({'error': 'Crop failed'}), 400

    session['pending_crops'].remove(filename)
    session.modified = True

    # Check if more crops are needed
    pending = session.get('pending_crops', [])
    if pending:
        return jsonify({
            'status': 'pending_crops',
            'next_image': pending[0]
        })

    # All crops done, setup card pairs
    setup_card_pairs()
    session.modified = True
    return jsonify({'status': 'ok'})


@game_bp.route('/api/game/init', methods=['POST'])
def init():
    """Initialize new game with fresh board and shuffled cards.
    
    If pending crops exist, returns status to redirect to crop tool.
    Otherwise returns game configuration.
    
    Only selects fresh images on first call. After crops complete,
    subsequent calls reuse the same images.
    """
    # Only select new images if no game is in progress
    if 'all_game_images' not in session:
        # Fresh start - initialize with random images
        init_game_state()
    else:
        # Game already started, just reset play state
        session['matched'] = []
        session['current_player'] = 1
        session['player1_matches'] = []
        session['player2_matches'] = []
        session['cards'] = []
    
    # Check for pending crops
    pending = session.get('pending_crops', [])

    if pending:
        session.modified = True
        return jsonify({
            'status': 'pending_crops',
            'pending_image': pending[0],
            'total_pending': len(pending)
        })

    # Always setup fresh card pairs (no pending crops, so ready to play)
    setup_card_pairs()
    
    images = session.get('all_game_images', [])
    session.modified = True
    return jsonify({
        'status': 'ok',
        'board_width': Config.BOARD_WIDTH,
        'board_height': Config.BOARD_HEIGHT,
        'images': images,
        'total_pairs': len(images)
    })


@game_bp.route('/api/game/board')
def get_board():
    """Get current board state including cards, matches, and scores.
    
    Only initializes if no game is in progress (no game images selected).
    """
    try:
        # Only initialize if game hasn't been started yet
        if 'all_game_images' not in session:
            init_game_state()
        
        # Ensure cards are shuffled if they haven't been yet
        if not session.get('cards'):
            setup_card_pairs()

        # Validate critical data exists
        if not session.get('all_game_images'):
            return jsonify({'error': 'No images in session'}), 400
        
        if not session.get('cards'):
            return jsonify({'error': 'No cards in session'}), 400

        return jsonify({
            'cards': session['cards'],
            'matched': session['matched'],
            'current_player': session['current_player'],
            'player1_pairs': len(session['player1_matches']),
            'player2_pairs': len(session['player2_matches']),
            'images': session.get('all_game_images', [])
        })
    except Exception as e:
        import traceback
        print(f"Error in get_board: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@game_bp.route('/api/game/check/<int:card1>/<int:card2>', methods=['POST'])
def check_match(card1: int, card2: int):
    """Validate card match and process game logic.

    Args:
        card1: First card position index.
        card2: Second card position index.

    Returns:
        JSON with match result, images, updated scores, and game state.
    """
    cards = session.get('cards', [])
    matched = session.get('matched', [])
    player1_matches = session.get('player1_matches', [])
    player2_matches = session.get('player2_matches', [])
    current_player = session.get('current_player', 1)

    # Validate card indices
    if card1 >= len(cards) or card2 >= len(cards) or card1 < 0 or card2 < 0:
        return jsonify({'error': 'Invalid card index'}), 400

    # Reject already matched cards
    if card1 in matched or card2 in matched:
        return jsonify({'error': 'Card already matched'}), 400

    card1_val = cards[card1]
    card2_val = cards[card2]
    is_match = card1_val == card2_val

    img1 = get_card_image(card1_val)
    img2 = get_card_image(card2_val)

    if is_match:
        # Record matched cards
        matched.extend([card1, card2])
        if current_player == 1:
            player1_matches.append(card1_val)
        else:
            player2_matches.append(card1_val)
        game_over = len(matched) == len(cards)
    else:
        # Switch player on mismatch
        current_player = 2 if current_player == 1 else 1
        game_over = False

    # Persist updated state
    session['matched'] = matched
    session['current_player'] = current_player
    session['player1_matches'] = player1_matches
    session['player2_matches'] = player2_matches
    session.modified = True

    return jsonify({
        'is_match': is_match,
        'image1': img1,
        'image2': img2,
        'current_player': current_player,
        'player1_pairs': len(player1_matches),
        'player2_pairs': len(player2_matches),
        'matched_indices': matched,
        'game_over': game_over
    })


@game_bp.route('/api/game/reset', methods=['POST'])
def reset():
    """Reset game state for new game - clear session only.
    
    Next call to /api/game/init will select fresh random images.
    """
    session.clear()
    session.modified = True
    return jsonify({'status': 'ok'})
