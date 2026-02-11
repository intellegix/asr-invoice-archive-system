# ASR Document Scanner v2.0.0

## Desktop Scanning Client with Offline Capabilities

The ASR Document Scanner is a sophisticated desktop application that provides seamless document scanning, upload, and processing capabilities for the ASR Records system. It features offline queue management, automatic server discovery, and comprehensive scanner hardware integration.

## 🚀 Key Features

### Core Functionality
- **Desktop GUI Interface** - Modern, intuitive interface built with Tkinter
- **Drag-and-Drop Upload** - Simple file addition to upload queue
- **Scanner Hardware Integration** - TWAIN/WIA scanner support for Windows
- **Offline Queue Management** - Documents processed when server available
- **Real-time Progress Tracking** - Live upload and processing status
- **Automatic Server Discovery** - Finds production servers on network

### Advanced Capabilities
- **Batch Processing** - Multiple document upload with progress tracking
- **Retry Logic** - Exponential backoff for failed uploads
- **Format Support** - PDF, JPEG, PNG, TIFF, GIF document formats
- **Server Failover** - Automatic connection to best available server
- **Health Monitoring** - Comprehensive system status tracking
- **Configuration Management** - Persistent settings and preferences

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux Ubuntu 20.04+
- **Python**: 3.8 or higher
- **RAM**: 2GB available memory
- **Storage**: 1GB free disk space
- **Network**: Internet connection for server communication

### Recommended Requirements
- **Operating System**: Windows 11 or macOS 12+
- **Python**: 3.11 or higher
- **RAM**: 4GB available memory
- **Storage**: 5GB free disk space (for offline queue)
- **Scanner**: TWAIN or WIA compatible scanner (Windows)

## 🔧 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd asr-systems/document-scanner
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Windows-specific scanner support
pip install python-twain pywin32  # If on Windows

# Optional GUI enhancements
pip install ttkthemes tkinterdnd2
```

### 3. Configuration
```bash
# Copy example configuration
cp config/scanner_config.example.json config/scanner_config.json

# Set environment variables (optional)
export ASR_SCANNER_DATA_DIR="/path/to/data"
export ASR_SCANNER_API_KEY="your-api-key"
```

## 🚀 Usage

### Basic Usage
```bash
# Start the scanner application
python -m asr-systems.document-scanner

# Or run directly
python main_scanner.py
```

### Command Line Options
```bash
# Show version information
python main_scanner.py --version

# Specify custom data directory
python main_scanner.py --data-dir /custom/path

# Set log level
python main_scanner.py --log-level DEBUG

# Start in offline mode
python main_scanner.py --offline

# Use custom configuration file
python main_scanner.py --config /path/to/config.json
```

### GUI Operation

1. **Start Application** - Launch the scanner GUI
2. **Connect to Server** - Click "Connect" to find production servers
3. **Add Documents** - Drag files to upload area or click "Browse Files"
4. **Scan Documents** - Click "Scan Document" to use connected scanner
5. **Monitor Progress** - View upload status in the queue section
6. **Review Results** - Check processing results and any errors

## ⚙️ Configuration

### Scanner Settings
```json
{
  "scanner_enabled": true,
  "scanner_resolution": 300,
  "scanner_color_mode": "color",
  "scanner_format": "pdf",
  "auto_scan": false
}
```

### Upload Settings
```json
{
  "max_file_size_mb": 50,
  "batch_upload_size": 5,
  "retry_attempts": 3,
  "retry_delay": 5,
  "supported_formats": ["pdf", "jpg", "jpeg", "png", "tiff", "gif"]
}
```

### Server Discovery
```json
{
  "server_discovery_enabled": true,
  "server_discovery_timeout": 10,
  "auto_connect_servers": true,
  "heartbeat_interval": 30
}
```

### Offline Queue
```json
{
  "offline_mode": false,
  "offline_queue_max_size": 1000,
  "offline_retention_days": 7
}
```

## 🗂️ Directory Structure

```
document-scanner/
├── main_scanner.py              # Main application entry point
├── requirements.txt             # Python dependencies
├── README.md                   # This documentation
├── config/
│   ├── scanner_settings.py     # Configuration management
│   └── scanner_config.example.json
├── services/
│   ├── upload_queue_service.py # Offline queue management
│   ├── server_discovery_service.py # Server discovery
│   ├── scanner_hardware_service.py # Scanner integration
│   └── production_client.py    # Production server API client
├── gui/
│   └── main_window.py          # Primary GUI interface
├── api/
│   └── production_client.py    # Server communication
└── tests/
    ├── test_services.py        # Service tests
    ├── test_gui.py            # GUI tests
    └── fixtures/              # Test data
