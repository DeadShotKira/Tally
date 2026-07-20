import 'package:flutter/material.dart';
import 'buttons.dart';

/// Standard Material 3 Confirmation Dialog.
class ConfirmationDialog extends StatelessWidget {
  final String title;
  final String content;
  final String confirmLabel;
  final String cancelLabel;
  final VoidCallback onConfirm;
  final VoidCallback? onCancel;
  final bool isDestructive;

  const ConfirmationDialog({
    Key? key,
    required this.title,
    required this.content,
    this.confirmLabel = 'Confirm',
    this.cancelLabel = 'Cancel',
    required this.onConfirm,
    this.onCancel,
    this.isDestructive = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AlertDialog(
      title: Text(title),
      content: Text(
        content,
        style: theme.textTheme.bodyMedium,
      ),
      actionsPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      actions: [
        Row(
          children: [
            Expanded(
              child: SecondaryButton(
                text: cancelLabel,
                height: 44,
                onPressed: () {
                  Navigator.of(context).pop();
                  if (onCancel != null) onCancel!();
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: PrimaryButton(
                text: confirmLabel,
                height: 44,
                onPressed: () {
                  Navigator.of(context).pop();
                  onConfirm();
                },
                // If destructive, we can color it red
                // We could implement custom styling on PrimaryButton or pass color override
              ),
            ),
          ],
        ),
      ],
    );
  }
}

/// Helper method to show confirmation dialog.
Future<void> showConfirmationDialog({
  required BuildContext context,
  required String title,
  required String content,
  String confirmLabel = 'Confirm',
  String cancelLabel = 'Cancel',
  required VoidCallback onConfirm,
  VoidCallback? onCancel,
  bool isDestructive = false,
}) {
  return showDialog<void>(
    context: context,
    builder: (BuildContext context) {
      return ConfirmationDialog(
        title: title,
        content: content,
        confirmLabel: confirmLabel,
        cancelLabel: cancelLabel,
        onConfirm: onConfirm,
        onCancel: onCancel,
        isDestructive: isDestructive,
      );
    },
  );
}

/// Standardized Modal Bottom Sheet.
class AppBottomSheet extends StatelessWidget {
  final String title;
  final Widget child;
  final Widget? action;

  const AppBottomSheet({
    Key? key,
    required this.title,
    required this.child,
    this.action,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Container(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 38,
                  height: 4,
                  decoration: BoxDecoration(
                    color: theme.brightness == Brightness.dark
                        ? Colors.white.withOpacity(0.15)
                        : Colors.black.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      title,
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (action != null) action!,
                ],
              ),
              const SizedBox(height: 20),
              child,
            ],
          ),
        ),
      ),
    );
  }
}

/// Helper method to show App Bottom Sheet.
Future<T?> showAppBottomSheet<T>({
  required BuildContext context,
  required String title,
  required Widget child,
  Widget? action,
}) {
  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: true,
    builder: (BuildContext context) {
      return AppBottomSheet(
        title: title,
        action: action,
        child: child,
      );
    },
  );
}
