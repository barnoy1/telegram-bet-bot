# Telegram Cash Game Bot with Ollama LLM

A cash game betting bot for Telegram (like poker cash games) that calculates fair settlement of bets between participants using Ollama (local LLM) agent reasoning (with deterministic fallback).

## Features

- **Cash Game Model**: Users can join/leave at any time, like poker cash games
- **Dynamic Betting**: No fixed betting phases - betting is always open
- **Simplified Betting**: Just send a number to place a bet - no command prefix needed
- **Easy Exit**: Users leave with "out <amount>" command (pot validated)
- **Auto-Settlement**: Settlement calculated automatically after every action
- **Rejoin Support**: Users can rejoin after leaving with new bets
- **Local LLM Settlement**: Uses Ollama (Gemma/Llama) to reason about fair settlement, with fallback to deterministic algorithm
- **Transaction Generation**: Produces minimal settlement transactions (no circular payments)
- **Persistent Storage**: SQLite database stores groups, bets, and transactions
- **Async/Await**: Full async support for Telegram API and Ollama calls
- **Zero External Dependencies**: Run fully locally without cloud APIs

## Architecture

```
Telegram Bot ──► Message Handler ──► Service Layer ──► Storage
                     (Numeric/Out)      (Business Logic)      (SQLite)
                           │                  │
                           │                  ▼
                           │          Settlement Engine (Auto-trigger)
                           │          (After each action)
                           │                  │
                           └──────────────────┘
                              (Immediate feedback)
                                   │
                                   ▼
                           Ollama (Local LLM)
                           (deterministic fallback)
```

### SOLID Principles Applied

**Single Responsibility Principle (SRP):**
- Each command handler has one responsibility (e.g., BetCommand, WinnerCommand)
- Formatters separated from business logic (status_formatter, settlement_formatter)
- Services focused on specific domains (GroupService, ParticipantService, etc.)

**Open/Closed Principle (OCP):**
- New commands can be added without modifying existing handlers
- Command registry enables dynamic handler registration
- Interfaces allow alternative implementations

**Dependency Inversion Principle (DIP):**
- Handlers depend on service interfaces, not concrete implementations
- Factories handle dependency injection
- Services depend on storage abstraction

### Multi-Group Support

The bot is designed to work in multiple independent Telegram groups simultaneously. Each group operates as its own "room" with isolated state:

- **One Brain, Many Rooms**: The bot instance serves multiple groups, each with its own memory
- **Per-Group State**: Each group is identified by its Telegram `group_id` and has independent bets, winners, and settlements
- **No Shared State**: Groups don't interfere with each other - all data is isolated by `group_id` in SQLite
- **Automatic Scaling**: Telegram handles message routing, so no special infrastructure is needed for multi-group support

**How it works:**
1. Add the bot to any Telegram group
2. Type `/start` to initialize the group
3. Each group maintains its own betting state independently
4. The bot can be in unlimited groups simultaneously

### Core Components

1. **Telegram Handler** (`bot/telegram_handler.py`): Processes numeric messages, out command, and manages auto-settlement
2. **Service Layer** (`bot/services/`): Business logic for groups, participants, transactions, and settlement
3. **Settlement Calculator** (`settlement/calculator.py`): Deterministic settlement algorithm
4. **Ollama Agent** (`settlement/ollama_agent.py`): Uses Ollama for local LLM-based reasoning
5. **Storage** (`db/storage.py`): SQLite persistence

## Setup

### Prerequisites

