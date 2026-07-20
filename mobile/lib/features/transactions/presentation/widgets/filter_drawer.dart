import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../shared/models/transaction_models.dart';
import '../../../../theme/app_colors.dart';

/// Bottom-sheet filter panel for the Timeline screen.
class FilterDrawer extends StatefulWidget {
  final TransactionFilters currentFilters;
  final void Function(TransactionFilters filters) onApply;

  const FilterDrawer({
    super.key,
    required this.currentFilters,
    required this.onApply,
  });

  @override
  State<FilterDrawer> createState() => _FilterDrawerState();
}

class _FilterDrawerState extends State<FilterDrawer> {
  late DateTime? _fromDate;
  late DateTime? _toDate;
  late Set<TransactionDirection> _selectedDirections;
  late Set<String> _selectedCategories;

  final _minAmountCtrl = TextEditingController();
  final _maxAmountCtrl = TextEditingController();

  static const _categoryOptions = [
    'Food & Dining',
    'Transport',
    'Shopping',
    'Healthcare',
    'Entertainment',
    'Bills & Utilities',
    'Groceries',
    'Personal Care',
    'Travel',
    'Finance',
  ];

  @override
  void initState() {
    super.initState();
    final f = widget.currentFilters;
    _fromDate = f.fromDate;
    _toDate = f.toDate;
    _selectedDirections = Set.from(f.directions);
    _selectedCategories = Set.from(f.categories);

    if (f.minAmount != null) _minAmountCtrl.text = f.minAmount!.toStringAsFixed(0);
    if (f.maxAmount != null) _maxAmountCtrl.text = f.maxAmount!.toStringAsFixed(0);
  }

