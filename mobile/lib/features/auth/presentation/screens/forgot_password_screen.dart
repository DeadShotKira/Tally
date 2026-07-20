import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../routing/routes.dart';
import '../../../../shared/widgets/buttons.dart';
import '../../../../shared/widgets/cards.dart';
import '../../../../shared/widgets/text_fields.dart';
import '../../../../theme/app_colors.dart';
import '../controllers/auth_controller.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      ref.read(authControllerProvider.notifier).resetPassword(
            _emailController.text.trim(),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final authState = ref.watch(authControllerProvider);
    final size = MediaQuery.of(context).size;
    final isTablet = size.width > 600;

    // Listen to status updates
    ref.listen<AuthControllerState>(authControllerProvider, (previous, next) {
      if (next.isError && next.errorMessage != null) {
        final isSuccessInfo = next.errorMessage!.contains('sent') || 
                            next.errorMessage!.contains('check');
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.errorMessage!),
            backgroundColor: isSuccessInfo ? AppColors.success : AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );

        if (isSuccessInfo) {
          context.go(Routes.login);
        }
      }
    });

    final forgotForm = Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          IconButton(
            alignment: Alignment.centerLeft,
            padding: EdgeInsets.zero,
            icon: const Icon(Icons.arrow_back),
            onPressed: () => context.pop(),
          ),
          const SizedBox(height: 16),
          Text(
            'Reset Password',
            style: theme.textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Enter your email to receive recovery instructions.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 32),
          AppTextField(
            controller: _emailController,
            labelText: 'Email Address',
            hintText: 'name@example.com',
            keyboardType: TextInputType.emailAddress,
            prefixIcon: const Icon(Icons.email_outlined),
            textInputAction: TextInputAction.done,
            onFieldSubmitted: (_) => _submit(),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter your email.';
              }
              final emailRegex = RegExp(r'^[^@]+@[^@]+\.[^@]+$');
              if (!emailRegex.hasMatch(value)) {
                return 'Please enter a valid email address.';
              }
              return null;
            },
          ),
          const SizedBox(height: 32),
          PrimaryButton(
            text: 'Send Reset Link',
            isLoading: authState.isLoading,
            onPressed: _submit,
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                "Remember your password?",
                style: TextStyle(
                  color: theme.textTheme.bodyMedium?.color?.withOpacity(0.8),
                ),
              ),
              TextButton(
                onPressed: () => context.go(Routes.login),
                child: const Text('Sign In'),
              ),
            ],
          ),
        ],
      ),
    );

    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 40.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: isTablet
                ? AppCard(
                    padding: const EdgeInsets.all(40),
                    child: forgotForm,
                  )
                : forgotForm,
          ),
        ),
      ),
    );
  }
}
