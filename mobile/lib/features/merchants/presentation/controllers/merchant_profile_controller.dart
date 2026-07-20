import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../shared/repositories/merchant_repository.dart';
import '../../../home/presentation/controllers/dashboard_controller.dart';
import '../../../transactions/presentation/controllers/timeline_controller.dart';

/// Provider for MerchantProfileController.
/// Uses family to resolve by merchant name/alias.
final merchantProfileControllerProvider = StateNotifierProvider.family<
    MerchantProfileController, AsyncValue<MerchantStats>, String>((ref, name) {
  final merchantRepo = ref.watch(merchantRepositoryProvider);
  return MerchantProfileController(
    ref: ref,
    merchantRepo: merchantRepo,
    merchantName: name,
  );
});

/// Controller managing stats aggregation and alias editing for a specific merchant.
class MerchantProfileController extends StateNotifier<AsyncValue<MerchantStats>> {
  final Ref _ref;
  final MerchantRepository _merchantRepo;
  final String _merchantName;

  MerchantProfileController({
    required Ref ref,
    required MerchantRepository merchantRepo,
    required String merchantName,
  })  : _ref = ref,
        _merchantRepo = merchantRepo,
        _merchantName = merchantName,
        super(const AsyncValue.loading()) {
    fetchStats();
  }

  /// Queries aggregated statistics and time series.
  Future<void> fetchStats() async {
    state = const AsyncValue.loading();
    try {
      final stats = await _merchantRepo.getMerchantStats(_merchantName);
      if (stats != null) {
        state = AsyncValue.data(stats);
      } else {
        state = AsyncValue.error(Exception('Merchant data not found.'), StackTrace.current);
      }
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  /// Renames alias and default categories, synchronizing global feeds.
  Future<bool> editMerchant({
    required String alias,
    required String? defaultCategory,
  }) async {
    try {
      await _merchantRepo.updateMerchant(
        name: _merchantName,
        alias: alias,
        defaultCategory: defaultCategory,
      );

      // Re-query stats with the new name to update UI
      final updatedStats = await _merchantRepo.getMerchantStats(alias);
      if (updatedStats != null) {
        state = AsyncValue.data(updatedStats);
      }

      // Synchronize changes back to timeline and dashboard
      _ref.read(timelineControllerProvider.notifier).fetchTransactions(silent: true);
      _ref.read(dashboardControllerProvider.notifier).refresh();
      return true;
    } catch (e) {
      return false;
    }
  }
}
