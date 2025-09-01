"""
dhis2kit CLI

Usage:
    dhis2kit --help
    dhis2kit --base-url http://localhost:8080/api --user admin --password district list dataElements --fields id,displayName --page-size 50
    # or via env vars:
    export DHIS2_URL=http://localhost:8080/api
    export DHIS2_USER=admin
    export DHIS2_PASS=district
    dhis2kit list organisationUnits --fields id,displayName,level --page-size 100

Environment variables:
    DHIS2_URL, DHIS2_USER, DHIS2_PASS

Commands:
    list <resource>             List a metadata collection (with paging)
    get <resource> <uid>        Get a single metadata object
    analytics                   Run an analytics query
    pull-dvs                    Export dataValueSets
    push-dvs                    Import dataValueSets from a JSON file
    demo                        Small sync demo against the server
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, Optional

from .client import Dhis2Client


def _env_or_default(value: Optional[str], env_name: str) -> Optional[str]:
    if value:
        return value
    return os.environ.get(env_name)


def _build_client(args: argparse.Namespace) -> Dhis2Client:
    base_url = _env_or_default(args.base_url, "DHIS2_URL")
    user = _env_or_default(args.user, "DHIS2_USER")
    password = _env_or_default(args.password, "DHIS2_PASS")

    missing = [k for k, v in [("base_url", base_url), ("user", user), ("password", password)] if not v]
    if missing:
        env_map = {"base_url": "DHIS2_URL", "user": "DHIS2_USER", "password": "DHIS2_PASS"}
        msg = "Missing required connection values: " + ", ".join(
            f"{m} (or set {env_map[m]})" for m in missing
        )
        print(msg, file=sys.stderr)
        sys.exit(2)

    return Dhis2Client(base_url, user, password, timeout=args.timeout)


def _parse_kv_list(kvs: Iterable[str]) -> Dict[str, Any]:
    """
    Parse CLI --param key=value pairs into a dict.
    Example: --param includeChildren=true --param level=2
    """
    out: Dict[str, Any] = {}
    for kv in kvs:
        if "=" not in kv:
            raise argparse.ArgumentTypeError(f"Expected key=value, got: {kv}")
        key, value = kv.split("=", 1)
        # best-effort type coercion
        if value.lower() in {"true", "false"}:
            out[key] = value.lower() == "true"
        elif value.isdigit():
            out[key] = int(value)
        else:
            out[key] = value
    return out


def cmd_list(args: argparse.Namespace) -> int:
    client = _build_client(args)
    try:
        fields = args.fields or "id,displayName"
        coll = args.resource
        params: Dict[str, Any] = {}
        if args.page is not None:
            params["page"] = args.page
        data = client.list_metadata(
            coll,
            fields=fields,
            page_size=args.page_size,
            total_pages=args.total_pages,
            **params,
        )
        print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def cmd_get(args: argparse.Namespace) -> int:
    client = _build_client(args)
    try:
        fields = args.fields or "id,displayName"
        data = client.get_metadata(args.resource, args.uid, fields=fields)
        print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def cmd_analytics(args: argparse.Namespace) -> int:
    client = _build_client(args)
    try:
        query: Dict[str, Any] = {}
        if args.dimension:
            # allow multiple --dimension entries, each possibly comma-separated
            dims = []
            for d in args.dimension:
                dims.extend([x for x in d.split(",") if x])
            query["dimension"] = dims
        if args.filter:
            query["filter"] = args.filter
        if args.params:
            query.update(_parse_kv_list(args.params))

        ar = client.get_analytics(**query)
        # Print a compact JSON for rows; headers/metaData are printed as-is.
        payload = {
            "headers": ar.headers,
            "metaData": ar.metaData,
            "rows": ar.rows,
        }
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        client.close()


def cmd_pull_dvs(args: argparse.Namespace) -> int:
    client = _build_client(args)
    try:
        params = _parse_kv_list(args.params or [])
        # convenience flags
        if args.dataSet:
            params["dataSet"] = args.dataSet
        if args.period:
            params["period"] = args.period
        if args.orgUnit:
            params["orgUnit"] = args.orgUnit
        if args.format:
            params["format"] = args.format

        data = client.pull_data_value_set(**params)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Wrote {args.out}")
        else:
            print(json.dumps(data, indent=2))
        return 0
    finally:
        client.close()


def cmd_push_dvs(args: argparse.Namespace) -> int:
    client = _build_client(args)
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        resp = client.push_data_value_set(payload)
        print(json.dumps(resp, indent=2))
        return 0
    finally:
        client.close()


def cmd_demo(args: argparse.Namespace) -> int:
    # keep your previous demo, but run through the CLI
    client = _build_client(args)
    try:
        print("=== DHIS2 Sync Client Demo ===")
        data = client.list_metadata("dataElements", fields="id,displayName,valueType", page_size=5, total_pages=True)
        for de in data.get("dataElements", []):
            print(f"DataElement: {de.get('id')} | {de.get('displayName')} | {de.get('valueType')}")

        print("First 10 organisationUnits via iterator:")
        n = 0
        for ou in client.iter_metadata("organisationUnits", fields="id,displayName,level", page_size=5, max_pages=2):
            print(f"OU: {ou.get('id')} | {ou.get('displayName')} | L{ou.get('level')}")
            n += 1
            if n >= 10:
                break
        return 0
    finally:
        client.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dhis2kit", description="DHIS2 CLI for metadata, analytics, and dataValueSets.")
    p.add_argument("--base-url", help="DHIS2 base URL, e.g., http://localhost:8080/api (env: DHIS2_URL)")
    p.add_argument("--user", help="Username (env: DHIS2_USER)")
    p.add_argument("--password", help="Password (env: DHIS2_PASS)")
    p.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds (default: 30)")

    sub = p.add_subparsers(dest="command", required=True)

    # list
    sp = sub.add_parser("list", help="List metadata collection with paging")
    sp.add_argument("resource", help="Resource name, e.g., dataElements, organisationUnits, dataSets")
    sp.add_argument("--fields", help="Comma-separated fields (default: id,displayName)")
    sp.add_argument("--page", type=int, help="Page number (1-based)")
    sp.add_argument("--page-size", type=int, default=50, help="Page size (default: 50)")
    sp.add_argument("--total-pages", action="store_true", help="Ask server to include totalPages")
    sp.set_defaults(func=cmd_list)

    # get
    sp = sub.add_parser("get", help="Get a single metadata object by UID")
    sp.add_argument("resource", help="Resource name, e.g., dataElements, organisationUnits, dataSets")
    sp.add_argument("uid", help="UID")
    sp.add_argument("--fields", help="Comma-separated fields (default: id,displayName)")
    sp.set_defaults(func=cmd_get)

    # analytics
    sp = sub.add_parser("analytics", help="Run an analytics query")
    sp.add_argument("--dimension", action="append", help="Dimension(s), repeatable or comma-separated. e.g., dx:Uvn...,pe:LAST_12_MONTHS")
    sp.add_argument("--filter", help="Filter string, e.g., ou:ImspTQPwCqd")
    sp.add_argument("--params", action="append", default=[], help="Additional key=value params (repeatable)")
    sp.set_defaults(func=cmd_analytics)

    # pull-dvs
    sp = sub.add_parser("pull-dvs", help="Export dataValueSets")
    sp.add_argument("--dataSet", help="dataSet UID")
    sp.add_argument("--period", help="Period (e.g., 202201)")
    sp.add_argument("--orgUnit", help="OrgUnit UID")
    sp.add_argument("--format", default="json", help="Format (json or xml). Default json")
    sp.add_argument("--out", help="Write to file instead of stdout")
    sp.add_argument("--params", action="append", default=[], help="Additional key=value params (repeatable)")
    sp.set_defaults(func=cmd_pull_dvs)

    # push-dvs
    sp = sub.add_parser("push-dvs", help="Import dataValueSets from JSON file")
    sp.add_argument("file", help="Path to JSON file with dataValueSets payload")
    sp.set_defaults(func=cmd_push_dvs)

    # demo
    sp = sub.add_parser("demo", help="Run a small demo (sync)")
    sp.set_defaults(func=cmd_demo)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
