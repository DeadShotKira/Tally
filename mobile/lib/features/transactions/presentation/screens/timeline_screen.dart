import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../shared/widgets/cards.dart';
import '../../../../shared/widgets/states.dart';
import '../../../../shared/widgets/text_fields.dart';
import '../../../../theme/app_colors.dart';
import '../controllers/timeline_controller.dart';
import '../widgets/filter_drawer.dart';

class TimelineScreen extends ConsumerStatefulWidget {
  const TimelineScreen({super.key});

  @override
  ConsumerState<TimelineScreen> createState() => _TimelineScreenState();
}

class _TimelineScreenState extends ConsumerState<TimelineScreen> {
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(timelineControllerProvider);
    final theme = Theme.of(context);
    final currencyFormatter = NumberFormat.currency(symbol: '₹', decimalDigits: 0);
    final hasActiveFilters = !state.filters.isEmpty;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transactions', style: TextStyle(fontWeight: FontWeight.w800)),
        actions: [
          Stack(
            children: [
              IconButton(
                icon: const Icon(Icons.tune_rounded),
                tooltip: 'Filters',
                onPressed: () => _showFilterDrawer(context),
              ),
              if (hasActiveFilters)
                Positioned(
                  right: 8,
                  top: 8,
                  child: Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: AppColors.primaryLight,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // ─── Search Bar ─────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: SearchField(
              controller: _searchController,
              hintText: 'Search merchant, category, notes…',
              onChanged: (q) => ref.read(timelineControllerProvider.notifier).setSearch(q),
              onClear: () => ref.read(timelineControllerProvider.notifier).setSearch(''),
            ),
          ),

          // ─── Active filter chips ─────────────────────────────────────────
          if (hasActiveFilters)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      'Filters active',
                      style: theme.textTheme.bodySmall?.copyWith(color: AppColors.primaryLight),
                    ),
                  ),
                  TextButton.icon(
                    onPressed: () {
                      _searchController.clear();
                      ref.read(timelineControllerProvider.notifier).resetFilters();
                    },
                    icon: const Icon(Icons.close, size: 14),
                    label: const Text('Clear All'),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      textStyle: const TextStyle(fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),

          // ─── Transaction List ────────────────────────────────────────────
          Expanded(
            child: state.isLoading
                ? const LoadingView(message: 'Loading transactions…')
                : state.errorMessage != null && state.transactions.isEmpty
                    ? ErrorView(
                        message: state.errorMessage!,
                        onRetry: () => ref.read(timelineControllerProvider.notifier).fetchTransactions(),
                      )
                    : state.transactions.isEmpty
                        ? const EmptyView(
                            icon: Icons.receipt_long_outlined,
                            title: 'No Transactions Found',
                            description: 'Try adjusting your search or filters to find transactions.',
                          )
                        : RefreshIndicator(
                            onRefresh: () => ref.read(timelineControllerProvider.notifier).refresh(),
                            child: _GroupedTransactionList(
                              transactions: state.transactions,
                              currencyFormatter: currencyFormatter,
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  void _showFilterDrawer(BuildContext context) {
    final currentFilters = ref.read(timelineControllerProvider).filters;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => FilterDrawer(
        currentFilters: currentFilters,
        onApply: (filters) {
          ref.read(timelineControllerProvider.notifier).setFilters(filters);
        },
      ),
    );
  }
}

// ─── Grouped Transaction List ──────────────────────────────────────────────────
class _GroupedTransactionList extends StatelessWidget {
  final List<Transaction> transactions;
  final NumberFormat currencyFormatter;

  const _GroupedTransactionList({
    required this.transactions,
    required this.currencyFormatter,
  });

  Map<String, List<Transaction>> _groupByDate(List<Transaction> list) {
    final map = <String, List<Transaction>>{};
    for (final tx in list) {
      final key = DateFormat('yyyy-MM-dd').format(tx.postedDate);
      map.putIfAbsent(key, () => []).add(tx);
    }
    return map;
  }

  @override
  Widget build(BuildContext context) {
    final grouped = _groupByDate(transactions);
    final sortedKeys = grouped.keys.toList()..sort((a, b) => b.compareTo(a));
    final theme = Theme.of(context);

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
      itemCount: sortedKeys.length,
      itemBuilder: (context, groupIndex) {
        final dateKey = sortedKeys[groupIndex];
        final dayTxs = grouped[dateKey]!;
        final date = DateTime.parse(dateKey);
        final dateLabel = _formatDateLabel(date);
        final dayIncome = dayTxs
            .where((tx) => tx.direction == TransactionDirection.credit)
            .fold(0.0, (sum, tx) => sum + tx.amount);
        final dayExpense = dayTxs
            .where((tx) => tx.direction == TransactionDirection.debit)
            .fold(0.0, (sum, tx) => sum + tx.amount);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Date header
            Padding(
              padding: const EdgeInsets.only(top: 20, bottom: 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      dateLabel,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ),
                  if (dayIncome > 0)
                    Text(
                      '+${currencyFormatter.format(dayIncome)}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.success,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  if (dayIncome > 0 && dayExpense > 0)
                    const SizedBox(width: 6),
                  if (dayExpense > 0)
                    Text(
                      '-${currencyFormatter.format(dayExpense)}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.error,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                ],
              ),
            ),
            // Transaction tiles for this date
            ...dayTxs.map((tx) => _TimelineTile(tx: tx, currencyFormatter: currencyFormatter)),
          ],
        );
      },
    );
  }

  String _formatDateLabel(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final d = DateTime(date.year, date.month, date.day);

    if (d == today) return 'Today';
    if (d == today.subtract(const Duration(days: 1))) return 'Yesterday';
    if (d.isAfter(today.subtract(const Duration(days: 7)))) {
      return DateFormat('EEEE, d MMM').format(date);
    }
    return DateFormat('d MMMM yyyy').format(date);
  }
}

// ─── Single Timeline Transaction Tile ──────────────────────────────────────────
class _TimelineTile extends ConsumerWidget {
  final Transaction tx;
  final NumberFormat currencyFormatter;

  const _TimelineTile({required this.tx, required this.currencyFormatter});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isCredit = tx.direction == TransactionDirection.credit;
    final amountColor = isCredit ? AppColors.success : AppColors.error;
    final amountPrefix = isCredit ? '+' : '-';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        onTap: () => context.push('/transactions/${tx.id}'),
        child: Row(
          children: [
            // Icon circle
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: amountColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(14),
              ),
              alignment: Alignment.center,
              child: Text(
                tx.merchant.isNotEmpty ? tx.merchant[0].toUpperCase() : '?',
                style: TextStyle(
                  color: amountColor,
                  fontWeight: FontWeight.w800,
                  fontSize: 18,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    tx.merchant,
                    style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    tx.category ?? 'Uncategorized',
                    style: theme.textTheme.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (tx.tags.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Wrap(
                        spacing: 4,
                        children: tx.tags.take(3).map((tag) => Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            tag,
                            style: TextStyle(
                              fontSize: 9,
                              color: AppColors.primaryLight,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        )).toList(),
                      ),
                    ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '$amountPrefix${currencyFormatter.format(tx.amount)}',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: amountColor,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  DateFormat('h:mm a').format(tx.postedDate),
                  style: theme.textTheme.bodySmall,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
