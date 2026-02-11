"""
Scanner Main Window
Primary GUI interface for ASR Document Scanner desktop application
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
from datetime import datetime

# Import scanner components
from ..services.upload_queue_service import UploadQueueService, QueuedDocument, UploadStatus
from ..services.server_discovery_service import ServerDiscoveryService, DiscoveredServer
from ..services.scanner_hardware_service import ScannerHardwareService, ScannerDevice, ScanRequest
from ..api.production_client import ProductionServerClient
from ..config.scanner_settings import scanner_settings

logger = logging.getLogger(__name__)


class ScannerMainWindow:
    """
    Main window for ASR Document Scanner

    Features:
    - Drag-and-drop document upload area
    - Upload queue management with progress tracking
    - Scanner hardware controls
    - Server connection status
    - Real-time processing status updates
    - Settings configuration
    """

    def __init__(self, root: tk.Tk, services: Dict[str, Any], async_loop: asyncio.AbstractEventLoop):
        self.root = root
        self.services = services
        self.async_loop = async_loop

        # GUI Components
        self.main_frame: Optional[ttk.Frame] = None
        self.upload_frame: Optional[ttk.Frame] = None
        self.queue_frame: Optional[ttk.Frame] = None
        self.status_frame: Optional[ttk.Frame] = None
        self.scanner_frame: Optional[ttk.Frame] = None

        # Status variables
        self.server_status_var = tk.StringVar(value="Disconnected")
        self.queue_status_var = tk.StringVar(value="0 documents")
        self.scanner_status_var = tk.StringVar(value="No scanner")

        # Upload progress tracking
        self.upload_progress_vars: Dict[str, tk.DoubleVar] = {}
        self.upload_status_vars: Dict[str, tk.StringVar] = {}

        # Initialize GUI
        self._setup_gui()
        self._setup_event_handlers()
        self._start_status_update_timer()

    def _setup_gui(self) -> None:
        """Setup the main GUI layout"""
        try:
            # Configure root window
            self.root.title("ASR Document Scanner v2.0.0")
            self.root.geometry("1000x700")
            self.root.minsize(800, 600)

            # Create main container with scrollbar
            main_canvas = tk.Canvas(self.root)
            scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
            self.main_frame = ttk.Frame(main_canvas)

            self.main_frame.bind(
                "<Configure>",
                lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            )

            main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
            main_canvas.configure(yscrollcommand=scrollbar.set)

            # Pack scrollable area
            main_canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Create GUI sections
            self._create_header_section()
            self._create_upload_section()
            self._create_scanner_section()
            self._create_queue_section()
            self._create_status_section()

            logger.info("✅ GUI layout created successfully")

        except Exception as e:
            logger.error(f"❌ Failed to setup GUI: {e}")

    def _create_header_section(self) -> None:
        """Create header section with title and server status"""
        header_frame = ttk.LabelFrame(self.main_frame, text="ASR Document Scanner", padding="10")
        header_frame.pack(fill="x", padx=10, pady=5)

        # Title
        title_label = tk.Label(
            header_frame,
            text="ASR Document Scanner v2.0.0",
            font=("Arial", 16, "bold"),
            fg="#2E86AB"
        )
        title_label.pack()

        # Server connection status
        server_frame = ttk.Frame(header_frame)
        server_frame.pack(fill="x", pady=(10, 0))

        tk.Label(server_frame, text="Server Status:", font=("Arial", 10, "bold")).pack(side="left")
        server_status_label = tk.Label(
            server_frame,
            textvariable=self.server_status_var,
            font=("Arial", 10),
            fg="#D32F2F"
        )
        server_status_label.pack(side="left", padx=(5, 0))

        # Server controls
        server_controls_frame = ttk.Frame(server_frame)
        server_controls_frame.pack(side="right")

        ttk.Button(
            server_controls_frame,
            text="Connect",
            command=self._connect_to_server
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            server_controls_frame,
            text="Refresh",
            command=self._refresh_servers
        ).pack(side="left")

    def _create_upload_section(self) -> None:
        """Create document upload section"""
        self.upload_frame = ttk.LabelFrame(self.main_frame, text="Document Upload", padding="10")
        self.upload_frame.pack(fill="x", padx=10, pady=5)

        # Drop area
        drop_area = tk.Frame(
            self.upload_frame,
            height=150,
            bg="#E3F2FD",
            relief="dashed",
            bd=2
        )
        drop_area.pack(fill="x", pady=(0, 10))

        # Drop area content
        drop_label = tk.Label(
            drop_area,
            text="📁 Drag and drop files here\n\nOr click to browse files",
            font=("Arial", 12),
            bg="#E3F2FD",
            fg="#1976D2"
        )
        drop_label.place(relx=0.5, rely=0.5, anchor="center")

        # Make drop area clickable
        drop_area.bind("<Button-1>", self._browse_files)
        drop_label.bind("<Button-1>", self._browse_files)

        # Setup drag and drop (simplified for now)
        drop_area.bind("<Button-1>", self._on_drop_area_click)

        # Upload controls
        controls_frame = ttk.Frame(self.upload_frame)
        controls_frame.pack(fill="x")

        ttk.Button(
            controls_frame,
            text="📁 Browse Files",
            command=self._browse_files
        ).pack(side="left")

        ttk.Button(
            controls_frame,
            text="📷 Scan Document",
            command=self._scan_document
        ).pack(side="left", padx=(10, 0))

        # Upload options
        options_frame = ttk.Frame(controls_frame)
        options_frame.pack(side="right")

        self.auto_process_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Auto-process uploads",
            variable=self.auto_process_var
        ).pack(side="right")

    def _create_scanner_section(self) -> None:
        """Create scanner hardware section"""
        self.scanner_frame = ttk.LabelFrame(self.main_frame, text="Scanner Hardware", padding="10")
        self.scanner_frame.pack(fill="x", padx=10, pady=5)

        # Scanner status
        status_frame = ttk.Frame(self.scanner_frame)
        status_frame.pack(fill="x", pady=(0, 10))

        tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(status_frame, textvariable=self.scanner_status_var, font=("Arial", 10)).pack(side="left", padx=(5, 0))

        # Scanner controls
        controls_frame = ttk.Frame(self.scanner_frame)
        controls_frame.pack(fill="x")

        # Scanner selection
        tk.Label(controls_frame, text="Scanner:").pack(side="left")
        self.scanner_combo = ttk.Combobox(controls_frame, state="readonly", width=30)
        self.scanner_combo.pack(side="left", padx=(5, 10))
        self.scanner_combo.bind('<<ComboboxSelected>>', self._on_scanner_selected)

        # Scanner settings
        ttk.Button(
            controls_frame,
            text="⚙️ Settings",
            command=self._show_scanner_settings
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            controls_frame,
            text="🔄 Refresh",
            command=self._refresh_scanners
        ).pack(side="left")

    def _create_queue_section(self) -> None:
        """Create upload queue section"""
        self.queue_frame = ttk.LabelFrame(self.main_frame, text="Upload Queue", padding="10")
        self.queue_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Queue status bar
        status_bar = ttk.Frame(self.queue_frame)
        status_bar.pack(fill="x", pady=(0, 10))

        tk.Label(status_bar, textvariable=self.queue_status_var, font=("Arial", 10, "bold")).pack(side="left")

        # Queue controls
        queue_controls = ttk.Frame(status_bar)
        queue_controls.pack(side="right")

        ttk.Button(
            queue_controls,
            text="⏸️ Pause",
            command=self._pause_queue
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            queue_controls,
            text="🧹 Clear Completed",
            command=self._clear_completed
        ).pack(side="left")

        # Queue list with scrollbar
        list_frame = ttk.Frame(self.queue_frame)
        list_frame.pack(fill="both", expand=True)

        # Treeview for queue items
        self.queue_tree = ttk.Treeview(
            list_frame,
            columns=("filename", "status", "progress", "error"),
            show="tree headings",
            height=10
        )

        # Configure columns
        self.queue_tree.heading("#0", text="Time")
        self.queue_tree.heading("filename", text="Filename")
        self.queue_tree.heading("status", text="Status")
        self.queue_tree.heading("progress", text="Progress")
        self.queue_tree.heading("error", text="Error")

        self.queue_tree.column("#0", width=100, minwidth=80)
        self.queue_tree.column("filename", width=250, minwidth=200)
        self.queue_tree.column("status", width=100, minwidth=80)
        self.queue_tree.column("progress", width=100, minwidth=80)
        self.queue_tree.column("error", width=200, minwidth=150)

        # Scrollbar for queue
        queue_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=queue_scrollbar.set)

        # Pack treeview and scrollbar
        self.queue_tree.pack(side="left", fill="both", expand=True)
        queue_scrollbar.pack(side="right", fill="y")

    def _create_status_section(self) -> None:
        """Create status section"""
        self.status_frame = ttk.LabelFrame(self.main_frame, text="System Status", padding="10")
        self.status_frame.pack(fill="x", padx=10, pady=5)

        # Status text widget
        self.status_text = tk.Text(
            self.status_frame,
            height=5,
            wrap="word",
            bg="#F5F5F5",
            fg="#333333",
            font=("Consolas", 9)
        )
        self.status_text.pack(fill="x")

        # Add initial status message
        self._add_status_message("ASR Document Scanner initialized")

    def _setup_event_handlers(self) -> None:
        """Setup event handlers"""
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_closing)

        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self._browse_files())
        self.root.bind("<Control-s>", lambda e: self._scan_document())
        self.root.bind("<F5>", lambda e: self._refresh_all())

    def _start_status_update_timer(self) -> None:
        """Start timer for regular status updates"""
        self._update_status()
        self.root.after(2000, self._start_status_update_timer)  # Update every 2 seconds

    def _browse_files(self, event=None) -> None:
        """Browse for files to upload"""
        try:
            file_types = [
                ("All supported", "*.pdf;*.jpg;*.jpeg;*.png;*.tiff;*.gif"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg;*.jpeg;*.png;*.tiff;*.gif"),
                ("All files", "*.*")
            ]

            file_paths = filedialog.askopenfilenames(
                title="Select documents to upload",
                filetypes=file_types
            )

            if file_paths:
                self._add_files_to_queue([Path(fp) for fp in file_paths])

        except Exception as e:
            self._show_error("File Browse Error", str(e))

    def _scan_document(self) -> None:
        """Scan document using hardware scanner"""
        try:
            if 'scanner_hardware' not in self.services:
                self._show_error("Scanner Error", "Scanner service not available")
                return

            # Run scan in background
            self._run_async_task(self._perform_scan())

        except Exception as e:
            self._show_error("Scan Error", str(e))

    async def _perform_scan(self) -> None:
        """Perform actual scan operation"""
        try:
            scanner_service: ScannerHardwareService = self.services['scanner_hardware']

            self._add_status_message("Starting document scan...")

            # Create scan request with current settings
            scan_request = ScanRequest(
                resolution=scanner_settings.scanner_resolution,
                color_mode=scanner_settings.scanner_color_mode,
                format=scanner_settings.scanner_format
            )

            # Perform scan
            result = await scanner_service.scan_document(scan_request)

            if result.success and result.file_path:
                self._add_status_message(f"Scan completed: {result.file_path.name}")

                # Add scanned document to upload queue
                await self._add_file_to_queue_async(result.file_path)
            else:
                self._add_status_message(f"Scan failed: {result.error_message}")

        except Exception as e:
            self._add_status_message(f"Scan error: {e}")

    def _add_files_to_queue(self, file_paths: List[Path]) -> None:
        """Add multiple files to upload queue"""
        self._run_async_task(self._add_files_to_queue_async(file_paths))

    async def _add_files_to_queue_async(self, file_paths: List[Path]) -> None:
        """Add files to queue asynchronously"""
        try:
            upload_service: UploadQueueService = self.services['upload_queue']

            for file_path in file_paths:
                try:
                    document_id = await upload_service.add_document(file_path)
                    self._add_status_message(f"Added to queue: {file_path.name}")

                    # Start upload if auto-process enabled and server connected
                    if self.auto_process_var.get() and self._is_server_connected():
                        await self._upload_document(document_id, file_path)

                except Exception as e:
                    self._add_status_message(f"Failed to add {file_path.name}: {e}")

        except Exception as e:
            self._add_status_message(f"Queue error: {e}")

    async def _add_file_to_queue_async(self, file_path: Path) -> None:
        """Add single file to queue asynchronously"""
        await self._add_files_to_queue_async([file_path])

    async def _upload_document(self, document_id: str, file_path: Path) -> None:
        """Upload document to production server"""
        try:
            if not self._is_server_connected():
                self._add_status_message("Cannot upload: No server connection")
                return

            upload_service: UploadQueueService = self.services['upload_queue']
            production_client: ProductionServerClient = self.services['production_client']

            # Update status to uploading
            await upload_service.update_document_status(document_id, UploadStatus.UPLOADING)

            self._add_status_message(f"Uploading: {file_path.name}")

            # Perform upload
            result = await production_client.upload_document(file_path)

            if result.success:
                await upload_service.update_document_status(
                    document_id,
                    UploadStatus.COMPLETED,
                    upload_result=result
                )
                self._add_status_message(f"Upload completed: {file_path.name}")
            else:
                await upload_service.update_document_status(
                    document_id,
                    UploadStatus.RETRY,
                    error_message=result.error_message
                )
                self._add_status_message(f"Upload failed: {file_path.name} - {result.error_message}")

        except Exception as e:
            self._add_status_message(f"Upload error: {e}")

    def _connect_to_server(self) -> None:
        """Connect to production server"""
        self._run_async_task(self._connect_to_server_async())

    async def _connect_to_server_async(self) -> None:
        """Connect to server asynchronously"""
        try:
            server_discovery: ServerDiscoveryService = self.services['server_discovery']
            production_client: ProductionServerClient = self.services['production_client']

            self._add_status_message("Discovering servers...")

            # Get best available server
            servers = await server_discovery.discover_servers()

            if not servers:
                self._add_status_message("No servers found")
                return

            best_server = servers[0]  # Already sorted by response time
            self._add_status_message(f"Connecting to: {best_server.url}")

            # Connect to server
            connected = await production_client.connect(best_server.url, scanner_settings.api_key)

            if connected:
                self._add_status_message(f"Connected to production server: {best_server.name}")
                await production_client.register_scanner()
            else:
                self._add_status_message("Connection failed")

        except Exception as e:
            self._add_status_message(f"Connection error: {e}")

    def _refresh_servers(self) -> None:
        """Refresh server discovery"""
        self._run_async_task(self._refresh_servers_async())

    async def _refresh_servers_async(self) -> None:
        """Refresh servers asynchronously"""
        try:
            server_discovery: ServerDiscoveryService = self.services['server_discovery']
            await server_discovery.refresh_discovery()
            self._add_status_message("Server discovery refreshed")
        except Exception as e:
            self._add_status_message(f"Server refresh error: {e}")

    def _refresh_scanners(self) -> None:
        """Refresh scanner list"""
        self._run_async_task(self._refresh_scanners_async())

    async def _refresh_scanners_async(self) -> None:
        """Refresh scanners asynchronously"""
        try:
            scanner_service: ScannerHardwareService = self.services['scanner_hardware']
            await scanner_service.refresh_scanners()

            # Update scanner combo box
            scanners = await scanner_service.get_available_scanners()
            scanner_names = [f"{s.name} ({s.manufacturer})" for s in scanners]

            self.scanner_combo['values'] = scanner_names
            if scanner_names:
                self.scanner_combo.current(0)

            self._add_status_message("Scanner list refreshed")
        except Exception as e:
            self._add_status_message(f"Scanner refresh error: {e}")

    def _is_server_connected(self) -> bool:
        """Check if connected to production server"""
        if 'production_client' in self.services:
            return self.services['production_client'].connected
        return False

    def _run_async_task(self, coro) -> None:
        """Run async coroutine in the event loop"""
        if self.async_loop:
            asyncio.run_coroutine_threadsafe(coro, self.async_loop)

    def update_status(self) -> None:
        """Update status displays (called from main loop)"""
        self._update_status()

    def _update_status(self) -> None:
        """Update all status indicators"""
        try:
            # Update server status
            if self._is_server_connected():
                self.server_status_var.set("Connected")
            else:
                self.server_status_var.set("Disconnected")

            # Update queue status
            self._run_async_task(self._update_queue_status())

            # Update scanner status
            self._run_async_task(self._update_scanner_status())

        except Exception as e:
            logger.warning(f"Status update error: {e}")

    async def _update_queue_status(self) -> None:
        """Update queue status"""
        try:
            if 'upload_queue' in self.services:
                upload_service: UploadQueueService = self.services['upload_queue']
                stats = await upload_service.get_queue_stats()
                self.queue_status_var.set(f"{stats['total']} documents ({stats['pending']} pending)")

                # Update queue display
                await self._refresh_queue_display()

        except Exception as e:
            logger.warning(f"Queue status update error: {e}")

    async def _update_scanner_status(self) -> None:
        """Update scanner status"""
        try:
            if 'scanner_hardware' in self.services:
                scanner_service: ScannerHardwareService = self.services['scanner_hardware']
                active_scanner = await scanner_service.get_active_scanner()

                if active_scanner:
                    self.scanner_status_var.set(f"{active_scanner.name} - {active_scanner.status.value}")
                else:
                    self.scanner_status_var.set("No scanner selected")

        except Exception as e:
            logger.warning(f"Scanner status update error: {e}")

    async def _refresh_queue_display(self) -> None:
        """Refresh the queue display"""
        try:
            if 'upload_queue' in self.services:
                # Clear current items
                for item in self.queue_tree.get_children():
                    self.queue_tree.delete(item)

                # Get pending documents
                upload_service: UploadQueueService = self.services['upload_queue']
                documents = await upload_service.get_pending_documents(limit=50)

                # Add documents to tree
                for doc in documents:
                    self.queue_tree.insert("", "end",
                                          text=doc.created_at.strftime("%H:%M:%S"),
                                          values=(
                                              doc.filename,
                                              doc.status.value,
                                              f"{doc.retry_count}/3" if doc.retry_count > 0 else "",
                                              doc.error_message or ""
                                          ))

        except Exception as e:
            logger.warning(f"Queue display refresh error: {e}")

    def _add_status_message(self, message: str) -> None:
        """Add message to status log"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"

            self.status_text.insert(tk.END, formatted_message)
            self.status_text.see(tk.END)

            # Limit status text length
            lines = self.status_text.get("1.0", tk.END).split('\n')
            if len(lines) > 100:
                self.status_text.delete("1.0", f"{len(lines) - 100}.0")

        except Exception as e:
            logger.warning(f"Status message error: {e}")

    def _show_error(self, title: str, message: str) -> None:
        """Show error dialog"""
        messagebox.showerror(title, message)

    def _show_info(self, title: str, message: str) -> None:
        """Show info dialog"""
        messagebox.showinfo(title, message)

    def _on_drop_area_click(self, event) -> None:
        """Handle drop area click"""
        self._browse_files()

    def _on_scanner_selected(self, event) -> None:
        """Handle scanner selection"""
        selection = self.scanner_combo.get()
        if selection:
            self._run_async_task(self._set_active_scanner(selection))

    async def _set_active_scanner(self, scanner_name: str) -> None:
        """Set active scanner"""
        try:
            if 'scanner_hardware' in self.services:
                scanner_service: ScannerHardwareService = self.services['scanner_hardware']
                scanners = await scanner_service.get_available_scanners()

                for scanner in scanners:
                    full_name = f"{scanner.name} ({scanner.manufacturer})"
                    if full_name == scanner_name:
                        await scanner_service.set_active_scanner(scanner.id)
                        self._add_status_message(f"Selected scanner: {scanner.name}")
                        break

        except Exception as e:
            self._add_status_message(f"Scanner selection error: {e}")

    def _show_scanner_settings(self) -> None:
        """Show scanner settings dialog"""
        # This would open a settings dialog (simplified for now)
        self._show_info("Scanner Settings", "Scanner settings dialog would open here")

    def _pause_queue(self) -> None:
        """Pause/resume queue processing"""
        # Toggle queue processing (simplified for now)
        self._add_status_message("Queue processing paused/resumed")

    def _clear_completed(self) -> None:
        """Clear completed documents from queue"""
        self._run_async_task(self._clear_completed_async())

    async def _clear_completed_async(self) -> None:
        """Clear completed documents asynchronously"""
        try:
            if 'upload_queue' in self.services:
                upload_service: UploadQueueService = self.services['upload_queue']
                cleared_count = await upload_service.clear_completed()
                self._add_status_message(f"Cleared {cleared_count} completed documents")

        except Exception as e:
            self._add_status_message(f"Clear completed error: {e}")

    def _refresh_all(self) -> None:
        """Refresh all components"""
        self._refresh_servers()
        self._refresh_scanners()
        self._add_status_message("Refreshed all components")

    def _on_window_closing(self) -> None:
        """Handle window closing"""
        try:
            # Save window geometry
            geometry = self.root.geometry()
            # Could save to settings here

            self._add_status_message("Shutting down scanner application...")
            self.root.quit()

        except Exception as e:
            logger.error(f"Window closing error: {e}")
            self.root.quit()