  @override
  void dispose() {
    _minAmountCtrl.dispose();
    _maxAmountCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate(bool isFrom) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: (isFrom ? _fromDate : _toDate) ?? now,
      firstDate: DateTime(2020),
      lastDate: now,
      helpText: isFrom ? 'Select Start Date' : 'Select End Date',
    );
    if (picked != null) {
      setState(() {
        if (isFrom) {
          _fromDate = picked;
          if (_toDate != null && _toDate!.isBefore(picked)) _toDate = null;
        } else {
          _toDate = picked;
        }
      });
    }
  }

  void _applyFilters() {
    final minAmt = double.tryParse(_minAmountCtrl.text);
    final maxAmt = double.tryParse(_maxAmountCtrl.text);
    final filters = TransactionFilters(
      fromDate: _fromDate,
      toDate: _toDate,
      minAmount: minAmt,
      maxAmount: maxAmt,
      directions: _selectedDirections,
      categories: _selectedCategories,
      search: widget.currentFilters.search,
    );
    widget.onApply(filters);
    Navigator.of(context).pop();
  }

  void _resetFilters() {
    setState(() {
      _fromDate = null;
      _toDate = null;
      _selectedDirections = {};
      _selectedCategories = {};
      _minAmountCtrl.clear();
      _maxAmountCtrl.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dateFormat = DateFormat('d MMM yyyy');
    final isDark = theme.brightness == Brightness.dark;

    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      maxChildSize: 0.95,
      minChildSize: 0.4,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            children: [
              // Drag handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(top: 12),
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.borderDark : AppColors.borderLight,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 8, 0),
                child: Row(
                  children: [
                    Text(
                      'Filter Transactions',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                    ),
                    const Spacer(),
                    TextButton(onPressed: _resetFilters, child: const Text('Reset')),
                  ],
                ),
              ),
              const Divider(height: 1),

              // Scrollable options
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 40),
                  children: [

                    // ── Date Range ─────────────────────────────────────────
                    _SectionLabel(label: 'Date Range'),
                    Row(
                      children: [
                        Expanded(
                          child: _DatePickerButton(
                            label: 'From',
                            value: _fromDate != null ? dateFormat.format(_fromDate!) : null,
                            onTap: () => _pickDate(true),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _DatePickerButton(
                            label: 'To',
                            value: _toDate != null ? dateFormat.format(_toDate!) : null,
                            onTap: () => _pickDate(false),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── Amount Range ────────────────────────────────────────
                    _SectionLabel(label: 'Amount Range (₹)'),
                    Row(
                      children: [
                        Expanded(
                          child: _FilterTextField(
                            controller: _minAmountCtrl,
                            hintText: 'Min',
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _FilterTextField(
                            controller: _maxAmountCtrl,
                            hintText: 'Max',
                            keyboardType: TextInputType.number,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── Transaction Type ────────────────────────────────────
                    _SectionLabel(label: 'Transaction Type'),
                    Wrap(
                      spacing: 8,
                      children: [
                        ChoiceChip(
                          label: const Text('Debit'),
                          selected: _selectedDirections.contains(TransactionDirection.debit),
                          onSelected: (sel) {
                            setState(() {
                              if (sel) {
                                _selectedDirections.add(TransactionDirection.debit);
                              } else {
                                _selectedDirections.remove(TransactionDirection.debit);
                              }
                            });
                          },
                        ),
                        ChoiceChip(
                          label: const Text('Credit'),
                          selected: _selectedDirections.contains(TransactionDirection.credit),
                          onSelected: (sel) {
                            setState(() {
                              if (sel) {
                                _selectedDirections.add(TransactionDirection.credit);
                              } else {
                                _selectedDirections.remove(TransactionDirection.credit);
                              }
                            });
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── Category ─────────────────────────────────────────────
                    _SectionLabel(label: 'Category'),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: _categoryOptions.map((cat) {
                        final isSelected = _selectedCategories.contains(cat);
                        return FilterChip(
                          label: Text(cat),
                          selected: isSelected,
                          onSelected: (_) {
                            setState(() {
                              if (isSelected) {
                                _selectedCategories.remove(cat);
                              } else {
                                _selectedCategories.add(cat);
                              }
                            });
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),

              // Footer
              Padding(
                padding: EdgeInsets.fromLTRB(
                  20, 8, 20, MediaQuery.of(context).padding.bottom + 16,
                ),
                child: SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: FilledButton(
                    onPressed: _applyFilters,
                    child: const Text(
                      'Apply Filters',
                      style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String label;
  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
            ),
      ),
    );
  }
}

class _DatePickerButton extends StatelessWidget {
  final String label;
  final String? value;
  final VoidCallback onTap;

  const _DatePickerButton({required this.label, this.value, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final hasValue = value != null;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        height: 50,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        decoration: BoxDecoration(
          border: Border.all(
            color: hasValue
                ? AppColors.primaryLight
                : (isDark ? AppColors.borderDark : AppColors.borderLight),
          ),
          borderRadius: BorderRadius.circular(12),
          color: hasValue ? AppColors.primaryLight.withValues(alpha: 0.08) : Colors.transparent,
        ),
        child: Row(
          children: [
            Icon(
              Icons.calendar_today_outlined,
              size: 16,
              color: hasValue ? AppColors.primaryLight : theme.hintColor,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                hasValue ? value! : label,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: hasValue ? AppColors.primaryLight : theme.hintColor,
                  fontWeight: hasValue ? FontWeight.w600 : FontWeight.w400,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FilterTextField extends StatelessWidget {
  final TextEditingController controller;
  final String hintText;
  final TextInputType keyboardType;

  const _FilterTextField({
    required this.controller,
    required this.hintText,
    this.keyboardType = TextInputType.text,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return SizedBox(
      height: 50,
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        style: theme.textTheme.bodyMedium,
        decoration: InputDecoration(
          hintText: hintText,
          contentPadding: const EdgeInsets.symmetric(horizontal: 14),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(
              color: isDark ? AppColors.borderDark : AppColors.borderLight,
            ),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(
              color: isDark ? AppColors.borderDark : AppColors.borderLight,
            ),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppColors.primaryLight, width: 2),
          ),
        ),
      ),
    );
  }
}
