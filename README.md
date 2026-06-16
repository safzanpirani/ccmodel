ccmodel
======

A tiny CLI that swaps **Claude Code** between your paid Anthropic subscription and third-party models exposed through an **Anthropic-compatible endpoint** (like `https://llm.safzan.dev/v1/messages`).

It manages only the `ANTHROPIC_*` keys inside the `env` block of `~/.claude/settings.json` and leaves everything else — hooks, model picker, `DISABLE_AUTOUPDATER`, etc. — untouched.

---

## What it does

Claude Code reads Anthropic endpoint configuration from environment variables. By writing those variables into `~/.claude/settings.json` under the `env` object, you can redirect Claude Code to any service that speaks the Anthropic Messages API.

`ccmodel` is a profile manager around that idea:

- `ccmodel sub` → clears overrides, use your real Claude subscription.
- `ccmodel use kimi-k2.7` → points Claude Code at `https://llm.safzan.dev/v1/messages` with `ANTHROPIC_MODEL=kimi-k2.7`.
- `ccmodel use gpt-5.5` → same endpoint, `ANTHROPIC_MODEL=gpt-5.5`.
- `ccmodel add` → add your own profiles with custom endpoints, keys, and models.
- `ccmodel current` → see what is currently active.
- `ccmodel ls` → list all profiles.

Each switch creates a timestamped backup in `~/.config/ccmodel/backups/` so you can roll back by hand if something breaks.

---

## Install

### One-liner (macOS / Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/safzanpirani/ccmodel/main/install.sh | sh
```

### Manual

```bash
git clone https://github.com/safzanpirani/ccmodel.git
cp ccmodel/src/ccmodel.py ~/.local/bin/ccmodel   # or /usr/local/bin
chmod +x ~/.local/bin/ccmodel
```

Requires **Python 3.7+** and `~/.claude/settings.json` to exist.

---

## Quick start

```bash
# see builtin profiles
ccmodel ls

# switch to Kimi K2.7 via your Anthropic-compatible endpoint
ccmodel use kimi-k2.7

# start / restart Claude Code in a new shell so the env is read
claude

# go back to your real Claude subscription
ccmodel sub
```

---

## Built-in profiles

| Profile | Model | Endpoint | Notes |
|---------|-------|----------|-------|
| `sub` | — | native | Your paid Claude subscription; clears all overrides. |
| `kimi-k2.7` | `kimi-k2.7` | `https://llm.safzan.dev` | Moonshot Kimi K2.7 over the Messages API. |
| `gpt-5.5` | `gpt-5.5` | `https://llm.safzan.dev` | OpenAI GPT-5.5 served as an Anthropic-compatible endpoint. |
| `glm-5.1` | `glm-5.1` | `https://llm.safzan.dev` | Zhipu GLM-5.1 served as an Anthropic-compatible endpoint. |

> **Note:** the default endpoint/key are just an example that matches the author's public gateway. If you run your own gateway or need a different key, edit `~/.config/ccmodel/profiles.json` or use `ccmodel add`.

---

## Add a custom profile

```bash
ccmodel add my-gpt \
  --base-url https://my-gw.example.com \
  --token sk-my-key \
  --model gpt-5.5 \
  --small-fast-model gpt-5.4-mini \
  --desc "My private gateway"

ccmodel use my-gpt
```

---

## How it works (non-destructive editing)

`ccmodel` only touches these seven environment variables:

- `ANTHROPIC_BASE_URL`
- `ANTHROPIC_AUTH_TOKEN`
- `ANTHROPIC_MODEL`
- `ANTHROPIC_SMALL_FAST_MODEL`
- `ANTHROPIC_DEFAULT_OPUS_MODEL`
- `ANTHROPIC_DEFAULT_SONNET_MODEL`
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`

When switching:

1. It reads `~/.claude/settings.json`.
2. It removes all managed keys from the `env` object.
3. It writes the keys for the selected profile (or none for `sub`).
4. It writes the file back with 2-space JSON indentation and a trailing newline.
5. It saves a timestamped backup of `settings.json` before each edit.

Anything else in `settings.json` — hooks, theme, `model`, `cleanupPeriodDays`, etc. — is preserved exactly.

---

## State files

```text
~/.config/ccmodel/
├── profiles.json                 # active profile + all profiles
├── settings.pristine.json        # first-seen snapshot of settings.json
└── backups/
    └── settings.20260616-143022.json
```

---

## Why an Anthropic-compatible endpoint?

Some model gateways (e.g. [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)) already proxy OpenAI, Gemini, CommandCode, and other providers through an OpenAI-compatible API. If they also expose an Anthropic-compatible `/v1/messages` translator, Claude Code can talk to them directly without a local shim.

Benefits:

- Prompt caching lives on the gateway, where it can hit across multiple clients.
- No local proxy to keep running.
- One key, one endpoint, works the same from every machine.

`ccmodel` is just the local switch that lets you pick which backend a given Claude Code session uses.

---

## Limitations / gotchas

- You must **start or restart Claude Code** after switching for the env changes to be read.
- The `sub` profile is the only one that cannot be removed.
- Token redaction in `ccmodel current` is cosmetic; it still lives in your `settings.json` in plaintext.
- The default profiles are illustrative — replace the key with your own if the example endpoint does not serve you.

---

## License

MIT
