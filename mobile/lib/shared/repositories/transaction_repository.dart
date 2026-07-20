import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/services/api_client.dart';
import '../models/transaction_models.dart';
import 'mock_data.dart';

/// Provider for TransactionRepository.
final transactionRepositoryProvider = Provider<TransactionRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return TransactionRepository(apiClient: apiClient);
});

/// Repository handling transaction listings and modifications.
class TransactionRepository {
  final ApiClient _apiClient;

  TransactionRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  /// Fetches a list of transactions, falling back to mock database on network errors.
  Future<List<Transaction>> getTransactions({
    required TransactionFilters filters,
  }) async {
    try {
      final queryParams = filters.toQueryParameters();
      final queryString = Uri(queryParameters: queryParams).query;
      final path = '/transactions${queryString.isNotEmpty ? '?$queryString' : ''}';

      final response = await _apiClient.get(path);
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final data = body['data'] as List;
        return data.map((e) => Transaction.fromJson(e as Map<String, dynamic>)).toList();
      }
      throw Exception('Server returned code ${response.statusCode}');
    } catch (_) {
      // Offline fallback: perform local filtering over MockDatabase
      return _getLocalFilteredTransactions(filters);
    }
  }

  /// Retrieves detailed information for a single transaction.
  Future<Transaction?> getTransactionDetail(String id) async {
    try {
      final response = await _apiClient.get('/transactions/$id');
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final data = body['data'] as Map<String, dynamic>;
        return Transaction.fromJson(data);
      }
      return null;
    } catch (_) {
      // Offline fallback
      try {
        return MockDatabase.transactions.firstWhere((tx) => tx.id == id);
      } catch (_) {
        return null;
      }
    }
  }

  /// Updates editable metadata tags, category, alias, or notes.
  Future<Transaction?> updateMetadata(
    String id, {
    String? merchantAlias,
    String? category,
    String? notes,
    List<String>? tags,
  }) async {
    final payload = <String, dynamic>{};
    if (merchantAlias != null) payload['merchant_alias'] = merchantAlias;
    if (category != null) payload['category_id'] = category;
    if (notes != null) payload['notes'] = notes;
    if (tags != null) payload['tag_ids'] = tags;

    try {
      final response = await _apiClient.patch('/transactions/$id', body: payload);
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final data = body['data'] as Map<String, dynamic>;
        final updatedTx = Transaction.fromJson(data);
        
        // Sync local mock database just in case
        _updateLocalMock(id, updatedTx);
        return updatedTx;
      }
      throw Exception('Failed to update metadata.');
    } catch (_) {
      // Offline fallback: update local mock record
      try {
        final index = MockDatabase.transactions.indexWhere((tx) => tx.id == id);
        if (index != -1) {
          final tx = MockDatabase.transactions[index];
          final updated = tx.copyWith(
            merchant: merchantAlias ?? tx.merchant,
            category: category ?? tx.category,
            notes: notes ?? tx.notes,
            tags: tags ?? tx.tags,
            updatedAt: DateTime.now(),
          );
          MockDatabase.transactions[index] = updated;
          return updated;
        }
      } catch (_) {}
      return null;
    }
  }

  void _updateLocalMock(String id, Transaction updatedTx) {
    final index = MockDatabase.transactions.indexWhere((tx) => tx.id == id);
    if (index != -1) {
      MockDatabase.transactions[index] = updatedTx;
    }
  }

  List<Transaction> _getLocalFilteredTransactions(TransactionFilters filters) {
    var result = List<Transaction>.from(MockDatabase.transactions);

    // Apply date range
    if (filters.fromDate != null) {
      result = result.where((tx) => tx.postedDate.isAfter(filters.fromDate!) || tx.postedDate.isAtSameMomentAs(filters.fromDate!)).toList();
    }
    if (filters.toDate != null) {
      result = result.where((tx) => tx.postedDate.isBefore(filters.toDate!) || tx.postedDate.isAtSameMomentAs(filters.toDate!)).toList();
    }

    // Apply category filter
    if (filters.categories.isNotEmpty) {
      result = result.where((tx) => filters.categories.contains(tx.category ?? 'Uncategorized')).toList();
    }

    // Apply merchant filter
    if (filters.merchants.isNotEmpty) {
      result = result.where((tx) => filters.merchants.contains(tx.merchant)).toList();
    }

    // Apply amount limits
    if (filters.minAmount != null) {
      result = result.where((tx) => tx.amount >= filters.minAmount!).toList();
    }
    if (filters.maxAmount != null) {
      result = result.where((tx) => tx.amount <= filters.maxAmount!).toList();
    }

    // Apply directions
    if (filters.directions.isNotEmpty) {
      result = result.where((tx) => filters.directions.contains(tx.direction)).toList();
    }

    // Apply tags
    if (filters.tags.isNotEmpty) {
      result = result.where((tx) => tx.tags.any((tag) => filters.tags.contains(tag))).toList();
    }

    // Apply search
    if (filters.search != null && filters.search!.trim().isNotEmpty) {
      final query = filters.search!.trim().toLowerCase();
      result = result.where((tx) {
        return tx.merchant.toLowerCase().contains(query) ||
            tx.description.toLowerCase().contains(query) ||
            (tx.category?.toLowerCase().contains(query) ?? false) ||
            (tx.notes?.toLowerCase().contains(query) ?? false) ||
            tx.tags.any((tag) => tag.toLowerCase().contains(query)) ||
            tx.amount.toString().contains(query);
      }).toList();
    }

    // Sort newest first by default
    result.sort((a, b) => b.postedDate.compareTo(a.postedDate));
    return result;
  }
}
