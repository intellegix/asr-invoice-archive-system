# ASR Records Legacy Frontend

A simplified, modern frontend for the ASR Records Document Management System that preserves all sophisticated backend capabilities while providing a clean, user-friendly interface.

## Overview

This legacy frontend provides:
- **Simplified UI/UX**: Clean, single-page interface vs. complex 4-tab navigation
- **Preserved Intelligence**: All 40+ GL account classifications, 5-method payment detection, 4 billing destinations
- **AWS Multi-Tenant Ready**: Built for scalable SaaS deployment
- **Enhanced User Experience**: Modern React with TypeScript and TailwindCSS

## Architecture

### Technology Stack
- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: TailwindCSS with custom design system
- **State Management**: Zustand (client) + React Query (server state)
- **Routing**: React Router DOM
- **Testing**: Vitest + Testing Library
- **Build**: Vite with optimized production builds

### Project Structure
```
legacy-frontend/
├── src/
│   ├── components/          # Organized component library
│   │   ├── common/         # Shared components (Button, MetricCard, etc.)
│   │   ├── layout/         # Layout components (Header, Navigation)
│   │   ├── upload/         # Upload-specific components
│   │   ├── dashboard/      # Dashboard components
│   │   └── documents/      # Document management components
│   ├── pages/              # Page-level components
│   │   ├── Dashboard/      # Main dashboard page
│   │   ├── Upload/         # Document upload page
│   │   └── Documents/      # Document browsing/search
│   ├── services/           # API and business logic
│   │   └── api/           # Backend integration services
│   ├── hooks/              # Custom React hooks
│   ├── stores/             # Zustand state stores
│   ├── types/              # TypeScript definitions
│   │   ├── api/           # API type definitions
│   │   ├── components/    # Component prop types
│   │   └── common/        # Shared types
│   ├── utils/              # Utility functions
│   └── styles/            # Global styles and Tailwind config
├── public/                 # Static assets
└── docs/                   # Documentation
```

## Backend Integration

### Preserved Capabilities
The frontend integrates with the sophisticated existing backend, preserving:

#### 40+ GL Account Classifications
- Full QuickBooks integration with expense category mapping
- Automatic keyword matching and machine learning classification
- Hierarchical account structure with usage analytics

#### 5-Method Payment Detection Consensus
- **Claude AI**: Advanced document analysis with vision capabilities
- **Regex Patterns**: Proven text pattern matching
- **Keywords**: Business rule-based detection
- **Amount Analysis**: Financial correlation detection
- **Date Analysis**: Payment timing correlation

#### 4 Billing Destinations
- **Open Payable**: Unpaid vendor invoices
- **Closed Payable**: Paid vendor invoices
- **Open Receivable**: Outstanding client payments
- **Closed Receivable**: Received client payments

#### Enhanced Routing Logic
- Rule-based routing with confidence scoring
- Manual override capabilities with audit trails
- Quality metrics and performance monitoring

## Features

### Dashboard
- **Real-time Metrics**: Document volume, processing accuracy, payment status
- **Payment Distribution**: Visual breakdown of payment statuses
- **Recent Activity**: Latest processed documents with classification details
- **System Health**: Processing performance and accuracy metrics

### Document Upload
- **Drag & Drop Interface**: Simple file upload with visual feedback
- **Batch Processing**: Multiple document support with progress tracking
- **Real-time Classification**: Live AI-powered document analysis
- **Confidence Scoring**: Visual indication of classification accuracy

### Document Management
- **Advanced Search**: Filter by vendor, GL account, payment status, date ranges
- **Classification Review**: Review and adjust AI classifications
- **Audit Trails**: Complete processing history for each document
- **Export Capabilities**: Multiple format support for reporting

### Design System
- **Modern UI**: Clean, accessible interface built with TailwindCSS
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Component Library**: Reusable, well-documented components
- **Dark Mode Ready**: Theme system prepared for multiple color schemes

## Development

### Getting Started
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run type checking
npm run type-check

# Run tests
npm test

# Build for production
npm run build
```

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript type checking
- `npm test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Generate coverage report

### Environment Variables
```bash
VITE_API_URL=http://localhost:8000  # Backend API URL
VITE_APP_TITLE=ASR Records Legacy   # Application title
VITE_TENANT_ID=your-tenant-id       # Multi-tenant identifier
```

## Backend API Integration

The frontend is designed to integrate with the existing sophisticated backend:

### Document Processing API
- `POST /api/documents/upload` - Upload documents for processing
- `GET /api/documents` - Retrieve document list with filters
- `POST /api/documents/{id}/classify` - Trigger manual reclassification

### GL Account API
- `GET /api/gl-accounts` - Retrieve all 40+ GL accounts
- `GET /api/gl-accounts/hierarchy` - Account hierarchy structure
- `POST /api/gl-accounts/sync` - QuickBooks synchronization

### Billing Router API
- `GET /api/billing/routes` - Retrieve routing configurations
- `POST /api/billing/route` - Manual routing override
- `GET /api/billing/analytics` - Routing performance metrics

### Payment Detection API
- `GET /api/payment/methods` - Available detection methods
- `POST /api/payment/analyze` - Run payment analysis
- `GET /api/payment/consensus` - Consensus results

## Multi-Tenant Support

The frontend is built with multi-tenant SaaS deployment in mind:

### Tenant Context
- All API calls include tenant identification
- UI adapts based on tenant configuration
- Feature flags for tenant-specific capabilities

### Data Isolation
- Client-segregated data access
- Tenant-specific GL account configurations
- Isolated payment detection settings

## Performance

### Optimization Features
- **Code Splitting**: Automatic route-based splitting
- **Tree Shaking**: Optimized bundle size
- **Lazy Loading**: Components loaded on demand
- **Caching**: Intelligent API response caching
- **Compression**: Gzip/Brotli asset compression

### Bundle Analysis
```bash
# Analyze bundle size
npm run build
npm run preview
```

## Testing

### Test Structure
- **Unit Tests**: Component and utility function tests
- **Integration Tests**: API integration and user flow tests
- **E2E Tests**: End-to-end user scenarios
- **Coverage**: Comprehensive test coverage reporting

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm run test:coverage
```

## Deployment

### Production Build
```bash
npm run build
```

### Docker Support
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Contributing

### Code Standards
- **TypeScript**: Strict typing for all components and functions
- **ESLint**: Automated code quality checking
- **Prettier**: Consistent code formatting
- **Conventional Commits**: Standardized commit messages

### Component Guidelines
- All components must be TypeScript with proper prop types
- Use barrel exports for clean imports
- Include comprehensive JSDoc documentation
- Follow accessibility best practices

## Support

For questions or issues:
1. Check the [existing documentation](../docs/)
2. Review the [API documentation](../docs/api/)
3. Create an issue in the project repository

## License

Copyright © 2024 ASR Records. All rights reserved.