<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Closed Invoice Archive System - Complete Blueprint

I've created a comprehensive blueprint for a production-grade closed invoice archival and management system designed to work with your Epson WorkForce ES-400 II scanner. This system combines modern cloud infrastructure, intelligent OCR processing, and robust data management practices.

![Closed Invoice Archive System - Multi-Layer Architecture](https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/085a537554ac299e10a8a41967388d01/f2a2fb16-dc0b-45be-8d7e-a1e3ab122bb6/184aad95.png)

Closed Invoice Archive System - Multi-Layer Architecture

## System Architecture Overview

The system is organized into five integrated layers:[^1_1][^1_2][^1_3][^1_4][^1_5]

**Presentation Layer** features a WPF desktop application for local scanning with Epson integration and a React web dashboard for browsing and management. The WPF app provides direct access to the scanner's 35 ppm duplex speed and 50-sheet auto-feeder, enabling batch processing of closed invoices.[^1_2][^1_6][^1_7][^1_8][^1_9][^1_10][^1_1]

**API Layer** uses Python FastAPI to provide RESTful endpoints for upload validation, OCR extraction, search operations, and lifecycle management. The async-first architecture handles high-volume document processing efficiently.[^1_11][^1_12][^1_13][^1_14]

**Processing Layer** integrates IronOCR or Azure Document Intelligence for extracting text and fields from scanned documents, performing confidence scoring, and providing structured data output.[^1_15][^1_11]

**Data Layer** comprises three specialized storage systems: PostgreSQL for invoice metadata and audit trails, Azure Blob Storage for original scanned PDFs and processed files, and Elasticsearch for full-text search across OCR results.[^1_3][^1_4][^1_5][^1_16]

## Key Database Design Concepts

The system implements a normalized relational schema with the following core entities:[^1_4][^1_5][^1_17]

**Invoices Table**: Stores header information including invoice_number, vendor reference, dates, amounts, and dual status fields (payment_status and invoice_status) to distinguish between open/closed/paid states and workflow states.[^1_5][^1_4]

**Invoice Line Items**: Maintains detailed line-level data with descriptions, quantities, unit prices, and GL account codes for accounting integration.[^1_4][^1_5]

**Invoice Files**: Tracks file metadata including original PDF path, OCR results, checksums for duplicate detection, and confidence scores.[^1_5][^1_4]

**Audit Logs**: Immutable records of all actions (uploads, validations, archival, deletions) with user identification and IP addresses for compliance.[^1_17][^1_4][^1_5]

The schema uses UUID primary keys for system resilience and proper indexing on status, dates, and search columns for query performance.[^1_4]

## Epson Scanner Integration

Your WorkForce ES-400 II offers specific capabilities that the system leverages:[^1_1][^1_2][^1_18][^1_19]

The 50-sheet automatic document feeder supports batch scanning up to 8.5" x 240" at varying DPI levels. The duplex mode scans both sides in a single pass at 35 pages-per-minute, delivering 70 images-per-minute. Integrated ultrasonic double-feed detection prevents missing pages, and paper protection prevents staple damage.

The WPF desktop application communicates directly with the scanner through TWAIN drivers, enabling automated scan settings like 300 DPI resolution, color mode, and blank page skip. Scanned documents are either saved as PDF immediately or converted to searchable PDFs with embedded OCR text.[^1_2][^1_6][^1_7][^1_1]

## OCR and Data Extraction

The system implements intelligent OCR processing using IronOCR's Tesseract engine with preprocessing steps including deskewing, denoising, and auto-cropping. Extracted text includes confidence scores that flag potentially misread fields for manual review.[^1_11][^1_15]

Structured field extraction uses pattern matching and regular expressions to identify invoice numbers, dates, vendors, amounts, and line items. Validation catches duplicates through checksum comparison, validates totals against line item sums, and flags missing required fields.[^1_15][^1_11]

## Search and Retrieval Architecture

Full-text search across all invoices is powered by Elasticsearch, indexing the OCR-extracted text and invoice metadata. Users can search by:[^1_3][^1_5][^1_16]

- Full-text keywords across OCR results and line item descriptions
- Vendor name and ID
- Invoice date ranges (0-30, 31-60, 61-90, 90+ days aging buckets)
- Payment status and invoice lifecycle status
- Invoice amount ranges
- Account codes for accounting reconciliation


## Security and Compliance Framework

Data is protected through multiple layers:[^1_3][^1_4][^1_5][^1_17]

- Encryption at rest using AES-256 in both cloud storage and database
- TLS 1.3 encryption in transit for all API communications
- Comprehensive audit logging with immutable write-once storage
- Role-based access control (RBAC) for admin, accountant, auditor, and viewer roles
- Automatic redaction for GDPR compliance rather than hard deletion
- Geo-redundant backup storage with 7-year retention for compliance


## File Storage Organization

The Azure Blob Storage container uses a hierarchical structure that supports lifecycle policies:[^1_3]

