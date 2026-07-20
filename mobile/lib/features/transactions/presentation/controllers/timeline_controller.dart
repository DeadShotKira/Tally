import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../shared/repositories/transaction_repository.dart';

/// State of the transaction timeline.
class TimelineState {
  final bool isLoading;
  final List<Transaction> transactions;
  final TransactionFilters filters;
  final String? errorMessage;

  const TimelineState({
    required this.isLoading,
    required this.transactions,
    required this.filters,
    this.errorMessage,
  });

  factory TimelineState.initial() {
    return const TimelineState(
      isLoading: true,
      transactions: [],
      filters: TransactionFilters(),
    );
  }

  TimelineState copyWith({
    bool? isLoading,
    List<Transaction>? transactions,
    TransactionFilters? filters,
    String? errorMessage,
  }) {
    return TimelineState(
      isLoading: isLoading ?? this.isLoading,
      transactions: transactions ?? this.transactions,
      filters: filters ?? this.filters,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

/// Provider for Timeline State Notifier.
final timelineControllerProvider =
    StateNotifierProvider<TimelineController, TimelineState>((ref) {
  final transactionRepo = ref.watch(transactionRepositoryProvider);
  return TimelineController(transactionRepo: transactionRepo);
});

/// State Controller managing list rendering, filters, and debounced queries.
class TimelineController extends StateNotifier<TimelineState> {
  final TransactionRepository _transactionRepo;
  Timer? _debounceTimer;

  TimelineController({required TransactionRepository transactionRepo})
      : _transactionRepo = transactionRepo,
        super(TimelineState.initial()) {
    fetchTransactions();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    super.dispose();
  }

  /// Fetches transactions based on current filters and search inputs.
  Future<void> fetchTransactions({bool silent = false}) async {
    if (!silent) {
      state = state.copyWith(isLoading: true, errorMessage: null);
    }
    try {
      final list = await _transactionRepo.getTransactions(filters: state.filters);
      state = state.copyWith(
        isLoading: false,
        transactions: list,
        errorMessage: null,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }

  /// Sets filter parameters and reloads list.
  void setFilters(TransactionFilters newFilters) {
    state = state.copyWith(filters: newFilters);
    fetchTransactions();
  }

  /// Clears all active filters.
  void resetFilters() {
    state = state.copyWith(filters: const TransactionFilters());
    fetchTransactions();
  }

  /// Sets search term and executes with debounce to avoid excessive database calls.
  void setSearch(String query) {
    state = state.copyWith(
      filters: state.filters.copyWith(search: query),
    );

    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      fetchTransactions(silent: true);
    });
  }

  /// Pull-to-refresh action trigger.
  Future<void> refresh() async {
    await fetchTransactions(silent: true);
  }
}
