# Telegram Betting Bot with Copilot SDK Integration

## Problem Statement

Build a Telegram-based betting group assistant that:
1. Allows multiple users to join a betting group and place bets
2. Collects bet amounts from participants
3. Accepts results/winners and prize distributions
4. Uses **Copilot SDK agent capabilities** to calculate settlement logic (who owes whom)
5. Generates a transaction table showing money flows between participants

Core logic: Given bets and winners, compute a settlement matrix ensuring no circular payments and minimal transactions.

## Architecture Approach

```
Telegram Bot ──→ Betting Group Manager ──→ Copilot SDK Client ──→ Copilot CLI
                     (session/state)           (settlement logic)
                                           (uses agent reasoning)
```

### High-Level Design

1. **Telegram Interface** (python-telegram-bot or similar)
   - `/bet` - User joins group and posts amount
   - `/results` - Admin posts winner and prize distribution
   - `/settle` - Trigger settlement calculation via Copilot

2. **Betting Group Manager** (in-memory or lightweight DB)
   - Track active groups, participants, bets
   - Maintain state across Telegram messages

3. **Copilot Settlement Agent**
   - Receive: participant bets, winner list with prizes
   - Output: settlement transactions (A→B: $X)
   - Implementation: Define custom tool for settlement math, or use agent reasoning to derive optimal settlement

4. **Data & Persistence**
   - Group data: SQLite or lightweight JSON store
   - Telegram session tokens: env vars
   - Copilot credentials: env vars

## Technical Stack

- **Language**: Python (aligns with Copilot SDK Python implementation)
- **Telegram**: `python-telegram-bot` async library
- **Copilot SDK**: `copilot` Python package
- **State**: SQLite (groups, bets, transactions) or in-memory for MVP
- **Orchestration**: asyncio for concurrent Telegram + Copilot operations

## Key Files to Create

```
project/
├── main.py                    # Telegram bot entry point
├── bot/
│   ├── __init__.py
│   ├── telegram_handler.py    # Command handlers (/bet, /results, /settle)
│   └── group_manager.py       # Track groups, participants, bets
├── settlement/
│   ├── __init__.py
│   ├── copilot_agent.py       # Copilot SDK client wrapper for settlement
│   └── calculator.py          # Fallback deterministic settlement logic
├── db/
│   ├── __init__.py
│   └── storage.py             # SQLite or in-memory models
├── config.py                  # Environment, Copilot auth, Telegram token
├── requirements.txt           # Dependencies
└── .env.example               # Secrets template
```

## Major Todos (Tracked in SQL)

1. **Setup & Infrastructure**
   - Initialize project structure
   - Setup Copilot SDK Python client (authenticate, verify CLI available)
   - Setup Telegram bot registration and token handling

2. **Telegram Bot Core**
   - Build command handlers (/start, /bet, /results, /settle)
   - Implement group + participant state management
   - Handle async message flow

3. **Copilot Integration**
   - Create Copilot session for settlement reasoning
   - Design settlement calculation as custom tool or agent prompt
   - Implement fallback deterministic calculator (in case agent doesn't work)

4. **Settlement Logic**
   - Copilot agent analyzes: {bets: {user: amount}, winners: {user: prize}}
   - Computes minimal settlement transactions
   - Returns formatted transaction table to Telegram

5. **Testing & Polish**
   - Unit tests for settlement calculations
   - E2E test with Telegram sandbox
   - Error handling and retry logic for Copilot calls

## Key Decisions

### Copilot vs. Deterministic Settlement Math
- **Copilot approach**: Let agent reason about fair settlement (flexible, learns edge cases)
- **Deterministic approach**: Implement optimal settlement algorithm (faster, reproducible)
- **Decision**: Start with Copilot, provide deterministic fallback for reliability

### State Management
- **In-memory (MVP)**: Simple, no deps, resets on bot restart
- **SQLite (production)**: Persistent, queryable, 1 file
- **Decision**: SQLite from start (minimal overhead, prevents data loss)

### Multi-User Concurrency
- Use asyncio for Telegram + Copilot calls
- Copilot SDK handles process/session lifecycle
- Lock bet collection window (admin sets when to close bets)

## Success Criteria

- [x] Users can join a group via Telegram and place bets
- [x] Admin can declare winners and prize amounts
- [x] Bot calls Copilot agent to compute settlement
- [x] Settlement table shows all transactions needed
- [x] No circular payments (A→B→C→A) in output
- [x] Deployed and testable via Telegram

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Copilot SDK not in environment | Provide setup instructions; fallback to deterministic calc |
| Telegram API delays | Implement timeouts, retry logic |
| Copilot agent hallucination on math | Validate output; deterministic fallback |
| State loss on bot restart | Use SQLite persistence |
| High latency on settlement | Cache agent session; optimize prompts |

## Next Steps (After Plan Approval)

1. Run `todo list` to confirm task breakdown
2. Start with project setup (dependencies, config)
3. Build Telegram handlers (quick wins for feedback)
4. Integrate Copilot SDK (core logic)
5. Test end-to-end