Original scanned PDFs are stored in `original/{year}/{month}/{invoice_id}.pdf` and automatically moved to cool storage after 90 days and archive tier after one year. OCR results are stored separately for independent retrieval. Processed and searchable PDFs provide compliance-ready versions.

Archive tier storage includes quarterly compressed archives with inventory manifests for long-term retention.[^1_5][^1_3]

## Deployment and Operations

The system supports multiple deployment scenarios:

Development uses local Docker containers for all services. Staging runs on Azure App Service with full production monitoring. Production deployments use containerized microservices with auto-scaling based on queue depth and API latency.

CI/CD pipelines automatically build, test, and deploy code changes with automated rollback capability. Application Insights provides real-time monitoring of upload success rates, OCR accuracy, search latency, and storage growth.[^1_13][^1_14]

## Implementation Technology Choices

| Component | Technology | Rationale |
| :-- | :-- | :-- |
| Desktop Scanner UI | C\# WPF .NET 8 | Native Windows performance, direct TWAIN access, enterprise reliability |
| Web Dashboard | React 19 + TypeScript | Modern responsive UI, type safety, accessibility compliance |
| Backend API | Python FastAPI | Async processing, automatic OpenAPI docs, rapid development |
| Primary Database | PostgreSQL | ACID compliance, advanced indexing, JSON metadata support |
| File Storage | Azure Blob Storage | Massive scalability, lifecycle policies, geo-redundancy |
| Search Engine | Elasticsearch | Full-text search, faceted navigation, real-time indexing |
| OCR Engine | IronOCR .NET | High accuracy, field recognition, confidence scoring |

code_file:29

The complete blueprint document includes detailed code examples for WPF scanner integration, FastAPI endpoint definitions, Pydantic validation models, PostgreSQL schema with proper indexes and constraints, Elasticsearch mapping configurations, and a 16-week implementation timeline with testing and deployment strategies. The system is designed to scale from hundreds to millions of invoices while maintaining sub-second search latency and 99.9% uptime SLA.
<span style="display:none">[^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26]</span>

<div align="center">⁂</div>

[^1_1]: https://epson.com/For-Home/Scanners/Document-Scanners/WorkForce-ES-400-II-Duplex-Desktop-Document-Scanner/p/B11B261201

[^1_2]: https://mediaserver.goepson.com/ImConvServlet/imconv/4495949c8c7e0d90440a08004b7db82166f4183d/original?assetDescr=WorkForce_ES-400II_Scanner_Specification_Sheet_CPD-59546R2_Final.pdf

[^1_3]: https://www.invoiceonline.com/business-newsletter/finance-and-accounting/best-practices-for-archiving-and-storing-invoices-digitally

[^1_4]: https://www.red-gate.com/blog/erd-for-invoice-management

[^1_5]: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/04e853229cf241a5a9739026d77974ef.html

[^1_6]: https://stackoverflow.com/questions/3359106/file-uploader-in-wpf

[^1_7]: https://www.youtube.com/watch?v=DKYssZ8JUx0

[^1_8]: https://codepal.ai/code-generator/query/tlWiyxHm/csharp-file-upload-wpf

[^1_9]: https://github.com/thekavikumar/ai-powered-invoice-management-system

[^1_10]: https://uploadcare.com/blog/how-to-upload-file-in-react/

[^1_11]: https://ironsoftware.com/csharp/ocr/blog/using-ironocr/ocr-invoice-processing/

[^1_12]: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/invoice?view=doc-intel-4.0.0

[^1_13]: https://terem.tech/api-file-upload-best-practice/

[^1_14]: https://tyk.io/blog/api-design-guidance-file-upload/

[^1_15]: https://blog.aspose.net/ocr/convert-scanned-pdf-to-text-csharp/

[^1_16]: https://docsvault.com/features/api-integration/

[^1_17]: https://docs.oracle.com/cd/E18727-01/doc.121/e13522/T355475T385615.htm

[^1_18]: https://www.target.com/p/epson-workforce-es-400-ii-color-duplex-desktop-document-scanner/-/A-90022724

[^1_19]: https://www.staples.com/epson-workforce-es-400-ii-duplex-document-scanner-black-b11b261201/product_24469378

[^1_20]: https://epson.com/Support/Scanners/ES-Series/Epson-WorkForce-ES-400-II/s/SPT_B11B261201

[^1_21]: https://epson.com/For-Home/Scanners/Document-Scanners/WorkForce-ES-400-Duplex-Document-Scanner/p/B11B226201

[^1_22]: https://patents.google.com/patent/US8321308B2/en

[^1_23]: https://www.linkedin.com/advice/0/what-best-practices-managing-invoice-archiving

[^1_24]: https://community.sap.com/t5/enterprise-resource-planning-q-a/dms-attachment-functionality-in-custom-application-in-public-cloud/qaq-p/14180812

[^1_25]: https://stackoverflow.com/questions/20021353/payable-invoice-capturing-or-extracting-automation

[^1_26]: https://learn.microsoft.com/en-us/answers/questions/1336771/file-upload-on-cloud-and-server-in-wpf

