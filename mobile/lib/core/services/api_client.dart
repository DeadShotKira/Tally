import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart';
import 'secure_storage_service.dart';

/// Provider for accessing the custom HTTP client wrapper.
final apiClientProvider = Provider<ApiClient>((ref) {
  final secureStorage = ref.watch(secureStorageProvider);
  return ApiClient(secureStorage: secureStorage);
});

/// API Client communicating with the FastAPI backend.
/// Automatically injects Bearer JWT authentication headers.
class ApiClient {
  final SecureStorageService _secureStorage;
  
  // Base URL pointing to FastAPI backend
  final String baseUrl;

  ApiClient({
    required SecureStorageService secureStorage,
    String? baseUrl,
  })  : _secureStorage = secureStorage,
        baseUrl = baseUrl ?? defaultBaseUrl;

  static String get defaultBaseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    if (kIsWeb) {
      return 'http://localhost:8000/api/v1';
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return 'http://localhost:8000/api/v1';
  }

  Future<Map<String, String>> _getHeaders() async {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    final token = await _secureStorage.getAccessToken();
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  /// Sends a POST request.
  Future<http.Response> post(String path, {Object? body}) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = await _getHeaders();
    final jsonBody = body != null ? jsonEncode(body) : null;
    
    return await http.post(
      uri,
      headers: headers,
      body: jsonBody,
    );
  }

  /// Sends a GET request.
  Future<http.Response> get(String path) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = await _getHeaders();
    
    return await http.get(
      uri,
      headers: headers,
    );
  }

  /// Sends a PATCH request.
  Future<http.Response> patch(String path, {Object? body}) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = await _getHeaders();
    final jsonBody = body != null ? jsonEncode(body) : null;
    
    return await http.patch(
      uri,
      headers: headers,
      body: jsonBody,
    );
  }

  /// Sends a DELETE request.
  Future<http.Response> delete(String path) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = await _getHeaders();
    
    return await http.delete(
      uri,
      headers: headers,
    );
  }
}
