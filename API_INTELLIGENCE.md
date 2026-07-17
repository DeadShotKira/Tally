# Intelligence Layer - API Reference

## Overview

The Intelligence Layer provides AI-powered insights, categorization, and chat capabilities while maintaining strict privacy guarantees. All AI operations are sandboxed, deterministic rules execute first, and confidence-based user confirmation workflows prevent unwanted auto-categorization.

## Quick Start

### Basic Categorization

```python
from backend.app.features.intelligence.categorization_service import CategorizationService
from backend.app.features.transactions.models import Transaction

# Initialize service
service = CategorizationService()

# Categorize a transaction
result = await service.categorize(
    transaction=transaction,
    user_id=user_id,
    existing_categories=["Groceries", "Shopping", "Food"],
)

# Check result
if result.auto_applied:
    print(f"Auto-applied: {result.category}")
elif result.requires_confirmation():
    print(f"Needs confirmation: {result.category} ({result.confidence:.2f})")
else:
    print(f"Fallback: {result.category}")
```

### Privacy Filtering

```python
from backend.app.features.intelligence.context_builder import PrivacyFilter

# Check if text is safe for AI
if not PrivacyFilter.is_safe_for_ai(description):
    print("Text contains sensitive data")
    
# Sanitize text
result = PrivacyFilter.sanitize_text(description)
print(f"Sanitized: {result.sanitized_text}")
```

### Rule Creation

```python
from backend.app.features.intelligence.rule_engine import RuleEngine, RuleType

# Create a simple rule
rule = RuleEngine.build_exact_match_rule(
    user_id=user_id,
    merchant="Amazon",
    category="Shopping",
)

# Evaluate rules
match = engine.evaluate_rules(transaction, [rule])
if match:
    print(f"Rule matched: {match.rule_name}")
```

### Merchant Memory

```python
from backend.app.features.intelligence.merchant_memory import MerchantMemoryEngine

engine = MerchantMemoryEngine()

# Record user decision
memory = engine.record_user_decision(
    user_id=user_id,
    merchant_raw="RAHUL KUMAR",
    merchant_canonical="Rahul Vegetable Vendor",
    category="Groceries",
)

# Find best match
match = engine.find_best_match(user_id, "RAHUL VEGETABLES", threshold=0.7)
if match:
    print(f"Found: {match.canonical}")
```

### Insights Generation

```python
from backend.app.features.intelligence.insights_engine import InsightsEngine

engine = InsightsEngine()

# Generate insights
insights = engine.generate_insights(
    transactions=transactions,
    user_id=user_id,
    lookback_days=90,
)

for insight in insights:
    print(f"[{insight.severity}] {insight.title}: {insight.description}")
```

## API Reference

### CategorizationService

**Main Service for Transaction Categorization**

```python
async def categorize(
    transaction: Transaction,
    user_id: UUID,
    rules: list[Any] | None = None,
    existing_categories: list[str] | None = None,
    allow_ai: bool = True,
    min_confidence: float = 0.0,
) -> CategorizationResult:
    """
    Categorize a transaction following priority:
    1. Rules → if match, auto-apply
    2. Merchant memory → if exact match, apply
    3. AI → get suggestion with confidence
    4. Fallback → keep existing or suggest default
    
    Args:
        transaction: Transaction to categorize
        user_id: User ID for personalization
        rules: Optional list of Rule objects
        existing_categories: Valid category names
        allow_ai: Whether to query AI
        min_confidence: Minimum acceptable confidence
        
    Returns:
        CategorizationResult with:
        - category: Suggested category
        - confidence: 0.0-1.0 score
        - confidence_level: HIGH/MEDIUM/LOW
        - source: "rule"/"memory"/"ai"/"fallback"
        - auto_applied: Whether auto-applied
        - requires_confirmation(): User confirmation needed?
    """
```

### PrivacyFilter

**Text Sanitization & Safety Checks**

```python
@staticmethod
def sanitize_text(text: str | None) -> SanitizationResult:
    """
    Sanitize text by redacting sensitive patterns.
    
    Detects and redacts:
    - Account numbers (9-18 digits)
    - IFSC codes (XXXX0XXXXXX)
    - UPI IDs (user@bank)
    - Phone numbers (6-9 + 9 digits)
    - Card numbers (4-4-4-4)
    - Reference IDs (REF/UTR/RRN format)
    
    Returns:
        SanitizationResult with sanitized text and redactions
    """

@staticmethod
def is_safe_for_ai(text: str | None) -> bool:
    """
    Check if text contains no sensitive patterns.
    
    Returns:
        True if safe to send to AI, False if contains sensitive data
    """
```

### AIContextBuilder

**Creates Privacy-Filtered AI Contexts**

