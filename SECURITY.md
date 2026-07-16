# Security Policy

## Reporting a vulnerability

If you find a security issue, please **do not open a public issue**. Email the maintainer at [simeonkolchin@gmail.com](mailto:simeonkolchin@gmail.com) with details and steps to reproduce. You can expect an acknowledgement within a few days.

## Secrets

- The team auth token (`DATS_TOKEN`) must live only in your local `.env`, which is gitignored.
- `.env.example` ships placeholders only.
- If a token is ever committed, **rotate it immediately** via the DatsTeam dashboard — rewriting git history is not enough, as the old token may already be exposed.

## Scope

This is a hackathon game client with no user data and no production deployment. The main risk surface is accidental credential exposure.
