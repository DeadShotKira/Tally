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
import '../controllers/transaction_detail_controller.dart';

class TransactionDetailScreen extends ConsumerStatefulWidget {
  final String transactionId;

  const TransactionDetailScreen({super.key, required this.transactionId});

  @override
  ConsumerState<TransactionDetailScreen> createState() =>
      _TransactionDetailScreenState();
}

class _TransactionDetailScreenState
    extends ConsumerState<TransactionDetailScreen> {
  final _aliasCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  final _categoryCtrl = TextEditingController();
  final _tagCtrl = TextEditingController();
  List<String> _editedTags = [];
  bool _isEditing = false;
  bool _isSaving = false;
  bool _didInitialize = false;

  @override
  void dispose() {
    _aliasCtrl.dispose();
    _notesCtrl.dispose();
    _categoryCtrl.dispose();
    _tagCtrl.dispose();
    super.dispose();
  }

  void _initFromTransaction(Transaction tx) {
    if (!_didInitialize) {
      _aliasCtrl.text = tx.merchant;
      _notesCtrl.text = tx.notes ?? '';
      _categoryCtrl.text = tx.category ?? '';
      _editedTags = List.from(tx.tags);
      _didInitialize = true;
    }
  }

  Future<void> _saveChanges(Transaction tx) async {
    setState(() => _isSaving = true);
    final success = await ref
        .read(transactionDetailControllerProvider(widget.transactionId).notifier)
        .editMetadata(
          merchantAlias:
              _aliasCtrl.text.trim().isNotEmpty ? _aliasCtrl.text.trim() : null,
          category: _categoryCtrl.text.trim().isNotEmpty
              ? _categoryCtrl.text.trim()
              : null,
          notes:
              _notesCtrl.text.trim().isNotEmpty ? _notesCtrl.text.trim() : null,
          tags: _editedTags,
        );
    setState(() {
      _isSaving = false;
      if (success) _isEditing = false;
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(success ? 'Changes saved.' : 'Could not save changes.'),
        backgroundColor: success ? AppColors.success : AppColors.error,
      ));
    }
  }

  void _addTag() {
    final val = _tagCtrl.text.trim();
    if (val.isNotEmpty && !_editedTags.contains(val)) {
      setState(() {
        _editedTags.add(val);
        _tagCtrl.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final txState =
        ref.watch(transactionDetailControllerProvider(widget.transactionId));
    final theme = Theme.of(context);
    final currencyFormatter =
        NumberFormat.currency(symbol: '₹', decimalDigits: 2);

    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: () => context.pop()),
        title: const Text('Transaction', style: TextStyle(fontWeight: FontWeight.w800)),
        actions: [
          if (!_isEditing)
            IconButton(
              icon: const Icon(Icons.edit_outlined),
              tooltip: 'Edit',
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
      body: txState.when(
        loading: () => const LoadingView(message: 'Loading transaction…'),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref
              .read(transactionDetailControllerProvider(widget.transactionId)
                  .notifier)
              .fetchDetail(),
        ),
        data: (tx) {
          _initFromTransaction(tx);
          final isCredit = tx.direction == TransactionDirection.credit;
          final amountColor = isCredit ? AppColors.success : AppColors.error;
          final amountPrefix = isCredit ? '+' : '-';

          return SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 48),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [

                // ── Amount Hero ─────────────────────────────────────────────
                AppCard(
                  gradientColors: AppColors.primaryGradient,
                  padding: const EdgeInsets.all(24),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Container(
                        width: 52,
                        height: 52,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        alignment: Alignment.center,
                        child: Icon(
                          isCredit
                              ? Icons.arrow_downward_rounded
                              : Icons.arrow_upward_rounded,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              tx.merchant,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w900,
                                fontSize: 18,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '$amountPrefix${currencyFormatter.format(tx.amount)}',
                              style: TextStyle(
                                color: isCredit
                                    ? Colors.greenAccent.shade100
                                    : Colors.redAccent.shade100,
                                fontWeight: FontWeight.w800,
                                fontSize: 22,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // ── Read-only Details ────────────────────────────────────────
                AppCard(
                  padding: const EdgeInsets.all(0),
                  child: Column(
                    children: [
                      _DetailRow(
                        label: 'Date',
                        value: DateFormat('d MMM yyyy, h:mm a').format(tx.postedDate),
                        icon: Icons.calendar_today_outlined,
                      ),
                      _Divider(),
                      _DetailRow(
                        label: 'Type',
                        value: isCredit ? 'Credit' : 'Debit',
                        icon: Icons.swap_horiz_rounded,
                        valueColor: amountColor,
                      ),
                      _Divider(),
                      if (tx.balance != null) ...[
                        _DetailRow(
                          label: 'Balance After',
                          value: currencyFormatter.format(tx.balance),
                          icon: Icons.account_balance_outlined,
                        ),
                        _Divider(),
                      ],
                      _DetailRow(
                        label: 'Description',
                        value: tx.description.isNotEmpty
                            ? tx.description
                            : 'No description',
                        icon: Icons.description_outlined,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // ── Editable Fields ─────────────────────────────────────────
                if (_isEditing) ...[
                  _SectionLabel(label: 'Edit Details'),
                  const SizedBox(height: 12),
                  AppTextField(
                    controller: _aliasCtrl,
                    labelText: 'Merchant Alias',
                    prefixIcon: const Icon(Icons.storefront_outlined),
                    hintText: 'Rename this merchant',
                  ),
                  const SizedBox(height: 14),
                  AppTextField(
                    controller: _categoryCtrl,
                    labelText: 'Category',
                    prefixIcon: const Icon(Icons.category_outlined),
                    hintText: 'e.g. Food & Dining',
                  ),
                  const SizedBox(height: 14),
                  AppTextField(
                    controller: _notesCtrl,
                    labelText: 'Notes',
                    prefixIcon: const Icon(Icons.notes_outlined),
                    hintText: 'Add a personal note…',
                  ),
                  const SizedBox(height: 14),

                  // Tag input
                  Row(
                    children: [
                      Expanded(
                        child: AppTextField(
                          controller: _tagCtrl,
                          labelText: 'Add Tag',
                          prefixIcon: const Icon(Icons.label_outline),
                          hintText: 'e.g. groceries',
                          textInputAction: TextInputAction.done,
                          onFieldSubmitted: (_) => _addTag(),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton.filled(
                        onPressed: _addTag,
                        icon: const Icon(Icons.add),
                      ),
                    ],
                  ),
                  if (_editedTags.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: _editedTags.map((tag) {
                        return InputChip(
                          label: Text(tag),
                          onDeleted: () => setState(() => _editedTags.remove(tag)),
                        );
                      }).toList(),
                    ),
                  ],
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: PrimaryButton(
                      text: _isSaving ? 'Saving…' : 'Save Changes',
                      isLoading: _isSaving,
                      onPressed: _isSaving ? null : () => _saveChanges(tx),
                    ),
                  ),
                ] else ...[
                  // Read-only editable section
                  AppCard(
                    padding: const EdgeInsets.all(0),
                    child: Column(
                      children: [
                        _DetailRow(
                          label: 'Category',
                          value: tx.category ?? 'Uncategorized',
                          icon: Icons.category_outlined,
                        ),
                        _Divider(),
                        _DetailRow(
                          label: 'Notes',
                          value: tx.notes?.isNotEmpty == true
                              ? tx.notes!
                              : 'No notes',
                          icon: Icons.notes_outlined,
                        ),
                        if (tx.tags.isNotEmpty) ...[
                          _Divider(),
                          Padding(
                            padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(Icons.label_outline,
                                    size: 18,
                                    color: theme.colorScheme.onSurfaceVariant),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Wrap(
                                    spacing: 6,
                                    runSpacing: 4,
                                    children: tx.tags.map((tag) => Chip(
                                      label: Text(tag),
                                      padding: EdgeInsets.zero,
                                      materialTapTargetSize:
                                          MaterialTapTargetSize.shrinkWrap,
                                    )).toList(),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Navigate to merchant profile
                  AppCard(
                    padding: const EdgeInsets.all(0),
                    onTap: () => context.push(
                      '/merchants/${Uri.encodeComponent(tx.merchant)}',
                    ),
                    child: _DetailRow(
                      label: 'View Merchant Profile',
                      value: tx.merchant,
                      icon: Icons.storefront_outlined,
                      trailing: const Icon(Icons.chevron_right, size: 20),
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

// ─── Row helper ───────────────────────────────────────────────────────────────
class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color? valueColor;
  final Widget? trailing;

  const _DetailRow({
    required this.label,
    required this.value,
    required this.icon,
    this.valueColor,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
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
                    letterSpacing: 0.4,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: valueColor,
                  ),
                ),
              ],
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

class _Divider extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Divider(
      height: 1,
      indent: 46,
      endIndent: 0,
      color: Theme.of(context).brightness == Brightness.dark
          ? AppColors.borderDark
          : AppColors.borderLight,
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String label;
  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.w800,
            letterSpacing: 0.2,
          ),
    );
  }
}
