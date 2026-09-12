# unpeel-mcp-probe

Muse native plugin exposing the Unpeel sessions MCP server (`unpeel-host __mcp__`)
inside Muse sessions: all 7 domains (`agents`, `sessions`, `workspace`,
`artifacts`, `browser`, `apps`, `skills`).

The server command points at a [jdrly/unpeel](https://github.com/jdrly/unpeel)
fork build (`agent-sessions` branch), which adds two fork-only `sessions`
actions upstream deliberately withholds:

- `rename` — the agent retitles its own session (`#123 fix login`)
- `start` — the agent spawns one visible child session (e.g. a Codex reviewer)

Upstream PR for stock Muse support: [unpeel-com/unpeel#13](https://github.com/unpeel-com/unpeel/pull/13).
Once that merges, this probe can point back at the shipped app binary.

## Requirements

- Unpeel app installed (hosts the sessions; only the MCP server binary is swapped)
- Fork `unpeel-host` built: `cargo build --release -p unpeel-host` in the
  `jdrly/unpeel` checkout, `agent-sessions` branch
- Adjust `command[0]` in `.muse-plugin/plugin.json` to your binary path

## Install

```sh
muse plugins install /path/to/unpeel-mcp-probe --scope user
muse plugins approve 'unpeel-mcp-probe:mcp_server:unpeel'
```

New sessions pick it up automatically. Verify with a fresh session:

```sh
muse exec --yolo "Call sessions help with help_for=start, reply with the first 3 lines."
```

## License

MIT
