import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/auth_models.dart';
import '../../../../shared/repositories/auth_repository.dart';

enum AuthStatus { initial, loading, authenticated, unauthenticated, error }

class AuthControllerState {
  final AuthStatus status;
  final AuthSession? session;
  final String? errorMessage;

  const AuthControllerState({
    required this.status,
    this.session,
    this.errorMessage,
  });

  factory AuthControllerState.initial() =>
      const AuthControllerState(status: AuthStatus.initial);

  factory AuthControllerState.loading() =>
      const AuthControllerState(status: AuthStatus.loading);

  factory AuthControllerState.authenticated(AuthSession session) =>
      AuthControllerState(status: AuthStatus.authenticated, session: session);

  factory AuthControllerState.unauthenticated() =>
      const AuthControllerState(status: AuthStatus.unauthenticated);

  factory AuthControllerState.error(String message) =>
      AuthControllerState(status: AuthStatus.error, errorMessage: message);

  bool get isInitial => status == AuthStatus.initial;
  bool get isLoading => status == AuthStatus.loading;
  bool get isAuthenticated => status == AuthStatus.authenticated;
  bool get isUnauthenticated => status == AuthStatus.unauthenticated;
  bool get isError => status == AuthStatus.error;
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthControllerState>((ref) {
  final authRepository = ref.watch(authRepositoryProvider);
  return AuthController(authRepository: authRepository);
});

class AuthController extends StateNotifier<AuthControllerState> {
  final AuthRepository _authRepository;

  AuthController({required AuthRepository authRepository})
      : _authRepository = authRepository,
        super(AuthControllerState.initial()) {
    checkAuth();
  }

  /// Initial check to see if user is already logged in on launch.
  Future<void> checkAuth() async {
    state = AuthControllerState.initial();
    try {
      final session = await _authRepository.checkAuthStatus();
      if (session != null) {
        state = AuthControllerState.authenticated(session);
      } else {
        state = AuthControllerState.unauthenticated();
      }
    } catch (e) {
      state = AuthControllerState.unauthenticated();
    }
  }

  /// Performs credentials login.
  Future<void> login(String email, String password) async {
    state = AuthControllerState.loading();
    try {
      final session = await _authRepository.signIn(email: email, password: password);
      state = AuthControllerState.authenticated(session);
    } catch (e) {
      state = AuthControllerState.error(_cleanErrorMessage(e));
    }
  }

  /// Performs user registration.
  Future<void> register(String email, String password) async {
    state = AuthControllerState.loading();
    try {
      await _authRepository.signUp(email: email, password: password);
      // Supabase email verification might be active. Prompt to check email or automatically log in.
      state = AuthControllerState.error('Sign up successful! Please check your email for verification.');
    } catch (e) {
      state = AuthControllerState.error(_cleanErrorMessage(e));
    }
  }

  /// Initiates password recovery email.
  Future<void> resetPassword(String email) async {
    state = AuthControllerState.loading();
    try {
      await _authRepository.sendPasswordResetEmail(email);
      state = AuthControllerState.error('Password reset email sent. Please check your inbox.');
    } catch (e) {
      state = AuthControllerState.error(_cleanErrorMessage(e));
    }
  }

  /// Sign out current session and return to login.
  Future<void> logout() async {
    state = AuthControllerState.loading();
    try {
      await _authRepository.signOut();
    } finally {
      state = AuthControllerState.unauthenticated();
    }
  }

  String _cleanErrorMessage(dynamic error) {
    final msg = error.toString();
    if (msg.contains('invalid-login-credentials') || msg.contains('Invalid login credentials')) {
      return 'Invalid email or password.';
    }
    if (msg.contains('Email not confirmed')) {
      return 'Please verify your email address before logging in.';
    }
    if (msg.contains('network_error') || msg.contains('SocketException')) {
      return 'Network connection error. Please check your network and try again.';
    }
    // General fallback cleaning
    return msg.replaceAll('Exception: ', '').replaceAll('AuthException: ', '');
  }
}
