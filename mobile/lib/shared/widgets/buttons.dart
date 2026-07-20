import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';

/// Premium Primary Button with loading states and hover/tap scale effects.
class PrimaryButton extends StatefulWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final IconData? icon;
  final bool isFullWidth;
  final double height;

  const PrimaryButton({
    Key? key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.icon,
    this.isFullWidth = true,
    this.height = 52,
  }) : super(key: key);

  @override
  State<PrimaryButton> createState() => _PrimaryButtonState();
}

class _PrimaryButtonState extends State<PrimaryButton> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 100),
    );
    _scale = Tween<double>(begin: 1.0, end: 0.96).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTapDown(TapDownDetails details) {
    if (widget.onPressed != null && !widget.isLoading) {
      _controller.forward();
    }
  }

  void _onTapUp(TapUpDetails details) {
    if (widget.onPressed != null && !widget.isLoading) {
      _controller.reverse();
    }
  }

  void _onTapCancel() {
    if (widget.onPressed != null && !widget.isLoading) {
      _controller.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isEnabled = widget.onPressed != null && !widget.isLoading;

    Widget buttonChild;
    if (widget.isLoading) {
      buttonChild = SizedBox(
        height: 24,
        width: 24,
        child: CircularProgressIndicator(
          strokeWidth: 2.5,
          valueColor: AlwaysStoppedAnimation<Color>(
            theme.brightness == Brightness.dark ? AppColors.backgroundDark : Colors.white,
          ),
        ),
      );
    } else {
      buttonChild = Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (widget.icon != null) ...[
            Icon(widget.icon, size: 18),
            const SizedBox(width: 8),
          ],
          Text(widget.text),
        ],
      );
    }

    final buttonStyle = ElevatedButton.styleFrom(
      minimumSize: widget.isFullWidth ? Size.fromHeight(widget.height) : Size(120, widget.height),
      backgroundColor: isEnabled ? theme.primaryColor : theme.disabledColor,
      foregroundColor: theme.brightness == Brightness.dark ? AppColors.backgroundDark : Colors.white,
    );

    return GestureDetector(
      onTapDown: _onTapDown,
      onTapUp: _onTapUp,
      onTapCancel: _onTapCancel,
      child: ScaleTransition(
        scale: _scale,
        child: ElevatedButton(
          style: buttonStyle,
          onPressed: isEnabled ? widget.onPressed : null,
          child: buttonChild,
        ),
      ),
    );
  }
}

/// Outlined Secondary Button with clean typography and hover scaling.
class SecondaryButton extends StatefulWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final IconData? icon;
  final bool isFullWidth;
  final double height;

  const SecondaryButton({
    Key? key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.icon,
    this.isFullWidth = true,
    this.height = 52,
  }) : super(key: key);

  @override
  State<SecondaryButton> createState() => _SecondaryButtonState();
}

class _SecondaryButtonState extends State<SecondaryButton> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 100),
    );
    _scale = Tween<double>(begin: 1.0, end: 0.97).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTapDown(TapDownDetails details) {
    if (widget.onPressed != null && !widget.isLoading) {
      _controller.forward();
    }
  }

  void _onTapUp(TapUpDetails details) {
    if (widget.onPressed != null && !widget.isLoading) {
      _controller.reverse();
    }
  }

  void _onTapCancel() {
    if (widget.onPressed != null && !widget.isLoading) {
      _controller.reverse();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isEnabled = widget.onPressed != null && !widget.isLoading;

    Widget buttonChild;
    if (widget.isLoading) {
      buttonChild = SizedBox(
        height: 20,
        width: 20,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          valueColor: AlwaysStoppedAnimation<Color>(theme.primaryColor),
        ),
      );
    } else {
      buttonChild = Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (widget.icon != null) ...[
            Icon(widget.icon, size: 18),
            const SizedBox(width: 8),
          ],
          Text(widget.text),
        ],
      );
    }

    final buttonStyle = OutlinedButton.styleFrom(
      minimumSize: widget.isFullWidth ? Size.fromHeight(widget.height) : Size(120, widget.height),
      side: BorderSide(
        color: isEnabled ? theme.primaryColor : theme.disabledColor.withOpacity(0.5),
        width: 1.5,
      ),
      foregroundColor: isEnabled ? theme.primaryColor : theme.disabledColor,
    );

    return GestureDetector(
      onTapDown: _onTapDown,
      onTapUp: _onTapUp,
      onTapCancel: _onTapCancel,
      child: ScaleTransition(
        scale: _scale,
        child: OutlinedButton(
          style: buttonStyle,
          onPressed: isEnabled ? widget.onPressed : null,
          child: buttonChild,
        ),
      ),
    );
  }
}

/// Custom squircle Icon Button with premium colors.
class AppIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;
  final Color? color;
  final Color? backgroundColor;
  final double size;
  final double padding;
  final String? tooltip;

  const AppIconButton({
    Key? key,
    required this.icon,
    required this.onPressed,
    this.color,
    this.backgroundColor,
    this.size = 24,
    this.padding = 12,
    this.tooltip,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final defaultBg = theme.brightness == Brightness.dark
        ? AppColors.borderDark
        : AppColors.borderLight;
    final defaultFg = theme.brightness == Brightness.dark
        ? Colors.white
        : AppColors.textPrimaryLight;

    Widget button = InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: EdgeInsets.all(padding),
        decoration: BoxDecoration(
          color: backgroundColor ?? defaultBg,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(
          icon,
          size: size,
          color: color ?? defaultFg,
        ),
      ),
    );

    if (tooltip != null) {
      button = Tooltip(
        message: tooltip!,
        child: button,
      );
    }

    return button;
  }
}
