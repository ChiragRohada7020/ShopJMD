# Shop Supplier Ledger

A focused full-stack shop management app for supplier records, supplier ledger accounts, voice-based transaction entry, and PDF ledger generation.

This project intentionally does not include ecommerce, inventory, billing, authentication, or complex admin panels.

## Tech Stack

- Frontend: React, Vite, React Router, Axios, TailwindCSS, lucide-react, react-hot-toast
- Backend: Flask, Flask-CORS, PyMongo, python-dotenv, Groq, ReportLab
- Database: MongoDB
- AI parsing: Groq API
- Voice recognition: Browser `SpeechRecognition` / `webkitSpeechRecognition`

## Project Structure

```text
root/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── routes/
│   ├── models/
│   ├── services/
│   ├── utils/
│   ├── requirements.txt
│   ├── .env
│   └── venv/              # created by setup command
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── .env
│   └── node_modules/      # created by npm install
└── README.md
```

## Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backend:

```bash
python app.py
```

The Flask API runs on `http://localhost:5000`.

## Backend Environment

Create or edit `backend/.env`:

```env
MONGO_URI=mongodb://localhost:27017/shopjmd
MONGO_DB_NAME=shopjmd
MONGO_SUPPLIERS_COLLECTION=shopjmd_suppliers
MONGO_TRANSACTIONS_COLLECTION=shopjmd_transactions
GROQ_API_KEY=your_key
GROQ_MODEL=llama3-70b-8192
SHOP_NAME=Shop JMD
FRONTEND_ORIGIN=http://localhost:5173
PORT=5000
FLASK_DEBUG=true
```

`bson.ObjectId` is provided by `pymongo`; do not install the standalone `bson` package because it can conflict with PyMongo.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The React app runs on `http://localhost:5173`.

## Frontend Environment

Create or edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:5000
```

## MongoDB Setup

Install and start MongoDB locally, then use:

```env
MONGO_URI=mongodb://localhost:27017/shopjmd
```

For MongoDB Atlas, replace `MONGO_URI` with your Atlas connection string and keep `MONGO_DB_NAME=shopjmd`. The default collections are `shopjmd_suppliers` and `shopjmd_transactions`.

## Deployment

Deploy the frontend on Vercel from the `frontend` directory. The included `frontend/vercel.json` builds the Vite app to `dist` and rewrites frontend routes to `index.html`.

Set this Vercel environment variable:

```env
VITE_API_URL=https://your-render-api.onrender.com
```

Deploy the backend on Render using the included `render.yaml`. Render installs `backend/requirements.txt` and starts the API with Gunicorn through `backend/wsgi.py`.

Set these Render environment variables:

```env
MONGO_URI=your_mongodb_atlas_uri
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
GROQ_API_KEY=your_key
```

## Groq API Setup

1. Create a Groq API key from your Groq dashboard.
2. Put it in `backend/.env` as `GROQ_API_KEY`.
3. Keep `GROQ_MODEL=llama3-70b-8192` or replace it with another Groq chat model available to your account.

If the key is missing, the backend still returns a basic regex-based fallback parse for development.

## Features

- Add, edit, delete, and view suppliers
- Supplier fields: name, mobile number, address, notes, opening balance, created date
- Credit and debit ledger transactions
- Quantity, unit, rate, amount, description, date, and created timestamp
- Running supplier balance
- Dashboard cards for suppliers, credit, debit, net balance, and recent transactions
- Voice entry in Hindi/Hinglish using browser speech recognition
- Groq-powered parsing into structured transaction JSON
- Confirmation modal before saving voice transactions
- Supplier ledger PDF with date range, totals, and final balance
- Responsive sidebar layout, clean tables, large buttons, loading states, validation, and toast feedback

## API Endpoints

Supplier APIs:

- `POST /api/suppliers`
- `GET /api/suppliers`
- `GET /api/suppliers/:id`
- `PUT /api/suppliers/:id`
- `DELETE /api/suppliers/:id`

Transaction APIs:

- `POST /api/transactions`
- `GET /api/transactions`
- `GET /api/suppliers/:id/transactions`

Voice and reports:

- `POST /api/parse-voice`
- `GET /api/suppliers/:id/pdf`
- `GET /api/dashboard`

## Example Voice Phrases

- `Ramesh supplier ko 10 katta 500 rupaye me debit karo`
- `Shyam se 20 bag 300 rate par credit`
- `10 katter bh ke inte rupees me`

Expected parsed shape:

```json
{
  "supplier_name": "",
  "transaction_type": "credit",
  "quantity": 0,
  "unit": "",
  "rate": 0,
  "amount": 0,
  "date": "YYYY-MM-DD",
  "description": ""
}
```

When amount is missing, the backend calculates `amount = quantity * rate`.
