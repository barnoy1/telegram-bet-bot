# Product Requirements Document: Telegram Bot Redesign - Simplified Betting Flow

## 1. Executive Summary

**Problem Statement**: The current betting flow requires users to remember multiple commands (`b <amount>`, `w <username> <prize>`, `s`, `sts`) and manually trigger settlements, creating friction and cognitive overhead during gameplay.

**Proposed Solution**: Simplify the betting flow to use natural numeric input for betting, a single "out <amount>" command for leaving, and automatic settlement calculation after every action.

**Success Criteria**:
- Reduce command errors by 80% (measured by invalid command rate before/after)
- Settlement latency < 500ms after each action
- User satisfaction score >= 4.5/5 based on post-redesign feedback
- Average game cycle time reduced by 30% (manual settlement trigger eliminated)
- 100% of existing groups can migrate without data loss

## 2. User Experience & Functionality

### User Personas
- **Casual Players**: Friends playing poker/card games who want quick, frictionless betting tracking
- **Game Hosts**: Users who organize games and want accurate settlement calculations without manual intervention

### User Stories

**Story 1: Numeric Betting**
- **As a player**, I want to send just a number (e.g., "50") to place a bet so that I don't have to remember the "b" command prefix.
- **Acceptance Criteria**:
  - Any numeric message (e.g., "50", "100", "25.50") is automatically interpreted as a bet
  - Bot confirms bet placement with user's display name and amount
  - Invalid numbers (negative, zero) are ignored with appropriate feedback
  - Non-numeric text is not interpreted as a bet

**Story 2: Leave Game with "out" Command**
- **As a player**, I want to type "out <amount>" to leave the game with my winnings so that I can exit gracefully without waiting for a settlement phase.
- **Acceptance Criteria**:
  - "out <amount>" command records the player's exit and prize amount
  - Amount cannot exceed current pot (validation error if attempted)
  - Player is marked as "out" in the system
  - Settlement is automatically triggered after the "out" command
  - Player can rejoin by placing new bets after leaving

**Story 3: Automatic Settlement**
- **As a player**, I want settlements to be calculated automatically after every action so that I always know the current state without manual intervention.
- **Acceptance Criteria**:
  - Settlement runs automatically after every bet placement
  - Settlement runs automatically after every "out" command
  - Settlement results display current state (who owes whom)
  - Settlement calculation completes within 500ms
  - Results are persisted to database for audit trail

**Story 4: Rejoin Capability**
- **As a player**, I want to rejoin the game after leaving by placing a new bet so that I can continue playing if I change my mind.
- **Acceptance Criteria**:
  - New bet after "out" resets player status to "in"
  - Previous winnings are preserved in transaction history
  - New settlement calculation includes the rejoining player

### Non-Goals
- Real-time multiplayer synchronization (settlement is asynchronous)
- Voice commands or alternative input methods
- Advanced analytics or game history tracking beyond current session
- Multi-currency support (single currency assumed)

## 3. Technical Specifications

### Architecture Overview

```
Telegram Bot ──► Message Handler ──► Service Layer ──► Storage
                     (Numeric)         (Business)      (SQLite)
                           │                  │
                           │                  ▼
                           │          Settlement Engine
                           │          (Auto-trigger)
                           │                  │
                           └──────────────────┘
                          (After each action)
```

### Component Changes

**Database Schema Updates**:
- Remove `is_winner` field from participants table (no longer needed)
- Add `settlement_timestamp` to track when last settlement was calculated
- Keep `status` field ("in"/"out") for tracking participation

**Command Changes**:
- **Removed**: `b <amount>`, `w <username> <prize>`, `s`, `sts`
- **Added**: `out <amount>` command
- **Modified**: Numeric message handler now primary betting mechanism
- **Modified**: Settlement trigger moved from manual to automatic

**Service Layer Updates**:
- `SettlementService` now auto-triggered by `ParticipantService` after bet/out actions
- Add validation logic for "out" amount vs current pot
- Add rejoin logic (status reset on new bet after "out")

### Integration Points
- **Telegram API**: python-telegram-bot for message handling
- **Ollama LLM**: Settlement calculation (existing integration maintained)
- **SQLite Database**: Persistent storage (schema migration required)

### Security & Privacy
- No new security concerns (existing auth via Telegram)
- Settlement calculations remain local (Ollama)
- No external API calls beyond existing dependencies

## 4. Risks & Roadmap

### Phased Rollout

**Phase 1: Documentation Update (Current)**
- Write PRD
- Update docs/plan.md
- Update README.md

**Phase 2: Code Implementation**
- Update database schema (migration script)
- Remove deprecated command handlers
- Add "out" command handler
- Implement auto-settlement trigger
- Add pot validation logic
- Add rejoin logic

**Phase 3: Testing**
- Unit tests for new functionality
- Integration tests for auto-settlement
- Migration testing for existing groups
- Manual testing with user feedback

**Phase 4: Deployment**
- Deploy to staging environment
- Run migration script
- Monitor for errors
- Deploy to production

### Technical Risks

**Risk 1: Database Migration Complexity**
- **Mitigation**: Create backup before migration, test on staging, provide rollback script

**Risk 2: Auto-settlement Performance**
- **Mitigation**: Add timeout protection, implement async settlement queue if needed

**Risk 3: User Confusion During Transition**
- **Mitigation**: Clear deprecation notices in old commands, in-app notifications about new flow

**Risk 4: Settlement Calculation Errors**
- **Mitigation**: Maintain existing Ollama + deterministic fallback, add error logging

## 5. Acceptance Criteria Summary

- [ ] PRD document completed and approved
- [ ] docs/plan.md updated with new command flow
- [ ] README.md updated with user-facing changes
- [ ] Database migration script created and tested
- [ ] "out <amount>" command implemented with pot validation
- [ ] Auto-settlement triggered after each bet/out action
- [ ] Rejoin logic implemented (status reset on new bet)
- [ ] All deprecated command handlers removed
- [ ] Unit tests written for new functionality
- [ ] Integration tests for auto-settlement flow
- [ ] Migration tested on staging environment
- [ ] Production deployment completed
- [ ] Post-deployment monitoring and user feedback collected
