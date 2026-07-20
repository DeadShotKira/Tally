import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../shared/widgets/buttons.dart';
import '../../../../shared/widgets/cards.dart';
import '../../../../shared/widgets/states.dart';
import '../../../../shared/widgets/text_fields.dart';
import '../../../../theme/app_colors.dart';
import '../controllers/merchant_profile_controller.dart';

class MerchantProfileScreen extends ConsumerStatefulWidget {
  final String merchantName;

  const MerchantProfileScreen({super.key, required this.merchantName});

  @override
  ConsumerState<MerchantProfileScreen> createState() =>
      _MerchantProfileScreenState();
}

class _MerchantProfileScreenState extends ConsumerState<MerchantProfileScreen> {
  final _aliasCtrl = TextEditingController();
  final _categoryCtrl = TextEditingController();
  bool _isEditing = false;
  bool _isSaving = false;
  bool _didInitialize = false;

  @override
  void dispose() {
    _aliasCtrl.dispose();
    _categoryCtrl.dispose();
    super.dispose();
  }

  void _initFromStats(MerchantStats stats) {
    if (!_didInitialize) {
      _aliasCtrl.text = stats.merchant;
      _categoryCtrl.text = stats.category ?? '';
      _didInitialize = true;
    }
  }

  Future<void> _saveChanges() async {
    setState(() => _isSaving = true);
    final success = await ref
        .read(merchantProfileControllerProvider(widget.merchantName).notifier)
        .editMerchant(
          alias: _aliasCtrl.text.trim().isNotEmpty
              ? _aliasCtrl.text.trim()
              : widget.merchantName,
          defaultCategory: _categoryCtrl.text.trim().isNotEmpty
              ? _categoryCtrl.text.trim()
              : null,
        );
    setState(() {
      _isSaving = false;
      if (success) _isEditing = false;
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(success ? 'Merchant updated.' : 'Could not save changes.'),
        backgroundColor: success ? AppColors.success : AppColors.error,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final state =
        ref.watch(merchantProfileControllerProvider(widget.merchantName));
    final theme = Theme.of(context);
    final currencyFormatter =
        NumberFormat.currency(symbol: '₹', decimalDigits: 0);
    final dateFormat = DateFormat('d MMM yyyy');

    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: () => context.pop()),
        title: Text(
          widget.merchantName,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        actions: [
          if (!_isEditing)
            IconButton(
              icon: const Icon(Icons.edit_outlined),
              tooltip: 'Edit merchant',
              onPressed: () => setState(() => _isEditing = true),
            )
          else
            TextButton(
              onPressed: () => setState(() {
                _isEditing = false;
                _didInitialize = false;
              }),
              child: const Text('Cancel'),
            ),
        ],
      ),
      body: state.when(
        loading: () => const LoadingView(message: 'Loading merchant data…'),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref
              .read(merchantProfileControllerProvider(widget.merchantName)
                  .notifier)
              .fetchStats(),
        ),
        data: (stats) {
          _initFromStats(stats);

          final initials = stats.merchant.isNotEmpty
              ? stats.merchant[0].toUpperCase()
              : 'M';

          return SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 48),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [

                // ── Hero Card ─────────────────────────────────────────────
                AppCard(
                  gradientColors: AppColors.primaryGradient,
                  padding: const EdgeInsets.all(24),
                  child: Row(
                    children: [
                      Container(
                        width: 60,
                        height: 60,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          shape: BoxShape.circle,
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          initials,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w900,
                            fontSize: 26,
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              stats.merchant,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w900,
                                fontSize: 20,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            if (stats.category != null) ...[
                              const SizedBox(height: 4),
                              Text(
                                stats.category!,
                                style: const TextStyle(
                                  color: Colors.white70,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // ── Metrics Row ───────────────────────────────────────────
                Row(
                  children: [
                    Expanded(
                      child: _StatCard(
                        label: 'Total Spent',
                        value: currencyFormatter.format(stats.totalSpent),
                        icon: Icons.payments_outlined,
                        color: AppColors.error,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _StatCard(
                        label: 'Avg. Spend',
                        value: currencyFormatter.format(stats.averageSpend),
                        icon: Icons.trending_flat_outlined,
                        color: AppColors.info,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _StatCard(
                        label: 'Transactions',
                        value: stats.transactionCount.toString(),
                        icon: Icons.receipt_outlined,
                        color: AppColors.primaryLight,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _StatCard(
                        label: 'Highest',
                        value: currencyFormatter.format(stats.highestTransaction),
                        icon: Icons.arrow_upward_rounded,
                        color: AppColors.warning,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                // ── Transaction History ────────────────────────────────────
                AppCard(
                  padding: const EdgeInsets.all(0),
                  child: Column(
                    children: [
                      if (stats.firstTransaction != null)
                        _InfoRow(
                          label: 'First Transaction',
                          value: dateFormat.format(stats.firstTransaction!),
                          icon: Icons.history_outlined,
                        ),
                      if (stats.firstTransaction != null &&
                          stats.lastTransaction != null)
                        const Divider(height: 1, indent: 46),
                      if (stats.lastTransaction != null)
                        _InfoRow(
                          label: 'Last Transaction',
                          value: dateFormat.format(stats.lastTransaction!),
                          icon: Icons.access_time_outlined,
                        ),
                      if (stats.frequencyPerMonth > 0) ...[
                        const Divider(height: 1, indent: 46),
                        _InfoRow(
                          label: 'Frequency',
                          value: '${stats.frequencyPerMonth.toStringAsFixed(1)}x / month',
                          icon: Icons.repeat_outlined,
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // ── Monthly Spending Trend ─────────────────────────────────
                if (stats.monthlySpending.isNotEmpty) ...[
                  SectionHeader(title: 'Monthly Spending'),
                  _MonthlyTrendChart(
                    points: stats.monthlySpending,
                    currencyFormatter: currencyFormatter,
                  ),
                  const SizedBox(height: 20),
                ],

                // ── Edit section ──────────────────────────────────────────
                if (_isEditing) ...[
                  SectionHeader(title: 'Edit Merchant'),
                  const SizedBox(height: 4),
                  AppTextField(
                    controller: _aliasCtrl,
                    labelText: 'Merchant Alias',
                    prefixIcon: const Icon(Icons.storefront_outlined),
                    hintText: 'Rename this merchant',
                  ),
                  const SizedBox(height: 14),
                  AppTextField(
                    controller: _categoryCtrl,
                    labelText: 'Default Category',
                    prefixIcon: const Icon(Icons.category_outlined),
                    hintText: 'e.g. Food & Dining',
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Setting a default category will apply to all future transactions from this merchant.',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: PrimaryButton(
                      text: _isSaving ? 'Saving…' : 'Save Changes',
                      isLoading: _isSaving,
                      onPressed: _isSaving ? null : _saveChanges,
                    ),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}

// ─── Stat Card ───────────────────────────────────────────────────────────────
class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(height: 10),
          Text(
            value,
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
          Text(label, style: theme.textTheme.bodySmall),
        ],
      ),
    );
  }
}

// ─── Info Row ─────────────────────────────────────────────────────────────────
class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _InfoRow({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Icon(icon, size: 18, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Monthly Trend Bar Chart ──────────────────────────────────────────────────
class _MonthlyTrendChart extends StatelessWidget {
  final List<MapEntry<String, double>> points;
  final NumberFormat currencyFormatter;

  const _MonthlyTrendChart({
    required this.points,
    required this.currencyFormatter,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final maxVal =
        points.map((e) => e.value).reduce((a, b) => a > b ? a : b);

    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 100,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: points.map((entry) {
                final ratio = maxVal > 0 ? (entry.value / maxVal) : 0.0;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Container(
                          height: 90 * ratio,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                AppColors.primaryLight.withValues(alpha: 0.9),
                                AppColors.secondaryLight.withValues(alpha: 0.6),
                              ],
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                            ),
                            borderRadius: BorderRadius.circular(5),
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
            children: points.map((entry) {
              final shortLabel = entry.key.length > 7
                  ? entry.key.substring(5)
                  : entry.key;
              return Expanded(
                child: Text(
                  shortLabel,
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
