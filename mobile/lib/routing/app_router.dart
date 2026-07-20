import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../features/auth/presentation/controllers/auth_controller.dart';
import '../features/auth/presentation/screens/forgot_password_screen.dart';
import '../features/auth/presentation/screens/login_screen.dart';
import '../features/auth/presentation/screens/register_screen.dart';
import '../features/auth/presentation/screens/splash_screen.dart';
import '../features/home/presentation/screens/dashboard_screen.dart';
import '../features/settings/presentation/screens/settings_placeholder.dart';
import '../features/transactions/presentation/screens/timeline_screen.dart';
import '../features/transactions/presentation/screens/transaction_detail_screen.dart';
import '../features/merchants/presentation/screens/merchant_profile_screen.dart';
import '../shared/widgets/states.dart';
import 'routes.dart';

/// Provider for accessing the application GoRouter instance.
final routerProvider = Provider<GoRouter>((ref) {
  final listenable = RouterTransitionNotifier(ref);

  return GoRouter(
    initialLocation: Routes.splash,
    refreshListenable: listenable,
    redirect: (context, state) {
      final authState = ref.read(authControllerProvider);
      
      final isSplash = state.matchedLocation == Routes.splash;
      final isLogin = state.matchedLocation == Routes.login;
      final isRegister = state.matchedLocation == Routes.register;
      final isForgot = state.matchedLocation == Routes.forgotPassword;
      
      final isAuthRoute = isLogin || isRegister || isForgot;

      // While checking token authenticity initially, stay on Splash
      if (authState.isInitial) {
        return Routes.splash;
      }

      // If user is authenticated, redirect them away from auth/splash routes to home
      if (authState.isAuthenticated) {
        if (isSplash || isAuthRoute) {
          return Routes.home;
        }
        return null;
      }

      // If user is unauthenticated, redirect them to login unless they are on an auth route
      if (authState.isUnauthenticated || authState.isError) {
        if (!isAuthRoute && !isSplash) {
          return Routes.login;
        }
        // If we finished splash checking and are not going anywhere, go to login
        if (isSplash) {
          return Routes.login;
        }
        return null;
      }

      return null;
    },
    routes: [
      GoRoute(
        path: Routes.splash,
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: Routes.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: Routes.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: Routes.forgotPassword,
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: Routes.home,
        builder: (context, state) => const DashboardScreen(),
      ),
      GoRoute(
        path: Routes.settings,
        builder: (context, state) => const SettingsPlaceholderScreen(),
      ),
      GoRoute(
        path: Routes.transactions,
        builder: (context, state) => const TimelineScreen(),
      ),
      GoRoute(
        path: Routes.transactionDetail,
        builder: (context, state) {
          final id = state.pathParameters['id'] ?? '';
          return TransactionDetailScreen(transactionId: id);
        },
      ),
      GoRoute(
        path: Routes.merchantProfile,
        builder: (context, state) {
          final name = Uri.decodeComponent(state.pathParameters['name'] ?? '');
          return MerchantProfileScreen(merchantName: name);
        },
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(
        title: const Text('Page Not Found'),
      ),
      body: ErrorView(
        title: '404 - Page Not Found',
        message: 'The requested route "${state.uri.path}" does not exist.',
        onRetry: () => context.go(Routes.home),
      ),
    ),
  );
});

/// Listenable adapter that reacts to changes in AuthController state and notifies GoRouter.
class RouterTransitionNotifier extends ChangeNotifier {
  final Ref _ref;

  RouterTransitionNotifier(this._ref) {
    _ref.listen<AuthControllerState>(
      authControllerProvider,
      (previous, next) {
        // Trigger router redirect check whenever auth status changes
        if (previous?.status != next.status) {
          notifyListeners();
        }
      },
    );
  }
}
