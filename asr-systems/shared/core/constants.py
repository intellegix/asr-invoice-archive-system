"""
ASR Systems - Shared Constants
Common constants and configuration values for both systems
"""

from enum import Enum
from typing import Dict, List

# Version information
VERSION = "2.0.0"
API_VERSION = "v1"

# System limits
MAX_FILE_SIZE_MB = 25
MAX_BATCH_SIZE = 50
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30

# File type support
SUPPORTED_DOCUMENT_TYPES = {
    "application/pdf": [".pdf"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/tiff": [".tif", ".tiff"],
    "image/bmp": [".bmp"],
    "text/plain": [".txt"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        ".docx"
    ],
    "application/msword": [".doc"],
}

SUPPORTED_EXTENSIONS = [
    ext for exts in SUPPORTED_DOCUMENT_TYPES.values() for ext in exts
]

# GL Account Categories (5 main categories with 79 total accounts)
GL_ACCOUNT_CATEGORIES = {
    "ASSETS": {
        "description": "Asset accounts",
        "codes": [
            "1000",
            "1100",
            "1200",
            "1300",
            "1400",
            "1500",
            "1600",
            "1700",
            "1800",
            "1900",
        ],
    },
    "LIABILITIES": {
        "description": "Liability accounts",
        "codes": [
            "2000",
            "2100",
            "2200",
            "2300",
            "2400",
            "2500",
            "2600",
            "2700",
            "2800",
            "2900",
        ],
    },
    "EQUITY": {
        "description": "Equity accounts",
        "codes": [
            "3000",
            "3100",
            "3200",
            "3300",
            "3400",
            "3500",
            "3600",
            "3700",
            "3800",
            "3900",
        ],
    },
    "REVENUE": {
        "description": "Revenue accounts",
        "codes": [
            "4000",
            "4100",
            "4200",
            "4300",
            "4400",
            "4500",
            "4600",
            "4700",
            "4800",
            "4900",
        ],
    },
    "EXPENSES": {
        "description": "Expense accounts",
        "codes": [
            "5000",
            "5010",
            "5020",
            "5030",
            "5040",
            "5050",
            "5060",
            "5070",
            "5080",
            "5090",
            "5095",
            "5100",
            "5200",
            "5300",
            "5400",
            "5500",
            "5600",
            "5700",
            "5800",
            "5900",
            "6000",
            "6100",
            "6200",
            "6300",
            "6400",
            "6500",
            "6600",
            "6700",
            "6800",
            "6900",
            "7000",
            "7100",
            "7200",
            "7300",
            "7400",
            "7500",
            "7600",
            "7700",
            "7800",
        ],
    },
}

# 79 QuickBooks GL Accounts with keyword mappings
GL_ACCOUNTS = {
    # Asset Accounts (1000-1900)
    "1000": {
        "name": "Cash - Operating",
        "category": "ASSETS",
        "keywords": ["cash", "checking", "operating"],
    },
    "1100": {
        "name": "Cash - Savings",
        "category": "ASSETS",
        "keywords": ["savings", "reserve"],
    },
    "1200": {
        "name": "Accounts Receivable",
        "category": "ASSETS",
        "keywords": ["receivable", "customer", "invoice"],
    },
    "1300": {
        "name": "Inventory",
        "category": "ASSETS",
        "keywords": ["inventory", "stock", "materials"],
    },
    "1400": {
        "name": "Prepaid Expenses",
        "category": "ASSETS",
        "keywords": ["prepaid", "advance payment"],
    },
    "1500": {
        "name": "Equipment",
        "category": "ASSETS",
        "keywords": ["equipment", "machinery", "tools"],
    },
    "1600": {
        "name": "Vehicles",
        "category": "ASSETS",
        "keywords": ["vehicle", "truck", "car", "fleet"],
    },
    "1700": {
        "name": "Buildings",
        "category": "ASSETS",
        "keywords": ["building", "property", "real estate"],
    },
    "1800": {
        "name": "Land",
        "category": "ASSETS",
        "keywords": ["land", "lot", "property"],
    },
    "1900": {
        "name": "Accumulated Depreciation",
        "category": "ASSETS",
        "keywords": ["depreciation"],
    },
    # Liability Accounts (2000-2900)
    "2000": {
        "name": "Accounts Payable",
        "category": "LIABILITIES",
        "keywords": ["payable", "vendor", "supplier"],
    },
    "2100": {
        "name": "Credit Cards",
        "category": "LIABILITIES",
        "keywords": ["credit card", "visa", "mastercard"],
    },
    "2200": {
        "name": "Payroll Liabilities",
        "category": "LIABILITIES",
        "keywords": ["payroll", "withholding", "taxes"],
    },
    "2300": {
        "name": "Sales Tax Payable",
        "category": "LIABILITIES",
        "keywords": ["sales tax", "tax payable"],
    },
    "2400": {
        "name": "Notes Payable",
        "category": "LIABILITIES",
        "keywords": ["notes payable", "loan"],
    },
    "2500": {
        "name": "Accrued Expenses",
        "category": "LIABILITIES",
        "keywords": ["accrued", "accrual"],
    },
    "2600": {
        "name": "Customer Deposits",
        "category": "LIABILITIES",
        "keywords": ["deposit", "advance"],
    },
    "2700": {
        "name": "Line of Credit",
        "category": "LIABILITIES",
        "keywords": ["line of credit", "loc"],
    },
    "2800": {
        "name": "Equipment Loans",
        "category": "LIABILITIES",
        "keywords": ["equipment loan", "financing"],
    },
    "2900": {
        "name": "Other Current Liabilities",
        "category": "LIABILITIES",
        "keywords": ["other liabilities"],
    },
    # Equity Accounts (3000-3900)
    "3000": {
        "name": "Owner's Equity",
        "category": "EQUITY",
        "keywords": ["equity", "owner", "capital"],
    },
    "3100": {
        "name": "Retained Earnings",
        "category": "EQUITY",
        "keywords": ["retained earnings"],
    },
    "3200": {
        "name": "Owner Draw",
        "category": "EQUITY",
        "keywords": ["draw", "distribution"],
    },
    "3300": {
        "name": "Common Stock",
        "category": "EQUITY",
        "keywords": ["stock", "shares"],
    },
    "3400": {
        "name": "Additional Paid-in Capital",
        "category": "EQUITY",
        "keywords": ["paid-in capital"],
    },
    "3500": {
        "name": "Treasury Stock",
        "category": "EQUITY",
        "keywords": ["treasury stock"],
    },
    "3600": {"name": "Dividends", "category": "EQUITY", "keywords": ["dividends"]},
    "3700": {
        "name": "Other Equity",
        "category": "EQUITY",
        "keywords": ["other equity"],
    },
    "3800": {
        "name": "Opening Bal Equity",
        "category": "EQUITY",
        "keywords": ["opening balance"],
    },
    "3900": {
        "name": "Unrestricted Net Assets",
        "category": "EQUITY",
        "keywords": ["net assets"],
    },
    # Revenue Accounts (4000-4900)
    "4000": {
        "name": "Service Revenue",
        "category": "REVENUE",
        "keywords": ["service", "revenue", "income"],
    },
    "4100": {
        "name": "Product Sales",
        "category": "REVENUE",
        "keywords": ["sales", "product", "merchandise"],
    },
    "4200": {
        "name": "Consulting Revenue",
        "category": "REVENUE",
        "keywords": ["consulting", "advisory"],
    },
    "4300": {
        "name": "Interest Income",
        "category": "REVENUE",
        "keywords": ["interest", "bank interest"],
    },
    "4400": {
        "name": "Rental Income",
        "category": "REVENUE",
        "keywords": ["rent", "rental", "lease"],
    },
    "4500": {
        "name": "Other Income",
        "category": "REVENUE",
        "keywords": ["other income", "miscellaneous"],
    },
    "4600": {
        "name": "Gain on Sale of Assets",
        "category": "REVENUE",
        "keywords": ["gain", "asset sale"],
    },
    "4700": {
        "name": "Reimbursements",
        "category": "REVENUE",
        "keywords": ["reimbursement", "refund"],
    },
    "4800": {
        "name": "Discounts Given",
        "category": "REVENUE",
        "keywords": ["discount", "markdown"],
    },
    "4900": {
        "name": "Returns and Allowances",
        "category": "REVENUE",
        "keywords": ["return", "allowance"],
    },
    # Expense Accounts (5000-7800) - 39 accounts
    "5000": {
        "name": "Cost of Goods Sold",
        "category": "EXPENSES",
        "keywords": ["cogs", "cost of goods", "materials"],
    },
    "5010": {
        "name": "Payroll Taxes",
        "category": "EXPENSES",
        "keywords": [
            "payroll tax",
            "fica",
            "medicare",
            "social security",
            "futa",
            "suta",
        ],
    },
    "5020": {
        "name": "Employee Benefits",
        "category": "EXPENSES",
        "keywords": ["benefits", "health plan", "dental", "vision", "employee benefit"],
    },
    "5030": {
        "name": "Workers Compensation",
        "category": "EXPENSES",
        "keywords": ["workers comp", "workers compensation", "work comp", "wc premium"],
    },
    "5040": {
        "name": "Retirement Contributions",
        "category": "EXPENSES",
        "keywords": ["401k", "retirement", "pension", "ira", "sep"],
    },
    "5050": {
        "name": "Uniforms & Safety",
        "category": "EXPENSES",
        "keywords": ["uniform", "safety", "ppe", "hard hat", "work boots"],
    },
    "5060": {
        "name": "Cleaning & Janitorial",
        "category": "EXPENSES",
        "keywords": ["cleaning", "janitorial", "custodial", "sanitation"],
    },
    "5070": {
        "name": "Security",
        "category": "EXPENSES",
        "keywords": ["security", "alarm", "surveillance", "guard"],
    },
    "5080": {
        "name": "Dues & Subscriptions",
        "category": "EXPENSES",
        "keywords": ["dues", "subscription", "membership", "association"],
    },
    "5090": {
        "name": "Printing & Reproduction",
        "category": "EXPENSES",
        "keywords": ["printing", "copies", "reproduction", "print shop"],
    },
    "5095": {
        "name": "Permits & Inspections",
        "category": "EXPENSES",
        "keywords": ["permit fee", "inspection", "building permit", "compliance"],
    },
    "5100": {
        "name": "Advertising",
        "category": "EXPENSES",
        "keywords": ["advertising", "marketing", "promotion"],
    },
    "5200": {
        "name": "Auto Expense",
        "category": "EXPENSES",
        "keywords": ["auto", "vehicle", "car expense", "mileage"],
    },
    "5300": {
        "name": "Bank Charges",
        "category": "EXPENSES",
        "keywords": ["bank fees", "service charges", "banking"],
    },
    "5400": {
        "name": "Equipment Rental",
        "category": "EXPENSES",
        "keywords": ["equipment rental", "tool rental"],
    },
    "5500": {
        "name": "Insurance",
        "category": "EXPENSES",
        "keywords": ["insurance", "liability", "coverage"],
    },
    "5600": {
        "name": "Interest Expense",
        "category": "EXPENSES",
        "keywords": ["interest", "loan interest"],
    },
    "5700": {
        "name": "Legal & Professional",
        "category": "EXPENSES",
        "keywords": ["legal", "attorney", "professional"],
    },
    "5800": {
        "name": "Office Supplies",
        "category": "EXPENSES",
        "keywords": ["supplies", "office", "stationery"],
    },
    "5900": {
        "name": "Postage",
        "category": "EXPENSES",
        "keywords": ["postage", "shipping", "mail"],
    },
    "6000": {
        "name": "Rent",
        "category": "EXPENSES",
        "keywords": ["rent", "lease", "facility"],
    },
    "6100": {
        "name": "Repairs & Maintenance",
        "category": "EXPENSES",
        "keywords": ["repair", "maintenance", "service"],
    },
    "6200": {
        "name": "Subcontractors",
        "category": "EXPENSES",
        "keywords": ["subcontractor", "contractor", "1099"],
    },
    "6300": {
        "name": "Supplies",
        "category": "EXPENSES",
        "keywords": ["supplies", "materials", "consumables"],
    },
    "6400": {
        "name": "Telephone",
        "category": "EXPENSES",
        "keywords": ["phone", "telephone", "cell phone"],
    },
    "6500": {
        "name": "Travel",
        "category": "EXPENSES",
        "keywords": ["travel", "lodging", "hotel"],
    },
    "6600": {
        "name": "Utilities",
        "category": "EXPENSES",
        "keywords": ["utilities", "electric", "gas", "water"],
    },
    "6700": {
        "name": "Wages",
        "category": "EXPENSES",
        "keywords": ["wages", "salary", "payroll"],
    },
    "6800": {
        "name": "Meals & Entertainment",
        "category": "EXPENSES",
        "keywords": ["meals", "entertainment", "dining"],
    },
    "6900": {
        "name": "Fuel",
        "category": "EXPENSES",
        "keywords": ["fuel", "gas", "diesel", "propane"],
    },
    "7000": {
        "name": "Training & Education",
        "category": "EXPENSES",
        "keywords": ["training", "education", "seminar"],
    },
    "7100": {
        "name": "Software & Technology",
        "category": "EXPENSES",
        "keywords": ["software", "technology", "saas"],
    },
    "7200": {
        "name": "Licenses & Permits",
        "category": "EXPENSES",
        "keywords": ["license", "permit", "registration"],
    },
    "7300": {
        "name": "Taxes & Fees",
        "category": "EXPENSES",
        "keywords": ["taxes", "fees", "penalties"],
    },
    "7400": {
        "name": "Charitable Contributions",
        "category": "EXPENSES",
        "keywords": ["charitable", "donation"],
    },
    "7500": {
        "name": "Depreciation",
        "category": "EXPENSES",
        "keywords": ["depreciation", "amortization"],
    },
    "7600": {
        "name": "Bad Debt",
        "category": "EXPENSES",
        "keywords": ["bad debt", "write off", "uncollectible"],
    },
    "7700": {
        "name": "Miscellaneous",
        "category": "EXPENSES",
        "keywords": ["miscellaneous", "other"],
    },
    "7800": {
        "name": "Contract Labor",
        "category": "EXPENSES",
        "keywords": ["contract", "temporary", "consulting"],
    },
}

# Payment detection patterns
PAYMENT_INDICATORS = {
    "PAID_KEYWORDS": [
        "paid",
        "payment received",
        "check",
        "cash",
        "wire transfer",
        "credit card",
        "ach",
        "electronic payment",
        "paid in full",
        "zero balance",
        "settled",
        "cleared",
        "processed",
    ],
    "UNPAID_KEYWORDS": [
        "unpaid",
        "outstanding",
        "due",
        "balance due",
        "payment due",
        "overdue",
        "past due",
        "pending payment",
        "invoice",
        "amount owed",
        "balance owing",
        "open",
    ],
    "PARTIAL_KEYWORDS": [
        "partial payment",
        "payment on account",
        "down payment",
        "installment",
        "partial",
        "balance remaining",
    ],
    "VOID_KEYWORDS": [
        "void",
        "cancelled",
        "canceled",
        "invalid",
        "reversed",
        "refunded",
        "credit memo",
        "credit note",
    ],
}

# Billing destinations routing rules
BILLING_DESTINATION_RULES = {
    "OPEN_PAYABLE": {
        "description": "Unpaid vendor invoices",
        "criteria": ["payment_status=unpaid", "document_type=vendor_invoice"],
    },
    "CLOSED_PAYABLE": {
        "description": "Paid vendor invoices",
        "criteria": ["payment_status=paid", "document_type=vendor_invoice"],
    },
    "OPEN_RECEIVABLE": {
        "description": "Unpaid customer invoices",
        "criteria": ["payment_status=unpaid", "document_type=customer_invoice"],
    },
    "CLOSED_RECEIVABLE": {
        "description": "Paid customer invoices",
        "criteria": ["payment_status=paid", "document_type=customer_invoice"],
    },
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "PAYMENT_DETECTION_MIN": 0.6,
    "PAYMENT_DETECTION_HIGH": 0.85,
    "GL_CLASSIFICATION_MIN": 0.7,
    "GL_CLASSIFICATION_HIGH": 0.9,
    "ROUTING_DECISION_MIN": 0.75,
    "MANUAL_REVIEW_THRESHOLD": 0.7,
}

# Scanner configuration defaults
SCANNER_DEFAULTS = {
    "HEARTBEAT_INTERVAL": 60,  # seconds
    "BATCH_UPLOAD_SIZE": 10,
    "RETRY_DELAY": 5,  # seconds
    "MAX_OFFLINE_QUEUE": 1000,
    "WATCH_FOLDER_SCAN_INTERVAL": 10,  # seconds
    "SUPPORTED_WATCH_EXTENSIONS": SUPPORTED_EXTENSIONS,
}

# API endpoints structure
API_ENDPOINTS = {
    "PRODUCTION_SERVER": {
        "HEALTH": "/health",
        "DOCUMENTS": "/api/v1/documents",
        "UPLOAD": "/api/v1/documents/upload",
        "CLASSIFICATION": "/api/v1/documents/{id}/classify",
        "ROUTING": "/api/v1/documents/{id}/route",
        "SCANNER_DISCOVERY": "/api/v1/scanner/discovery",
        "SCANNER_UPLOAD": "/api/v1/scanner/upload",
        "SCANNER_STATUS": "/api/v1/scanner/status/{id}",
        "SCANNER_BATCH": "/api/v1/scanner/batch",
    },
    "DOCUMENT_SCANNER": {
        "HEALTH": "/health",
        "CONFIG": "/config",
        "QUEUE": "/queue",
        "STATUS": "/status",
        "UPLOAD": "/upload",
    },
}

# System health check intervals
HEALTH_CHECK_INTERVALS = {
    "PRODUCTION_SERVER": 60,  # seconds
    "DOCUMENT_SCANNER": 30,  # seconds
    "SCANNER_HEARTBEAT": 60,  # seconds
    "DATABASE_CHECK": 120,  # seconds
    "STORAGE_CHECK": 300,  # seconds
}

# Storage configuration
STORAGE_CONFIG = {
    "TENANT_ISOLATION_PREFIX": "tenants/{tenant_id}",
    "DOCUMENT_STORAGE_PATH": "documents",
    "TEMP_STORAGE_PATH": "temp",
    "BACKUP_STORAGE_PATH": "backups",
    "DEFAULT_RETENTION_DAYS": 2555,  # 7 years
    "CLEANUP_BATCH_SIZE": 100,
}

# Database configuration
DATABASE_CONFIG = {
    "POOL_SIZE": 20,
    "MAX_OVERFLOW": 30,
    "POOL_TIMEOUT": 30,
    "POOL_RECYCLE": 3600,
    "ISOLATION_LEVEL": "READ_COMMITTED",
}

# External service timeouts
EXTERNAL_TIMEOUTS = {
    "CLAUDE_API": 60,  # seconds
    "DATABASE": 30,  # seconds
    "STORAGE_UPLOAD": 300,  # seconds
    "STORAGE_DOWNLOAD": 60,  # seconds
    "SCANNER_HEARTBEAT": 10,  # seconds
}

# Logging configuration
LOGGING_CONFIG = {
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
    "MAX_LOG_SIZE": "10MB",
    "BACKUP_COUNT": 5,
    "LEVELS": {"PRODUCTION": "INFO", "DEVELOPMENT": "DEBUG", "TESTING": "WARNING"},
}

# Security constants
SECURITY_CONFIG = {
    "API_KEY_LENGTH": 32,
    "TOKEN_EXPIRY_HOURS": 24,
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOCKOUT_DURATION_MINUTES": 15,
    "PASSWORD_MIN_LENGTH": 8,
    "SESSION_TIMEOUT_MINUTES": 60,
}


# Export all constants
__all__ = [
    "VERSION",
    "API_VERSION",
    "MAX_FILE_SIZE_MB",
    "MAX_BATCH_SIZE",
    "SUPPORTED_DOCUMENT_TYPES",
    "SUPPORTED_EXTENSIONS",
    "GL_ACCOUNT_CATEGORIES",
    "GL_ACCOUNTS",
    "PAYMENT_INDICATORS",
    "BILLING_DESTINATION_RULES",
    "CONFIDENCE_THRESHOLDS",
    "SCANNER_DEFAULTS",
    "API_ENDPOINTS",
    "HEALTH_CHECK_INTERVALS",
    "STORAGE_CONFIG",
    "DATABASE_CONFIG",
    "EXTERNAL_TIMEOUTS",
    "LOGGING_CONFIG",
    "SECURITY_CONFIG",
]
