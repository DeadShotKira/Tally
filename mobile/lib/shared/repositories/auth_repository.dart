import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as sb;
import '../../core/services/secure_storage_service.dart';
import '../models/auth_models.dart';

/// Provider for accessing the Auth Repository.
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final secureStorage = ref.watch(secureStorageProvider);
  return AuthRepository(
    secureStorage: secureStorage,
  );
});

/// Handles Supabase authentication and the local session representation.
class AuthRepository {
  final SecureStorageService _secureStorage;
  final sb.SupabaseClient _supabaseClient;

  AuthRepository({
    required SecureStorageService secureStorage,
    sb.SupabaseClient? supabaseClient,
  })  : _secureStorage = secureStorage,
        _supabaseClient = supabaseClient ?? sb.Supabase.instance.client;

  static String get _authRedirectUrl =>
      kIsWeb ? Uri.base.origin : 'tally://auth/callback';

  /// Logs in a user using Supabase Auth and persists its session tokens.
  Future<AuthSession> signIn({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _supabaseClient.auth.signInWithPassword(
        email: email,
        password: password,
      );

      final session = response.session;
      if (session == null) {
        throw Exception('Failed to establish Supabase session.');
      }

      // Save tokens securely
      await _secureStorage.saveAccessToken(session.accessToken);
      if (session.refreshToken != null) {
        await _secureStorage.saveRefreshToken(session.refreshToken!);
      }

      return _toAuthSession(response.user);
    } catch (_) {
      rethrow;
    }
  }

  /// Registers a new user using Supabase Auth.
  Future<AuthSession?> signUp({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _supabaseClient.auth.signUp(
        email: email,
        password: password,
        emailRedirectTo: _authRedirectUrl,
      );
      final session = response.session;
      if (session == null) return null;
      await _saveSessionTokens(session);
      return _toAuthSession(response.user);
    } catch (_) {
      rethrow;
    }
  }

  /// Sends a password reset email using Supabase.
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      await _supabaseClient.auth.resetPasswordForEmail(
        email,
        redirectTo: _authRedirectUrl,
      );
    } catch (_) {
      rethrow;
    }
  }

  Future<void> _saveSessionTokens(sb.Session session) async {
    await _secureStorage.saveAccessToken(session.accessToken);
    if (session.refreshToken != null) {
      await _secureStorage.saveRefreshToken(session.refreshToken!);
    }
  }

  AuthSession _toAuthSession(sb.User? user) {
    if (user == null || user.email == null) {
      throw Exception('Supabase did not return a user email for this session.');
    }
    return AuthSession(
      user: UserProfile(id: user.id, email: user.email!),
      settings: const UserSettings(
        privacyMode: 'maximum_privacy',
        aiEnabled: false,
        theme: 'system',
      ),
    );
  }

  /// Checks if a valid session exists in Secure Storage/Supabase.
  /// If expired, attempts auto-refresh.
  Future<AuthSession?> checkAuthStatus() async {
    try {
      final currentSession = _supabaseClient.auth.currentSession;
      if (currentSession == null) {
        // No active session in memory, check if we have a refresh token
        final refreshToken = await _secureStorage.getRefreshToken();
        if (refreshToken != null) {
          final refreshResponse = await _supabaseClient.auth.setSession(refreshToken);
          if (refreshResponse.session != null) {
            final session = refreshResponse.session!;
            await _saveSessionTokens(session);
            return _toAuthSession(refreshResponse.user);
          }
        }
        return null;
      }

      // Check if access token is expired or close to expiring
      if (currentSession.isExpired) {
        // Force refresh
        final refreshResponse = await _supabaseClient.auth.refreshSession();
        if (refreshResponse.session == null) {
          return null;
        }
        final session = refreshResponse.session!;
        await _saveSessionTokens(session);
      } else {
        // Save current active token
        await _secureStorage.saveAccessToken(currentSession.accessToken);
      }

      return _toAuthSession(_supabaseClient.auth.currentUser);
    } catch (_) {
      // Return null on failure (e.g. offline or expired tokens) to prompt login
      return null;
    }
  }

  /// Logs out of Supabase and deletes local tokens.
  Future<void> signOut() async {
    try {
      // Sign out from Supabase Auth
      await _supabaseClient.auth.signOut();
    } finally {
      // Always wipe secure tokens locally
      await _secureStorage.clearAll();
    }
  }
}
