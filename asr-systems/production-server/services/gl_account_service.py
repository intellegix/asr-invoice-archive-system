"""
ASR Production Server - GL Account Service
Manages 79 QuickBooks GL Accounts with keyword matching and sophisticated classification
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Import shared components
from shared.core.constants import GL_ACCOUNT_CATEGORIES, GL_ACCOUNTS
from shared.core.exceptions import ClassificationError, ValidationError
from shared.core.models import GLAccount

logger = logging.getLogger(__name__)


def load_gl_accounts_from_yaml(config_path: str) -> Dict[str, Dict[str, Any]]:
    """Load GL accounts from a YAML config file.

    Returns the accounts dict on success, or raises on parse error.
    """
    path = Path(config_path)
    if not path.is_absolute():
        # Resolve relative to asr-systems/
        path = Path(__file__).parent.parent.parent / path
    if not path.exists():
        raise FileNotFoundError(f"GL accounts config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "accounts" not in data:
        raise ValueError("GL accounts YAML must have a top-level 'accounts' key")
    accounts = data["accounts"]
    if not isinstance(accounts, dict) or len(accounts) == 0:
        raise ValueError("GL accounts YAML 'accounts' must be a non-empty mapping")
    # Validate each entry has required fields
    for code, entry in accounts.items():
        for field in ("name", "category", "keywords"):
            if field not in entry:
                raise ValueError(
                    f"GL account '{code}' missing required field '{field}'"
                )
    return accounts


@dataclass
class GLClassificationResult:
    """Result of GL account classification"""

    gl_account_code: str
    gl_account_name: str
    category: str
    confidence: float
    reasoning: str
    keywords_matched: List[str]
    classification_method: str


class GLAccountService:
    """
    Service for managing 79 QuickBooks GL Accounts with sophisticated classification
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        vendor_service: Optional[Any] = None,
    ):
        self.config_path = config_path
        self._vendor_service = vendor_service
        self.gl_accounts: Dict[str, GLAccount] = {}
        self.keyword_index: Dict[str, List[str]] = {}  # keyword -> [gl_codes]
        self.category_index: Dict[str, List[str]] = {}  # category -> [gl_codes]
        self.initialized = False

    async def initialize(self):
        """Initialize GL Account service with 79 QuickBooks accounts"""
        try:
            logger.info("Initializing GL Account Service...")

            # Load all 79 GL accounts from constants
            self._load_gl_accounts()

            # Build keyword index for fast searching
            self._build_keyword_index()

            # Build category index
            self._build_category_index()

            self.initialized = True

            logger.info(f"✅ GL Account Service initialized:")
            logger.info(f"   • {len(self.gl_accounts)} GL accounts loaded")
            logger.info(f"   • {len(self.keyword_index)} keywords indexed")
            logger.info(f"   • {len(self.category_index)} categories available")

        except Exception as e:
            logger.error(f"Failed to initialize GL Account Service: {e}")
            raise ClassificationError(f"GL Account service initialization failed: {e}")

    def _load_gl_accounts(self) -> None:
        """Load GL accounts from YAML config, falling back to constants."""
        source = "constants"
        accounts_data = GL_ACCOUNTS

        if self.config_path:
            try:
                accounts_data = load_gl_accounts_from_yaml(self.config_path)
                source = self.config_path
            except Exception as e:
                logger.warning(
                    "Failed to load GL accounts from %s, using built-in constants: %s",
                    self.config_path,
                    e,
                )
                accounts_data = GL_ACCOUNTS

        for code, account_data in accounts_data.items():
            self.gl_accounts[str(code)] = GLAccount(
                code=str(code),
                name=account_data["name"],
                category=account_data["category"],
                keywords=account_data["keywords"],
                active=True,
            )

        logger.info("Loaded %d GL accounts from %s", len(self.gl_accounts), source)

    def _build_keyword_index(self):
        """Build reverse index of keywords to GL account codes"""
        for code, account in self.gl_accounts.items():
            for keyword in account.keywords:
                # Normalize keyword for better matching
                normalized_keyword = keyword.lower().strip()
                if normalized_keyword not in self.keyword_index:
                    self.keyword_index[normalized_keyword] = []
                self.keyword_index[normalized_keyword].append(code)

    def _build_category_index(self):
        """Build index of categories to GL account codes"""
        for code, account in self.gl_accounts.items():
            if account.category not in self.category_index:
                self.category_index[account.category] = []
            self.category_index[account.category].append(code)

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all 79 GL accounts"""
        if not self.initialized:
            raise ClassificationError("GL Account service not initialized")

        return [
            {
                "code": account.code,
                "name": account.name,
                "category": account.category,
                "keywords": account.keywords,
                "active": account.active,
            }
            for account in self.gl_accounts.values()
        ]

    def get_accounts(
        self, category: Optional[str] = None, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get GL accounts with filtering"""
        if not self.initialized:
            raise ClassificationError("GL Account service not initialized")

        accounts = self.get_all_accounts()

        # Filter by category
        if category:
            accounts = [acc for acc in accounts if acc["category"] == category.upper()]

        # Filter by search term
        if search:
            search_term = search.lower()
            filtered_accounts = []

            for account in accounts:
                # Search in code, name, and keywords
                if (
                    search_term in account["code"].lower()
                    or search_term in account["name"].lower()
                    or any(
                        search_term in keyword.lower()
                        for keyword in account["keywords"]
                    )
                ):
                    filtered_accounts.append(account)

            accounts = filtered_accounts

        return accounts

    def get_account_by_code(self, code: str) -> Optional[GLAccount]:
        """Get specific GL account by code"""
        if not self.initialized:
            raise ClassificationError("GL Account service not initialized")

        return self.gl_accounts.get(code)

    def get_categories(self) -> Dict[str, List[str]]:
        """Get all categories with their GL account codes"""
        if not self.initialized:
            raise ClassificationError("GL Account service not initialized")

        return self.category_index.copy()

    async def classify_document_text(
        self,
        document_text: str,
        vendor_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> GLClassificationResult:
        """
        Classify document using sophisticated keyword matching and vendor analysis

        Args:
            document_text: Extracted text from document
            vendor_name: Detected vendor name (if available)
            tenant_id: Tenant for vendor DB lookup (if available)

        Returns:
            GLClassificationResult with best match and confidence
        """
        if not self.initialized:
            raise ClassificationError("GL Account service not initialized")

        try:
            # Normalize text for analysis
            normalized_text = document_text.lower()

            # Try multiple classification approaches
            results = []

            # Method 1: Vendor-specific mapping (DB-backed + hardcoded fallback)
            if vendor_name:
                vendor_result = await self._classify_by_vendor(vendor_name, tenant_id)
                if vendor_result:
                    results.append(vendor_result)

            # Method 2: Keyword matching in document text
            keyword_result = self._classify_by_keywords(normalized_text)
            if keyword_result:
                results.append(keyword_result)

            # Method 3: Pattern matching for common document types
            pattern_result = self._classify_by_patterns(normalized_text)
            if pattern_result:
                results.append(pattern_result)

            # Method 4: Category-based heuristics
            category_result = self._classify_by_category_heuristics(normalized_text)
            if category_result:
                results.append(category_result)

            # Select best result based on confidence
            if results:
                best_result = max(results, key=lambda x: x.confidence)

                # Boost confidence if multiple methods agree
                if len(results) > 1:
                    same_account_results = [
                        r
                        for r in results
                        if r.gl_account_code == best_result.gl_account_code
                    ]
                    if len(same_account_results) > 1:
                        confidence_boost = min(
                            0.2, 0.1 * (len(same_account_results) - 1)
                        )
                        best_result.confidence = min(
                            1.0, best_result.confidence + confidence_boost
                        )
                        best_result.reasoning += f" (Confidence boosted by {len(same_account_results)} matching methods)"

                return best_result
            else:
                # Default to miscellaneous expense if no matches
                default_code = "7700"  # Miscellaneous
                default_account = self.gl_accounts.get(default_code)

                if default_account:
                    return GLClassificationResult(
                        gl_account_code=default_code,
                        gl_account_name=default_account.name,
                        category=default_account.category,
                        confidence=0.3,
                        reasoning="No specific matches found, defaulted to miscellaneous expense",
                        keywords_matched=[],
                        classification_method="default",
                    )
                else:
                    raise ClassificationError(
                        "Unable to classify document and default account not available"
                    )

        except Exception as e:
            logger.error(f"GL classification error: {e}")
            raise ClassificationError(f"Failed to classify document: {e}")

    async def _classify_by_vendor(
        self, vendor_name: str, tenant_id: Optional[str] = None
    ) -> Optional[GLClassificationResult]:
        """Classify based on DB vendor lookup, then fall back to hardcoded patterns."""
        # --- DB lookup (via VendorService) ---
        if self._vendor_service:
            try:
                matched = await self._vendor_service.match_vendor(
                    vendor_name, tenant_id
                )
                if matched and matched.get("default_gl_account"):
                    gl_code = matched["default_gl_account"]
                    account = self.gl_accounts.get(gl_code)
                    if account:
                        logger.info(
                            "Vendor DB match: vendor=%s gl=%s method=database",
                            vendor_name,
                            gl_code,
                        )
                        return GLClassificationResult(
                            gl_account_code=gl_code,
                            gl_account_name=account.name,
                            category=account.category,
                            confidence=0.95,
                            reasoning=(
                                f"Vendor '{vendor_name}' matched DB vendor "
                                f"'{matched['name']}' (id={matched['id']})"
                            ),
                            keywords_matched=[matched["name"]],
                            classification_method="vendor_database",
                        )
            except Exception:
                logger.exception("Vendor DB lookup failed for '%s'", vendor_name)

        # --- Hardcoded fallback ---
        vendor_lower = vendor_name.lower()

        vendor_mappings = {
            # Materials/Supplies
            "home depot": "5000",
            "lowes": "5000",
            "lowe's": "5000",
            "abc supply": "5000",
            "beacon": "5000",
            "ferguson": "5000",
            # Utilities
            "sdge": "6600",
            "san diego gas": "6600",
            "cox": "6600",
            "verizon": "6600",
            "at&t": "6600",
            "att": "6600",
            # Waste Management
            "usa waste": "6600",
            "waste management": "6600",
            "republic": "6600",
            "edco": "6600",
            # Fuel
            "shell": "6900",
            "chevron": "6900",
            "mobil": "6900",
            "exxon": "6900",
            "arco": "6900",
            # Professional Services
            "attorney": "5700",
            "law firm": "5700",
            "legal": "5700",
            "accountant": "5700",
            "cpa": "5700",
            # Insurance
            "insurance": "5500",
            "farmers": "5500",
            "state farm": "5500",
            "allstate": "5500",
        }

        for vendor_pattern, gl_code in vendor_mappings.items():
            if vendor_pattern in vendor_lower:
                account = self.gl_accounts.get(gl_code)
                if account:
                    logger.info(
                        "Vendor hardcoded match: vendor=%s gl=%s method=hardcoded",
                        vendor_name,
                        gl_code,
                    )
                    return GLClassificationResult(
                        gl_account_code=gl_code,
                        gl_account_name=account.name,
                        category=account.category,
                        confidence=0.85,
                        reasoning=f"Vendor '{vendor_name}' matches known pattern '{vendor_pattern}'",
                        keywords_matched=[vendor_pattern],
                        classification_method="vendor_mapping",
                    )

        return None

    def _classify_by_keywords(self, text: str) -> Optional[GLClassificationResult]:
        """Classify based on keyword matching in document text"""
        keyword_matches = {}

        for keyword, gl_codes in self.keyword_index.items():
            if keyword in text:
                for gl_code in gl_codes:
                    if gl_code not in keyword_matches:
                        keyword_matches[gl_code] = {"keywords": [], "score": 0}
                    keyword_matches[gl_code]["keywords"].append(keyword)
                    keyword_matches[gl_code]["score"] += 1

        if keyword_matches:
            # Get best match by score
            best_match = max(keyword_matches.items(), key=lambda x: x[1]["score"])
            gl_code = best_match[0]
            match_data = best_match[1]

            account = self.gl_accounts.get(gl_code)
            if account:
                # Calculate confidence based on number of keyword matches
                confidence = min(0.9, 0.6 + (match_data["score"] * 0.1))

                return GLClassificationResult(
                    gl_account_code=gl_code,
                    gl_account_name=account.name,
                    category=account.category,
                    confidence=confidence,
                    reasoning=f"Keywords matched: {', '.join(match_data['keywords'])}",
                    keywords_matched=match_data["keywords"],
                    classification_method="keyword_matching",
                )

        return None

    def _classify_by_patterns(self, text: str) -> Optional[GLClassificationResult]:
        """Classify based on document patterns and context"""
        patterns = {
            # Fuel patterns
            (r"\b(?:gallon|gal|diesel|gas|fuel)\b", "6900"): 0.8,
            (r"\b(?:pump|station|fuel up)\b", "6900"): 0.7,
            # Utilities patterns
            (r"\b(?:electric|electricity|kwh|utility)\b", "6600"): 0.8,
            (r"\b(?:water|sewer|gas bill)\b", "6600"): 0.8,
            (r"\b(?:phone|internet|cable)\b", "6600"): 0.7,
            # Materials patterns
            (r"\b(?:lumber|plywood|drywall|materials)\b", "5000"): 0.8,
            (r"\b(?:tools|hardware|supplies)\b", "5800"): 0.7,
            # Professional services patterns
            (r"\b(?:consultation|legal fee|attorney)\b", "5700"): 0.8,
            (r"\b(?:accounting|tax prep|cpa)\b", "5700"): 0.7,
            # Vehicle patterns
            (r"\b(?:oil change|maintenance|repair)\b", "6100"): 0.7,
            (r"\b(?:truck|vehicle|auto)\b", "5200"): 0.6,
            # Insurance patterns
            (r"\b(?:premium|coverage|policy)\b", "5500"): 0.7,
            # Rent patterns
            (r"\b(?:rent|lease|monthly)\b", "6000"): 0.7,
        }

        for (pattern, gl_code), confidence in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                account = self.gl_accounts.get(gl_code)
                if account:
                    return GLClassificationResult(
                        gl_account_code=gl_code,
                        gl_account_name=account.name,
                        category=account.category,
                        confidence=confidence,
                        reasoning=f"Document pattern matched: {pattern}",
                        keywords_matched=[pattern],
                        classification_method="pattern_matching",
                    )

        return None

    def _classify_by_category_heuristics(
        self, text: str
    ) -> Optional[GLClassificationResult]:
        """Classify using category-level heuristics"""
        # Simple heuristics for common expense types
        if any(term in text for term in ["invoice", "bill", "receipt"]):
            # Most common expense categories in order of likelihood
            common_expense_codes = ["5000", "6600", "6900", "5200", "5700"]

            for gl_code in common_expense_codes:
                account = self.gl_accounts.get(gl_code)
                if account:
                    return GLClassificationResult(
                        gl_account_code=gl_code,
                        gl_account_name=account.name,
                        category=account.category,
                        confidence=0.4,
                        reasoning="Category heuristic based on common expense patterns",
                        keywords_matched=["invoice", "bill", "receipt"],
                        classification_method="category_heuristic",
                    )

        return None

    def validate_gl_account(self, gl_code: str) -> bool:
        """Validate if GL account code exists and is active"""
        if not self.initialized:
            raise ClassificationError("GL Account service not initialized")

        account = self.gl_accounts.get(gl_code)
        return account is not None and account.active

    async def cleanup(self):
        """Cleanup GL Account service"""
        logger.info("Cleaning up GL Account Service...")
        self.gl_accounts.clear()
        self.keyword_index.clear()
        self.category_index.clear()
        self.initialized = False
