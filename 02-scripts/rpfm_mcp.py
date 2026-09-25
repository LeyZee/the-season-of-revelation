#!/usr/bin/env python3
"""
rpfm_mcp.py - appelle les outils MCP de rpfm_server 5.0.6 (Streamable HTTP) sans client MCP.

Prérequis : rpfm_server lancé (`lancer-outils.ps1 -Outil rpfm-server`), qui écoute sur
http://127.0.0.1:45127/mcp. Les 150 outils sont listés dans `05-journal\\rpfm-mcp-20-09-2026\\tools.md`.

Règle apprise le 20.09.2026 : **une session MCP = un état** (jeu sélectionné, packs ouverts).
Tout ce qui doit partager un état se fait dans un seul appel `--batch`, `set_game_selected` en tête.

Usage :
    python rpfm_mcp.py schema set_game_selected,open_packfiles          # schéma d'entrée des outils
    python rpfm_mcp.py call list_open_packs
    python rpfm_mcp.py call set_game_selected '{"game_name":"warhammer","rebuild_dependencies":true}'
    python rpfm_mcp.py batch appels.json      # [["set_game_selected", {...}], ["open_packfiles", {...}], ...]

Depuis un autre script : `from rpfm_mcp import session, call, text` puis
    sid = session(); r = call(sid, "list_open_packs", {}); print(text(r))

Formes de réponse vues (20.09.2026) : `{"StringContainerInfo": [...]}`, `{"VecStringContainerInfo": [...]}`,
`{"HashMapDataSourceHashSetContainerPath": {...}}`, `{"DependenciesInfo": {...}}` : toujours regarder la
réponse brute avant d'écrire l'analyse.
"""

import json
import sys
import urllib.request

URL = "http://127.0.0.1:45127/mcp"


def post(body, session_id=None):
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        sid = r.headers.get("Mcp-Session-Id")
        raw = r.read().decode("utf-8", "replace")
    payload = None
    for line in raw.splitlines():          # réponse SSE : garder la dernière ligne data: qui est du JSON
        if line.startswith("data:"):
            s = line[5:].strip()
            if s:
                try:
                    payload = json.loads(s)
                except ValueError:
                    pass
    if payload is None:
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"raw": raw}
    return sid, payload


def session():
    sid, _ = post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                              "clientInfo": {"name": "atelier", "version": "1"}}})
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    return sid


def fermer(sid):
    """Ferme une session MCP (25.09.2026, 20 h 50 ; Charles : « comment ça se fait que RPFM garde autant de mémoire ? »).
    Chaque script ouvrait sa session sans la fermer ; rpfm_server (5.0.6) les garde sans délai d'expiration, avec la base
    du jeu chargée et les packs OUVERTS (`/sessions` : pack_names) : ~1,5 à 2 Go par pack construit, 9,4 Go en une soirée
    (erreurs 265, 275). Ferme les packs, puis termine la session par un DELETE (transport MCP « Streamable HTTP »).
    Rend True si le serveur a accepté la fin de session."""
    try:
        call(sid, "close_all_packs", {}, 90)
    except Exception:
        pass
    req = urllib.request.Request(URL, headers={"Mcp-Session-Id": sid}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def call(sid, tool, args, request_id=2):
    _, res = post({"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                   "params": {"name": tool, "arguments": args}}, sid)
    return res


def text(res):
    """Concatène les contenus texte d'une réponse tools/call."""
    return "".join(c.get("text", "") for c in res.get("result", {}).get("content", []))


def show(res):
    if "result" in res:
        print(text(res))
        if res["result"].get("isError"):
            print("[isError]")
    else:
        print(json.dumps(res, ensure_ascii=False)[:4000])


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) < 2 or argv[1] not in ("schema", "call", "batch"):
        print(__doc__)
        return 2
    sid = session()
    if argv[1] == "schema":
        _, res = post({"jsonrpc": "2.0", "id": 5, "method": "tools/list", "params": {}}, sid)
        wanted = set(argv[2].split(","))
        for t in res["result"]["tools"]:
            if t["name"] in wanted:
                schema = t.get("inputSchema", {})
                print("###", t["name"])
                print(json.dumps(schema.get("properties", {}), ensure_ascii=False)[:1500])
                print("required:", schema.get("required"))
    elif argv[1] == "call":
        args = json.loads(argv[3]) if len(argv) > 3 else {}
        show(call(sid, argv[2], args))
    else:
        calls = json.load(open(argv[2], encoding="utf-8"))
        for i, (tool, args) in enumerate(calls, start=2):
            print(f"=== {tool} {json.dumps(args, ensure_ascii=False)[:200]} ===")
            show(call(sid, tool, args, i))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
