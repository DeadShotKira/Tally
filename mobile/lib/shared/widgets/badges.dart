import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

/// Customized select/action chip with rounded corners.
class AppChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final void Function(bool)? onSelected;
  final VoidCallback? onDelete;
  final IconData? icon;

  const AppChip({
    Key? key,
    required this.label,
    this.isSelected = false,
    this.onSelected,
    this.onDelete,
    this.icon,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasSelection = onSelected != null;

    if (hasSelection) {
      return FilterChip(
        label: Text(label),
        selected: isSelected,
        onSelected: onSelected,
        avatar: icon != null ? Icon(icon, size: 16, color: isSelected ? theme.colorScheme.onPrimary : theme.textTheme.bodyMedium?.color) : null,
        onDeleted: onDelete,
      );
    }

    return RawChip(
      label: Text(label),
      avatar: icon != null ? Icon(icon, size: 16) : null,
      onDeleted: onDelete,
      deleteIcon: const Icon(Icons.close, size: 14),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
    );
  }
}

/// Status Badge showing semantic indicator types (success, info, warning, error, or custom colors).
enum StatusBadgeType { success, warning, error, info, neutral }

class StatusBadge extends StatelessWidget {
  final String label;
  final StatusBadgeType type;
  final IconData? icon;

  const StatusBadge({
    Key? key,
    required this.label,
    this.type = StatusBadgeType.neutral,
    this.icon,
  }) : super(key: key);

  Color _getBadgeColor(BuildContext context) {
    switch (type) {
      case StatusBadgeType.success:
        return AppColors.success;
      case StatusBadgeType.warning:
        return AppColors.warning;
      case StatusBadgeType.error:
        return AppColors.error;
      case StatusBadgeType.info:
        return AppColors.info;
      case StatusBadgeType.neutral:
        return Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF475569)
            : const Color(0xFFE2E8F0);
    }
  }

  Color _getOnBadgeColor(BuildContext context) {
    switch (type) {
      case StatusBadgeType.neutral:
        return Theme.of(context).brightness == Brightness.dark
            ? Colors.white
            : AppColors.textPrimaryLight;
      default:
        return Colors.white;
    }
  }

  @override
  Widget build(BuildContext context) {
    final badgeColor = _getBadgeColor(context);
    final onBadgeColor = _getOnBadgeColor(context);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: badgeColor.withOpacity(0.12),
        borderRadius: BorderRadius.circular(100),
        border: Border.all(
          color: badgeColor.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(
              icon,
              size: 12,
              color: badgeColor,
            ),
            const SizedBox(width: 4),
          ],
          Text(
            label.toUpperCase(),
            style: TextStyle(
              color: type == StatusBadgeType.neutral ? onBadgeColor : badgeColor,
              fontSize: 11,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
