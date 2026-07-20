import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart' as pk_shimmer;
import '../../theme/app_colors.dart';

/// AppCard container supporting subtle shadows, gradients, and border options.
class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final List<Color>? gradientColors;
  final bool hasBorder;
  final double borderRadius;
  final VoidCallback? onTap;

  const AppCard({
    Key? key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.gradientColors,
    this.hasBorder = true,
    this.borderRadius = 16,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final borderSide = hasBorder
        ? BorderSide(
            color: theme.brightness == Brightness.dark
                ? AppColors.borderDark
                : AppColors.borderLight,
            width: 1,
          )
        : BorderSide.none;

    final boxDecoration = BoxDecoration(
      color: gradientColors == null ? theme.cardColor : null,
      gradient: gradientColors != null
          ? LinearGradient(
              colors: gradientColors!,
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            )
          : null,
      borderRadius: BorderRadius.circular(borderRadius),
      border: gradientColors == null ? Border.fromBorderSide(borderSide) : null,
      boxShadow: theme.brightness == Brightness.light
          ? [
              BoxShadow(
                color: Colors.black.withOpacity(0.02),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ]
          : null,
    );

    if (onTap != null) {
      return Container(
        decoration: boxDecoration,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(borderRadius),
            child: Padding(
              padding: padding,
              child: child,
            ),
          ),
        ),
      );
    }

    return Container(
      decoration: boxDecoration,
      padding: padding,
      child: child,
    );
  }
}

/// Standardized Section Header with action triggers.
class SectionHeader extends StatelessWidget {
  final String title;
  final String? actionLabel;
  final VoidCallback? onActionPressed;
  final double bottomSpacing;

  const SectionHeader({
    Key? key,
    required this.title,
    this.actionLabel,
    this.onActionPressed,
    this.bottomSpacing = 16,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: EdgeInsets.only(bottom: bottomSpacing),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              letterSpacing: 0.2,
            ),
          ),
          if (actionLabel != null && onActionPressed != null)
            TextButton(
              onPressed: onActionPressed,
              style: TextButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: Text(actionLabel!),
            ),
        ],
      ),
    );
  }
}

/// Avatar with initials or image, applying premium brand gradients.
class Avatar extends StatelessWidget {
  final String? imageUrl;
  final String name;
  final double radius;

  const Avatar({
    Key? key,
    this.imageUrl,
    required this.name,
    this.radius = 24,
  }) : super(key: key);

  String get _initials {
    if (name.isEmpty) return 'U';
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.length > 1) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0][0].toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final hasImage = imageUrl != null && imageUrl!.isNotEmpty;
    final initialsText = _initials;

    return CircleAvatar(
      radius: radius,
      backgroundColor: Colors.transparent,
      child: Container(
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(
            colors: AppColors.primaryGradient,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        alignment: Alignment.center,
        child: hasImage
            ? ClipRRect(
                borderRadius: BorderRadius.circular(radius),
                child: Image.network(
                  imageUrl!,
                  fit: BoxFit.cover,
                  width: radius * 2,
                  height: radius * 2,
                  errorBuilder: (context, error, stackTrace) => Text(
                    initialsText,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: radius * 0.8,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              )
            : Text(
                initialsText,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: radius * 0.8,
                  fontWeight: FontWeight.bold,
                ),
              ),
      ),
    );
  }
}

/// Shimmer skeleton animation wrapper.
class Shimmer extends StatelessWidget {
  final double width;
  final double height;
  final double borderRadius;
  final BoxShape shape;

  const Shimmer({
    Key? key,
    required this.width,
    required this.height,
    this.borderRadius = 8,
    this.shape = BoxShape.rectangle,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return pk_shimmer.Shimmer.fromColors(
      baseColor: isDark ? AppColors.shimmerBaseDark : AppColors.shimmerBaseLight,
      highlightColor: isDark ? AppColors.shimmerHighlightDark : AppColors.shimmerHighlightLight,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: shape,
          borderRadius: shape == BoxShape.rectangle
              ? BorderRadius.circular(borderRadius)
              : null,
        ),
      ),
    );
  }
}
