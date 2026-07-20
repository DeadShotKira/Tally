import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/services/api_client.dart';
import '../models/transaction_models.dart';
import 'mock_data.dart';

/// Provider for MerchantRepository.
final merchantRepositoryProvider = Provider<MerchantRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return MerchantRepository(apiClient: apiClient);
});

/// Repository query/update managers for merchant profiles.
class MerchantRepository {
  final ApiClient _apiClient;

  MerchantRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Retrieves merchant stats and history, falling back to mock database offline.
  Future<MerchantStats?> getMerchantStats(String name) async {
    try {
      final response = await _apiClient.get('/merchants/$name/stats');
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final data = body['data'] as Map<String, dynamic>;
        return MerchantStats.fromJson(data);
      }
      return null;
    } catch (_) {
      // Offline fallback: calculate stats locally over MockDatabase
      return MockDatabase.getMockMerchantStats(name);
    }
  }

  /// Updates merchant default category or canonical alias.
  Future<void> updateMerchant({
    required String name,
    required String alias,
    required String? defaultCategory,
  }) async {
    final payload = {
      'name': alias,
      'category_id': defaultCategory,
    };
    try {
      await _apiClient.patch('/merchants/$name', body: payload);
    } catch (_) {
      // Offline fallback: edit all corresponding transactions locally to reflect the alias
      final oldLower = name.trim().toLowerCase();
      for (var i = 0; i < MockDatabase.transactions.length; i++) {
        final tx = MockDatabase.transactions[i];
        if (tx.merchant.trim().toLowerCase() == oldLower) {
          MockDatabase.transactions[i] = tx.copyWith(
            merchant: alias,
            category: defaultCategory ?? tx.category,
            updatedAt: DateTime.now(),
          );
        }
      }
    }
  }
}
