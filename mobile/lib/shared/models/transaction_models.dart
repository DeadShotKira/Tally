import 'package:intl/intl.dart';

/// Transaction Direction type.
enum TransactionDirection {
  credit,
  debit;

  static TransactionDirection fromString(String val) {
    if (val.toLowerCase() == 'credit') return TransactionDirection.credit;
    return TransactionDirection.debit;
  }

  String get valueName => name;
}

/// Rich domain model representing a financial transaction.
class Transaction {
  final String id;
  final DateTime postedDate;
  final String description;
  final double amount;
  final TransactionDirection direction;
  final String merchant;
  final String? category;
  final String? notes;
  final List<String> tags;
  final String? referenceNumber;
  final double? balance;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Transaction({
    required this.id,
    required this.postedDate,
    required this.description,
    required this.amount,
    required this.direction,
    required this.merchant,
    this.category,
    this.notes,
    required this.tags,
    this.referenceNumber,
    this.balance,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic val) {
      if (val == null) return 0.0;
      if (val is num) return val.toDouble();
      return double.tryParse(val.toString()) ?? 0.0;
    }

    DateTime parseDate(dynamic val) {
      if (val == null) return DateTime.now();
      if (val is String) {
        return DateTime.tryParse(val) ?? DateTime.now();
      }
      return DateTime.now();
    }

    List<String> parseTags(dynamic val) {
      if (val == null) return [];
      if (val is List) {
        return val.map((e) => e.toString()).toList();
      }
      return [];
    }

    return Transaction(
      id: json['id'] as String? ?? '',
      postedDate: parseDate(json['posted_date']),
      description: json['description'] as String? ?? '',
      amount: parseDouble(json['amount']),
      direction: TransactionDirection.fromString(json['direction'] as String? ?? 'debit'),
      merchant: json['merchant'] as String? ?? 'Unknown',
      category: json['category'] as String?,
      notes: json['notes'] as String?,
      tags: parseTags(json['tags']),
      referenceNumber: json['reference_number'] as String?,
      balance: json['balance'] != null ? parseDouble(json['balance']) : null,
      createdAt: parseDate(json['created_at']),
      updatedAt: parseDate(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'posted_date': DateFormat('yyyy-MM-dd').format(postedDate),
      'description': description,
      'amount': amount,
      'direction': direction.valueName,
      'merchant': merchant,
      'category': category,
      'notes': notes,
      'tags': tags,
      'reference_number': referenceNumber,
      'balance': balance,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  Transaction copyWith({
    String? id,
    DateTime? postedDate,
    String? description,
    double? amount,
    TransactionDirection? direction,
    String? merchant,
    String? category,
    String? notes,
    List<String>? tags,
    String? referenceNumber,
    double? balance,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Transaction(
      id: id ?? this.id,
      postedDate: postedDate ?? this.postedDate,
      description: description ?? this.description,
      amount: amount ?? this.amount,
      direction: direction ?? this.direction,
      merchant: merchant ?? this.merchant,
      category: category ?? this.category,
      notes: notes ?? this.notes,
      tags: tags ?? this.tags,
      referenceNumber: referenceNumber ?? this.referenceNumber,
      balance: balance ?? this.balance,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

/// Dashboard financial metrics summary.
class DashboardSummary {
  final double totalIncome;
  final double totalExpense;
  final double netSavings;
  final int transactionCount;
  final int activeMerchants;
  final double currentMonthSpending;

  const DashboardSummary({
    required this.totalIncome,
    required this.totalExpense,
    required this.netSavings,
    required this.transactionCount,
    required this.activeMerchants,
    required this.currentMonthSpending,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic val) {
      if (val == null) return 0.0;
      if (val is num) return val.toDouble();
      return double.tryParse(val.toString()) ?? 0.0;
    }

    return DashboardSummary(
      totalIncome: parseDouble(json['total_income']),
      totalExpense: parseDouble(json['total_expense']),
      netSavings: parseDouble(json['net_savings']),
      transactionCount: json['transaction_count'] as int? ?? 0,
      activeMerchants: json['active_merchants'] as int? ?? 0,
      currentMonthSpending: parseDouble(json['current_month_spending']),
    );
  }
}

/// Category distribution spend item.
class CategorySpend {
  final String category;
  final double totalSpent;
  final int transactionCount;
  final double percentage;

  const CategorySpend({
    required this.category,
    required this.totalSpent,
    required this.transactionCount,
    required this.percentage,
  });

  factory CategorySpend.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic val) {
      if (val == null) return 0.0;
      if (val is num) return val.toDouble();
      return double.tryParse(val.toString()) ?? 0.0;
    }

    return CategorySpend(
      category: json['category'] as String? ?? 'Uncategorized',
      totalSpent: parseDouble(json['total_spent']),
      transactionCount: json['transaction_count'] as int? ?? 0,
      percentage: parseDouble(json['percentage_of_total_spending']),
    );
  }
}

/// Merchant spend summary.
class MerchantSpend {
  final String merchant;
  final String? category;
  final double totalSpent;
  final int transactionCount;

  const MerchantSpend({
    required this.merchant,
    this.category,
    required this.totalSpent,
    required this.transactionCount,
  });

  factory MerchantSpend.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic val) {
      if (val == null) return 0.0;
      if (val is num) return val.toDouble();
      return double.tryParse(val.toString()) ?? 0.0;
    }

    return MerchantSpend(
      merchant: json['merchant'] as String? ?? 'Unknown',
      category: json['category'] as String?,
      totalSpent: parseDouble(json['total_spent'] ?? json['average_spend']),
      transactionCount: json['transaction_count'] as int? ?? 0,
    );
  }
}

/// Time-series point for spending trends.
class TrendPoint {
  final String period;
  final double income;
  final double expense;
  final int transactionCount;

  const TrendPoint({
    required this.period,
    required this.income,
    required this.expense,
    required this.transactionCount,
  });

  factory TrendPoint.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic val) {
      if (val == null) return 0.0;
      if (val is num) return val.toDouble();
      return double.tryParse(val.toString()) ?? 0.0;
    }

    return TrendPoint(
      period: json['period'] as String? ?? '',
      income: parseDouble(json['income']),
      expense: parseDouble(json['expense']),
      transactionCount: json['transaction_count'] as int? ?? 0,
    );
  }
}

/// Aggregated dashboard data model.
class DashboardAnalytics {
  final DashboardSummary summary;
  final List<TrendPoint> monthlySpendingTrend;
  final List<TrendPoint> monthlyIncomeTrend;
  final List<CategorySpend> categoryDistribution;
  final List<MerchantSpend> merchantSpending;
  final List<CategorySpend> topCategories;
  final List<MerchantSpend> topMerchants;
  final List<Transaction> largestExpenses;
  final List<Transaction> largestIncome;

