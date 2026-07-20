import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../shared/repositories/analytics_repository.dart';

/// Provider for Dashboard State.
final dashboardControllerProvider =
    StateNotifierProvider<DashboardController, AsyncValue<DashboardAnalytics>>((ref) {
  final analyticsRepo = ref.watch(analyticsRepositoryProvider);
  return DashboardController(analyticsRepo: analyticsRepo);
});

/// Controller handling dashboard calculations and caching updates.
class DashboardController extends StateNotifier<AsyncValue<DashboardAnalytics>> {
  final AnalyticsRepository _analyticsRepo;

  DashboardController({required AnalyticsRepository analyticsRepo})
      : _analyticsRepo = analyticsRepo,
        super(const AsyncValue.loading()) {
    fetchDashboard();
  }

  /// Fetches summary metrics and trends.
  Future<void> fetchDashboard() async {
    state = const AsyncValue.loading();
    try {
      final data = await _analyticsRepo.getDashboardAnalytics();
      state = AsyncValue.data(data);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }

  /// Triggers a silent refresh.
  Future<void> refresh() async {
    try {
      final data = await _analyticsRepo.getDashboardAnalytics();
      state = AsyncValue.data(data);
    } catch (e, stack) {
      state = AsyncValue.error(e, stack);
    }
  }
}
