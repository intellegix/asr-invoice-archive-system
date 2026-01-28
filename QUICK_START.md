# Quick Start Guide - Claude AI Enhanced System
## Get Up and Running in 5 Minutes

---

## 🚀 Installation (One Time)

### Python Backend
```bash
cd invoice-archive-system
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### JavaScript Anomaly Detection
```bash
cd "anomaly detection logic/claude anomaly detection"
npm install
```

---

## ▶️ Start the System

```bash
cd invoice-archive-system
python run_server.py
```

API Server runs at: **http://localhost:8000**

---

## 🧪 Test AI Features

### 1. Check AI Status
```bash
curl http://localhost:8000/ai/status
```

### 2. Run Demo Script
```bash
python examples/demo_claude_features.py
```

### 3. Open API Docs
Visit: **http://localhost:8000/docs**

---

## 💬 Try Natural Language Search

In the API docs, test `/ai/search/natural-language`:

**Example Queries:**
- "Show me all unpaid invoices"
- "What's our total spending this month?"
- "Find invoices from ABC Construction over $5,000"
- "Are there any overdue payments?"

---

## 📊 Analyze an Invoice

**Endpoint:** POST `/ai/analyze-document`

**Request:**
```json
{
  "text_content": "INVOICE\nABC Corp\nInvoice: 123\nAmount: $1,234.56",
  "filename": "invoice.pdf"
}
```

**What you get:**
- Vendor name
- Amount extracted
- Date detection
- Category suggestion
- Confidence score

---

## 🚨 Detect Fraud

**Endpoint:** POST `/ai/detect-anomalies`

**Request:**
```json
{
  "invoice_data": {
    "vendor_name": "Test Vendor",
    "amount": 9999.99,
    "date": "2025-12-31"
  }
}
```

**What you get:**
- Risk score (0-1)
- Fraud indicators
- Recommendations
- Reasoning

---

## 🗂️ File Cleanup

Review the `DELETE` folder:
```
DELETE/
├── _BACKUPS/ (16KB)
├── _OLD_SNAPSHOTS/ (130KB)
├── _VIRTUAL_ENVS/ (76MB)
└── _OLD_DATABASES/ (2.9GB)

Total to free: ~3GB
```

**Safe to delete all files** - They're backups or regenerable.

---

## 📚 Documentation

- **Full Guide:** `CLAUDE_AI_INTEGRATION_GUIDE.md`
- **Summary:** `IMPLEMENTATION_SUMMARY.md`
- **API Docs:** http://localhost:8000/docs

---

## 🎯 Key Features

| Feature | Endpoint | What It Does |
|---------|----------|--------------|
| Document Analysis | `/ai/analyze-document` | Extract invoice metadata |
| Categorization | `/ai/categorize` | Smart invoice categorization |
| Fraud Detection | `/ai/detect-anomalies` | Detect anomalies & fraud |
| Natural Search | `/ai/search/natural-language` | Query with plain English |
| Workflow Suggestions | `/ai/suggest-workflow` | Automation recommendations |
| Chat Interface | `/ai/chat` | Conversational queries |

---

## ⚙️ Configuration

All settings in: `invoice-archive-system/.env`

**Key Variables:**
```bash
ANTHROPIC_API_KEY=your-key-here  # ✅ Already configured
CLAUDE_MODEL=claude-sonnet-4-5-20250929
AI_DOCUMENT_ANALYSIS_ENABLED=True
AI_ANOMALY_DETECTION_ENABLED=True
```

---

## 🐛 Quick Troubleshooting

**Problem:** "Claude AI service is not available"
- Check `.env` has `ANTHROPIC_API_KEY`
- Run: `pip install anthropic`

**Problem:** Import errors
- Activate venv: `venv\Scripts\activate`
- Reinstall: `pip install -r requirements.txt`

**Problem:** Server won't start
- Check port 8000 is free
- Try different port in `.env`: `API_PORT=8001`

---

## 🎉 You're Ready!

**Start using AI features now:**
1. ✅ API key configured
2. ✅ Dependencies installed
3. ✅ Server running
4. ✅ Try the demo script
5. ✅ Visit API docs

**Happy invoicing!** 🚀
