# Telegram Cash Game Bot with Ollama LLM

A cash game betting bot for Telegram (like poker cash games) that calculates fair settlement of bets between participants using Ollama (local LLM) agent reasoning (with deterministic fallback).

## Features

- **Cash Game Model**: Users can join/leave at any time, like poker cash games
- **Dynamic Betting**: No fixed betting phases - betting is always open
- **Partial Settlements**: Users can declare winnings and leave while others continue playing
- **Rejoin Support**: Users can rejoin after leaving with new bets
- **Local LLM Settlement**: Uses Ollama (Gemma/Llama) to reason about fair settlement, with fallback to deterministic algorithm
- **Transaction Generation**: Produces minimal settlement transactions (no circular payments)
- **Persistent Storage**: SQLite database stores groups, bets, winners, and transactions
- **Async/Await**: Full async support for Telegram API and Ollama calls
- **Zero External Dependencies**: Run fully locally without cloud APIs

## Architecture

```
Telegram Bot ──► Group Manager ──► Settlement Logic ──► Ollama (Local LLM)
                     (state)            (deterministic)    (agent reasoning)
                  (SQLite)           (fallback)
```

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

1. **Telegram Handler** (`bot/telegram_handler.py`): Processes `/bet`, `/settle`, `/winner` commands
2. **Group Manager** (`bot/group_manager.py`): Tracks groups, participants, bets, winners
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
- **`b <amount>`** - Place a bet (e.g., `b 50`) - or just send a number like `50`
- **`w <username> <prize>`** - Record winnings when user leaves (e.g., `w ron 150`)
- **`s`** - Calculate settlements (can be done anytime)
- **`sts`** - Show current group status with in/out tracking
- **`t`** - Show settlement transactions
- **`u`** - Remove the last bet placed
- **`r`** - Reset all bets (empty the pot)

**Quick Betting**: Simply send a number (e.g., `50` or `100`) to place a bet. The bot automatically uses your Telegram display name (first name + last name, or username if set).

### Example Workflow

```
1. Group chat initialized: str
2. User 1: 50 (just send the number)
3. User 2: 100
4. User 3: 50
5. User 2 leaves: w user2 150 (User 2 wins $150 and leaves)
6. User 1 adds more: 50 (can add money anytime)
7. User 3 leaves: w user3 75 (User 3 wins $75 and leaves)
8. Calculate: s
   ✅ Output: Settlement transactions
      - User 1 → User 2: $50.00
      - User 1 → User 3: $25.00
```

## Settlement Algorithm

### Ollama LLM Agent

The Ollama LLM receives a structured prompt with bets and winners, and reasons about fair settlement:

**Input:**
```
Participants:
- User 1 (Alice): bet $50
- User 2 (Bob): bet $100
- User 3 (Carol): bet $50

Winners:
- User 2 (Bob): won $150
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

1. Compute net positions: `balance = prize - bet`
2. Separate debtors and creditors
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
    Participant(1, "Alice", Decimal("50"), False, Decimal("0")),
    Participant(2, "Bob", Decimal("100"), True, Decimal("150")),
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
