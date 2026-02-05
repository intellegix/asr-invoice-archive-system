# Digital Records Management System - Complete Blueprint

**Project:** Intellegix Digital Records Audit & Review Platform  
**Status:** Development Blueprint  
**Version:** 1.0  
**Date:** December 08, 2025  
**Stack:** HTML5/CSS/JavaScript + PDF.js → C# WPF (future)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Directory Structure](#directory-structure)
4. [Phase 1: MVP (Weeks 1-2)](#phase-1-mvp-weeks-1-2)
5. [Phase 2: Enhancement (Weeks 3-4)](#phase-2-enhancement-weeks-3-4)
6. [Phase 3: Advanced Features](#phase-3-advanced-features)
7. [Data Schemas](#data-schemas)
8. [UI/UX Specifications](#uiux-specifications)
9. [Database Strategy](#database-strategy)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Testing Strategy](#testing-strategy)
12. [Deployment & Distribution](#deployment--distribution)

---

## Project Overview

### Purpose
Build a user-friendly digital records management application that allows users to:
- **Store** batch-scanned PDFs with metadata
- **Review** digitized records in an intuitive UI
- **Audit** access and modifications with full trail
- **Navigate** records dynamically with search/filter
- **Export** records and audit reports

### Use Cases
1. **Employee Records Review** - Access batched employee documents (payroll, HR, benefits)
2. **Invoice & Billing Audit** - Review scanned billing documents with audit trail
3. **Compliance Verification** - Demonstrate document handling and review process
4. **Records Digitization** - Transform paper records into auditable digital format

### Target Users
- Systems Integration staff reviewing digitized records
- Compliance officers auditing document handling
- HR/Payroll teams verifying employee records
- Clients of Intellegix requiring document audit trails

### Success Criteria
- [ ] Load and display batch-scanned PDFs without errors
- [ ] Search/filter records in <500ms
- [ ] Multi-page PDF navigation smooth and responsive
- [ ] Audit trail captures all access events
- [ ] Simple enough for non-technical users
- [ ] Deployable as single .BAT file for testing
- [ ] Scalable to 50,000+ records

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE (HTML/CSS/JS)         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Left Panel    │   Center Panel   │  Right Panel  │  │
│  │  Records List  │   PDF Viewer     │  Metadata     │  │
│  │  Search/Filter │   Page Nav       │  Audit Trail  │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       │                               │
┌──────▼──────────┐          ┌────────▼─────────┐
│  Data Layer     │          │  PDF.js Library  │
│  - records.json │          │  - PDF Rendering │
│  - audits.json  │          │  - Canvas Display│
│  - User Prefs   │          │  - Page Mgmt     │
└─────────────────┘          └──────────────────┘
       │
┌──────▼──────────────────────────┐
│   File System Access            │
│   ├── data/documents/*.pdf      │
│   ├── data/records.json         │
│   └── data/audits.json          │
└─────────────────────────────────┘
```

### Technology Stack

#### Phase 1 (MVP): Browser-Based
- **Frontend Framework:** Vanilla JavaScript (no dependencies)
- **UI Framework:** Custom CSS with design system variables
- **PDF Rendering:** PDF.js (Mozilla)
- **Data Storage:** JSON files
- **Server:** Python SimpleHTTPServer OR Node.js http-server
- **Execution:** run.bat → Launches server + opens browser

#### Phase 2 (Enhancement): Browser-Based (Advanced)
- **State Management:** Simple ES6 class-based architecture
- **Search/Filter:** Lunr.js (client-side full-text)
- **Data:** SQLite with Node.js
- **Execution:** Electron app or standalone .exe

#### Phase 3 (Production): Native Windows
- **Language:** C# (.NET 8 or higher)
- **Framework:** WPF (Windows Presentation Foundation)
- **PDF Rendering:** PdfSharp or PDFiumSharp
- **Database:** SQLite with Entity Framework Core
- **Distribution:** Single .exe installer

---

## Directory Structure

### Complete Project Layout

```
DigitalRecordsManager/
│
├── run.bat                          # Starter script (Phase 1)
├── run.ps1                          # PowerShell alternative
├── README.md                        # Project documentation
├── .gitignore                       # Git ignore rules
│
├── data/                            # All user data
│   ├── records.json                 # Record metadata index
│   ├── audits.json                  # Audit trail log
│   ├── user_preferences.json        # UI state & settings
│   ├── documents/                   # PDF storage
│   │   ├── 2025-01-001.pdf
│   │   ├── 2025-01-002.pdf
│   │   ├── 2025-02-001.pdf
│   │   └── ...
│   └── backup/                      # Auto-backup folder
│       ├── records_backup_20250108.json
│       └── audits_backup_20250108.json
│
├── app/                             # Application code
│   ├── index.html                   # Main UI (Phase 1)
│   ├── styles/
│   │   ├── main.css                 # Primary stylesheet
│   │   ├── layout.css               # Grid/flexbox layouts
│   │   ├── components.css           # Reusable components
│   │   ├── theme.css                # Color system & variables
│   │   └── responsive.css           # Mobile/tablet rules
│   ├── scripts/
│   │   ├── app.js                   # Main application logic
│   │   ├── pdf-viewer.js            # PDF.js integration
│   │   ├── records-manager.js       # Record CRUD operations
│   │   ├── audit-logger.js          # Audit trail tracking
│   │   ├── search-filter.js         # Search/filter engine
│   │   ├── ui-controller.js         # UI event handling
│   │   └── utils.js                 # Utility functions
│   └── lib/                         # Third-party libraries
│       └── pdf.min.js               # PDF.js library
│
├── server/                          # Backend (Phase 2+)
│   ├── server.js                    # Express/Node server
│   ├── api/
│   │   ├── records.js               # Record endpoints
│   │   ├── audits.js                # Audit endpoints
│   │   └── documents.js             # Document endpoints
│   ├── database/
│   │   ├── db.js                    # Database connection
│   │   ├── models/
│   │   │   ├── Record.js
│   │   │   ├── Audit.js
│   │   │   └── User.js
│   │   └── records.db               # SQLite database
│   └── middleware/
│       ├── auth.js                  # Authentication
│       └── logging.js               # Request logging
│
├── desktop/                         # WPF Project (Phase 3)
│   ├── DigitalRecordsManager.sln
│   ├── DigitalRecordsManager/
│   │   ├── App.xaml
│   │   ├── App.xaml.cs
│   │   ├── MainWindow.xaml
│   │   ├── MainWindow.xaml.cs
│   │   ├── ViewModels/
│   │   ├── Models/
│   │   ├── Services/
│   │   └── Resources/
│   └── ...
│
├── tests/                           # Test suites
│   ├── unit/
│   │   ├── records-manager.test.js
│   │   ├── search-filter.test.js
│   │   └── audit-logger.test.js
│   ├── integration/
│   │   ├── pdf-loading.test.js
│   │   └── data-persistence.test.js
│   └── e2e/
│       └── user-workflow.test.js
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md              # System design
│   ├── API.md                       # API documentation
│   ├── USER_GUIDE.md                # End-user guide
│   ├── DEVELOPER_GUIDE.md           # Development guide
│   └── DEPLOYMENT.md                # Deployment steps
│
├── config/                          # Configuration files
│   ├── app.config.json              # App settings
│   ├── database.config.json         # DB settings
│   ├── logging.config.json          # Log settings
│   └── theme.config.json            # Theme settings
│
├── scripts/                         # Utility scripts
│   ├── generate-sample-data.js      # Create test records
│   ├── migrate-data.js              # Data migration tools
│   ├── export-audit-report.js       # Report generation
│   └── backup-data.js               # Backup automation
│
└── CHANGELOG.md                     # Version history
```

### Recommended File Sizes (Phase 1)

| File | Size | Purpose |
|------|------|---------|
| index.html | 25-35KB | Main UI markup |
| main.css | 15-20KB | Styling |
| app.js | 30-50KB | Core logic |
| pdf.min.js | 600-700KB | PDF.js library |
| records.json | Variable | Metadata (100KB = ~2000 records) |

---

## Phase 1: MVP (Weeks 1-2)

### Goals
✅ Working record browser with PDF viewing  
✅ Search and basic filtering  
✅ Audit logging for access  
✅ Deployable via run.bat

### Components to Build

#### 1.1 Data Files

**records.json** (Master Record Index)
```json
{
  "version": "1.0",
  "lastModified": "2025-01-15T10:30:00Z",
  "totalRecords": 2,
  "records": [
    {
      "id": "2025-01-001",
      "filename": "2025-01-001.pdf",
      "docType": "Employee Record",
      "department": "Payroll",
      "dateScanned": "2025-01-10T14:30:00Z",
      "scannerName": "Scanner-01",
      "pageCount": 12,
      "fileSize": 2400000,
      "status": "verified",
      "tags": ["payroll", "2025", "batch-001"],
      "description": "Complete employee personnel file",
      "checksum": "abc123def456",
      "metadata": {
        "employee_id": "EMP-12345",
        "name": "John Doe",
        "period": "2025-01-01 to 2025-01-31"
      }
    },
    {
      "id": "2025-01-002",
      "filename": "2025-01-002.pdf",
      "docType": "Invoice",
      "department": "Finance",
      "dateScanned": "2025-01-11T09:15:00Z",
      "scannerName": "Scanner-02",
      "pageCount": 3,
      "fileSize": 456000,
      "status": "verified",
      "tags": ["billing", "january", "batch-001"],
      "description": "Monthly invoice for vendor ABC",
      "checksum": "xyz789uvw012",
      "metadata": {
        "vendor_id": "VND-54321",
        "invoice_number": "INV-2025-001",
        "amount": "$5,234.50"
      }
    }
  ]
}
```

**audits.json** (Audit Trail Log)
```json
{
  "version": "1.0",
  "lastModified": "2025-01-15T11:45:00Z",
  "totalEvents": 3,
  "events": [
    {
      "eventId": "evt-001",
      "recordId": "2025-01-001",
      "timestamp": "2025-01-15T10:30:00Z",
      "action": "viewed",
      "user": "john.doe",
      "details": {
        "pagesViewed": [1, 2, 3],
        "timeSpent": 180,
        "zoomLevel": 1.5
      }
    },
    {
      "eventId": "evt-002",
      "recordId": "2025-01-001",
      "timestamp": "2025-01-15T10:45:00Z",
      "action": "exported",
      "user": "manager",
      "details": {
        "format": "PDF",
        "pages": "all"
      }
    },
    {
      "eventId": "evt-003",
      "recordId": "2025-01-001",
      "timestamp": "2025-01-15T11:00:00Z",
      "action": "approved",
      "user": "auditor",
      "details": {
        "status": "verified",
        "notes": "All documents match source records",
        "approvalDate": "2025-01-15"
      }
    }
  ]
}
```

#### 1.2 HTML Structure

**index.html** - Key Sections:
```
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Digital Records Manager</title>
  <link rel="stylesheet" href="styles/main.css">
</head>
<body>
  <div class="app-container">
    
    <!-- Left Panel: Records List -->
    <aside class="records-panel">
      <header class="panel-header">
        <h1>Digital Records</h1>
        <div class="controls">
          <input type="search" id="searchBox" placeholder="Search records...">
          <button id="advancedFilterBtn">Filters</button>
        </div>
      </header>
      <div id="recordsList" class="records-list"></div>
    </aside>
    
    <!-- Center Panel: PDF Viewer -->
    <main class="viewer-panel">
      <header class="panel-header">
        <div class="breadcrumb" id="breadcrumb"></div>
        <div class="viewer-controls">
          <button id="zoomOut">−</button>
          <span id="zoomLevel">100%</span>
          <button id="zoomIn">+</button>
          <button id="fitWidth">Fit Width</button>
          <button id="fitPage">Fit Page</button>
        </div>
        <div class="page-controls">
          <button id="prevPage">← Prev</button>
          <span id="pageInfo">1 / 0</span>
          <button id="nextPage">Next →</button>
          <input type="number" id="pageJump" placeholder="Go to page" min="1">
        </div>
      </header>
      <div id="pdfContainer" class="pdf-viewer">
        <canvas id="pdfCanvas"></canvas>
      </div>
      <footer class="panel-footer">
        <span id="status">Ready</span>
      </footer>
    </main>
    
    <!-- Right Panel: Metadata & Audit -->
    <aside class="metadata-panel">
      <header class="panel-header">
        <h2>Details</h2>
      </header>
      <div id="metadataPanel" class="metadata-content">
        <div class="empty-state">Select a record to view details</div>
      </div>
    </aside>
    
  </div>

  <script src="lib/pdf.min.js"></script>
  <script src="scripts/app.js"></script>
  <script src="scripts/pdf-viewer.js"></script>
  <script src="scripts/records-manager.js"></script>
  <script src="scripts/audit-logger.js"></script>
  <script src="scripts/search-filter.js"></script>
  <script src="scripts/ui-controller.js"></script>
  <script src="scripts/utils.js"></script>
</body>
</html>
```

#### 1.3 CSS Layout (main.css)

Key structure:
- CSS Grid for 3-column layout (320px | 1fr | 280px)
- Flexbox for internal components
- CSS variables for theming
- Responsive breakpoints for mobile

#### 1.4 JavaScript Modules

**app.js** - Application State & Initialization
```javascript
class DigitalRecordsApp {
  constructor() {
    this.records = [];
    this.audits = [];
    this.currentRecord = null;
    this.currentPage = 1;
    this.totalPages = 0;
    this.userSession = {
      userId: 'user-001',
      sessionStart: new Date(),
      actions: []
    };
  }

  async init() {
    // Load data from JSON files
    // Initialize UI components
    // Setup event listeners
    // Create sample data if needed
  }

  logAuditEvent(action, details = {}) {
    // Create audit event
    // Save to audits.json
    // Update UI audit panel
  }
}
```

**pdf-viewer.js** - PDF Rendering
```javascript
class PDFViewer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.pdfDoc = null;
    this.currentPage = 1;
    this.scale = 1.5;
  }

  async loadPDF(filePath) {
    // Load PDF using PDF.js
    // Render first page
    // Update page count
  }

  renderPage(pageNum) {
    // Render specific page to canvas
    // Handle errors
  }

  nextPage() { }
  prevPage() { }
  goToPage(num) { }
  zoom(direction) { }
}
```

**records-manager.js** - Data Operations
```javascript
class RecordsManager {
  constructor(dataPath = 'data/') {
    this.dataPath = dataPath;
    this.records = [];
  }

  async loadRecords() {
    // Fetch records.json
    // Parse and validate
    // Cache in memory
  }

  addRecord(recordData) { }
  updateRecord(recordId, updates) { }
  deleteRecord(recordId) { }
  getRecord(recordId) { }
  
  async saveRecords() {
    // Serialize to JSON
    // Save to file system
  }
}
```

**audit-logger.js** - Audit Trail
```javascript
class AuditLogger {
  constructor(dataPath = 'data/') {
    this.dataPath = dataPath;
    this.events = [];
  }

  async logEvent(recordId, action, details = {}) {
    const event = {
      eventId: generateId(),
      recordId,
      timestamp: new Date().toISOString(),
      action,
      user: getCurrentUser(),
      details
    };
    
    this.events.push(event);
    await this.saveEvents();
  }

  getRecordAuditTrail(recordId) { }
  async saveEvents() { }
}
```

**search-filter.js** - Search & Filter Engine
```javascript
class SearchFilter {
  constructor(records) {
    this.records = records;
    this.filteredResults = records;
  }

  search(query) {
    // Simple text search across:
    // - id, docType, description, tags, metadata
    return this.records.filter(r => 
      r.id.includes(query) ||
      r.docType.includes(query) ||
      r.description.includes(query) ||
      JSON.stringify(r).includes(query)
    );
  }

  filter(criteria) {
    // Filter by:
    // - docType, dateRange, department, status, tags
  }

  combineSearchAndFilter(query, criteria) { }
}
```

### Phase 1 Deliverables

- ✅ Complete HTML/CSS/JS application
- ✅ Sample records.json with 5-10 test documents
- ✅ Sample audits.json with audit events
- ✅ PDF.js integration for rendering
- ✅ Search functionality (basic)
- ✅ Audit trail logging
- ✅ run.bat script for execution
- ✅ README with quick start guide
- ✅ Sample PDFs in data/documents/ folder

---

## Phase 2: Enhancement (Weeks 3-4)

### Goals
✅ Advanced filtering and search  
✅ Audit trail visualization  
✅ User sessions & preferences  
✅ Data persistence (upgrade to SQLite)  
✅ Batch operations

### Components to Add

1. **Advanced Filtering UI**
   - Date range picker
   - Multi-select filters
   - Saved filter presets
   - Filter by user/department/status

2. **Audit Trail Visualization**
   - Timeline view of events
   - User access history
   - Document modification log
   - Statistics dashboard

3. **User Sessions**
   - User login (optional)
   - Session tracking
   - User preferences
   - Role-based access (future)

4. **Database Upgrade**
   - Migrate from JSON to SQLite
   - Implement data indexing
   - Query optimization
   - Backup automation

5. **Batch Operations**
   - Multi-select records
   - Bulk export
   - Bulk update metadata
   - Bulk audit marking

### Technology Additions
- Lunr.js for full-text search
- Chart.js for audit visualization
- Moment.js for date handling
- SQLite with Node.js driver

---

## Phase 3: Advanced Features

### Goals
✅ OCR text search  
✅ Document annotations  
✅ Workflow status tracking  
✅ Report generation  
✅ Advanced security

### Components to Add

1. **OCR Integration**
   - Tesseract.js for client-side OCR
   - Full-text search inside PDFs
   - Text extraction and export

2. **Annotations**
   - Highlight areas in PDF
   - Add comments/notes
   - Annotation persistence
   - Export annotated PDFs

3. **Workflow Status**
   - Document review states (new, reviewed, approved, rejected)
   - Workflow automation
   - Status change notifications
   - SLA tracking

4. **Report Generation**
   - Audit trail reports
   - Compliance reports
   - Record inventory reports
   - Export to PDF/Excel

5. **Security & Access Control**
   - User authentication
   - Role-based access control
   - Encryption of sensitive data
   - API authentication tokens
   - Activity logging for compliance

---

## Data Schemas

### Records Schema

```json
{
  "id": "string",                    // Unique identifier (YYYY-MM-NNN format)
  "filename": "string",              // PDF filename
  "docType": "string",               // Category (Employee Record, Invoice, etc.)
  "department": "string",            // Department/team
  "dateScanned": "ISO8601",          // When document was scanned
  "scannerName": "string",           // Scanner/device that scanned it
  "pageCount": "integer",            // Number of pages
  "fileSize": "integer",             // File size in bytes
  "status": "enum",                  // verified|pending|rejected|archived
  "tags": ["string"],                // Custom tags for categorization
  "description": "string",           // Human-readable description
  "checksum": "string",              // MD5 hash for integrity verification
  "metadata": {
    "[key]": "value"                 // Custom metadata fields
  },
  "createdAt": "ISO8601",            // When record was created in system
  "updatedAt": "ISO8601",            // Last modification
  "createdBy": "string",             // User who created record
  "lastModifiedBy": "string"         // Last user to modify
}
```

### Audits Schema

```json
{
  "eventId": "string",               // Unique event ID
  "recordId": "string",              // Reference to record
  "timestamp": "ISO8601",            // When action occurred
  "action": "enum",                  // viewed|edited|exported|approved|rejected|deleted
  "user": "string",                  // User who performed action
  "ipAddress": "string",             // (Optional) IP for remote access
  "userAgent": "string",             // (Optional) Browser/client info
  "details": {
    // Action-specific details
    "pagesViewed": ["integer"],      // For 'viewed' action
    "timeSpent": "integer",          // Seconds spent
    "changes": {
      "fieldName": {
        "oldValue": "value",
        "newValue": "value"
      }
    },                               // For 'edited' action
    "exportFormat": "string",        // For 'exported' action
    "approvalNotes": "string"        // For 'approved/rejected' actions
  }
}
```

### User Preferences Schema

```json
{
  "userId": "string",
  "theme": "enum",                   // light|dark
  "recordsPerPage": "integer",       // Default: 20
  "defaultZoom": "number",           // Default: 1.5
  "defaultSortBy": "string",         // dateScanned|docType|id
  "savedFilters": [{
    "name": "string",
    "criteria": { }
  }],
  "columnsVisible": ["string"],      // Which columns shown in list
  "lastAccessedRecord": "string",    // Last viewed record ID
  "sessionTimeout": "integer"        // Minutes before auto-logout
}
```

---

## UI/UX Specifications

### Layout Grid System

```
┌─────────────┬───────────────────────────┬───────────────┐
│   320px     │         1fr (flex)        │     280px     │
│             │                           │               │
│  Left Panel │      Center Panel         │  Right Panel  │
│             │                           │               │
└─────────────┴───────────────────────────┴───────────────┘
     Sidebar        Main Content Area       Side Details
```

### Left Panel: Records List

**Components:**
- Search box with real-time filtering
- Filter/Sort controls
- Scrollable record list
- Record item cards with:
  - Document type badge
  - Record ID
  - Scan date
  - Status indicator
  - Tag pills

**Interactions:**
- Click record → Load in center
- Hover → Show preview tooltip
- Right-click → Context menu (export, delete, view audit)
- Drag-drop → Organize into collections (Phase 2)

### Center Panel: PDF Viewer

**Components:**
- Breadcrumb navigation
- Page navigation (buttons + input)
- Zoom controls (in/out/fit-width/fit-page)
- Full PDF canvas
- Status bar

**Interactions:**
- Scroll through pages
- Keyboard shortcuts (arrow keys, +/-, J for jump)
- Click-to-zoom
- Pinch-to-zoom on mobile

### Right Panel: Metadata & Audit

**Sections:**
1. **Record Details** (collapsed/expandable)
   - Document type
   - Scan date
   - Page count
   - File size
   - Custom metadata

2. **Audit Trail** (scrollable)
   - Timeline of events
   - User, action, timestamp
   - Click event → Show details

3. **Quick Actions**
   - Export PDF
   - Print
   - Download
   - View full audit trail

### Color System

**Primary:**
- Primary Blue: #2180CE (actions, highlights)
- Primary Hover: #1A6AAA
- Success Green: #22B659
- Error Red: #C01530
- Warning Orange: #A84D2F

**Neutrals:**
- Text: #134252 (dark mode: #F5F5F5)
- Background: #FCFCF9 (dark mode: #1F2121)
- Border: #5E5240 at 20% opacity
- Disabled: #6B7C7C

### Typography

- **Font Family:** System UI stack (-apple-system, Segoe UI, etc.)
- **Headings:** Semibold (600 weight)
- **Body:** Regular (400 weight)
- **Small text:** 12px
- **Body text:** 14px
- **Headings:** 16px-20px

### Responsive Design

**Breakpoints:**
- **Desktop:** 1200px+ (3 columns)
- **Tablet:** 768px-1199px (2 columns, stacked right panel)
- **Mobile:** <768px (full-width stacked, left drawer)

---

## Database Strategy

### Phase 1: JSON Files
- ✅ Simple, no dependencies
- ✅ Easy to backup and share
- ✅ Good for < 5000 records
- ⚠️ No indexing
- ⚠️ Full file reads every time

**Files:**
- `data/records.json` - All record metadata
- `data/audits.json` - All audit events
- `data/user_preferences.json` - User settings

### Phase 2: SQLite Migration

**Database Schema:**

```sql
-- Records Table
CREATE TABLE records (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  docType TEXT,
  department TEXT,
  dateScanned DATETIME,
  scannerName TEXT,
  pageCount INTEGER,
  fileSize INTEGER,
  status TEXT,
  description TEXT,
  checksum TEXT,
  metadata JSON,
  createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  createdBy TEXT,
  lastModifiedBy TEXT,
  FULLTEXT tags
);

-- Audits Table
CREATE TABLE audits (
  eventId TEXT PRIMARY KEY,
  recordId TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  action TEXT,
  user TEXT,
  ipAddress TEXT,
  userAgent TEXT,
  details JSON,
  FOREIGN KEY (recordId) REFERENCES records(id)
);

-- Users Table (Phase 2+)
CREATE TABLE users (
  userId TEXT PRIMARY KEY,
  username TEXT UNIQUE,
  email TEXT,
  passwordHash TEXT,
  role TEXT,
  department TEXT,
  lastLogin DATETIME,
  createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User Preferences Table
CREATE TABLE user_preferences (
  userId TEXT PRIMARY KEY,
  theme TEXT DEFAULT 'light',
  recordsPerPage INTEGER DEFAULT 20,
  defaultZoom REAL DEFAULT 1.5,
  defaultSortBy TEXT,
  savedFilters JSON,
  columnsVisible JSON,
  lastAccessedRecord TEXT,
  sessionTimeout INTEGER DEFAULT 60,
  FOREIGN KEY (userId) REFERENCES users(userId)
);

-- Create Indexes
CREATE INDEX idx_records_docType ON records(docType);
CREATE INDEX idx_records_dateScanned ON records(dateScanned);
CREATE INDEX idx_records_status ON records(status);
CREATE INDEX idx_records_department ON records(department);
CREATE INDEX idx_audits_recordId ON audits(recordId);
CREATE INDEX idx_audits_timestamp ON audits(timestamp);
CREATE INDEX idx_audits_action ON audits(action);
```

**Migration Path:**
1. Keep both JSON and SQLite in sync (Phase 2 initial)
2. Deprecate JSON in Phase 2.1
3. JSON export available for backup

### Phase 3: Production Database

Options:
- **SQLite:** Single-file deployment
- **PostgreSQL:** Multi-user, cloud-ready
- **SQL Server:** Enterprise integration

---

## Implementation Roadmap

### Week 1: Core Infrastructure

**Monday-Tuesday:**
- [ ] Set up directory structure
- [ ] Create sample records.json (5 test PDFs)
- [ ] Create sample audits.json
- [ ] Build HTML structure and CSS layout
- [ ] Set up PDF.js and configure canvas

**Wednesday-Thursday:**
- [ ] Implement RecordsManager class
- [ ] Load and display records list
- [ ] Build search functionality
- [ ] Implement PDF loading and rendering

**Friday:**
- [ ] Page navigation controls
- [ ] Zoom controls
- [ ] Metadata panel display
- [ ] Create run.bat launcher

### Week 2: Enhancement & Polishing

**Monday-Tuesday:**
- [ ] Audit logging system
- [ ] Audit trail display
- [ ] Filter UI and logic
- [ ] Sort and re-order functionality

**Wednesday-Thursday:**
- [ ] Keyboard shortcuts
- [ ] Error handling and validation
- [ ] Empty states and loading states
- [ ] Performance optimization

**Friday:**
- [ ] User testing
- [ ] Bug fixes
- [ ] Documentation
- [ ] Release MVP v1.0

### Week 3-4: Phase 2 Features

**Week 3:**
- [ ] Advanced filtering UI
- [ ] Full-text search (Lunr.js)
- [ ] Date range pickers
- [ ] Saved filter presets

**Week 4:**
- [ ] Audit visualization (Charts)
- [ ] User sessions
- [ ] SQLite migration
- [ ] Batch operations
- [ ] Release v1.1

---

## Testing Strategy

### Unit Tests (Jest/Mocha)

```javascript
// test/records-manager.test.js
describe('RecordsManager', () => {
  it('should load records from JSON', async () => { });
  it('should add new record with validation', () => { });
  it('should update record metadata', () => { });
  it('should filter records by criteria', () => { });
});

// test/search-filter.test.js
describe('SearchFilter', () => {
  it('should search by ID', () => { });
  it('should search by docType', () => { });
  it('should combine search and filters', () => { });
  it('should handle special characters', () => { });
});

// test/audit-logger.test.js
describe('AuditLogger', () => {
  it('should log view event', () => { });
  it('should log export event', () => { });
  it('should retrieve audit trail for record', () => { });
});
```

### Integration Tests

```javascript
// test/integration/pdf-loading.test.js
describe('PDF Loading Integration', () => {
  it('should load PDF from file system', async () => { });
  it('should render PDF pages to canvas', async () => { });
  it('should navigate between pages', async () => { });
});

// test/integration/audit-flow.test.js
describe('Audit Flow', () => {
  it('should log event when record is viewed', () => { });
  it('should persist audit to disk', () => { });
  it('should display audit trail in UI', () => { });
});
```

### E2E Tests (Playwright/Selenium)

```javascript
// test/e2e/user-workflow.test.js
describe('User Workflow', () => {
  it('should open app and load records', () => { });
  it('should search and filter records', () => { });
  it('should view PDF and navigate pages', () => { });
  it('should export record and verify audit', () => { });
});
```

### Performance Benchmarks

- [ ] Load 1000 records in < 500ms
- [ ] Search 10,000 records in < 200ms
- [ ] Render PDF page in < 500ms
- [ ] UI response to user actions < 100ms
- [ ] Startup time < 3 seconds

### Browser Compatibility

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ⚠️ IE11 (not supported, too old)

---

## Deployment & Distribution

### Phase 1: Development (.BAT)

**run.bat:**
```batch
@echo off
REM Start Python HTTP Server on port 8000
REM Navigate to app directory
REM Open browser to localhost:8000

cd /d "%~dp0"
python -m http.server 8000
```

**Distribution:**
- Zip entire folder
- Include README with instructions
- No installation needed

### Phase 2: Standalone Executable

**Using Electron:**
```bash
npm init -y
npm install electron electron-builder
```

Package as:
- Windows: `.exe` installer
- macOS: `.dmg` installer
- Linux: `.AppImage`

### Phase 3: Desktop App (.NET)

**Build & Deploy:**
```powershell
# Build WPF application
dotnet build DigitalRecordsManager.sln -c Release

# Create installer using WiX Toolset
# Distribute as .msi installer
```

**Installation:**
- NSIS installer
- WiX Toolset
- Windows Store deployment

### Distribution Methods

1. **For Team Use:** Shared network folder with instructions
2. **For Client Distribution:** GitHub releases with installers
3. **For Enterprise:** Windows deployment via SCCM/Intune

---

## Configuration Files

### app.config.json

```json
{
  "app": {
    "name": "Digital Records Manager",
    "version": "1.0.0",
    "author": "Intellegix Systems",
    "description": "Audit and review digital records system"
  },
  "data": {
    "path": "./data",
    "recordsFile": "records.json",
    "auditsFile": "audits.json",
    "documentsFolder": "documents",
    "backupFolder": "backup"
  },
  "ui": {
    "theme": "light",
    "recordsPerPage": 20,
    "defaultZoom": 1.5,
    "enableDarkMode": true
  },
  "security": {
    "requireLogin": false,
    "enableAudit": true,
    "sessionTimeout": 60
  },
  "pdf": {
    "renderQuality": 2.0,
    "maxPagesBeforeWarning": 500,
    "enableOCR": false
  },
  "performance": {
    "enableIndexing": true,
    "cacheSize": 100,
    "lazyLoadPDFs": true
  }
}
```

---

## API Endpoints (Phase 2+)

### Records API

```
GET    /api/records              - List all records (with pagination)
POST   /api/records              - Create new record
GET    /api/records/:id          - Get specific record
PUT    /api/records/:id          - Update record
DELETE /api/records/:id          - Delete record
GET    /api/records/search       - Search records
GET    /api/records/:id/audits   - Get record's audit trail
```

### Documents API

```
GET    /api/documents/:id        - Download PDF
POST   /api/documents            - Upload new PDF
DELETE /api/documents/:id        - Delete PDF file
```

### Audits API

```
GET    /api/audits               - List audit events
POST   /api/audits               - Log new event
GET    /api/audits/:recordId     - Get audits for record
GET    /api/audits/report        - Generate audit report
```

---

## Security Considerations

### Phase 1: Development
- No authentication required (local use only)
- Basic input validation
- File access controls via OS permissions

### Phase 2: Enhanced Security
- User login with password hashing (bcrypt)
- Session management with tokens
- HTTPS for remote access
- Input sanitization
- CSRF protection

### Phase 3: Enterprise Security
- LDAP/AD integration
- OAuth 2.0 support
- Role-based access control (RBAC)
- Encryption at rest and in transit
- Audit logging for compliance
- API rate limiting
- SQL injection prevention (parameterized queries)

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Startup Time** | < 3s | Time from launch to first record loaded |
| **Search Speed** | < 200ms | Time to filter 5000 records |
| **PDF Load Time** | < 500ms | Time to render first page |
| **UI Responsiveness** | < 100ms | Keyboard/click response time |
| **Audit Accuracy** | 100% | All actions logged correctly |
| **Data Persistence** | 100% | No data loss on crash |
| **Record Capacity** | 50,000+ | Test with max records |
| **User Satisfaction** | > 4/5 | Collect feedback after testing |

---

## Troubleshooting Guide

### Common Issues & Solutions

**PDF Not Loading**
- Check file path is correct
- Verify PDF.js library loaded
- Check browser console for errors
- Test with different PDF file

**Records List Empty**
- Verify records.json exists in data folder
- Check JSON syntax is valid
- Verify file permissions
- Run generate-sample-data.js

**Audit Not Logging**
- Check audits.json has write permissions
- Verify audit logger initialized
- Check browser console for errors
- Increase log level to debug

**Performance Slow**
- Check number of records (> 10,000?)
- Clear browser cache
- Check available RAM
- Upgrade to SQLite for indexing

---

## Future Enhancements

### Short-term (3-6 months)
- [ ] Mobile app (React Native)
- [ ] Cloud sync (AWS S3)
- [ ] Advanced search with relevance ranking
- [ ] Batch upload wizard
- [ ] Export to Excel/CSV

### Medium-term (6-12 months)
- [ ] OCR implementation
- [ ] Document annotations
- [ ] Workflow automation
- [ ] Machine learning categorization
- [ ] Multi-user collaboration

### Long-term (12+ months)
- [ ] AI-powered document classification
- [ ] Blockchain audit trail verification
- [ ] Multi-tenant SaaS platform
- [ ] Mobile offline sync
- [ ] Advanced analytics dashboard

---

## Document Metadata

- **Created:** December 08, 2025
- **Last Updated:** December 08, 2025
- **Version:** 1.0.0
- **Status:** Blueprint (Ready for Implementation)
- **Author:** Intellegix Systems Development Team
- **Target Release:** 1.0 MVP by end of Week 2

---

## Quick Start Checklist

To begin implementation, ensure you have:

- [ ] Node.js 14+ installed (for server)
- [ ] Python 3.8+ installed (for simple HTTP server)
- [ ] Text editor (VS Code recommended)
- [ ] Git for version control
- [ ] Sample PDFs in data/documents/
- [ ] This blueprint document

**Start here:** Follow Phase 1 Week 1 Implementation Roadmap

---

*End of Blueprint Document*