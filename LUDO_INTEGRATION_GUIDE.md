# LUDO Frontend Integration Guide

## Quick Start for Backend Integration

### 1. Ensure Template Context Variables

In your Django view (`ludo/views.py`), pass these to the template:

```python
context = {
    'game': game,
    'player_color': player.color,
    'game_id': str(game.id),
    'player_id': player.id,
}
return render(request, 'ludo/game.html', context)
```

### 2. Verify Static Files Configuration

Ensure your `settings.py` has:

```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# For development
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

### 3. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 4. Verify WebSocket Path

The frontend expects WebSocket at:
```
ws://hostname/ws/ludo/{game_id}/
```

Make sure your `routing.py` has the correct pattern.

---

## Template Data Requirements

The game template expects data attributes on the main container:

```django
<div class="ludo-game-container" 
     data-game-id="{{ game.id }}" 
     data-player-color="{{ player_color }}">
```

---

## Game State Structure

The WebSocket consumer should send game state in this format:

```python
{
    'type': 'game_state',
    'state': {
        'players': {
            'red': {
                'tokens': [-1, 5, 12, 30],
                'finished_tokens': 0,
                'username': 'Player1',
                'connected': True,
                'timer': 15000,
                'valid_moves': [
                    {'token_index': 0, 'new_position': 0},
                    {'token_index': 1, 'new_position': 17}
                ]
            },
            'blue': { ... },
            'green': { ... },
            'yellow': { ... }
        },
        'current_turn': 0,  # Index in players object
        'dice': [5],        # Current dice value
        'last_dice_roll': [5],
        'extra_turn': False,
        'captured_this_turn': False
    }
}
```

---

## WebSocket Events the Frontend Expects

### From Server → Frontend

1. **game_state** - Full game state update
   ```json
   {
     "type": "game_state",
     "state": { ... }
   }
   ```

2. **dice_rolled** - Dice roll result
   ```json
   {
     "type": "dice_rolled",
     "dice_value": 5
   }
   ```

3. **token_moved** - Token movement
   ```json
   {
     "type": "token_moved",
     "color": "red",
     "token_index": 0,
     "old_position": -1,
     "new_position": 0
   }
   ```

4. **token_captured** - Piece capture
   ```json
   {
     "type": "token_captured",
     "captured_color": "blue",
     "captured_token_index": 2,
     "capturing_color": "red"
   }
   ```

5. **turn_changed** - Turn switch
   ```json
   {
     "type": "turn_changed",
     "current_turn": 1
   }
   ```

6. **game_finished** - Game end
   ```json
   {
     "type": "game_finished",
     "winner_color": "red",
     "winner_name": "Player1"
   }
   ```

### From Frontend → Server

1. **roll_dice** - Request dice roll
   ```json
   {
     "type": "roll_dice"
   }
   ```

2. **move_token** - Request token movement
   ```json
   {
     "type": "move_token",
     "token_index": 0
   }
   ```

3. **pass_turn** - Request turn pass
   ```json
   {
     "type": "pass_turn"
   }
   ```

4. **get_game_state** - Request current state
   ```json
   {
     "type": "get_game_state"
   }
   ```

---

## Testing the Frontend

### Test 1: Board Rendering
1. Load the game page
2. SVG should display a colorful LUDO board
3. Should be responsive (test at different screen sizes)

### Test 2: WebSocket Connection
1. Open browser console (F12)
2. Should see "WebSocket connected" message
3. Check Network tab → WS for connection

### Test 3: Token Rendering
Make sure your consumer sends game state. Tokens should appear on board.

### Test 4: Notifications
- Trigger an error on server
- Frontend should show notification

### Test 5: Player Cards
- Multiple players should show in player cards
- Current player should be highlighted

---

## Common Issues & Solutions

### Issue: Tokens don't appear on board
**Solution**: Check that game state is being sent from consumer with correct structure

### Issue: Board is blank
**Solution**: Verify SVG file is at `static/ludo/images/ludo-board.svg`

### Issue: WebSocket connection fails
**Solution**: Check WebSocket URL pattern in Django `routing.py`

### Issue: Styles look broken
**Solution**: Run `python manage.py collectstatic`

### Issue: Animations are choppy
**Solution**: Check browser DevTools Performance tab for dropped frames

---

## Important Notes for Backend

1. **Server is Authority**: Frontend doesn't calculate moves or validate anything. Server must do all validation and game logic.

2. **No Offline Support**: Frontend requires active WebSocket connection.

3. **State Sync**: Always send full game state on significant changes.

4. **Reconnection**: Frontend handles reconnection automatically with exponential backoff.

5. **Messages are JSON**: Use `json.dumps()` / `json.loads()` for serialization.

---

## Debugging

### Enable Browser Console
1. Open DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for WebSocket frames

### Check Game Instance
```javascript
// In browser console
console.log(window.ludoGame);        // Main game
console.log(window.ludoUI);          // UI manager
console.log(window.ludoGame.board);  // Board instance
console.log(window.ludoGame.websocket.getConnectionState());
```

### Check Game State
```javascript
console.log(window.ludoGame.gameState);
console.log(window.ludoGame.isMyTurn);
console.log(window.ludoGame.validMoves);
```

---

## Performance Tips

1. **Batch Updates**: Don't send individual events for each animation frame
2. **Compress Messages**: Send minimal JSON
3. **Use Game State**: Leverage full state updates instead of real-time events
4. **Rate Limit**: Don't send updates faster than 60/second

---

## Security Considerations

1. **Validate on Server**: Never trust frontend data
2. **Rate Limit**: Set limits on message frequency
3. **Auth Check**: Verify user is allowed in game room
4. **CSRF**: Use Django CSRF protection for WebSocket

---

## Production Checklist

- [ ] Static files collected
- [ ] WebSocket paths configured
- [ ] Consumer updated with new event types
- [ ] Game state structure matches specification
- [ ] Error handling implemented
- [ ] Reconnection logic tested
- [ ] Performance optimized
- [ ] Sound files added (optional)
- [ ] HTTPS/WSS configured
- [ ] Rate limiting configured

---

## Next Steps

1. Update your consumer to emit the correct events
2. Update your game logic to match new state structure
3. Test WebSocket connection
4. Verify game flow from start to finish
5. Add sound files (optional)
6. Performance test on mobile
7. Deploy to production

---

For questions or issues, refer to the main refactor document: `LUDO_FRONTEND_REFACTOR.md`
