# LUDO Frontend - Quick Reference

## File Organization

```
static/ludo/
├── css/game.css              # All styling
├── js/
│   ├── board.js              # Board coordinate system  
│   ├── animations.js         # Animation engine
│   ├── websocket.js          # WebSocket manager
│   ├── ui.js                 # UI components
│   └── game.js               # Main orchestrator
├── images/ludo-board.svg     # Game board
└── sounds/                   # Audio files (to be added)

templates/ludo/game.html      # Main template
```

---

## Key Classes & Methods

### LudoBoard
```javascript
new LudoBoard()
  .getCoordinates(color, position)           // Get piece coordinates
  .renderToken(pieceId, color, position)     // Place token
  .moveToken(pieceId, color, newPos, ms)     // Animate movement
  .setValidMoves(tokenIds)                   // Highlight valid moves
  .clearAllTokens()                          // Clear board
```

### LudoAnimations
```javascript
new LudoAnimations(board)
  .animateTokenMove(id, from, to, ms)        // Piece movement
  .animateDiceRoll(diceElements, ms)         // Dice animation
  .animateCapture(pieceId, ms)               // Capture effect
  .animateVictory(ms)                        // Victory effect
  .playSound(type)                           // Play audio
```

### LudoWebSocket
```javascript
new LudoWebSocket(gameId, onUpdate, onError)
  .connect()                                 // Connect to server
  .send(type, data)                          // Send message
  .rollDice()                                // Request roll
  .moveToken(tokenIndex)                     // Request move
  .on(eventType, handler)                    // Listen for events
  .getConnectionState()                      // Get connection info
```

### LudoUI
```javascript
ludoUI
  .showNotification(msg, type, duration)     // Show toast
  .updatePlayerCard(color, data)             // Update player
  .setActivePlayer(color)                    // Highlight player
  .showVictoryOverlay(color, name)           // Victory screen
  .setControlsEnabled(enabled)               // Enable/disable UI
  .showLoadingSpinner(msg)                   // Show spinner
```

### LudoGame
```javascript
window.ludoGame
  .init()                                    // Initialize game
  .board                                     // Board instance
  .animations                                // Animation instance
  .websocket                                 // WebSocket instance
  .gameState                                 // Current game state
  .isMyTurn                                  // Is it my turn?
  .validMoves                                // Available moves
```

---

## Common Tasks

### Display a Notification
```javascript
ludoUI.showNotification('Roll a 6!', 'info', 2000);
ludoUI.showNotification('Error!', 'error', 3000);
ludoUI.showNotification('Success!', 'success', 2000);
```

### Update Player Display
```javascript
ludoUI.updatePlayerCard('red', {
  username: 'Alice',
  connected: true,
  timer: 15000,
  tokens: [2, 5, 10, -1]
});
```

### Animate Token Movement
```javascript
const board = window.ludoGame.board;
const fromCoord = board.getCoordinates('red', 5);
const toCoord = board.getCoordinates('red', 12);

await board.animations.animateTokenMove(
  'red-token-0',
  fromCoord,
  toCoord,
  400  // 400ms duration
);
```

### Handle WebSocket Events
```javascript
window.ludoGame.websocket.on('dice_rolled', (data) => {
  console.log('Dice:', data.dice_value);
});

window.ludoGame.websocket.on('token_moved', (data) => {
  console.log('Token moved:', data);
});
```

### Send Commands to Server
```javascript
window.ludoGame.websocket.rollDice();
window.ludoGame.websocket.moveToken(0);
window.ludoGame.websocket.passTurn();
```

---

## CSS Classes

### For Styling
```css
.ludo-game-container    /* Main container */
.board-wrapper          /* Board wrapper */
.tokens-layer           /* Token layer */
.dice                   /* Dice button */
.player-card            /* Player card */
.player-card.active     /* Active player */
.notification           /* Toast notification */
.modal-overlay          /* Modal dialog */
.btn.btn-primary        /* Primary button */
.btn.btn-secondary      /* Secondary button */
```

### For Animation States
```css
.token.valid-move       /* Valid move highlight */
.dice.rolling           /* Dice rolling */
.player-status-indicator.connected  /* Connected status */
```

---

## Debug Helpers

### Check Connection Status
```javascript
window.ludoGame.websocket.getConnectionState()
// Returns: { isConnected, readyState, pendingMessages }
```

### Check Game State
```javascript
console.log(window.ludoGame.gameState)
console.log(window.ludoGame.isMyTurn)
console.log(window.ludoGame.validMoves)
```

### Force Reconnect
```javascript
window.ludoGame.websocket.close();
await window.ludoGame.websocket.connect();
```

### List All Tokens
```javascript
window.ludoGame.board.pieces  // Map of all tokens
```

### Manual Render
```javascript
window.ludoGame.board.renderGameState(stateObject)
```

---

## WebSocket Message Format

### Send Roll Dice
```json
{ "type": "roll_dice" }
```

### Send Move Token
```json
{ "type": "move_token", "token_index": 0 }
```

### Send Get State
```json
{ "type": "get_game_state" }
```

### Receive Game State
```json
{
  "type": "game_state",
  "state": {
    "players": { ... },
    "current_turn": 0,
    "dice": [5]
  }
}
```

---

## CSS Variables

Change theme with CSS variables:

```css
:root {
  --color-red: #ef4444;
  --color-blue: #3b82f6;
  --color-green: #22c55e;
  --color-yellow: #eab308;
  
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  
  --transition-base: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Performance Tips

1. **Use translate3d**: Always use `transform: translate3d()` for animations
2. **Batch Updates**: Group multiple updates into single render
3. **Event Delegation**: Attach event listeners to parent elements
4. **Lazy Load**: Use `loading="lazy"` for images
5. **Throttle Events**: Limit event frequency to 60fps max

---

## Testing

### Check Board Rendering
```javascript
// In console
window.ludoGame.board.pieces  // Should have tokens
```

### Simulate Piece Movement
```javascript
window.ludoGame.board.renderToken('red-token-0', 'red', 5);
```

### Simulate WebSocket Event
```javascript
window.ludoGame.websocket.handleMessage(JSON.stringify({
  type: 'dice_rolled',
  dice_value: 6
}));
```

---

## Keyboard Shortcuts

In browser console:

```javascript
// Quick access
g = window.ludoGame
b = window.ludoGame.board
a = window.ludoGame.animations
w = window.ludoGame.websocket
u = window.ludoUI

// Debug
g.gameState
w.getConnectionState()
b.pieces.size
```

---

## Common Errors

| Error | Solution |
|-------|----------|
| "Cannot read property 'board'" | Game not initialized yet, wait for init() |
| "WebSocket connection failed" | Check WebSocket URL and server configuration |
| "Token not found" | Verify token ID format: `{color}-token-{index}` |
| "Styles not loading" | Run `python manage.py collectstatic` |
| "Animations choppy" | Check browser performance, reduce effect count |

---

## Resources

- **Main Docs**: `LUDO_FRONTEND_REFACTOR.md`
- **Integration Guide**: `LUDO_INTEGRATION_GUIDE.md`
- **CSS**: `static/ludo/css/game.css`
- **Template**: `casino_app/ludo/templates/ludo/game.html`

---

Last Updated: 2026-05-11
Version: 1.0
