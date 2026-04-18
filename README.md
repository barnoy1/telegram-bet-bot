# Telegram Betting Bot with Copilot SDK

A group betting bot for Telegram that calculates fair settlement of bets between participants using Copilot SDK agent reasoning (with deterministic fallback).

## Features

- **Group Betting**: Create betting groups in Telegram and track participant bets
- **Winner Declaration**: Admin declares winners and prize distributions
- **Intelligent Settlement**: Uses GitHub Copilot SDK to reason about fair settlement, with fallback to deterministic algorithm
- **Transaction Generation**: Produces minimal settlement transactions (no circular payments)
- **Persistent Storage**: SQLite database stores groups, bets, winners, and transactions
- **Async/Await**: Full async support for Telegram API and Copilot SDK calls

## Architecture

```
Telegram Bot ──► Group Manager ──► Settlement Logic ──► Copilot SDK
                    (state)            (deterministic)    (agent reasoning)
                 (SQLite)           (fallback)
```

### Core Components

1. **Telegram Handler** (`bot/telegram_handler.py`): Processes `/bet`, `/settle`, `/winner` commands
2. **Group Manager** (`bot/group_manager.py`): Tracks groups, participants, bets, winners
3. **Settlement Calculator** (`settlement/calculator.py`): Deterministic settlement algorithm
4. **Copilot Agent** (`settlement/copilot_agent.py`): Uses Copilot SDK for agent-based reasoning
5. **Storage** (`db/storage.py`): SQLite persistence

## Setup

### Prerequisites

- Python 3.8+
- Telegram Bot Token (create via @BotFather)
- GitHub account (for Copilot authentication)
- Copilot CLI installed or available in PATH

### Installation

1. **Clone/extract the project:**
   ```bash
   cd agent-bot
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram token and Copilot credentials
   ```

5. **Run the bot:**
   ```bash
   python main.py
   ```

## Usage

### Bot Commands

- **`/start`** - Initialize bot in a group
- **`/bet <amount>`** - Place a bet (e.g., `/bet 50`)
- **`/close`** - Close the betting phase (admin only)
- **`/winner <user_id> <prize>`** - Declare a winner (e.g., `/winner 123456789 150`)
- **`/settle`** - Calculate settlements and generate transaction table
- **`/status`** - Show current group status (participants, bets, winners)
- **`/transactions`** - Show settlement transactions from last settlement

### Example Workflow

1. Group chat initialized with `/start`
2. User 1: `/bet 50`
3. User 2: `/bet 100`
4. User 3: `/bet 50`
5. Admin: `/close` (betting ends)
6. Admin: `/winner 2 150` (User 2 wins $150)
7. Admin: `/settle` → Bot outputs settlement table:
   - User 1 → User 2: $50.00
   - User 3 breaks even (no payment)

## Settlement Algorithm

### Deterministic Calculator

1. **Compute net positions**: For each participant, `prize - bet` = their balance
2. **Separate**: Debtors (negative balance) and creditors (positive balance)
3. **Greedy matching**: Pair largest debtor with largest creditor, settle, repeat
4. **Result**: Minimal transactions with no circular payments

### Copilot Agent

The Copilot agent receives a structured prompt with all bets and winners, and reasons about fair settlement:

```
Participants: [Alice: $50 bet, Bob: $100 bet, Carol: $50 bet]
Winners: [Bob: $150 prize]
→ Copilot outputs: [{from: Alice, to: Bob, amount: 50}, ...]
```

If Copilot is unavailable or times out, the bot silently falls back to the deterministic calculator.

## Configuration

Edit `.env` or environment variables:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
COPILOT_CLI_PATH=/path/to/copilot/cli    # or just 'copilot' if in PATH
COPILOT_AUTH_TOKEN=your_github_token
DATABASE_PATH=./betting_bot.db
LOG_LEVEL=INFO
```

## Development & Testing

### Run Tests

```bash
pytest tests/ -v
```

### Test Settlement Logic

```python
from settlement.calculator import SettlementCalculator
from db.storage import Participant

participants = [
    Participant(1, "Alice", Decimal("50"), False, Decimal("0")),
    Participant(2, "Bob", Decimal("100"), True, Decimal("150")),
]
transactions = SettlementCalculator.calculate_settlement(participants)
print(transactions)  # [(1, "Alice", 2, "Bob", Decimal("50"))]
```

## Limitations & Future Work

- **Single bot instance**: Designed for single deployment; horizontal scaling requires state coordination
- **Precision**: Amounts rounded to 2 decimal places (USD/EUR/etc.)
- **Copilot optional**: Bot works without Copilot SDK; agent reasoning is enhancement, not requirement
- **No persistence across restarts** (for group state): Group records persist, but active betting sessions reset

## Troubleshooting

**Bot not responding to commands:**
- Verify `TELEGRAM_BOT_TOKEN` is correct in `.env`
- Check bot is added to the group with correct permissions

**Copilot not initializing:**
- Check `COPILOT_CLI_PATH` points to valid CLI executable
- Verify GitHub credentials are correct
- Bot will fallback to deterministic calculator automatically

**Settlement calculation errors:**
- Review logs: `LOG_LEVEL=DEBUG` for verbose output
- Check total prizes don't exceed total pot

## License

MIT
