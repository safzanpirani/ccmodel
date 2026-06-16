#!/usr/bin/env python3
"""ccmodel — swap Claude Code between your Claude subscription and third-party
models served over an Anthropic-compatible endpoint (e.g. llm.safzan.dev).

State lives in ~/.config/ccmodel/ (profiles.json + a pristine settings backup).
Switching rewrites ONLY the ANTHROPIC_* keys this tool manages inside the
`env` block of ~/.claude/settings.json — every other setting (hooks, model
picker, DISABLE_AUTOUPDATER, ...) is left untouched.

The `sub` profile is special: it strips the managed keys so Claude Code falls
back to your logged-in Claude subscription.
"""
import argparse
import datetime
import json
import os
import shutil
import sys

HOME = os.path.expanduser("~")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")
CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "ccmodel"
)
PROFILES = os.path.join(CONFIG_DIR, "profiles.json")
PRISTINE = os.path.join(CONFIG_DIR, "settings.pristine.json")
BACKUP_DIR = os.path.join(CONFIG_DIR, "backups")

# The only env keys ccmodel ever writes or deletes. Anything else in `env`
# is preserved verbatim.
MANAGED = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
]

DEFAULT_ENDPOINT = "https://llm.safzan.dev"
# Example admin token for the default endpoint. Replace with your own key in
# ~/.config/ccmodel/profiles.json if you run a different gateway.
DEFAULT_TOKEN = "sk-oracle-1b6386a37e4b54c1da760c36b523559b"

DEFAULT_PROFILES = {
    "current": "sub",
    "profiles": {
        "sub": {
            "builtin": True,
            "desc": "Your Claude subscription (native, no override)",
        },
        "friend-kimi-k2.7-code": {
            "base_url": DEFAULT_ENDPOINT,
            "token": DEFAULT_TOKEN,
            "model": "friend-kimi-k2.7-code",
            "small_fast_model": "friend-kimi-k2.7-code",
            "desc": "Friend-accessible Kimi K2.7 (CommandCode) via llm.safzan.dev",
        },
        "kimi-k2.7": {
            "base_url": DEFAULT_ENDPOINT,
            "token": DEFAULT_TOKEN,
            "model": "kimi-k2.7",
            "small_fast_model": "kimi-k2.7",
            "desc": "Moonshot Kimi K2.7 via llm.safzan.dev",
        },
        "gpt-5.5": {
            "base_url": DEFAULT_ENDPOINT,
            "token": DEFAULT_TOKEN,
            "model": "gpt-5.5",
            "small_fast_model": "gpt-5.4-mini",
            "desc": "GPT-5.5 via llm.safzan.dev",
        },
        "glm-5.1": {
            "base_url": DEFAULT_ENDPOINT,
            "token": DEFAULT_TOKEN,
            "model": "glm-5.1",
            "small_fast_model": "glm-5.1",
            "desc": "GLM-5.1 via llm.safzan.dev",
        },
    },
}

GREEN, DIM, BOLD, RESET = "\033[32m", "\033[2m", "\033[1m", "\033[0m"


def die(msg):
    print(f"ccmodel: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def ensure_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(PROFILES):
        with open(PROFILES, "w") as f:
            json.dump(DEFAULT_PROFILES, f, indent=2)
    if not os.path.exists(PRISTINE) and os.path.exists(SETTINGS):
        shutil.copy2(SETTINGS, PRISTINE)


def load_profiles():
    return load_json(PROFILES)


def save_profiles(p):
    with open(PROFILES, "w") as f:
        json.dump(p, f, indent=2)


def read_settings():
    if not os.path.exists(SETTINGS):
        die(f"{SETTINGS} not found")
    return load_json(SETTINGS)


def backup_settings():
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"settings.{ts}.json")
    shutil.copy2(SETTINGS, dst)
    return dst


def write_settings(data):
    backup_settings()
    tmp = SETTINGS + ".ccmodel.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, SETTINGS)


def env_for_profile(name, prof):
    if prof.get("builtin"):
        return {}  # sub: no overrides
    for req in ("base_url", "token", "model"):
        if not prof.get(req):
            die(f"profile '{name}' is missing '{req}'")
    sfm = prof.get("small_fast_model") or prof["model"]
    return {
        "ANTHROPIC_BASE_URL": prof["base_url"],
        "ANTHROPIC_AUTH_TOKEN": prof["token"],
        "ANTHROPIC_MODEL": prof["model"],
        "ANTHROPIC_SMALL_FAST_MODEL": sfm,
        # Map the named-tier overrides too, so /model picks and subagents stay
        # on the third-party model instead of trying real Anthropic tiers.
        "ANTHROPIC_DEFAULT_OPUS_MODEL": prof["model"],
        "ANTHROPIC_DEFAULT_SONNET_MODEL": prof["model"],
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": sfm,
    }


