# RPG Maker MV Map Data Structure

Based on the two map files provided, here's a detailed breakdown:

---

## Top-Level Map Properties

| Property | Description |
|---|---|
| `displayName` | Map name shown on screen (e.g., "CHECKPOINT", "HOOKTON VILLAGE") |
| `width` / `height` | Map dimensions in tiles |
| `tilesetId` | Which tileset to use |
| `bgm` / `bgs` | Background music and sounds (name, volume, pitch, pan) |
| `autoplayBgm` / `autoplayBgs` | Whether music/sound starts automatically |
| `battleback1Name` / `battleback2Name` | Battle background images |
| `encounterList` / `encounterStep` | Random encounter settings (empty = no encounters) |
| `disableDashing` | Whether the player can run |
| `specifyBattleback` | Whether to use custom battle backgrounds |
| `parallax*` | Parallax scrolling layer settings |
| `note` | Free-text field for plugin annotations |

---

## The `data` Array

This is a **flat 1D array** representing the tile grid, stored **row by row, left to right, top to bottom**.

- Each value is a **tile ID** referencing the tileset
- `0` = empty/transparent tile
- The array length = `width × height × number_of_layers` (RPG Maker MV uses multiple tile layers stacked)

For example, in the CHECKPOINT map (`width: 17, height: 13`), the data array is `17 × 13 = 221` entries per layer.

---

## The `events` Array

This is the most complex part. The array is indexed by position — `events[0]` is always `null`, and each subsequent index corresponds to an event ID. Events at positions with no event are also `null`.

### Event Object Structure

```
{
  "id": 3,              // Unique event ID
  "name": "Auto",       // Editor name (not shown in-game)
  "note": "",           // Plugin annotation field
  "x": 0,               // Tile X position
  "y": 0,               // Tile Y position
  "pages": [...]        // Array of event pages (the logic)
}
```

### Event Pages

Pages are the core of RPG Maker MV eventing. The engine evaluates pages **from last to first** and runs the **first page whose conditions are met**. This allows conditional behavior.

#### Page Conditions

```json
"conditions": {
  "actorId": 1, "actorValid": false,      // Require specific actor in party?
  "itemId": 1, "itemValid": false,        // Require specific item?
  "selfSwitchCh": "A", "selfSwitchValid": false,  // Self-switch state?
  "switch1Id": 1, "switch1Valid": false,  // Global switch 1?
  "switch2Id": 1, "switch2Valid": false,  // Global switch 2?
  "variableId": 1, "variableValid": false, "variableValue": 0  // Variable check?
}
```

The `*Valid` flags determine whether each condition is active. All active conditions must be true for the page to run.

#### Page Appearance & Behavior

| Property | Description |
|---|---|
| `image` | Sprite: `characterName` (spritesheet), `characterIndex` (which character), `direction` (2=down,4=left,6=right,8=up), `pattern` (frame), `tileId` (tile graphic) |
| `priorityType` | 0=below player, 1=same as player, 2=above player |
| `trigger` | **0**=Action button, **1**=Player touch, **2**=Event touch, **3**=Autorun, **4**=Parallel |
| `moveType` | 0=fixed, 1=random, 2=toward player, 3=custom route |
| `moveSpeed` / `moveFrequency` | Movement parameters (1-6) |
| `stepAnime` / `walkAnime` | Animation settings |
| `through` | Can walk through obstacles? |
| `directionFix` | Does the event face the player? |
| `moveRoute` | Custom movement route definition |

---

## Event Command Codes (`list`)

Each command in the `list` array has:

```json
{ "code": <number>, "indent": <number>, "parameters": [...] }
```

- **`code`**: The command type (see table below)
- **`indent`**: Nesting level (0=top, 1=inside first conditional, 2=inside nested conditional, etc.)
- **`parameters`**: Command-specific arguments

### Key Command Codes

