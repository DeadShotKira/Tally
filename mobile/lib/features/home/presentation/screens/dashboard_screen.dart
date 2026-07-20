import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../routing/routes.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../shared/widgets/cards.dart';
import '../../../../shared/widgets/states.dart';
import '../../../../theme/app_colors.dart';
import '../controllers/dashboard_controller.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardState = ref.watch(dashboardControllerProvider);
    final currencyFormatter = NumberFormat.currency(symbol: '₹', decimalDigits: 0);

    return Scaffold(
      body: dashboardState.when(
        loading: () => const LoadingView(message: 'Loading your finances…'),
        error: (error, _) => ErrorView(
          title: 'Could not load dashboard',
          message: error.toString(),
          onRetry: () => ref.read(dashboardControllerProvider.notifier).fetchDashboard(),
        ),
        data: (analytics) {
          return RefreshIndicator(
            onRefresh: () => ref.read(dashboardControllerProvider.notifier).refresh(),
            child: CustomScrollView(
              slivers: [
                // ─── App Bar ──────────────────────────────────────────────
                SliverAppBar(
                  expandedHeight: 0,
                  floating: true,
                  snap: true,
                  title: Row(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(colors: AppColors.primaryGradient),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.account_balance_wallet_outlined,
                            color: Colors.white, size: 18),
                      ),
                      const SizedBox(width: 10),
                      const Text('Tally', style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1)),
                    ],
                  ),
                  actions: [
                    IconButton(
                      icon: const Icon(Icons.search),
                      tooltip: 'Search',
                      onPressed: () => context.push(Routes.transactions),
                    ),
                    IconButton(
                      icon: const Icon(Icons.receipt_long_outlined),
                      tooltip: 'All Transactions',
                      onPressed: () => context.push(Routes.transactions),
                    ),
                  ],
                ),

                SliverPadding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
                  sliver: SliverList(
                    delegate: SliverChildListDelegate([

                      // ─── Balance Hero Card ───────────────────────────────
                      _HeroBalanceCard(
                        analytics: analytics,
                        currencyFormatter: currencyFormatter,
                      ),
                      const SizedBox(height: 20),

                      // ─── Income / Expense / Savings Row ─────────────────
                      _MetricsRow(
                        analytics: analytics,
                        currencyFormatter: currencyFormatter,
                      ),
                      const SizedBox(height: 24),

                      // ─── Spending Trend Chart ────────────────────────────
                      if (analytics.monthlySpendingTrend.isNotEmpty) ...[
                        SectionHeader(title: 'Monthly Spending', actionLabel: 'All', onActionPressed: () => context.push(Routes.transactions)),
                        _SpendingTrendChart(points: analytics.monthlySpendingTrend),
                        const SizedBox(height: 24),
                      ],

                      // ─── Top Categories ──────────────────────────────────
                      if (analytics.topCategories.isNotEmpty) ...[
                        SectionHeader(title: 'Top Categories'),
                        ...analytics.topCategories.take(5).map(
                          (cat) => _CategoryTile(category: cat, currencyFormatter: currencyFormatter),
                        ),
                        const SizedBox(height: 24),
                      ],

                      // ─── Top Merchants ───────────────────────────────────
                      if (analytics.topMerchants.isNotEmpty) ...[
                        SectionHeader(title: 'Top Merchants'),
                        SizedBox(
                          height: 110,
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemCount: analytics.topMerchants.length,
                            separatorBuilder: (_, __) => const SizedBox(width: 12),
                            itemBuilder: (context, index) {
                              final merchant = analytics.topMerchants[index];
                              return _MerchantCard(
                                merchant: merchant,
                                currencyFormatter: currencyFormatter,
                                onTap: () => context.push(
                                  '/merchants/${Uri.encodeComponent(merchant.merchant)}',
                                ),
                              );
                            },
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],

                      // ─── Recent Transactions ─────────────────────────────
                      SectionHeader(
                        title: 'Recent Transactions',
                        actionLabel: 'See All',
                        onActionPressed: () => context.push(Routes.transactions),
                      ),
                      ...analytics.largestExpenses.take(5).map(
                        (tx) => _TransactionListTile(
                          tx: tx,
                          currencyFormatter: currencyFormatter,
                          onTap: () => context.push('/transactions/${tx.id}'),
                        ),
                      ),
                    ]),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

// ─── Hero Balance Card ─────────────────────────────────────────────────────
class _HeroBalanceCard extends StatelessWidget {
  final DashboardAnalytics analytics;
  final NumberFormat currencyFormatter;

  const _HeroBalanceCard({required this.analytics, required this.currencyFormatter});

  @override
  Widget build(BuildContext context) {
    final balance = analytics.summary.totalIncome - analytics.summary.totalExpense;
    final isPositive = balance >= 0;

    return AppCard(
      gradientColors: AppColors.primaryGradient,
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Net Balance',
            style: TextStyle(color: Colors.white70, fontSize: 13, letterSpacing: 0.5),
          ),
          const SizedBox(height: 8),
          Text(
            currencyFormatter.format(balance.abs()),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 36,
              fontWeight: FontWeight.w900,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            isPositive ? '▲ Positive savings' : '▼ Net deficit',
            style: TextStyle(
              color: isPositive ? Colors.greenAccent.shade100 : Colors.redAccent.shade100,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              _HeroStat(label: 'This Month', value: currencyFormatter.format(analytics.summary.currentMonthSpending)),
              const Spacer(),
              _HeroStat(label: 'Transactions', value: analytics.summary.transactionCount.toString()),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroStat extends StatelessWidget {
  final String label;
  final String value;

  const _HeroStat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white54, fontSize: 11)),
        Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
      ],
    );
  }
}

// ─── Metrics Row ─────────────────────────────────────────────────────────────
class _MetricsRow extends StatelessWidget {
  final DashboardAnalytics analytics;
  final NumberFormat currencyFormatter;

  const _MetricsRow({required this.analytics, required this.currencyFormatter});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _MetricCard(
            label: 'Income',
            value: currencyFormatter.format(analytics.summary.totalIncome),
            icon: Icons.arrow_downward_rounded,
            iconColor: AppColors.success,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _MetricCard(
            label: 'Expenses',
            value: currencyFormatter.format(analytics.summary.totalExpense),
            icon: Icons.arrow_upward_rounded,
            iconColor: AppColors.error,
          ),
        ),
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color iconColor;

  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: iconColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: theme.textTheme.bodySmall),
              Text(
                value,
                style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── Spending Trend Chart ─────────────────────────────────────────────────────
class _SpendingTrendChart extends StatelessWidget {
  final List<TrendPoint> points;

  const _SpendingTrendChart({required this.points});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final maxExpense = points.map((p) => p.expense).reduce((a, b) => a > b ? a : b);
    final isDark = theme.brightness == Brightness.dark;

    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 120,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: points.map((point) {
                final ratio = maxExpense > 0 ? (point.expense / maxExpense) : 0.0;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Container(
                          height: 100 * ratio,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                AppColors.primaryLight.withValues(alpha: 0.9),
                                AppColors.secondaryLight.withValues(alpha: 0.6),
                              ],
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                            ),
                            borderRadius: BorderRadius.circular(6),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: points.map((point) {
              final label = point.period.length > 7 ? point.period.substring(5) : point.period;
              return Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 9,
                    color: isDark ? Colors.white38 : Colors.black38,
                    fontWeight: FontWeight.w600,
                  ),
                  textAlign: TextAlign.center,
                  overflow: TextOverflow.ellipsis,
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

// ─── Category Tile ────────────────────────────────────────────────────────────
class _CategoryTile extends StatelessWidget {
  final CategorySpend category;
  final NumberFormat currencyFormatter;

  const _CategoryTile({required this.category, required this.currencyFormatter});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final pct = category.percentage.clamp(0.0, 100.0) / 100;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.category_outlined, size: 18, color: AppColors.primaryLight),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    category.category,
                    style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                  ),
                ),
                Text(
                  currencyFormatter.format(category.totalSpent),
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: AppColors.error,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: pct,
                minHeight: 5,
                backgroundColor: theme.brightness == Brightness.dark
                    ? AppColors.borderDark
                    : AppColors.borderLight,
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.primaryLight),
              ),
            ),
            const SizedBox(height: 4),
            Align(
              alignment: Alignment.centerRight,
              child: Text(
                '${category.percentage.toStringAsFixed(1)}%',
                style: theme.textTheme.bodySmall,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Merchant Card ────────────────────────────────────────────────────────────
class _MerchantCard extends StatelessWidget {
  final MerchantSpend merchant;
  final NumberFormat currencyFormatter;
  final VoidCallback onTap;

  const _MerchantCard({
    required this.merchant,
    required this.currencyFormatter,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final initials = merchant.merchant.isNotEmpty ? merchant.merchant[0].toUpperCase() : 'M';

    return AppCard(
      padding: const EdgeInsets.all(16),
      onTap: onTap,
      child: SizedBox(
        width: 120,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: AppColors.primaryGradient),
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Text(
                initials,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              merchant.merchant,
              style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w700),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
            ),
            Text(
              currencyFormatter.format(merchant.totalSpent),
              style: theme.textTheme.bodySmall?.copyWith(color: AppColors.error),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Transaction List Tile ─────────────────────────────────────────────────
class _TransactionListTile extends StatelessWidget {
  final Transaction tx;
  final NumberFormat currencyFormatter;
  final VoidCallback onTap;

  const _TransactionListTile({
    required this.tx,
    required this.currencyFormatter,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isCredit = tx.direction == TransactionDirection.credit;
    final amountColor = isCredit ? AppColors.success : AppColors.error;
    final amountPrefix = isCredit ? '+' : '-';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        onTap: onTap,
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: amountColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              alignment: Alignment.center,
              child: Icon(
                isCredit ? Icons.arrow_downward_rounded : Icons.arrow_upward_rounded,
                color: amountColor,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    tx.merchant,
                    style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    tx.category ?? 'Uncategorized',
                    style: theme.textTheme.bodySmall,
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
                    fontWeight: FontWeight.w700,
                    color: amountColor,
                  ),
                ),
                Text(
                  DateFormat('d MMM').format(tx.postedDate),
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
