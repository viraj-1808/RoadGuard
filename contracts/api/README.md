# API Contracts

This directory contains draft and placeholder contract documents for the API interface.

## Authoritative Source

The authoritative API contract documentation is in `docs/`:

- `docs/API_CONTRACTS.md` — Backend → Frontend contract
- `docs/DATABASE_SCHEMA.md` — Conceptual entities
- `docs/DEPLOYMENT.md` — Deployment model

## Purpose

API contracts define the interface between:
- Backend API → Frontend
- External consumers → Backend API

### Backend → Frontend Contract

The frontend communicates with the backend through a REST API (or GraphQL) that exposes:

- PotholeEvent CRUD operations
- Report management
- Evidence retrieval
- Camera/status endpoints
- Model version info

See `docs/API_CONTRACTS.md` for the current placeholder contract table.

## Status

- Backend → Frontend schema: **TO BE FINALIZED**
- API technology (REST/GraphQL): **OPEN**
- Authentication/Authorization: **OPEN**