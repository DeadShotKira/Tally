import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../shared/repositories/transaction_repository.dart';
import '../../../home/presentation/controllers/dashboard_controller.dart';
import 'timeline_controller.dart';

/// Provider for a specific transaction details.
/// Uses family to load on demand.
final transactionDetailControllerProvider = StateNotifierProvider.family<
    TransactionDetailController, AsyncValue<Transaction>, String>((ref, id) {
  final transactionRepo = ref.watch(transactionRepositoryProvider);
  return TransactionDetailController(
    ref: ref,
    transactionRepo: transactionRepo,
    transactionId: id,
  );
});

/// Controller handling modifications for a single transaction.
class TransactionDetailController extends StateNotifier<AsyncValue<Transaction>> {
  final Ref _ref;
  final TransactionRepository _transactionRepo;
  final String _transactionId;

  TransactionDetailController({
    required Ref ref,
    required TransactionRepository transactionRepo,
    required String transactionId,
  })  : _ref = ref,
        _transactionRepo = transactionRepo,
        _transactionId = transactionId,
        super(const AsyncValue.loading()) {
    fetchDetail();
  }

  /// Fetches rich details for the transaction.
  Future<void> fetchDetail() async {
    state = const AsyncValue.loading();
    try {
      final tx = await _transactionRepo.getTransactionDetail(_transactionId);
      if (tx != null) {
        state = AsyncValue.data(tx);
      } else {
        state = AsyncValue.error(Exception('Transaction not found'), StackTrace.current);
      }
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  /// Updates transaction notes, tags, categories, or aliases.
  Future<bool> editMetadata({
    String? merchantAlias,
    String? category,
    String? notes,
    List<String>? tags,
  }) async {
    try {
      final updated = await _transactionRepo.updateMetadata(
        _transactionId,
        merchantAlias: merchantAlias,
        category: category,
        notes: notes,
        tags: tags,
      );

      if (updated != null) {
        state = AsyncValue.data(updated);
        
        // Notify other controllers to synchronize transaction updates
        _ref.read(timelineControllerProvider.notifier).fetchTransactions(silent: true);
        _ref.read(dashboardControllerProvider.notifier).refresh();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}
