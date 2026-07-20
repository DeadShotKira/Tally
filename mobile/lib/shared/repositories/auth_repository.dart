import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as sb;
import 'package:uuid/uuid.dart';
import '../../core/services/api_client.dart';
import '../../core/services/secure_storage_service.dart';
import '../models/auth_models.dart';

/// Provider for accessing the Auth Repository.
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final secureStorage = ref.watch(secureStorageProvider);
  return AuthRepository(
    apiClient: apiClient,
    secureStorage: secureStorage,
  );
});

/// Bridge between Supabase Auth and Tally FastAPI backend profiles.
class AuthRepository {
  final ApiClient _apiClient;
  final SecureStorageService _secureStorage;
  final sb.SupabaseClient _supabaseClient;

  AuthRepository({
    required ApiClient apiClient,
    required SecureStorageService secureStorage,
    sb.SupabaseClient? supabaseClient,
  })  : _apiClient = apiClient,
        _secureStorage = secureStorage,
        _supabaseClient = supabaseClient ?? sb.Supabase.instance.client;

  /// Gets or generates a stable device ID for auth tracking.
  Future<String> _getOrCreateDeviceId() async {
    var deviceId = await _secureStorage.getDeviceId();
    if (deviceId == null) {
      deviceId = const Uuid().v4();
      await _secureStorage.saveDeviceId(deviceId);
    }
    return deviceId;
  }

  /// Logs in a user using Supabase Auth, updates secure storage, and bootstraps profile.
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

      // Bootstrap backend session
      return await _bootstrapBackendSession();
    } catch (e) {
      rethrow;
    }
  }

  /// Registers a new user using Supabase Auth.
  Future<void> signUp({
    required String email,
    required String password,
  }) async {
    try {
      await _supabaseClient.auth.signUp(
        email: email,
        password: password,
        emailRedirectTo: kIsWeb ? Uri.base.origin : null,
      );
    } catch (e) {
      rethrow;
    }
  }

  /// Sends a password reset email using Supabase.
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      await _supabaseClient.auth.resetPasswordForEmail(
        email,
        redirectTo: kIsWeb ? Uri.base.origin : null,
      );
    } catch (e) {
      rethrow;
    }
  }

  /// Bootstraps/Syncs profile with the FastAPI backend.
  Future<AuthSession> _bootstrapBackendSession() async {
    final deviceId = await _getOrCreateDeviceId();
    
    final response = await _apiClient.post(
      '/auth/session',
      body: {'device_id': deviceId},
    );

    if (response.statusCode == 200) {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      final data = body['data'] as Map<String, dynamic>;
      return AuthSession.fromJson(data);
    } else {
      throw Exception(
        'Failed to sync session with Tally backend (HTTP ${response.statusCode}).',
      );
    }
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
            await _secureStorage.saveAccessToken(session.accessToken);
            if (session.refreshToken != null) {
              await _secureStorage.saveRefreshToken(session.refreshToken!);
            }
            return await _bootstrapBackendSession();
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
        await _secureStorage.saveAccessToken(session.accessToken);
        if (session.refreshToken != null) {
          await _secureStorage.saveRefreshToken(session.refreshToken!);
        }
      } else {
        // Save current active token
        await _secureStorage.saveAccessToken(currentSession.accessToken);
      }

      return await _bootstrapBackendSession();
    } catch (_) {
      // Return null on failure (e.g. offline or expired tokens) to prompt login
      return null;
    }
  }

  /// Logs out of Supabase and deletes local tokens.
  Future<void> signOut() async {
    try {
      final deviceId = await _secureStorage.getDeviceId() ?? '';
      
      // Notify backend to clean up device sessions
      try {
        await _apiClient.post(
          '/auth/logout',
          body: {'device_id': deviceId},
        );
      } catch (_) {
        // Network failures on backend logout should not block local signout
      }

      // Sign out from Supabase Auth
      await _supabaseClient.auth.signOut();
    } finally {
      // Always wipe secure tokens locally
      await _secureStorage.clearAll();
    }
  }
}
