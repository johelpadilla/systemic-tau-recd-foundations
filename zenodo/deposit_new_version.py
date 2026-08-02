#!/usr/bin/env python3
"""Create a new Zenodo version of the Systemic Tau foundations preprint.

Parent published deposition: 21287252
  conceptrecid / concept DOI: 21287251 / 10.5281/zenodo.21287251

Environment
-----------
  ZENODO_TOKEN   PAT with deposit:write + deposit:actions
  or ~/.zenodo_token

Usage
-----
  python3 deposit_new_version.py              # new version + upload (DRAFT)
  python3 deposit_new_version.py --publish    # also publish
  python3 deposit_new_version.py --publish-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
META_PATH = HERE / "metadata.json"
STATE_PATH = HERE / "deposition_state.json"
PARENT_ID = 21287252

# (local path, remote filename)
UPLOADS = [
    (ROOT / "Systemic_Tau_RECD_Framework.pdf", "Systemic_Tau_RECD_Framework.pdf"),
    (ROOT / "Systemic_Tau_RECD_Framework.tex", "Systemic_Tau_RECD_Framework.tex"),
    (ROOT / "references.bib", "references.bib"),
    (ROOT / "figures" / "excess3_pre_vs_chaos.png", "excess3_pre_vs_chaos.png"),
    (ROOT / "figures" / "contribs_stacked_pre_vs_chaos.png", "contribs_stacked_pre_vs_chaos.png"),
    (ROOT / "figures" / "lambda_emp_vs_regime.png", "lambda_emp_vs_regime.png"),
    (ROOT / "figures" / "cascade_A3_vs_r.png", "cascade_A3_vs_r.png"),
    (ROOT / "figures" / "cascade_ews_vs_A3.png", "cascade_ews_vs_A3.png"),
    (ROOT / "figures" / "gibbs_share_vs_abundance.png", "gibbs_share_vs_abundance.png"),
]


def token_and_base() -> tuple[str, str]:
    tok = os.environ.get("ZENODO_TOKEN", "").strip()
    if not tok:
        for cand in (HERE / ".zenodo_token", Path.home() / ".zenodo_token"):
            if cand.is_file():
                tok = cand.read_text(encoding="utf-8").strip().splitlines()[0].strip()
                if tok:
                    break
    if not tok:
        sys.exit("Missing ZENODO_TOKEN (or ~/.zenodo_token)")
    base = os.environ.get("ZENODO_BASE", "https://zenodo.org").rstrip("/")
    return tok, base


def headers(tok: str, json_body: bool = False) -> dict:
    h = {"Authorization": f"Bearer {tok}"}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {STATE_PATH}")


def load_state() -> dict:
    if not STATE_PATH.is_file():
        sys.exit(f"No state at {STATE_PATH}")
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def get_dep(tok: str, base: str, dep_id: int) -> dict:
    r = requests.get(
        f"{base}/api/deposit/depositions/{dep_id}",
        headers=headers(tok),
        timeout=60,
    )
    if r.status_code != 200:
        sys.exit(f"GET deposition {dep_id} failed {r.status_code}: {r.text}")
    return r.json()


def create_new_version(tok: str, base: str) -> dict:
    r = requests.post(
        f"{base}/api/deposit/depositions/{PARENT_ID}/actions/newversion",
        headers=headers(tok),
        timeout=120,
    )
    if r.status_code not in (200, 201, 202):
        sys.exit(f"newversion failed {r.status_code}: {r.text}")
    parent = r.json()
    draft_url = parent["links"]["latest_draft"]
    r2 = requests.get(draft_url, headers=headers(tok), timeout=60)
    if r2.status_code != 200:
        sys.exit(f"GET latest_draft failed {r2.status_code}: {r2.text}")
    draft = r2.json()
    dep_id = draft["id"]
    doi = draft["metadata"].get("prereserve_doi", {}).get("doi") or draft.get("doi")
    state = {
        "deposition_id": dep_id,
        "parent_id": PARENT_ID,
        "conceptrecid": draft.get("conceptrecid"),
        "doi": doi,
        "doi_url": f"https://doi.org/{doi}" if doi else None,
        "concept_doi": "10.5281/zenodo.21287251",
        "bucket": draft["links"]["bucket"],
        "html": draft["links"]["html"],
        "base": base,
        "created": date.today().isoformat(),
        "published": False,
        "version": "1.1.0",
    }
    save_state(state)
    print(f"New draft id={dep_id}  reserved DOI={doi}")
    return state


def put_metadata(tok: str, base: str, dep_id: int, metadata: dict) -> dict:
    r = requests.put(
        f"{base}/api/deposit/depositions/{dep_id}",
        data=json.dumps({"metadata": metadata}),
        headers=headers(tok, json_body=True),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"Put metadata failed {r.status_code}: {r.text}")
    print("Metadata updated.")
    return r.json()


def list_files(tok: str, base: str, dep_id: int) -> list[dict]:
    dep = get_dep(tok, base, dep_id)
    return dep.get("files", [])


def delete_file(tok: str, base: str, dep_id: int, file_id: str) -> None:
    r = requests.delete(
        f"{base}/api/deposit/depositions/{dep_id}/files/{file_id}",
        headers=headers(tok),
        timeout=60,
    )
    if r.status_code not in (200, 201, 204):
        print(f"  warn: delete file {file_id} → {r.status_code}: {r.text[:200]}")
    else:
        print(f"  deleted old file id={file_id}")


def upload_file(tok: str, bucket: str, local: Path, remote_name: str) -> None:
    if not local.is_file():
        sys.exit(f"Missing upload: {local}")
    print(f"Uploading {local.name} → {remote_name} ({local.stat().st_size} bytes)…")
    with local.open("rb") as fp:
        r = requests.put(
            f"{bucket}/{remote_name}",
            data=fp,
            headers=headers(tok),
            timeout=300,
        )
    if r.status_code not in (200, 201):
        sys.exit(f"Upload failed {r.status_code}: {r.text}")
    info = r.json()
    print(f"  OK checksum={info.get('checksum')} size={info.get('size')}")


def publish(tok: str, base: str, dep_id: int) -> dict:
    r = requests.post(
        f"{base}/api/deposit/depositions/{dep_id}/actions/publish",
        headers=headers(tok),
        timeout=120,
    )
    if r.status_code not in (200, 201, 202):
        sys.exit(f"Publish failed {r.status_code}: {r.text}")
    dep = r.json()
    doi = dep.get("doi") or dep.get("metadata", {}).get("doi")
    print(f"PUBLISHED  DOI={doi}")
    print(f"  record: {dep.get('links', {}).get('record_html') or dep.get('links', {}).get('html')}")
    return dep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--publish-only", action="store_true")
    ap.add_argument("--reuse-draft", action="store_true", help="Reuse state draft")
    args = ap.parse_args()

    tok, base = token_and_base()
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    meta.setdefault("publication_date", date.today().isoformat())

    if args.publish_only:
        state = load_state()
        dep = publish(tok, state.get("base", base), state["deposition_id"])
        state["published"] = True
        state["doi"] = dep.get("doi") or state.get("doi")
        state["doi_url"] = f"https://doi.org/{state['doi']}"
        state["record_html"] = dep.get("links", {}).get("record_html") or dep.get(
            "links", {}
        ).get("latest_html")
        save_state(state)
        return

    if args.reuse_draft and STATE_PATH.is_file():
        state = load_state()
        if state.get("published"):
            sys.exit(f"Already published: {state.get('doi_url')}")
        print(f"Reusing draft {state['deposition_id']}")
        dep = get_dep(tok, state.get("base", base), state["deposition_id"])
        state["bucket"] = dep["links"]["bucket"]
        save_state(state)
    elif STATE_PATH.is_file() and not json.loads(STATE_PATH.read_text()).get("published"):
        state = load_state()
        print(f"Reusing unpublished draft {state['deposition_id']} (delete state to force newversion)")
        dep = get_dep(tok, state.get("base", base), state["deposition_id"])
        state["bucket"] = dep["links"]["bucket"]
        save_state(state)
    else:
        if STATE_PATH.is_file():
            old = load_state()
            if old.get("published"):
                print(f"Previous version published as {old.get('doi')}; creating newer version…")
        state = create_new_version(tok, base)

    put_metadata(tok, state.get("base", base), state["deposition_id"], meta)

    # Remove inherited files so names/content match this version
    for f in list_files(tok, state.get("base", base), state["deposition_id"]):
        fid = f.get("id") or f.get("file_id")
        if fid:
            delete_file(tok, state.get("base", base), state["deposition_id"], str(fid))

    # refresh bucket after deletes
    dep = get_dep(tok, state.get("base", base), state["deposition_id"])
    state["bucket"] = dep["links"]["bucket"]
    save_state(state)

    for local, remote in UPLOADS:
        upload_file(tok, state["bucket"], local, remote)

    print("\n=== DRAFT READY ===")
    print(f"  Edit UI : {state['html']}")
    print(f"  DOI     : {state['doi']}  (registers on publish)")
    print(f"  Concept : {state.get('concept_doi')}")
    print("  To publish: python3 deposit_new_version.py --publish-only")

    if args.publish:
        dep = publish(tok, state.get("base", base), state["deposition_id"])
        state["published"] = True
        state["doi"] = dep.get("doi") or state.get("doi")
        state["doi_url"] = f"https://doi.org/{state['doi']}"
        state["record_html"] = dep.get("links", {}).get("record_html") or dep.get(
            "links", {}
        ).get("latest_html")
        state["title"] = meta.get("title")
        save_state(state)


if __name__ == "__main__":
    main()