| Code | Name | Parameters | Description |
|---|---|---|---|
| **0** | End | `[]` | Marks end of command list |
| **101** | Show Text | `[faceName, faceIndex, background, position]` | Sets the speaker. Text follows in code 401 |
| **401** | Text Line | `[textString]` | A line of dialogue (follows 101) |
| **102** | Show Choices | `[choices[], default, cancel, position, background]` | Displays choice window |
| **402** | When [Choice] | `[choiceIndex, choiceText]` | Branch for a specific choice |
| **403** | When Cancel | | Branch when cancelled |
| **404** | End Choices | `[]` | Ends the choice block |
| **111** | Conditional Branch | `[type, ...args]` | If/else logic. Type 6=script, 7=gold check |
| **411** | Else | `[]` | Else branch |
| **412** | End Conditional | `[]` | Ends the if/else block |
| **121** | Control Switches | `[startId, endId, value(0=ON/1=OFF)]` | Set global switches |
| **122** | Control Variables | `[startId, endId, operation, operand]` | Set game variables |
| **123** | Control Self Switch | `[ch(A/B/C/D), value]` | Set event's self-switch |
| **125** | Change Gold | `[operation(0=add/1=sub), type, amount]` | Modify party gold |
| **201** | Transfer Player | `[type, mapId, x, y, direction, fade]` | Move player to a location |
| **205** | Set Move Route | `[eventId(-1=player), moveRoute]` | Start a movement sequence |
| **505** | Move Route Param | `[{code, parameters}]` | Part of a move route (sub-command) |
| **230** | Wait | `[frames]` | Pause execution (100 frames ≈ 1.67 seconds) |
| **250** | Play SE | `[{name, volume, pitch, pan}]` | Play sound effect |
| **317** | Change Items | `[type, itemId, operation, amount]` | Add/remove items |
| **355** | Script | `[codeString]` | Execute JavaScript |
| **356** | Plugin Command | `[commandString]` | Call a plugin (e.g., quest system) |

### Move Route Sub-Codes (used in 205/505)

| Code | Description |
|---|---|
| 12 | Move Down |
| 13 | Move Left |
| 14 | Move Right |
| 15 | Move Up |
| 16 | Move Lower Left |
| 17 | Move Lower Right |
| 18 | Move Upper Left |
| 19 | Move Upper Right |
| 29 | Change Speed `[speed]` |
| 36 | Turn Toward Player |
| 42 | Change Opacity `[value]` |
| 43 | Change Blend Mode `[mode]` |

---

## Concrete Examples from the Data

### Example 1: Autorun Event (Event 3 — "Auto" in CHECKPOINT)

- **Trigger: 3** (Autorun — runs immediately when the map loads)
- Starts with a move route for the player (code 205, eventId -1)
- Plays a sound effect (code 250 — "Move1")
- Transfers the player (code 201 — to map 3, coordinates 44,7)
- Contains a full cutscene with dialogue between Claire and guardsmen
- Uses code 102 for a player choice: "(Pay 50 silvers)" vs "(Leave them)"
- Uses code 111 (Conditional Branch) to check if player has enough gold
- Uses code 356 (Plugin Command) for quest system updates like `"Quest 2 Show Objective 3"`
- Uses code 123 to set self-switch "A" (prevents re-running)

### Example 2: Touch-Triggered Guard (Event 6 — "Guards" in CHECKPOINT)

- **Trigger: 1** (Player touch — runs when player walks into the event)
- Shows dialogue, then presents 3 choices: "Pay 40 silver", "Turn back", "Insult them"
- **Pay branch**: Checks gold (code 111 type 7), deducts money (code 125), gives quest update
- **Insult branch**: Sets switch 278 (permanently locks this route), gives +1 Defiance
- Has a **second page** conditioned on switch 278 = ON, which just says "Get out of here!"

### Example 3: Multi-Page Conditional NPC (Event 7 — "Shady Person" in HOOKTON)

- **Page 1**: Default — says "Nothin' to see here"
- **Page 2**: Conditioned on switch 5 = ON — says "Pleasure doin' business with ya"
- This demonstrates how pages create state-dependent NPC behavior

---

## Summary

```
Map
├── Metadata (name, size, music, etc.)
├── data[] (tile grid, flat array)
└── events[]
    └── Event
        ├── Position (x, y)
        └── Pages[]
            ├── Conditions (switches, variables, items, actors)
            ├── Appearance (sprite, priority, trigger)
            ├── Movement (route, speed, type)
            └── Commands[]
                └── { code, indent, parameters }
```

The event system is essentially a **state machine**: conditions select which page is active, and the command list on that page executes sequentially when triggered, with indentation representing nested control flow (conditionals, choices).