def cmd_use(args):
    p = load_profiles()
    name = args.name
    if name not in p["profiles"]:
        die(f"unknown profile '{name}'. Try: ccmodel ls")
    prof = p["profiles"][name]
    settings = read_settings()
    env = settings.get("env", {})
    # Strip every managed key first, then apply this profile's set.
    for k in MANAGED:
        env.pop(k, None)
    env.update(env_for_profile(name, prof))
    settings["env"] = env
    write_settings(settings)
    p["current"] = name
    save_profiles(p)
    if prof.get("builtin"):
        print(
            f"{GREEN}✓{RESET} switched to {BOLD}{name}{RESET} — Claude subscription (overrides cleared)"
        )
    else:
        print(
            f"{GREEN}✓{RESET} switched to {BOLD}{name}{RESET} → {prof['model']} @ {prof['base_url']}"
        )
    print(
        f"{DIM}  open a new Claude Code session (or restart) for it to take effect{RESET}"
    )


def cmd_ls(args):
    p = load_profiles()
    cur = p.get("current")
    for name, prof in p["profiles"].items():
        mark = f"{GREEN}*{RESET}" if name == cur else " "
        if prof.get("builtin"):
            detail = "Claude subscription (native)"
        else:
            detail = f"{prof['model']} @ {prof['base_url']}"
        desc = prof.get("desc", "")
        print(f" {mark} {BOLD}{name:<16}{RESET} {detail}")
        if desc:
            print(f"     {DIM}{desc}{RESET}")


def cmd_current(args):
    p = load_profiles()
    cur = p.get("current", "?")
    print(f"current profile: {BOLD}{cur}{RESET}")
    env = read_settings().get("env", {})
    active = {k: env[k] for k in MANAGED if k in env}
    if not active:
        print(f"{DIM}  no ANTHROPIC_* overrides set — using Claude subscription{RESET}")
    else:
        for k, v in active.items():
            shown = v if k != "ANTHROPIC_AUTH_TOKEN" else v[:8] + "…" + v[-4:]
            print(f"  {k}={shown}")


def cmd_add(args):
    p = load_profiles()
    p["profiles"][args.name] = {
        "base_url": args.base_url,
        "token": args.token,
        "model": args.model,
        "small_fast_model": args.small_fast_model or args.model,
        "desc": args.desc or "",
    }
    save_profiles(p)
    print(
        f"{GREEN}✓{RESET} saved profile {BOLD}{args.name}{RESET} → {args.model} @ {args.base_url}"
    )


def cmd_rm(args):
    p = load_profiles()
    if args.name == "sub":
        die("cannot remove the builtin 'sub' profile")
    if args.name not in p["profiles"]:
        die(f"unknown profile '{args.name}'")
    del p["profiles"][args.name]
    if p.get("current") == args.name:
        p["current"] = "sub"
    save_profiles(p)
    print(f"{GREEN}✓{RESET} removed profile {BOLD}{args.name}{RESET}")


def main():
    ensure_config()
    ap = argparse.ArgumentParser(
        prog="ccmodel",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("use", help="activate a profile")
    s.add_argument("name")
    s.set_defaults(func=cmd_use)

    s = sub.add_parser("sub", help="shortcut for: use sub (back to Claude subscription)")
    s.set_defaults(func=lambda a: cmd_use(argparse.Namespace(name="sub")))

    sub.add_parser("ls", help="list profiles").set_defaults(func=cmd_ls)
    sub.add_parser("current", help="show active profile + env").set_defaults(func=cmd_current)

    s = sub.add_parser("add", help="add/update a profile")
    s.add_argument("name")
    s.add_argument("--base-url", default=DEFAULT_ENDPOINT)
    s.add_argument("--token", default=DEFAULT_TOKEN)
    s.add_argument("--model", required=True)
    s.add_argument("--small-fast-model", default=None)
    s.add_argument("--desc", default=None)
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("rm", help="remove a profile")
    s.add_argument("name")
    s.set_defaults(func=cmd_rm)

    args = ap.parse_args()
    if not getattr(args, "func", None):
        cmd_ls(args)
        return
    args.func(args)


if __name__ == "__main__":
    main()