```

## 🔌 Production Server Integration

### Server Discovery
The scanner automatically discovers ASR Production Servers using:
- **Local Network Broadcast** - Scans common ports for servers
- **Manual Configuration** - User-specified server addresses
- **Cloud Endpoints** - Known production server URLs

### API Communication
- **Authentication** - Bearer token authentication with API keys
- **Document Upload** - Multipart form upload with metadata
- **Status Monitoring** - Real-time processing status updates
- **Health Checks** - Regular server connectivity validation

### Supported Endpoints
- `POST /api/scanner/upload` - Document upload
- `GET /api/scanner/discovery` - Server capabilities
- `GET /api/scanner/status/{id}` - Upload status
- `POST /api/scanner/batch` - Batch upload
- `POST /api/scanner/register` - Scanner registration

## 📊 Monitoring & Health

### Health Indicators
- **Service Status** - Upload queue, server discovery, scanner hardware
- **Connection Status** - Production server connectivity
- **Queue Status** - Pending, uploading, completed, failed documents
- **System Resources** - Memory usage, disk space, network

### Logging
```bash
# View application logs
tail -f ~/.asr_scanner/logs/scanner.log

# Enable debug logging
python main_scanner.py --log-level DEBUG
```

### Queue Management
- **View Queue** - Monitor pending and processed documents
- **Clear Completed** - Remove successfully processed documents
- **Retry Failed** - Reprocess failed uploads
- **Pause/Resume** - Control queue processing

## 🛠️ Troubleshooting

### Common Issues

#### Scanner Not Detected
```bash
# Check scanner drivers
# Install manufacturer drivers
# Verify TWAIN/WIA compatibility
# Restart scanner service
```

#### Server Connection Failed
```bash
# Check network connectivity
ping production-server.com

# Verify API key
echo $ASR_SCANNER_API_KEY

# Test manual connection
curl -H "Authorization: Bearer $API_KEY" http://server/health
```

#### Upload Failures
```bash
# Check file permissions
ls -la document.pdf

# Verify file size limits
du -h document.pdf

# Check supported formats
file document.pdf
```

### Error Codes
- **E001** - Scanner hardware not available
- **E002** - Server connection timeout
- **E003** - File validation failed
- **E004** - Authentication error
- **E005** - Queue storage full

### Performance Optimization
- **Batch Size** - Adjust upload batch size for network conditions
- **Queue Retention** - Configure retention policy for disk space
- **Scan Resolution** - Balance quality vs. processing time
- **Network Timeout** - Adjust timeouts for slow connections

## 🧪 Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/test_services.py
pytest tests/test_gui.py

# Run with coverage
pytest --cov=scanner tests/
```

### Building Distribution
```bash
# Create executable with PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed main_scanner.py

# Build installer (Windows)
pip install cx_Freeze
python setup.py bdist_msi
```

### Contributing
1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## 📝 License

ASR Document Scanner is proprietary software developed by ASR Systems Inc.

## 📞 Support

- **Documentation**: https://docs.asr-records.com
- **Support Email**: support@asr-systems.com
- **Issue Tracker**: https://github.com/asr-systems/scanner/issues

---

*ASR Document Scanner v2.0.0 - Enterprise Document Processing Platform*