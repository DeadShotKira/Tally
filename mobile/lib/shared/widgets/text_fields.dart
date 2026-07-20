import 'package:flutter/material.dart';

/// Central input component for clean form entries.
class AppTextField extends StatelessWidget {
  final TextEditingController? controller;
  final String labelText;
  final String? hintText;
  final bool isObscureText;
  final TextInputType keyboardType;
  final String? Function(String?)? validator;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final TextInputAction textInputAction;
  final void Function(String)? onFieldSubmitted;
  final void Function(String)? onChanged;
  final bool enabled;

  const AppTextField({
    Key? key,
    this.controller,
    required this.labelText,
    this.hintText,
    this.isObscureText = false,
    this.keyboardType = TextInputType.text,
    this.validator,
    this.prefixIcon,
    this.suffixIcon,
    this.textInputAction = TextInputAction.next,
    this.onFieldSubmitted,
    this.onChanged,
    this.enabled = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      obscureText: isObscureText,
      keyboardType: keyboardType,
      validator: validator,
      textInputAction: textInputAction,
      onFieldSubmitted: onFieldSubmitted,
      onChanged: onChanged,
      enabled: enabled,
      style: const TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w500,
      ),
      decoration: InputDecoration(
        labelText: labelText,
        hintText: hintText,
        prefixIcon: prefixIcon,
        suffixIcon: suffixIcon,
      ),
    );
  }
}

/// Password Field with toggleable visibility state.
class PasswordField extends StatefulWidget {
  final TextEditingController? controller;
  final String labelText;
  final String? Function(String?)? validator;
  final TextInputAction textInputAction;
  final void Function(String)? onFieldSubmitted;

  const PasswordField({
    Key? key,
    this.controller,
    this.labelText = 'Password',
    this.validator,
    this.textInputAction = TextInputAction.done,
    this.onFieldSubmitted,
  }) : super(key: key);

  @override
  State<PasswordField> createState() => _PasswordFieldState();
}

class _PasswordFieldState extends State<PasswordField> {
  bool _isObscure = true;

  @override
  Widget build(BuildContext context) {
    return AppTextField(
      controller: widget.controller,
      labelText: widget.labelText,
      isObscureText: _isObscure,
      keyboardType: TextInputType.visiblePassword,
      validator: widget.validator,
      textInputAction: widget.textInputAction,
      onFieldSubmitted: widget.onFieldSubmitted,
      prefixIcon: const Icon(Icons.lock_outline),
      suffixIcon: IconButton(
        icon: Icon(
          _isObscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
          color: Theme.of(context).colorScheme.secondary,
        ),
        onPressed: () {
          setState(() {
            _isObscure = !_isObscure;
          });
        },
      ),
    );
  }
}

/// Search Field with real-time text clear action.
class SearchField extends StatefulWidget {
  final TextEditingController? controller;
  final String hintText;
  final void Function(String)? onChanged;
  final void Function()? onClear;

  const SearchField({
    Key? key,
    this.controller,
    this.hintText = 'Search transactions...',
    this.onChanged,
    this.onClear,
  }) : super(key: key);

  @override
  State<SearchField> createState() => _SearchFieldState();
}

class _SearchFieldState extends State<SearchField> {
  late final TextEditingController _controller;
  bool _showClear = false;

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController();
    _controller.addListener(_textListener);
  }

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    } else {
      _controller.removeListener(_textListener);
    }
    super.dispose();
  }

  void _textListener() {
    final hasText = _controller.text.isNotEmpty;
    if (hasText != _showClear) {
      setState(() {
        _showClear = hasText;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return TextFormField(
      controller: _controller,
      onChanged: widget.onChanged,
      textInputAction: TextInputAction.search,
      style: const TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w500,
      ),
      decoration: InputDecoration(
        hintText: widget.hintText,
        prefixIcon: const Icon(Icons.search),
        suffixIcon: _showClear
            ? IconButton(
                icon: const Icon(Icons.clear),
                onPressed: () {
                  _controller.clear();
                  if (widget.onChanged != null) {
                    widget.onChanged!('');
                  }
                  if (widget.onClear != null) {
                    widget.onClear!();
                  }
                },
              )
            : null,
        fillColor: theme.brightness == Brightness.dark
            ? theme.cardColor
            : Color(0xFFE2E8F0).withOpacity(0.5),
      ),
    );
  }
}