```python
def build_categorization_context(
    transaction: Transaction,
    existing_categories: list[str] | None = None,
) -> SanitizedContext:
    """
    Build sanitized context for category suggestions.
    
    Returns minimal context:
    - sanitized merchant name
    - sanitized description
    - amount
    - direction
    - date
    
    Raises:
        ValueError: If unsafe patterns detected
    """

def build_chat_context(
    transactions: list[Transaction],
    filters: TransactionFilters | None = None,
    aggregates_only: bool = True,
) -> dict[str, Any]:
    """
    Build context for chat queries.
    
    Prefers aggregates over individual transactions:
    - transaction_count
    - total_spent / total_income
    - category_breakdown
    - top_merchants
    - (optional) recent_transactions (if count <= 50)
    """

def validate_context_safety(
    context: SanitizedContext | dict,
) -> bool:
    """
    Validate that context contains no sensitive patterns.
    
    Raises:
        ValueError: If unsafe patterns found
        
    Returns:
        True if safe
    """
```

### RuleEngine

**Deterministic Rule Evaluation**

```python
def evaluate_rules(
    transaction: Transaction,
    rules: list[Rule],
) -> RuleMatch | None:
    """
    Find first matching rule for transaction.
    
    Rules evaluated in priority order (lower priority = higher priority).
    
    Returns:
        RuleMatch if rule matches, None otherwise
    """

def apply_rule_action(
    transaction: Transaction,
    rule_match: RuleMatch,
) -> Transaction:
    """Apply matched rule's action to transaction."""

@staticmethod
def build_exact_match_rule(
    user_id: UUID,
    merchant: str,
    category: str | None = None,
    priority: int = 100,
) -> Rule:
    """Create a simple exact merchant match rule."""

@staticmethod
def build_pattern_rule(
    user_id: UUID,
    pattern_type: RuleType,
    pattern: str,
    category: str | None = None,
    priority: int = 100,
) -> Rule:
    """Create a pattern matching rule."""
```

**Supported Rule Types**:
- `merchant_exact` - Exact merchant name match
- `merchant_contains` - Substring matching
- `merchant_prefix` - Starts with pattern
- `merchant_suffix` - Ends with pattern
- `merchant_regex` - Regular expression matching
- `amount_threshold` - Amount-based matching
- `combined` - Multiple conditions (AND logic)

### MerchantMemoryEngine

**Learning from User Decisions**

```python
def find_exact_match(
    user_id: UUID,
    merchant: str,
) -> MerchantMemoryCandidate | None:
    """Find exact merchant memory match."""

def find_best_match(
    user_id: UUID,
    merchant: str,
    threshold: float = 0.7,
) -> MerchantMemoryCandidate | None:
    """Find best matching merchant memory with similarity scoring."""

def apply_memory_to_transaction(
    transaction: Transaction,
    user_id: UUID,
    auto_apply_threshold: float = 0.95,
) -> tuple[Transaction, MerchantMemoryCandidate | None]:
    """
    Try to apply merchant memory to transaction.
    
    Returns:
        (possibly modified transaction, matching memory or None)
    """

def record_user_decision(
    user_id: UUID,
    merchant_raw: str,
    merchant_canonical: str,
    category: str | None = None,
    user_renamed_to: str | None = None,
) -> MerchantMemory:
    """Record user's decision about a merchant."""
```

### ConfidenceEngine

**Confidence Scoring & Thresholding**

```python
def calculate_confidence_level(
    score: float,
) -> ConfidenceLevel:
    """
    Map confidence score (0.0-1.0) to level.
    
    HIGH:   >= 0.85
    MEDIUM: 0.70-0.84
    LOW:    < 0.70
    """

def should_auto_apply(
    score: float,
    level: ConfidenceLevel | None = None,
) -> bool:
    """Check if confidence >= auto_apply_threshold (default 0.90)."""

def should_require_confirmation(
    score: float,
    level: ConfidenceLevel | None = None,
) -> bool:
    """Check if user confirmation is required (anything below HIGH)."""

def should_reject(
    score: float,
    level: ConfidenceLevel | None = None,
) -> bool:
    """Check if suggestion should be hidden (< 0.40)."""

def adjust_category_suggestion(
    suggestion: AICategory,
) -> AICategory:
    """Adjust category with proper confidence level."""

def evaluate_confidence_breakdown(
    score: float,
) -> dict[str, Any]:
    """Get detailed breakdown of confidence score."""
```

### AICache

**Response Caching for Efficiency**

```python
def get_category(
    user_id: UUID,
    context: SanitizedContext,
) -> AICategory | None:
    """Retrieve cached category suggestion or None."""

def set_category(
    user_id: UUID,
    context: SanitizedContext,
    suggestion: AICategory,
) -> None:
    """Cache a category suggestion."""

def get_merchant(
    user_id: UUID,
    context: SanitizedContext,
) -> AIMerchant | None:
    """Retrieve cached merchant suggestion or None."""

def set_merchant(
    user_id: UUID,
    context: SanitizedContext,
    suggestion: AIMerchant,
) -> None:
    """Cache a merchant suggestion."""

def clear_user_cache(user_id: UUID) -> int:
    """Clear all cache for user. Returns count cleared."""

def cleanup_expired() -> int:
    """Remove expired entries. Returns count removed."""

def get_stats() -> dict[str, Any]:
    """Get cache statistics."""
```

