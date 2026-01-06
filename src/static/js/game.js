/**
 * Memory Game - Client-side game logic and UI management.
 * Handles card flipping, match detection, animations, and player management.
 */

// Animation timing constants (milliseconds)
const REVEAL_TIME = 5000;      // Duration to display matched pair
const FLIP_TIME = 600;         // Card flip animation duration
const EXPAND_DELAY = 1000;     // Delay before expansion animation starts
const FADE_OUT_TIME = 300;     // Expanded view fade-out duration
const ZOOM_HOLD_TIME = 2500;   // Time to hold zoom on mismatch
const ZOOM_DURATION = 800;     // Zoom in/out animation duration

/**
 * Centralized game state - single source of truth.
 * @type {Object}
 */
let gameState = {
    cards: [],                 // Card values (indices into images array)
    images: [],                // Image filenames from server
    matched: [],               // Positions of successfully matched cards
    currentPlayer: 1,          // Active player (1 or 2)
    boardWidth: 6,             // Grid columns
    boardHeight: 5,            // Grid rows
    selectedCards: [],         // Currently selected card positions (max 2)
    isWaiting: false,          // Prevents clicks during animations
    gameOver: false,           // Blocks input after game ends
    player1Name: 'Spieler 1',  // Player 1 display name
    player2Name: 'Spieler 2'   // Player 2 display name
};

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', initGame);

/**
 * Initialize game session: fetch configuration and start board.
 */
function initGame() {
    // Reset player names to defaults for new game
    gameState.player1Name = 'Spieler 1';
    gameState.player2Name = 'Spieler 2';
    document.getElementById('p1-name').textContent = 'Spieler 1';
    document.getElementById('p2-name').textContent = 'Spieler 2';

    // Check if we're continuing a crop flow (coming back from crop tool)
    const urlParams = new URLSearchParams(window.location.search);
    const isContinuing = urlParams.has('continue');
    
    // If not continuing from crop flow, reset to start fresh game
    const initPromise = isContinuing 
        ? Promise.resolve() 
        : fetch('/api/game/reset', { method: 'POST' }).then(r => r.json());
    
    initPromise
        .then(() => fetch('/api/game/init', { method: 'POST' }))
        .then(r => r.json())
        .then(data => {
            console.log('Game init response:', data);
            if (data.status === 'pending_crops') {
                // Redirect to crop tool for first image (no need to hide overlay)
                console.log('Redirecting to crop tool for:', data.pending_image);
                window.location.href = `/crop/${data.pending_image}`;
                return;
            }
            gameState.boardWidth = data.board_width;
            gameState.boardHeight = data.board_height;
            gameState.images = data.images;
            console.log('Game ready with', gameState.images.length, 'images');
            // Hide loading overlay only after game is ready
            document.getElementById('loading-overlay').classList.add('hidden');
            loadBoard();
        })
        .catch(e => {
            console.error('Failed to initialize game:', e);
            document.getElementById('loading-overlay').classList.add('hidden');
        });
}

/**
 * Fetch current board state from server.
 */
function loadBoard() {
    fetch('/api/game/board')
        .then(r => {
            console.log('Board fetch response status:', r.status, 'ok:', r.ok);
            console.log('Board response headers:', r.headers);
            const text = r.text();
            console.log('Board response text promise:', text);
            return text.then(text => {
                console.log('Board response text content:', text);
                if (!r.ok) {
                    console.error('Board request failed with status:', r.status);
                    throw new Error(`HTTP ${r.status}: ${text}`);
                }
                try {
                    const json = JSON.parse(text);
                    console.log('Board parsed JSON:', json);
                    return json;
                } catch (e) {
                    console.error('Failed to parse JSON:', e, 'text was:', text);
                    throw e;
                }
            });
        })
        .then(data => {
            console.log('Board data after parsing:', data);
            if (data.error) {
                console.error('Board error:', data.error);
                return;
            }
            if (!data || !data.cards || data.cards.length === 0) {
                console.error('Board returned empty cards:', data);
                return;
            }
            gameState.cards = data.cards;
            gameState.matched = data.matched;
            gameState.currentPlayer = data.current_player;
            console.log('Rendering board with', gameState.cards.length, 'cards, matched:', gameState.matched);
            renderBoard();
            updateScoreboard(data.player1_pairs, data.player2_pairs);
            updatePlayerIndicator();
        })
        .catch(e => console.error('Failed to load board:', e));
}

/**
 * Render game board with dynamic grid layout.
 */