- Python 3.8+
- Telegram Bot Token (create via @BotFather)
- Ollama installed and running (http://localhost:11434)
- Ollama model (e.g., `gemma:7b`, `llama2:7b`)

### Quick Start

1. **Start Ollama server:**
   ```bash
   ollama serve
   # In another terminal:
   ollama pull gemma:7b
   ```

2. **Setup the bot:**
   ```bash
   cd agent-bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your Telegram token
   python main.py
   ```

3. **Add to Telegram:**
   - Find your bot via @BotFather username
   - Add it to a group
   - Type `/start` to initialize

## Usage

### Bot Commands

- **`str`** - Initialize bot in a group
- **`h`** - Show all available commands
- **Numeric messages** (e.g., `50`, `100`) - Automatically place a bet using your display name
- **`out <amount>`** - Leave game with specified amount (max = current pot)
- **`t`** - Show settlement transactions
- **`u`** - Remove the last bet placed
- **`r`** - Reset all bets (empty the pot)

**Quick Betting**: Simply send a number (e.g., `50` or `100`) to place a bet. No command prefix needed. The bot automatically uses your Telegram display name (first name + last name, or username if set). Settlement is calculated automatically after each action.

### Example Workflow

```
1. Group chat initialized: str
2. User 1: 50 (just send the number)
   ✅ Auto-settlement runs (User 1: -$50)
3. User 2: 100
   ✅ Auto-settlement runs (User 1: -$50, User 2: -$100)
4. User 3: 50
   ✅ Auto-settlement runs (User 1: -$50, User 2: -$100, User 3: -$50)
5. User 2 leaves: out 150 (User 2 takes $150 from pot)
   ✅ Auto-settlement runs immediately
      Output: User 1 → User 2: $50.00
              User 3 → User 2: $50.00
6. User 1 adds more: 50 (can add money anytime)
   ✅ Auto-settlement runs
7. User 3 leaves: out 75 (User 3 takes $75 from pot)
   ✅ Auto-settlement runs immediately
      Output: User 1 → User 3: $25.00
```

## Settlement Algorithm

### Auto-Triggered Settlement

Settlement is automatically calculated after every action (bet placement or "out" command). This ensures users always know the current state without manual intervention.

### Ollama LLM Agent

The Ollama LLM receives a structured prompt with bets and exits, and reasons about fair settlement:

**Input:**
```
Participants:
- User 1 (Alice): bet $50, status: in
- User 2 (Bob): bet $100, status: out, took $150
- User 3 (Carol): bet $50, status: in
```

**Agent Output (JSON):**
```json
[
  {"from_user_id": 1, "to_user_id": 2, "amount": 50.00},
  {"from_user_id": 3, "to_user_id": 2, "amount": 50.00}
]
```

### Deterministic Fallback

If Ollama is unavailable or timeout occurs, the bot uses a greedy settlement algorithm:

1. Compute net positions: `balance = (amount taken when out) - bet_amount`
2. Separate debtors (negative balance) and creditors (positive balance)
3. Match greedily: largest debtor pays largest creditor
4. Result: minimal transactions, no circular payments

Both approaches guarantee the same outcome: fair, minimal settlement with no circular payments.

## Configuration

Edit `.env`:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma:7b
DATABASE_PATH=./betting_bot.db
LOG_LEVEL=INFO
```

### Supported Ollama Models

Any Ollama model works, but text-based reasoning works best:
- `gemma:7b` (fast, good reasoning) ⭐ Recommended
- `llama2:7b` (powerful, slower)
- `mistral:7b` (fast, good reasoning)

Pull a model:
```bash
ollama pull gemma:7b
```

## Development & Testing

### Run Tests

```bash
pytest tests/ -v
```

All 8 tests for settlement logic pass:
- Empty groups
- Single winner/loser
- Multi-way splits
- Fractional amounts
- Circular payment detection
- Decimal precision

### Smoke Test

```python
from settlement.calculator import SettlementCalculator
from db.storage import Participant
from decimal import Decimal

participants = [
    Participant(1, "Alice", Decimal("50"), "in", Decimal("0")),
    Participant(2, "Bob", Decimal("100"), "out", Decimal("150")),
]
result = SettlementCalculator.calculate_settlement(participants)
print(result)  # [(1, 'Alice', 2, 'Bob', Decimal('50'))]
```

## Troubleshooting

**Bot not responding:**
- Verify `TELEGRAM_BOT_TOKEN` in `.env` is correct
- Bot must be added to group with message permissions

**Ollama connection failed:**
- Ensure Ollama is running: `ollama serve` (default: http://localhost:11434)
- Check `OLLAMA_BASE_URL` in `.env`
- Verify model is downloaded: `ollama list`

**Settlement timeout:**
- Increase `OLLAMA_TIMEOUT_SECONDS` in config.py
- Use faster model (Gemma is faster than Llama2)
- Bot will fallback to deterministic calculator automatically

**Settlement calculation error:**
- Check logs: set `LOG_LEVEL=DEBUG`
- Verify total prizes don't exceed total pot
- Deterministic fallback always works as backup

## Performance

- **Ollama LLM**: ~500ms-2s (depends on model + hardware)
- **Deterministic Fallback**: <1ms
- **Telegram Response**: Instant, shows processing status

## License

MIT

## Contributing

Pull requests welcome! Focus areas:
- Additional settlement strategies
- Support for more Ollama models
- Web interface for group management
- Integration with payment systems
