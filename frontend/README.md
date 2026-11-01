# MediExplain AI — Frontend

React + Vite client for MediExplain AI. Implements the Phase 1 user journey:
landing → register/login → dashboard → upload → report analysis → AI explanations.

## Setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

- Dev URL: <http://localhost:5173>
- API base URL: `VITE_API_BASE_URL` (default `http://localhost:8000`)
- Production build: `npm run build` → `dist/`

The backend must be running and its `FRONTEND_ORIGINS` must include the frontend origin.

## Implemented pages

| Route | Screen | Notes |
|-------|--------|-------|
| `/` | Landing | Product overview, workflow, safety and CTA |
| `/login` | Login | JWT session stored in localStorage |
| `/register` | Register | Creates account then signs in |
| `/app` | Dashboard | Totals, latest analysis, recent reports, empty state |
| `/app/upload` | Upload | Drag & drop, validation, image preview, progress |
| `/app/reports/:id` | Report analysis | Results table, flags, critical alert, explanations |
| `*` | Not found | — |

## Structure

```text
frontend/
├── src/
│   ├── components/          # Brand, badges, disclaimer, dropzone pieces, text renderer
│   ├── context/AuthContext  # Session bootstrap, login/register/logout
│   ├── layouts/AppLayout    # Sidebar shell + mobile navigation
│   ├── pages/               # Landing, auth, dashboard, upload, report
│   ├── services/api.js      # Fetch wrapper, typed errors, XHR upload progress
│   ├── utils/format.js      # Dates, numbers, file sizes, status counts
│   ├── App.jsx
│   └── main.jsx
├── .env.example
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
└── vite.config.js
```

## Behaviour and safety

- Status is always shown with a **text label and icon**, never colour alone.
- Uploads are validated client-side (type, size) and again on the server (signature, size).
- Critical-value results show an urgent banner and never an AI reassurance.
- AI explanations are labelled with their source (`Offline template` or `AI · provider`).
- The original extracted value, unit and report range stay visible above the explanation.
- The report can be deleted from the UI, including its stored file.

## Next frontend work (Phase 2/3)

- Report-grounded chat screen with citations.
- Multi-report comparison and trend charts (Recharts).
- PDF export and sharing.
- Hindi UI copy (explanations already support Hindi/Hinglish).