  const DashboardAnalytics({
    required this.summary,
    required this.monthlySpendingTrend,
    required this.monthlyIncomeTrend,
    required this.categoryDistribution,
    required this.merchantSpending,
    required this.topCategories,
    required this.topMerchants,
    required this.largestExpenses,
    required this.largestIncome,
  });

  factory DashboardAnalytics.fromJson(Map<String, dynamic> json) {
    List<T> parseList<T>(dynamic val, T Function(Map<String, dynamic>) fromJson) {
      if (val == null || val is! List) return [];
      return val
          .map((e) => fromJson(e as Map<String, dynamic>))
          .toList();
    }

    return DashboardAnalytics(
      summary: DashboardSummary.fromJson(json['summary'] as Map<String, dynamic>? ?? {}),
      monthlySpendingTrend: parseList(json['monthly_spending_trend'], TrendPoint.fromJson),
      monthlyIncomeTrend: parseList(json['monthly_income_trend'], TrendPoint.fromJson),
      categoryDistribution: parseList(json['category_distribution'], CategorySpend.fromJson),
      merchantSpending: parseList(json['merchant_spending'], MerchantSpend.fromJson),
      topCategories: parseList(json['top_categories'], CategorySpend.fromJson),
      topMerchants: parseList(json['top_merchants'], MerchantSpend.fromJson),
      largestExpenses: parseList(json['largest_expenses'], Transaction.fromJson),
      largestIncome: parseList(json['largest_income'], Transaction.fromJson),
    );
  }
}

/// Merchant specific statistical overview.
class MerchantStats {
  final String merchant;
  final String? category;
  final DateTime? firstTransaction;
  final DateTime? lastTransaction;
  final int transactionCount;
  final double totalSpent;
  final double averageSpend;
  final double highestTransaction;
  final double lowestTransaction;
  final double frequencyPerMonth;
  final List<MapEntry<String, double>> monthlySpending;

