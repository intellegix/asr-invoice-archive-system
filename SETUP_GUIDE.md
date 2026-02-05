# Complete Setup & Deployment Guide
## ASR Invoice Management System 2.0 - Claude AI Enhanced

**Last Updated:** December 15, 2025
**Estimated Setup Time:** 15-20 minutes

---

## 📋 Prerequisites

### Required Software
- ✅ **Python 3.8+** - [Download](https://www.python.org/downloads/)
- ✅ **Node.js 14+** (for anomaly detection) - [Download](https://nodejs.org/)
- ✅ **Git** (optional) - [Download](https://git-scm.com/)

### Required Credentials
- ✅ **Anthropic API Key** - Already configured in your `.env` file

### System Requirements
- **OS:** Windows 10/11, macOS, or Linux
- **RAM:** 4GB minimum (8GB recommended)
- **Disk Space:** 500MB free space
- **Internet:** Required for Claude AI API

---

## 🚀 Step-by-Step Setup

### Part 1: Python Backend Setup (10 minutes)

#### Step 1: Navigate to Project Directory
```bash
cd "ASR Records APP 2.0/ASR Records App/invoice-archive-system"
```

#### Step 2: Run Installation Script (Windows)
```bash
install_claude.bat
```

**Or Manual Installation:**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Verify Installation
```bash
python test_claude_integration.py
```

You should see:
```
✓ PASS: ANTHROPIC_API_KEY is set
✓ PASS: Claude service is available
✓ PASS: All tests passed
```

#### Step 4: Start the Server
```bash
python run_server.py
```

Or use the batch file:
```bash
run_server.bat
```

Server will start at: **http://localhost:8000**

#### Step 5: Verify Server is Running
Open your browser and visit:
- **API Docs:** http://localhost:8000/docs
- **Main App:** http://localhost:8000

You should see the FastAPI documentation interface.

---

### Part 2: JavaScript Anomaly Detection Setup (5 minutes)

#### Step 1: Navigate to Anomaly Detection Directory
```bash
cd "../anomaly detection logic/claude anomaly detection"
```

#### Step 2: Install Dependencies
```bash
npm install
```

This installs:
- `@anthropic-ai/sdk` - Claude AI integration

#### Step 3: Verify Configuration
Check that `.env` file exists with your API key:
```bash
# Should show your ANTHROPIC_API_KEY
type .env    # Windows
cat .env     # Mac/Linux
```

#### Step 4: Test Anomaly Detection
```bash
npm start
```

You should see analysis results in the `analysis_results/` folder.

---

### Part 3: Verification & Testing (5 minutes)

#### Test 1: Check AI Status
```bash
curl http://localhost:8000/ai/status
```

Expected response:
```json
{
  "available": true,
  "model": "claude-sonnet-4-5-20250929",
  "features": {
    "document_analysis": true,
    "categorization": true,
    ...
  }
}
```

#### Test 2: Run Demo Scripts

**Python Demo:**
```bash
cd invoice-archive-system
python examples/demo_claude_features.py
```

**Real-World Workflow Demo:**
```bash
python examples/real_world_workflow.py
```

#### Test 3: Test Document Analysis
Visit http://localhost:8000/docs and try the `/ai/analyze-document` endpoint with:

```json
{
  "text_content": "INVOICE\nABC Corp\nAmount: $1,234.56\nDate: 2025-01-15",
  "filename": "test.pdf"
}
```

---

## 🗂️ Post-Setup: File Cleanup

### Review DELETE Folder

Navigate to the `DELETE` folder:
```bash
cd "ASR Records APP 2.0/ASR Records App/DELETE"
```

**Contents:**
- `_BACKUPS/` - 16KB
- `_OLD_SNAPSHOTS/` - 130KB
- `_VIRTUAL_ENVS/` - 76MB (regenerable)
- `_OLD_DATABASES/` - 2.9GB

**To Free ~3GB:**
```bash
# Review contents first, then delete
# Windows:
rmdir /s DELETE

# Mac/Linux:
rm -rf DELETE
```

⚠️ **Regenerate Virtual Environment if Needed:**
```bash
cd invoice-archive-system
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📍 Directory Structure

After setup, your structure should look like:

```
ASR Records APP 2.0/ASR Records App/
├── invoice-archive-system/
│   ├── venv/                    # ✅ Virtual environment
│   ├── api/
│   │   ├── main.py
│   │   └── ai_endpoints.py      # ✅ AI endpoints
│   ├── services/
│   │   ├── claude_service.py    # ✅ Claude service
│   │   └── ...
│   ├── examples/
│   │   ├── demo_claude_features.py      # ✅ Demos
│   │   └── real_world_workflow.py       # ✅ Workflows
│   ├── .env                     # ✅ API key configured
│   └── requirements.txt         # ✅ Updated
│
├── anomaly detection logic/
│   └── claude anomaly detection/
│       ├── node_modules/        # ✅ Dependencies installed
│       ├── claudeIntegration.js # ✅ AI integration
│       ├── .env                 # ✅ API key configured
│       └── package.json         # ✅ Updated
│
├── Digital Billing Records/     # ✅ Active database
├── CLOSED Billing/              # ✅ Archive
├── DELETE/                      # ⚠️ Review & delete
│
├── QUICK_START.md               # ✅ Quick reference
├── CLAUDE_AI_INTEGRATION_GUIDE.md  # ✅ Full guide
├── IMPLEMENTATION_SUMMARY.md    # ✅ Implementation details
├── SETUP_GUIDE.md               # ✅ This file
└── README.md                    # ✅ Overview
```

---

## 🎯 Quick Access Commands

### Start the API Server
```bash
cd "invoice-archive-system"
python run_server.py
```

### Run Tests
```bash
cd "invoice-archive-system"
python test_claude_integration.py
```

### Run Demos
```bash
cd "invoice-archive-system"
python examples/demo_claude_features.py
python examples/real_world_workflow.py
```

### Run Anomaly Detection
```bash
cd "anomaly detection logic/claude anomaly detection"
npm start
```

### Access API Documentation
http://localhost:8000/docs

---

## 🔧 Configuration

### Environment Variables

**Location:** `invoice-archive-system/.env`

**Key Variables:**
```bash
# API Key (Required)
ANTHROPIC_API_KEY=sk-ant-api03-z7ekhhHIJ...

# Claude Configuration
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.3

# Feature Flags
AI_DOCUMENT_ANALYSIS_ENABLED=True
AI_ANOMALY_DETECTION_ENABLED=True
AI_NATURAL_LANGUAGE_SEARCH_ENABLED=True
AI_AUTO_CATEGORIZATION_ENABLED=True
AI_WORKFLOW_SUGGESTIONS_ENABLED=True

# API Settings
API_HOST=127.0.0.1
API_PORT=8000

# Database
DATABASE_URL=sqlite:///./data/invoice_archive.db
```

### Change API Port

Edit `.env`:
```bash
API_PORT=8001  # Use different port
```

### Disable AI Features

Edit `.env`:
```bash
AI_DOCUMENT_ANALYSIS_ENABLED=False  # Disable specific feature
```

---

## 🧪 Testing Checklist

Use this checklist to verify everything is working:

- [ ] Python installed and accessible
- [ ] Virtual environment created
- [ ] All Python dependencies installed
- [ ] Claude service initialized
- [ ] API server starts without errors
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] `/ai/status` endpoint returns `"available": true`
- [ ] Node.js installed (for anomaly detection)
- [ ] NPM dependencies installed
- [ ] Anomaly detection runs successfully
- [ ] Demo scripts run without errors
- [ ] Document analysis works
- [ ] Natural language search works
- [ ] Anomaly detection works

---

## 🚨 Troubleshooting

### Issue: "Python not found"
**Solution:**
1. Install Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart terminal

### Issue: "Module not found" errors
**Solution:**
```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Claude AI service is not available"
**Solution:**
1. Check `.env` file has `ANTHROPIC_API_KEY`
2. Verify API key is valid
3. Check internet connection
4. Try restarting the server

### Issue: Port 8000 already in use
**Solution:**
```bash
# Option 1: Change port in .env
API_PORT=8001

# Option 2: Kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8000
kill <PID>
```

### Issue: "Permission denied" on venv creation
**Solution:**
```bash
# Run as administrator (Windows)
# Or use sudo (Mac/Linux)
sudo python -m venv venv
```

### Issue: NPM install fails
**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Try again
npm install
```

---

## 📊 Usage Examples

### Example 1: Analyze an Invoice

**Via API (http://localhost:8000/docs):**

POST `/ai/analyze-document`:
```json
{
  "text_content": "INVOICE\nABC Construction\nInvoice: 12345\nAmount: $5,000.00",
  "filename": "invoice_12345.pdf"
}
```

**Via Python:**
```python
from services.claude_service import claude_service
import asyncio

async def analyze():
    result = await claude_service.analyze_document(
        text_content="Your invoice text here",
        filename="invoice.pdf"
    )
    print(result)

asyncio.run(analyze())
```

### Example 2: Natural Language Search

**Via API:**

POST `/ai/search/natural-language`:
```json
{
  "query": "Show me all unpaid invoices over $5,000"
}
```

### Example 3: Detect Fraud

**Via API:**

POST `/ai/detect-anomalies`:
```json
{
  "invoice_data": {
    "vendor_name": "Test Corp",
    "amount": 9999.99,
    "date": "2025-12-31"
  }
}
```

---

## 🔄 Daily Operations

### Starting Your Day
```bash
# 1. Navigate to project
cd "ASR Records APP 2.0/ASR Records App/invoice-archive-system"

# 2. Activate environment
venv\Scripts\activate

# 3. Start server
python run_server.py
```

### Processing Invoices
1. Upload invoice PDF to system
2. System automatically:
   - Extracts metadata with Claude AI
   - Categorizes invoice
   - Checks for fraud
   - Suggests workflow
3. Review high-risk items
4. Approve and route

### End of Day
1. Review flagged invoices
2. Generate reports
3. Shut down server (Ctrl+C)

---

## 📈 Performance Optimization

### For Large Datasets

**Enable Batch Processing:**
```python
# Process multiple invoices at once
results = await batch_analyze_invoices(invoice_list)
```

**Use Caching:**
```python
# Cache repeated queries
from functools import lru_cache
```

**Optimize Database:**
```bash
# Use PostgreSQL for production
# Edit .env:
DATABASE_URL=postgresql://user:pass@localhost/invoice_db
```

### For Faster API Responses

**Increase Workers:**
```python
# In run_server.py
uvicorn.run(
    "main:app",
    workers=4,  # Multiple workers
    host=settings.API_HOST,
    port=settings.API_PORT
)
```

---

## 🔐 Security Best Practices

1. **Protect API Key**
   - Never commit `.env` to version control
   - Rotate keys regularly
   - Use environment-specific keys

2. **Enable Authentication**
   - Add API key authentication
   - Implement user roles
   - Audit all access

3. **Secure Database**
   - Use strong passwords
   - Enable encryption
   - Regular backups

4. **Monitor Usage**
   - Track API calls
   - Set up alerts
   - Review logs regularly

---

## 📚 Additional Resources

### Documentation
- **Quick Start:** `QUICK_START.md`
- **Full Integration Guide:** `CLAUDE_AI_INTEGRATION_GUIDE.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`
- **System Overview:** `README.md`

### API Documentation
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### External Resources
- **Claude API Docs:** https://docs.anthropic.com/
- **FastAPI Tutorial:** https://fastapi.tiangolo.com/tutorial/
- **Python Best Practices:** https://docs.python-guide.org/

---

## ✅ Setup Complete!

If you've followed all steps, you should now have:

- ✅ Python backend running with Claude AI
- ✅ JavaScript anomaly detection configured
- ✅ All tests passing
- ✅ Demo scripts working
- ✅ API accessible and documented
- ✅ Files organized and cleaned up

**You're ready to revolutionize your invoice management!** 🚀

---

## 🎓 Next Steps

1. **Learn the Features**
   - Read `QUICK_START.md` for quick reference
   - Review `CLAUDE_AI_INTEGRATION_GUIDE.md` for details

2. **Start Processing**
   - Upload your first invoice
   - Try natural language search
   - Review fraud detection results

3. **Customize**
   - Adjust detection thresholds
   - Configure workflows
   - Set up automation rules

4. **Scale Up**
   - Process historical invoices
   - Set up scheduled analysis
   - Generate regular reports

---

**Need Help?** Check the troubleshooting section or review the comprehensive documentation.

**Ready to begin!** 🎉
