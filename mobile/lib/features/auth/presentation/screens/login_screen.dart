import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../routing/routes.dart';
import '../../../../shared/widgets/buttons.dart';
import '../../../../shared/widgets/cards.dart';
import '../../../../shared/widgets/text_fields.dart';
import '../../../../theme/app_colors.dart';
import '../controllers/auth_controller.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      ref.read(authControllerProvider.notifier).login(
            _emailController.text.trim(),
            _passwordController.text,
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final authState = ref.watch(authControllerProvider);
    final size = MediaQuery.of(context).size;
    final isTablet = size.width > 600;

    // Listen to errors
    ref.listen<AuthControllerState>(authControllerProvider, (previous, next) {
      if (next.isError && next.errorMessage != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.errorMessage!),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    });

    final loginForm = Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Sign In',
            style: theme.textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Manage your finances securely.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 32),
          AppTextField(
            controller: _emailController,
            labelText: 'Email Address',
            hintText: 'name@example.com',
            keyboardType: TextInputType.emailAddress,
            prefixIcon: const Icon(Icons.email_outlined),
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
          const SizedBox(height: 20),
          PasswordField(
            controller: _passwordController,
            labelText: 'Password',
            onFieldSubmitted: (_) => _submit(),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter your password.';
              }
              if (value.length < 6) {
                return 'Password must be at least 6 characters.';
              }
              return null;
            },
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () => context.push(Routes.forgotPassword),
              child: const Text('Forgot Password?'),
            ),
          ),
          const SizedBox(height: 16),
          PrimaryButton(
            text: 'Sign In',
            isLoading: authState.isLoading,
            onPressed: _submit,
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                "Don't have an account?",
                style: TextStyle(
                  color: theme.textTheme.bodyMedium?.color?.withOpacity(0.8),
                ),
              ),
              TextButton(
                onPressed: () => context.push(Routes.register),
                child: const Text('Sign Up'),
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
                    child: loginForm,
                  )
                : loginForm,
          ),
        ),
      ),
    );
  }
}
