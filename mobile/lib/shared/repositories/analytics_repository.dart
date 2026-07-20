import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/services/api_client.dart';
import '../models/transaction_models.dart';
import 'mock_data.dart';

/// Provider for AnalyticsRepository.
final analyticsRepositoryProvider = Provider<AnalyticsRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AnalyticsRepository(apiClient: apiClient);
});

/// Repository querying analytical summaries for dashboard visualizations.
class AnalyticsRepository {
  final ApiClient _apiClient;

  AnalyticsRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Fetches aggregated metrics and trend series, falling back to mock calculations offline.
  Future<DashboardAnalytics> getDashboardAnalytics() async {
    try {
      final response = await _apiClient.get('/analytics/summary');
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final data = body['data'] as Map<String, dynamic>;
        return DashboardAnalytics.fromJson(data);
      }
      throw Exception('Server returned ${response.statusCode}');
    } catch (_) {
      // Offline fallback: calculate over local MockDatabase
      return MockDatabase.getMockDashboardAnalytics();
    }
  }
}