function renderBoard() {
    const boardEl = document.getElementById('game-board');
    boardEl.innerHTML = '';
    boardEl.style.gridTemplateColumns = `repeat(${gameState.boardWidth}, 1fr)`;

    gameState.cards.forEach((_, pos) => {
        const cardEl = document.createElement('div');
        cardEl.className = 'card';
        cardEl.dataset.index = pos;
        cardEl.innerHTML = '<div class="card-front"></div>';

        if (gameState.matched.includes(pos)) {
            cardEl.classList.add('matched');
        }

        cardEl.addEventListener('click', () => selectCard(pos, cardEl));
        boardEl.appendChild(cardEl);
    });
}

/**
 * Handle card selection and flip animation.
 * @param {number} pos - Card position index
 * @param {HTMLElement} cardEl - Card DOM element
 */
function selectCard(pos, cardEl) {
    // Prevent interaction during animations or after game ends
    if (gameState.isWaiting || gameState.gameOver) return;
    if (gameState.matched.includes(pos)) return;
    if (gameState.selectedCards.includes(pos)) return;

    gameState.selectedCards.push(pos);
    cardEl.classList.add('selected');

    const cardValue = gameState.cards[pos];
    const imageFile = gameState.images[cardValue];

    if (!imageFile) {
        console.error('Invalid card value:', cardValue);
        return;
    }

    // Flip animation with image load
    cardEl.style.transform = 'scaleX(0)';
    setTimeout(() => {
        const imgUrl = `/img/${imageFile}`;
        console.log(`Card ${pos}: Loading image from ${imgUrl} (imageFile: ${imageFile}, cardValue: ${cardValue})`);
        const imgElement = document.createElement('img');
        imgElement.src = imgUrl;
        imgElement.alt = 'Card';
        imgElement.style.cssText = 'width: 100%; height: 100%; object-fit: cover; border-radius: 8px; border: 4px solid #4CAF50; box-sizing: border-box;';
        imgElement.onerror = function() {
            console.error(`Failed to load image: ${imgUrl}`);
        };
        imgElement.onload = function() {
            console.log(`Successfully loaded image: ${imgUrl}`);
        };
        cardEl.innerHTML = '';
        cardEl.appendChild(imgElement);
        cardEl.classList.add('flipped');
        cardEl.style.transform = 'scaleX(1)';
    }, FLIP_TIME / 2);

    // Check for match when both cards selected
    if (gameState.selectedCards.length === 2) {
        gameState.isWaiting = true;
        setTimeout(() => checkMatch(), FLIP_TIME);
    }
}

/**
 * Send card pair to server for match validation.
 */
