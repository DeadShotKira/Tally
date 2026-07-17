from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from .bank_detector import BankDetector
from .duplicates import DuplicateDetector
from .errors import ImportEngineError
from .file_manager import TemporaryStatementFileManager
from .logging import SafeImportLogger
from .merchant_resolver import MerchantResolver
from .models import (
    ImportRecord,
    ImportRequest,
    ImportStatus,
    ImportSummary,
    NormalizedCandidate,
    NormalizedTransaction,
    PrivacyAction,
    PrivacyMode,
    ValidationIssue,
)
from .normalizer import TransactionNormalizer
from .parsers import StatementParserFactory
from .privacy import PrivacyEngine
from .repository import ImportRepository
from .validator import TransactionValidator


class ImportService:
    def __init__(
        self,
        *,
        file_manager: TemporaryStatementFileManager,
        bank_detector: BankDetector,
        parser_factory: StatementParserFactory,
        normalizer: TransactionNormalizer,
        validator: TransactionValidator,
        privacy_engine: PrivacyEngine,
        merchant_resolver: MerchantResolver,
        duplicate_detector: DuplicateDetector,
        repository: ImportRepository,
        logger: SafeImportLogger | None = None,
    ):
        self.file_manager = file_manager
        self.bank_detector = bank_detector
        self.parser_factory = parser_factory
        self.normalizer = normalizer
        self.validator = validator
        self.privacy_engine = privacy_engine
        self.merchant_resolver = merchant_resolver
        self.duplicate_detector = duplicate_detector
        self.repository = repository
        self.logger = logger or SafeImportLogger()

    def import_csv(self, request: ImportRequest) -> ImportSummary:
        started = perf_counter()
        temporary = None
        import_record: ImportRecord | None = None
        privacy_actions: list[PrivacyAction] = []
        try:
            self.logger.info("import_started", user_id=str(request.user_id), privacy_mode=request.privacy_mode.value)
            temporary = self.file_manager.prepare_csv(request.source_path, request.original_filename)
            csv_text = self.file_manager.read_text(temporary)
            detection = self.bank_detector.detect(csv_text)
            self.logger.info("bank_detected", bank_code=detection.bank_code, confidence=detection.confidence)
            if not detection.supported:
                raise ImportEngineError("Unsupported bank format.", technical_detail="Bank detector returned unsupported format")

            parser = self.parser_factory.for_bank(detection.bank_code)
            self.logger.info("parser_selected", parser=parser.__class__.__name__)
            parsed = parser.parse(csv_text)
            parse_warnings = tuple(
                ValidationIssue(None, "parser_warning", warning) for warning in parsed.warnings
            )

            import_record = ImportRecord.start(
                user_id=request.user_id,
                filename=temporary.original_filename,
                file_hash=temporary.sha256,
                detected_bank=detection.bank_code,
                privacy_mode=request.privacy_mode,
            )

            if self.duplicate_detector.file_already_imported(user_id=request.user_id, file_hash=temporary.sha256):
                self.repository.save_import(import_record)
                privacy_actions.extend(self._handle_file_lifecycle(request.privacy_mode, temporary))
                duration_ms = self._duration_ms(started)
                self.repository.complete_import(
                    import_record,
                    status=ImportStatus.COMPLETED,
                    transaction_count=0,
                    validation_error_count=0,
                    validation_warning_count=len(parse_warnings),
                    processing_duration_ms=duration_ms,
                )
                return ImportSummary(
                    import_id=import_record.id,
                    status=ImportStatus.COMPLETED,
                    detected_bank=detection.bank_code,
                    imported_transactions=0,
                    failed_rows=0,
                    duplicate_rows=len(parsed.rows),
                    validation_warnings=parse_warnings,
                    validation_errors=(),
                    privacy_actions=tuple(privacy_actions),
                    processing_duration_ms=duration_ms,
                    user_message="This statement was already imported. No duplicate transactions were created.",
                )

            self.repository.save_import(import_record)
            candidates, normalization_errors = self._normalize_rows(parsed.rows)
            validation_report = self.validator.validate_candidates(tuple(candidates))
            warnings = parse_warnings + validation_report.warnings
            errors = normalization_errors + validation_report.errors
            transactions = self._build_transactions(request.user_id, import_record.id, tuple(candidates))
            new_transactions, duplicate_transactions = self.duplicate_detector.split_new_transactions(
                user_id=request.user_id,
                transactions=transactions,
            )
            self.logger.info(
                "duplicate_detection_completed",
                new_count=len(new_transactions),
                duplicate_count=len(duplicate_transactions),
            )
            self.repository.save_transactions(new_transactions)
            self.logger.info("database_writes_completed", transaction_count=len(new_transactions))

            archive_path = None
            if request.privacy_mode == PrivacyMode.ARCHIVE:
                archive_path, archive_action = self.file_manager.archive_encrypted(temporary)
                privacy_actions.append(archive_action)
            privacy_actions.append(self.file_manager.delete(temporary.path))
            self.logger.info("file_lifecycle_completed", actions=[action.action for action in privacy_actions])

            duration_ms = self._duration_ms(started)
            self.repository.complete_import(
                import_record,
                status=ImportStatus.COMPLETED,
                transaction_count=len(new_transactions),
                validation_error_count=len(errors),
                validation_warning_count=len(warnings),
                processing_duration_ms=duration_ms,
                archive_path=str(archive_path) if archive_path else None,
            )
            return ImportSummary(
                    import_id=import_record.id,
                    status=ImportStatus.COMPLETED,
                    detected_bank=detection.bank_code,
                    imported_transactions=len(new_transactions),
                    failed_rows=self._failed_row_count(errors),
                    duplicate_rows=len(duplicate_transactions),
                validation_warnings=warnings,
                validation_errors=errors,
                privacy_actions=tuple(privacy_actions),
                processing_duration_ms=duration_ms,
                archive_path=str(archive_path) if archive_path else None,
            )
        except ImportEngineError as exc:
            self.logger.error("import_failed", code=exc.code, technical_detail=exc.technical_detail)
            if temporary is not None and temporary.path.exists():
                privacy_actions.append(self.file_manager.delete(temporary.path))
            return ImportSummary(
                import_id=import_record.id if import_record else None,
                status=ImportStatus.FAILED,
                detected_bank=None,
                imported_transactions=0,
                failed_rows=0,
                duplicate_rows=0,
                validation_warnings=(),
                validation_errors=(),
                privacy_actions=tuple(privacy_actions),
                processing_duration_ms=self._duration_ms(started),
                user_message=exc.user_message,
                technical_details={"code": exc.code, "detail": exc.technical_detail},
            )

    def _normalize_rows(self, rows) -> tuple[list[NormalizedCandidate], tuple[ValidationIssue, ...]]:
        candidates: list[NormalizedCandidate] = []
        errors: list[ValidationIssue] = []
        for row in rows:
            candidate, row_errors = self.normalizer.normalize(row)
            if candidate is not None:
                candidates.append(candidate)
            errors.extend(row_errors)
        self.logger.info("validation_completed", valid_count=len(candidates), error_count=len(errors))
        return candidates, tuple(errors)

    def _build_transactions(
        self, user_id, import_id, candidates: tuple[NormalizedCandidate, ...]
    ) -> tuple[NormalizedTransaction, ...]:
        transactions: list[NormalizedTransaction] = []
        now = datetime.now(UTC)
        for candidate in candidates:
            privacy = self.privacy_engine.sanitize_description(candidate.description)
            dedupe_key = self.normalizer.dedupe_key_for(candidate, privacy.sanitized_description)
            merchant = self.merchant_resolver.resolve(privacy.sanitized_description)
            transactions.append(
                NormalizedTransaction(
                    id=uuid4(),
                    user_id=user_id,
                    import_id=import_id,
                    date=candidate.date,
                    description=privacy.sanitized_description,
                    sanitized_description=privacy.sanitized_description,
                    amount=candidate.amount,
                    direction=candidate.direction,
                    balance=candidate.balance,
                    merchant=merchant,
                    category=None,
                    reference_number=candidate.reference_number,
                    notes=candidate.notes,
                    tags=(),
                    dedupe_key=dedupe_key,
                    created_at=now,
                    updated_at=now,
                )
            )
        return tuple(transactions)

    def _handle_file_lifecycle(self, privacy_mode: PrivacyMode, temporary) -> tuple[PrivacyAction, ...]:
        actions: list[PrivacyAction] = []
        if privacy_mode == PrivacyMode.ARCHIVE:
            _, archive_action = self.file_manager.archive_encrypted(temporary)
            actions.append(archive_action)
        actions.append(self.file_manager.delete(temporary.path))
        return tuple(actions)

    @staticmethod
    def _duration_ms(started: float) -> int:
        return int((perf_counter() - started) * 1000)

    @staticmethod
    def _failed_row_count(errors: tuple[ValidationIssue, ...]) -> int:
        row_numbers = {error.row_number for error in errors if error.row_number is not None}
        return len(row_numbers)


def build_default_import_service(repository: ImportRepository, file_manager: TemporaryStatementFileManager) -> ImportService:
    duplicate_detector = DuplicateDetector(repository)
    return ImportService(
        file_manager=file_manager,
        bank_detector=BankDetector(),
        parser_factory=StatementParserFactory(),
        normalizer=TransactionNormalizer(),
        validator=TransactionValidator(),
        privacy_engine=PrivacyEngine(),
        merchant_resolver=MerchantResolver(),
        duplicate_detector=duplicate_detector,
        repository=repository,
    )
