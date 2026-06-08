# 🎮 Malta SMP Discord Bot

A fully-featured, production-ready Discord bot for the Malta SMP server. Built with Python 3.12+, discord.py 2.x, and SQLite. Deployable on Railway in minutes.

---

## ✨ Features

| Module | Description |
|---|---|
| 🎫 Tickets | Panel with 4 categories, claim/close/reopen/delete, HTML transcripts, inactivity timer |
| 🔨 Moderation | Warn, timeout, kick, ban, unban, lock, unlock, slowmode with logs |
| 📋 Logging | Join/leave, messages, voice, roles, nicknames, channels, tickets |
| 📨 Invites | Inviter tracking, invite leaderboard, per-member stats |
| 👋 Welcome | Custom welcome/goodbye embeds, auto-role assignment |
| 🤖 AutoMod | Anti-spam, anti-mention-spam, anti-emoji-spam, anti-link, scam detection |
| 🔒 Security | Anti-raid lockdown, new account kick, configurable thresholds |
| ⚙️ Admin | Full configuration via slash commands, view config, bot stats |

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.12+
- A Discord bot token ([create one here](https://discord.com/developers/applications))
- Bot Intents: **All Privileged Gateway Intents must be enabled**

### 2. Clone & Install

```bash
git clone https://github.com/your-repo/Malta-SMP-Bot
cd Malta-SMP-Bot
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your DISCORD_TOKEN
```

### 4. Run

```bash
python main.py
```

---

## 🚂 Railway Deployment

1. Push your code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Add the environment variable: `DISCORD_TOKEN = your_token_here`
5. Railway auto-detects the `Procfile` and deploys automatically

> **Note:** The SQLite database (`database/bot.db`) is stored on the Railway volume. For persistence across deploys, configure a Railway volume mounted at `/app/database`.

---

## ⚙️ Setup After Invite

Run these commands in your Discord server (requires Administrator):

### 1. Set Roles
```
/setstaffrole role:@Staff
/setmodrole role:@Moderator
/setautorole role:@Member
```

### 2. Set Log Channels
```
/setlogs join_log:#join-logs leave_log:#leave-logs message_log:#message-logs mod_log:#mod-logs voice_log:#voice-logs role_log:#role-logs security_log:#security-logs
```

### 3. Set Ticket System
```
/settickets category:Tickets log_channel:#ticket-logs
/settranscripts channel:#transcripts
/ticketpanel   ← run in your #support channel
```

### 4. Set Welcome
```
/setwelcome channel:#welcome message:Welcome {user} to {server}! You are member #{count}.
/setgoodbye channel:#goodbye
```

### 5. Security
```
/setminaccountage days:7
/setraidthreshold joins:10 window:10
```

### 6. View Full Config
```
/viewconfig
```

---

## 📋 Command Reference

### Moderation
| Command | Description | Permission |
|---|---|---|
| `/warn <member> <reason>` | Warn a member | Moderator |
| `/warnings <member>` | View member warnings | Moderator |
| `/delwarn <id>` | Remove a warning | Moderator |
| `/clear <amount>` | Delete messages (1-100) | Moderator |
| `/timeout <member> <minutes>` | Timeout a member | Moderator |
| `/untimeout <member>` | Remove timeout | Moderator |
| `/kick <member>` | Kick a member | Moderator |
| `/ban <member>` | Ban a member | Moderator |
| `/unban <user_id>` | Unban a user | Moderator |
| `/lock` | Lock current channel | Moderator |
| `/unlock` | Unlock current channel | Moderator |
| `/slowmode <seconds>` | Set slowmode | Moderator |

### Tickets
| Command | Description | Permission |
|---|---|---|
| `/ticket` | Open ticket picker | Everyone |
| `/ticketpanel` | Send panel to channel | Staff |
| `/ticketstats` | View ticket statistics | Staff |
| `/adduser <member>` | Add user to ticket | Staff |
| `/removeuser <member>` | Remove user from ticket | Staff |

### Invites
| Command | Description | Permission |
|---|---|---|
| `/invites [member]` | View invite count | Everyone |
| `/inviteleaderboard` | Top inviters | Everyone |
| `/inviteinfo <member>` | Who invited this member | Staff |

### Welcome
| Command | Description | Permission |
|---|---|---|
| `/setwelcome` | Configure welcome | Staff |
| `/setgoodbye` | Configure goodbye | Staff |
| `/setautorole` | Set auto-role | Staff |
| `/testwelcome` | Test welcome message | Staff |
| `/testgoodbye` | Test goodbye message | Staff |

### Security
| Command | Description | Permission |
|---|---|---|
| `/lockdown [reason]` | Manual server lockdown | Staff |
| `/unlockdown [reason]` | Lift lockdown | Staff |
| `/setminaccountage <days>` | Min account age | Admin |
| `/setraidthreshold` | Raid detection | Admin |
| `/securitystatus` | View security status | Staff |
| `/automod <true/false>` | Toggle AutoMod | Admin |
| `/setspamthreshold` | Spam thresholds | Admin |
| `/setlinkwhitelist` | Whitelist domains | Admin |

### Admin
| Command | Description | Permission |
|---|---|---|
| `/setup` | Setup guide | Admin |
| `/setlogs` | Configure log channels | Admin |
| `/settranscripts` | Set transcript channel | Admin |
| `/settickets` | Configure tickets | Admin |
| `/setstaffrole` | Set staff role | Admin |
| `/setmodrole` | Set mod role | Admin |
| `/viewconfig` | View all settings | Staff |
| `/botstats` | Bot statistics | Everyone |
| `/ping` | Bot latency | Everyone |

---

## 🗄️ Database Schema

Tables: `guild_config`, `users`, `warnings`, `moderation_logs`, `tickets`, `ticket_messages`, `invites`, `invite_uses`, `security_logs`, `staff_logs`, `automod_violations`

The database auto-initializes on first run. No manual setup required.

---

## 🔐 Required Bot Permissions

- Read Messages / View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Manage Messages
- Manage Channels
- Manage Roles
- Kick Members
- Ban Members
- Moderate Members (Timeout)
- View Audit Log
- Manage Guild (for invite tracking)

**Required Privileged Intents (enable in Developer Portal):**
- Server Members Intent
- Message Content Intent
- Presence Intent

---

## 📁 Project Structure

```
Malta-SMP-Bot/
├── cogs/
│   ├── tickets.py       # Ticket system
│   ├── moderation.py    # Mod commands
│   ├── logs.py          # Event logging
│   ├── invites.py       # Invite tracking
│   ├── welcome.py       # Welcome/goodbye
│   ├── automod.py       # Anti-spam/links
│   ├── security.py      # Anti-raid
│   └── admin.py         # Configuration
├── database/
│   └── bot.db           # SQLite database (auto-created)
├── utils/
│   ├── transcript.py    # HTML transcript generator
│   ├── embeds.py        # Embed helpers
│   ├── database.py      # Database manager
│   └── permissions.py   # Permission checks
├── config/
│   └── config.json      # Bot configuration
├── main.py              # Entry point
├── requirements.txt
├── Procfile
├── railway.json
└── .env.example
```

---

## 🛠️ Tech Stack

- **Python** 3.12+
- **discord.py** 2.3.2
- **aiosqlite** — Async SQLite
- **python-dotenv** — Environment variables
- **Railway** — Cloud deployment

---

## 📝 License

MIT License — Free to use and modify for your server.
