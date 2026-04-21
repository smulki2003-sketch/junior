# frontend-admin

Phase 15 admin frontend for the Student Housing platform.

React + Tailwind admin control center with:
- Admin auth route guard
- KPI dashboard
- Users, housing, bookings, payments operations
- Complaint workspace and complaint case detail
- Reports and export panel
- Broadcast notifications center
- Roommate questionnaire management

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Test

```bash
npm run test
```

## Environment

Copy `.env.example` to `.env` and configure:

```bash
VITE_ADMIN_API_BASE_URL=http://localhost:8000
```

## Structure

```text
src/
├── api/
│   ├── client.js
│   ├── auth.js
│   └── admin/
├── components/
│   ├── ui/
│   ├── layout/
│   ├── charts/
│   └── shared/
├── pages/admin/
├── hooks/
├── store/
├── animations/
├── styles/
├── tests/
└── utils/
```

## Gateway Contract

This app connects only through API gateway endpoints under `/api/v1/*`.
No direct microservice calls are made from the frontend.