### RecurringDetector

**Subscription & Recurring Payment Detection**

```python
def detect_recurring(
    transactions: list[Transaction],
    user_id: UUID,
) -> list[RecurringTransaction]:
    """
    Detect recurring transactions.
    
    Requirements:
    - Minimum 3 occurrences
    - Consistent frequency (configurable variance)
    - Amount similarity ±1%
    
    Returns:
        List of RecurringTransaction objects with confidence scores
    """
```

### InsightsEngine

**Proactive Financial Insights**

```python
def generate_insights(
    transactions: list[Transaction],
    user_id: UUID,
    lookback_days: int = 90,
) -> list[Insight]:
    """
    Generate insights.
    
    Generates:
    - subscription_detected: Recurring payments
    - anomaly: Unusual expenses
    - spending_trend: Increase/decrease >20%
    - category_insight: Top spending categories
    
    Returns:
        List of Insight objects
    """
```

## Privacy Guarantees

### What AI Can See
✅ Sanitized merchant names (redacted)
✅ Sanitized descriptions (redacted)
✅ Amount (rounded when appropriate)
✅ Direction (debit/credit)
✅ Date (ISO format)
✅ Aggregated statistics
✅ Category names only

### What AI Cannot See
❌ Account numbers or identifiers
❌ IFSC codes, UPI IDs, phone numbers
❌ Statement headers or raw files
❌ Customer IDs, reference numbers
❌ Authentication tokens
❌ Any original banking data

## Configuration

### Confidence Thresholds
```python
from backend.app.features.intelligence.confidence_engine import ConfidenceThresholds

thresholds = ConfidenceThresholds(
    high_threshold=0.85,      # >= this = HIGH
    medium_threshold=0.70,    # >= this = MEDIUM
    auto_apply_threshold=0.90, # minimum for auto-apply
)

engine = ConfidenceEngine(thresholds=thresholds)
```

### Cache Configuration
```python
from backend.app.features.intelligence.cache import AICache

cache = AICache(
    max_entries=10000,  # Maximum cache size
    ttl_days=30,       # Time-to-live for entries
)
```

### Recurring Detection Configuration
```python
from backend.app.features.intelligence.insights_engine import RecurringDetector

detector = RecurringDetector(
    min_occurrences=3,      # Minimum transactions to consider recurring
    max_days_variance=5,    # Maximum variance in days between occurrences
)
```

## Error Handling

### Privacy Violations
```python
from backend.app.features.intelligence.context_builder import AIContextBuilder

builder = AIContextBuilder()
try:
    context = builder.build_categorization_context(transaction)
except ValueError as e:
    # Handle privacy violation
    print(f"Privacy violation prevented: {e}")
    # Don't send to AI - use fallback
```

### AI Unavailability
The categorization service gracefully falls back when AI is unavailable:
- Keeps existing category if present
- Suggests first available category
- Returns low confidence (0.0) result
- Does NOT auto-apply

## Testing

### Run All Tests
```bash
pytest backend/tests/features/intelligence/ -v
```

### Run Specific Test
```bash
pytest backend/tests/features/intelligence/test_context_builder.py -v
```

## Performance Characteristics

- **Context Building**: O(n) text processing
- **Rule Evaluation**: O(m) where m = number of rules
- **Merchant Matching**: O(k) where k = stored memories
- **Cache Lookups**: O(1) dictionary access
- **Insight Generation**: O(t) where t = transaction count

## Examples

See `EXAMPLE.py` for a complete end-to-end example demonstrating all components working together.

## Architecture Decision Records

- **Why privacy filter before AI**: Prevents exposure of sensitive data
- **Why confidence scoring**: Enables user control over auto-categorization
- **Why rules before AI**: Deterministic first, AI as enhancement
- **Why merchant memory**: Learn from user feedback
- **Why caching**: Reduces API calls and latency
- **Why provider abstraction**: Allows easy AI provider switching

## Future Enhancements

- [ ] Real OpenAI/Gemini integration
- [ ] Advanced NLP for chat
- [ ] Multi-language support
- [ ] Custom model training
- [ ] Budget alert integration
- [ ] Anomaly detection ML model
- [ ] Spending prediction
- [ ] Tax category suggestions

## Contributing

When extending the Intelligence Layer:
1. Maintain privacy-first approach
2. Add confidence scoring
3. Include fallback behavior
4. Write comprehensive tests
5. Document sensitive operations
6. Update this API reference

## License

Proprietary - See LICENSE file