  const MerchantStats({
    required this.merchant,
    this.category,
    this.firstTransaction,
    this.lastTransaction,
    required this.transactionCount,
    required this.totalSpent,
    required this.averageSpend,
    required this.highestTransaction,
    required this.lowestTransaction,
    required this.frequencyPerMonth,
    required this.monthlySpending,
  });

  factory MerchantStats.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic val) {
      if (val == null) return 0.0;
      if (val is num) return val.toDouble();
      return double.tryParse(val.toString()) ?? 0.0;
    }

    DateTime? parseDate(dynamic val) {
      if (val == null) return null;
      return DateTime.tryParse(val.toString());
    }

    List<MapEntry<String, double>> parseMonthly(dynamic val) {
      if (val == null || val is! List) return [];
      final list = <MapEntry<String, double>>[];
      for (final item in val) {
        if (item is List && item.length == 2) {
          list.add(MapEntry(item[0].toString(), parseDouble(item[1])));
        }
      }
      return list;
    }

    return MerchantStats(
      merchant: json['merchant'] as String? ?? '',
      category: json['category'] as String?,
      firstTransaction: parseDate(json['first_transaction']),
      lastTransaction: parseDate(json['last_transaction']),
      transactionCount: json['transaction_count'] as int? ?? 0,
      totalSpent: parseDouble(json['total_spent']),
      averageSpend: parseDouble(json['average_spend']),
      highestTransaction: parseDouble(json['highest_transaction']),
      lowestTransaction: parseDouble(json['lowest_transaction']),
      frequencyPerMonth: parseDouble(json['frequency_per_month']),
      monthlySpending: parseMonthly(json['monthly_spending']),
    );
  }
}

/// Local state mapping of timeline filter inputs.
class TransactionFilters {
  final DateTime? fromDate;
  final DateTime? toDate;
  final Set<String> categories;
  final Set<String> merchants;
  final double? minAmount;
  final double? maxAmount;
  final Set<TransactionDirection> directions;
  final Set<String> tags;
  final String? search;

  const TransactionFilters({
    this.fromDate,
    this.toDate,
    this.categories = const {},
    this.merchants = const {},
    this.minAmount,
    this.maxAmount,
    this.directions = const {},
    this.tags = const {},
    this.search,
  });

  bool get isEmpty =>
      fromDate == null &&
      toDate == null &&
      categories.isEmpty &&
      merchants.isEmpty &&
      minAmount == null &&
      maxAmount == null &&
      directions.isEmpty &&
      tags.isEmpty &&
      (search == null || search!.trim().isEmpty);

  TransactionFilters copyWith({
    DateTime? fromDate,
    DateTime? toDate,
    Set<String>? categories,
    Set<String>? merchants,
    double? minAmount,
    double? maxAmount,
    Set<TransactionDirection>? directions,
    Set<String>? tags,
    String? search,
  }) {
    return TransactionFilters(
      fromDate: fromDate ?? this.fromDate,
      toDate: toDate ?? this.toDate,
      categories: categories ?? this.categories,
      merchants: merchants ?? this.merchants,
      minAmount: minAmount ?? this.minAmount,
      maxAmount: maxAmount ?? this.maxAmount,
      directions: directions ?? this.directions,
      tags: tags ?? this.tags,
      search: search ?? this.search,
    );
  }

  TransactionFilters reset() {
    return const TransactionFilters();
  }

  Map<String, String> toQueryParameters() {
    final params = <String, String>{};
    if (fromDate != null) {
      params['from_date'] = DateFormat('yyyy-MM-dd').format(fromDate!);
    }
    if (toDate != null) {
      params['to_date'] = DateFormat('yyyy-MM-dd').format(toDate!);
    }
    if (categories.isNotEmpty) {
      params['category_id'] = categories.join(',');
    }
    if (merchants.isNotEmpty) {
      params['merchant_id'] = merchants.join(',');
    }
    if (minAmount != null) {
      params['min_amount'] = minAmount.toString();
    }
    if (maxAmount != null) {
      params['max_amount'] = maxAmount.toString();
    }
    if (directions.isNotEmpty) {
      params['direction'] = directions.map((e) => e.valueName).join(',');
    }
    if (tags.isNotEmpty) {
      params['tag_id'] = tags.join(',');
    }
    if (search != null && search!.isNotEmpty) {
      params['search'] = search!;
    }
    return params;
  }
}