function checkMatch() {
    const [idx1, idx2] = gameState.selectedCards;

    fetch(`/api/game/check/${idx1}/${idx2}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.is_match) {
                handleMatchLogic(idx1, idx2, data);
            } else {
                handleNonMatchLogic(idx1, idx2);
            }
        })
        .catch(e => console.error('Match check failed:', e));
}

/**
 * Handle successful card match: show expansion, vanish cards.
 * @param {number} idx1 - First card index
 * @param {number} idx2 - Second card index
 * @param {Object} data - Server response with match data
 */
/**
 * Handle successful card match: show expansion, vanish cards.
 * @param {number} idx1 - First card index
 * @param {number} idx2 - Second card index
 * @param {Object} data - Server response with match data
 */
function handleMatchLogic(idx1, idx2, data) {
    if (!data.image1 || !data.image2) {
        console.error('Missing images in match response');
        gameState.selectedCards = [];
        gameState.isWaiting = false;
        return;
    }

    setTimeout(() => {
        // For a match, both image1 and image2 should be the same
        // Display the matched image twice
        const matchedImage = data.image1;
        showExpandedView(matchedImage, matchedImage);

        setTimeout(() => {
            hideExpandedView();

            // Vanish matched cards with animation
            const card1 = document.querySelector(`[data-index="${idx1}"]`);
            const card2 = document.querySelector(`[data-index="${idx2}"]`);

            [card1, card2].forEach(card => {
                if (card) {
                    card.style.transform = 'scale(1)';
                    card.classList.remove('selected', 'flipped', 'shrinking');
                    void card.offsetWidth; // Force reflow
                    card.classList.add('matched');
                    card.style.animation = '';
                }
            });

            // Update game state
            addToStack(matchedImage, data.current_player);
            updateScoreboard(data.player1_pairs, data.player2_pairs);
            gameState.currentPlayer = data.current_player;
            gameState.matched = data.matched_indices;
            updatePlayerIndicator();

            if (data.game_over) {
                showGameOver(data);
            }

            gameState.selectedCards = [];
            gameState.isWaiting = false;
        }, REVEAL_TIME);
    }, EXPAND_DELAY);
}

/**
 * Handle mismatched cards: zoom effect, flip back.
 * @param {number} idx1 - First card index
 * @param {number} idx2 - Second card index
 */
function handleNonMatchLogic(idx1, idx2) {
    const card1 = document.querySelector(`[data-index="${idx1}"]`);
    const card2 = document.querySelector(`[data-index="${idx2}"]`);
    const container = document.querySelector('.container');

    // Calculate zoom center between cards
    if (card1 && card2) {
        const rect1 = card1.getBoundingClientRect();
        const rect2 = card2.getBoundingClientRect();
        const centerX = (rect1.left + rect1.right + rect2.left + rect2.right) / 4;
        const centerY = (rect1.top + rect1.bottom + rect2.top + rect2.bottom) / 4;

        const containerRect = container.getBoundingClientRect();
        const originX = ((centerX - containerRect.left) / containerRect.width) * 100;
        const originY = ((centerY - containerRect.top) / containerRect.height) * 100;

        container.style.transformOrigin = `${originX}% ${originY}%`;
    }

    // Zoom magnifying glass animation
    void container.offsetWidth; // Force reflow
    container.classList.add('zoom-in');

    setTimeout(() => {
        container.classList.remove('zoom-in');
        container.classList.add('zoom-out');

        setTimeout(() => {
            container.classList.remove('zoom-out');
            container.style.transformOrigin = 'center center';

            setTimeout(() => {
                flipCardBack(card1);
                flipCardBack(card2);

                // Fetch updated state after flip animation
                fetch('/api/game/board')
                    .then(r => r.json())
                    .then(data => {
                        gameState.currentPlayer = data.current_player;
                        updateScoreboard(data.player1_pairs, data.player2_pairs);
                        updatePlayerIndicator();
                        gameState.selectedCards = [];
                        gameState.isWaiting = false;
                    })
                    .catch(e => console.error('Failed to load board:', e));
            }, FLIP_TIME / 2);
        }, ZOOM_DURATION);
    }, ZOOM_HOLD_TIME);
}

/**
 * Flip card back to face-down state.
 * @param {HTMLElement} cardEl - Card element to flip
 */
function flipCardBack(cardEl) {
    if (!cardEl) return;

    cardEl.classList.remove('selected', 'shrinking');
    cardEl.style.animation = 'none';
    cardEl.style.transform = 'scale(1)';

    setTimeout(() => {
        cardEl.style.transform = 'scaleX(0)';

        setTimeout(() => {
            cardEl.innerHTML = '<div class="card-front"></div>';
            cardEl.style.transform = 'scaleX(1)';

            setTimeout(() => {
                cardEl.classList.remove('flipped');
            }, FLIP_TIME / 2);
        }, FLIP_TIME / 2);
    }, 10);
}

/**
 * Display matched pair with growth animation.
 * @param {string} image1 - First image filename
 * @param {string} image2 - Second image filename
 */
function showExpandedView(image1, image2) {
    const expandedView = document.getElementById('expanded-view');
    const img1 = document.getElementById('expanded-card1');
    const img2 = document.getElementById('expanded-card2');

    if (!expandedView || !img1 || !img2) {
        console.error('Expanded view elements not found');
        return;
    }

    img1.src = `/img/${image1}`;
    img2.src = `/img/${image2}`;

    expandedView.classList.remove('show');
    void expandedView.offsetWidth; // Force reflow
    expandedView.classList.add('show');
}

/**
 * Hide expanded view with fade-out animation.
 */
function hideExpandedView() {
    const expandedView = document.getElementById('expanded-view');
    if (!expandedView) return;

    expandedView.classList.add('fade-out');
    setTimeout(() => {
        expandedView.classList.remove('show', 'fade-out');
    }, FADE_OUT_TIME);
}

/**
 * Add matched image to player's score stack.
 * @param {string} imageName - Image filename
 * @param {number} player - Player number (1 or 2)
 */
function addToStack(imageName, player) {
    const stackId = player === 1 ? 'p1-stack' : 'p2-stack';
    const stackEl = document.getElementById(stackId);

    const matchEl = document.createElement('div');
    matchEl.className = 'matched-card';
    matchEl.innerHTML = `<img src="/img/${imageName}" alt="Matched card" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;">`;
    matchEl.style.background = player === 1 ? '#FFD700' : '#FF6B6B';

    stackEl.appendChild(matchEl);
}

/**
 * Update score display with proper German grammar.
 * @param {number} p1Pairs - Player 1 matched pairs
 * @param {number} p2Pairs - Player 2 matched pairs
 */
function updateScoreboard(p1Pairs, p2Pairs) {
    const formatScore = (pairs) => `${pairs} ${pairs === 1 ? 'Paar' : 'Paare'}`;
    document.getElementById('p1-score').textContent = formatScore(p1Pairs);
    document.getElementById('p2-score').textContent = formatScore(p2Pairs);
}

/**
 * Update active player indicator.
 */
function updatePlayerIndicator() {
    const p1Ind = document.getElementById('p1-indicator');
    const p2Ind = document.getElementById('p2-indicator');
    const p1El = document.querySelector('.player1');
    const p2El = document.querySelector('.player2');

    if (gameState.currentPlayer === 1) {
        p1Ind.textContent = '👉';
        p2Ind.textContent = '';
        p1El.classList.add('active');
        p2El.classList.remove('active');
    } else {
        p1Ind.textContent = '';
        p2Ind.textContent = '👉';
        p1El.classList.remove('active');
        p2El.classList.add('active');
    }
}

/**
 * Display game-over modal with winner using actual player names.
 * @param {Object} data - Game result data from server
 */
function showGameOver(data) {
    gameState.gameOver = true;

    const p1Name = gameState.player1Name;
    const p2Name = gameState.player2Name;
    const winnerNameEl = document.getElementById('winner-name');
    const winnerTextEl = document.getElementById('winner-text');

    if (data.player1_pairs > data.player2_pairs) {
        winnerNameEl.textContent = p1Name;
        winnerTextEl.textContent = `${p1Name} hat alle Paare gefunden!`;
    } else if (data.player2_pairs > data.player1_pairs) {
        winnerNameEl.textContent = p2Name;
        winnerTextEl.textContent = `${p2Name} hat alle Paare gefunden!`;
    } else {
        winnerNameEl.textContent = 'Unentschieden!';
        winnerNameEl.style.fontSize = '2.5rem';
        winnerTextEl.textContent = `${p1Name} und ${p2Name} haben gleich viele Paare gefunden!`;
    }

    document.getElementById('game-over-modal').classList.add('show');
}

/**
 * Display goodbye modal.
 */
function showGoodbye() {
    document.getElementById('game-over-modal').classList.remove('show');
    document.getElementById('goodbye-modal').classList.add('show');
}

/**
 * Navigate to home page.
 */
function goHome() {
    window.location.href = '/';
}

/**
 * Reset game state and restart.
 */
function resetGame() {
    fetch('/api/game/reset', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
            gameState.selectedCards = [];
            gameState.isWaiting = false;
            gameState.gameOver = false;
            document.getElementById('p1-stack').innerHTML = '';
            document.getElementById('p2-stack').innerHTML = '';
            document.getElementById('game-over-modal').classList.remove('show');
            hideExpandedView();
            // Show loading overlay and reinitialize with new images
            document.getElementById('loading-overlay').classList.remove('hidden');
            initGame();
        })
        .catch(e => console.error('Failed to reset game:', e));
}

