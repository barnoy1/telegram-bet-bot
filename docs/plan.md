# Telegram Cash Game Bot with Ollama LLM Integration

## Problem Statement

Build a Telegram-based cash game betting assistant (like poker cash games) that:
1. Allows multiple users to join a betting group and place bets
2. Users can join/leave at any time (no fixed betting phases)
3. Users can declare winnings when they leave (partial settlements)
4. Users can rejoin after leaving with new bets
5. Uses **Ollama LLM agent capabilities** to calculate settlement logic (who owes whom)
6. Generates a transaction table showing money flows between participants

Core logic: Given bets and winnings, compute a settlement matrix ensuring no circular payments and minimal transactions. Settlement can be calculated at any time.

## Architecture Approach

```
Telegram Bot ──→ Betting Group Manager ──→ Settlement Logic ──► Ollama (Local LLM)
                     (state)            (deterministic)    (agent reasoning)
                  (SQLite)           (fallback)
```

### High-Level Design

1. **Telegram Interface** (python-telegram-bot or similar)
   - `str` - Initialize bot in a group
   - `h` - Show all available commands
   - `b <amount>` - Place a bet (or just send a number)
   - Numeric messages (e.g., `50`, `100`) - Automatically placed as bets using display name
   - `w <username> <prize>` - Record winnings when user leaves (marks user as 'out')
   - `u` - Remove the last bet placed
   - `r` - Reset all bets (empty the pot)
   - `s` - Trigger settlement calculation via Ollama (can be done anytime)
   - `sts` - Show current group status with in/out tracking
   - `t` - Show settlement transactions

2. **Betting Group Manager** (SQLite)
   - Track active groups, participants, bets
   - Track user status (in/out) for cash game model
   - **Multi-Group Support**: Each group operates independently with its own state

## Multi-Group Architecture

### Core Concept
The bot operates as "one brain, many rooms" where:
- Each Telegram group is an independent "room" with its own memory
- GroupManager tracks state per `group_id` from Telegram
- SQLite database isolates data by group
- Bot logic is stateless - all state is in the database

### Database Structure
```
groups table:
- group_id (primary key, Telegram chat ID)
- chat_title
- admin_user_id
- created_at

participants table:
- group_id (foreign key)
- user_id
- username
- bet_amount
- is_winner
- prize_amount
```

### Scaling Across Many Small Groups
- **Telegram Native Support**: Telegram API handles routing messages to correct group_id automatically
- **No Special Infrastructure Needed**: Each group operates independently with no shared state
- **Stateless Bot Logic**: Bot processes messages based on group_id, all state persisted in SQLite
- **ACID Guarantees**: SQLite provides transaction integrity for concurrent group operations

### When Bot Joins a New Group
- Bot detects `new_chat_members` event
- Sends welcome message with `/start` instructions
- Group is automatically created in database on first `/start` command

### Implementation Status
- ✅ GroupManager handles per-group state
- ✅ SQLite database structured per group
- ✅ Bot can be added to multiple groups simultaneously
- ⏳ Add new_chat_members handler for automatic welcome messages

3. **Ollama Settlement Agent**
   - Receive: participant bets, winner list with prizes
   - Output: settlement transactions (A→B: $X)
   - Implementation: Use Ollama LLM for agent reasoning, with deterministic fallback

4. **Data & Persistence**
   - Group data: SQLite database
   - Telegram bot token: env vars
   - Ollama connection: env vars (OLLAMA_BASE_URL, OLLAMA_MODEL)

## Technical Stack

- **Language**: Python 
- **Telegram**: `python-telegram-bot` async library
- **Ollama SDK**: `ollama` Python package
- **State**: SQLite (groups, bets, transactions) 
- **Orchestration**: asyncio for concurrent Telegram + Ollama operations

## Key Files

```
project/
├── main.py                    # Telegram bot entry point
├── bot/
│   ├── __init__.py
│   ├── telegram_handler.py    # Command handlers (b, w, s, sts, t, u, r)
│   └── group_manager.py       # Track groups, participants, bets
├── settlement/
│   ├── __init__.py
│   ├── ollama_agent.py        # Ollama LLM client wrapper for settlement
│   └── calculator.py          # Fallback deterministic settlement logic
├── db/
│   ├── __init__.py
│   └── storage.py             # SQLite models with status tracking
├── config.py                  # Environment, Ollama auth, Telegram token
├── requirements.txt           # Dependencies
└── .env.example               # Secrets template
```

## Major Todos

1. **Setup & Infrastructure**
   - Initialize project structure
   - Setup Ollama connection (OLLAMA_BASE_URL, OLLAMA_MODEL)
   - Setup Telegram bot registration and token handling

2. **Telegram Bot Core**
   - Build command handlers (str, b, w, s, sts, t, u, r)
   - Implement group + participant state management with in/out tracking
   - Handle async message flow

3. **Ollama Integration**
   - Create Ollama session for settlement reasoning
   - Design settlement calculation as agent prompt
   - Implement fallback deterministic calculator (in case agent doesn't work)

4. **Settlement Logic**
   - Ollama agent analyzes: {bets: {user: amount}, winners: {user: prize}}
   - Computes minimal settlement transactions (works with in/out status)
   - Returns formatted transaction table to Telegram

5. **Testing & Polish**
   - Unit tests for settlement calculations
   - E2E test with Telegram sandbox
   - Error handling and retry logic for Copilot calls

## Key Decisions

### Ollama vs. Deterministic Settlement Math
- **Ollama approach**: Let agent reason about fair settlement (flexible, learns edge cases)
- **Deterministic approach**: Implement optimal settlement algorithm (faster, reproducible)
- **Decision**: Start with Ollama, provide deterministic fallback for reliability

### State Management
- **In-memory (MVP)**: Simple, no deps, resets on bot restart
- **SQLite (production)**: Persistent, queryable, 1 file
- **Decision**: SQLite from start (minimal overhead, prevents data loss)

### Cash Game Model
- No fixed betting phases - betting is always open
- Users can join/leave at any time
- Users marked "in" or "out" to track participation
- Settlement can be calculated at any point

## Success Criteria

- [x] Users can join a group via Telegram and place bets
- [x] Users can declare winnings and leave at any time
- [x] Bot calls Ollama agent to compute settlement
- [x] Settlement table shows all transactions needed
- [x] No circular payments (A→B→C→A) in output
- [x] Users can rejoin after leaving
- [x] Deployed and testable via Telegram

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Ollama not in environment | Provide setup instructions; fallback to deterministic calc |
| Telegram API delays | Implement timeouts, retry logic |
| Ollama agent hallucination on math | Validate output; deterministic fallback |
| State loss on bot restart | Use SQLite persistence |
| High latency on settlement | Cache agent session; optimize prompts |

## Next Steps

1. Run `todo list` to confirm task breakdown
2. Start with project setup (dependencies, config)
3. Build Telegram handlers (quick wins for feedback)
4. Integrate Ollama SDK (core logic)
5. Test end-to-end