/**
 * Edit player name on double-click.
 * @param {number} playerNum - Player number (1 or 2)
 */
function editPlayerName(playerNum) {
    const nameEl = document.getElementById(`p${playerNum}-name`);
    const currentName = nameEl.textContent;

    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentName;
    input.maxLength = 20;
    Object.assign(input.style, {
        fontSize: '1.5rem',
        fontWeight: '700',
        padding: '0.3rem 0.8rem',
        border: '2px solid #4CAF50',
        borderRadius: '8px',
        textAlign: 'center',
        width: '80%'
    });

    nameEl.innerHTML = '';
    nameEl.appendChild(input);
    input.focus();
    input.select();

    const saveName = () => {
        const newName = input.value.trim() || currentName;
        nameEl.textContent = newName;
        // Store in gameState for use in winner announcement
        if (playerNum === 1) {
            gameState.player1Name = newName;
        } else {
            gameState.player2Name = newName;
        }
    };

    input.addEventListener('blur', saveName);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveName();
    });
}

/**
 * Load saved player names from localStorage.
 */
function loadPlayerNames() {
    for (let i = 1; i <= 2; i++) {
        const savedName = localStorage.getItem(`player${i}Name`);
        if (savedName) {
            document.getElementById(`p${i}-name`).textContent = savedName;
        }
    }
}
