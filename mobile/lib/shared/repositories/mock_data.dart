import 'package:intl/intl.dart';
import '../../shared/models/transaction_models.dart';

/// Local in-memory mock database to ensure functional offline/demo state.
/// Persists edits in-session when local backend is not running.
class MockDatabase {
  MockDatabase._();

  static final List<Transaction> transactions = _generateInitialMockTransactions();

  static List<Transaction> _generateInitialMockTransactions() {
    final now = DateTime.now();
    final list = <Transaction>[];

    // Salary (Credit)
    list.add(Transaction(
      id: 'tx-salary-1',
      postedDate: now.subtract(const Duration(days: 1)),
      description: 'SALARY / TALLY FINANCE INC / DIRECT DEP',
      amount: 4500.00,
      direction: TransactionDirection.credit,
      merchant: 'Tally Corp',
      category: 'Salary',
      notes: 'Monthly basic salary pay check',
      tags: ['salary', 'income'],
      referenceNumber: 'REF-DEP-09823472',
      balance: 8900.50,
      createdAt: now.subtract(const Duration(days: 1)),
      updatedAt: now.subtract(const Duration(days: 1)),
    ));

    // Rent (Debit)
    list.add(Transaction(
      id: 'tx-rent-1',
      postedDate: now.subtract(const Duration(days: 2)),
      description: 'RENT PAYMENT / APARTMENT 404 / ACH OUT',
      amount: 1200.00,
      direction: TransactionDirection.debit,
      merchant: 'Apex Realty',
      category: 'Rent',
      notes: 'July rent payment',
      tags: ['home', 'essential'],
      referenceNumber: 'REF-ACH-88374199',
      balance: 4400.50,
      createdAt: now.subtract(const Duration(days: 2)),
      updatedAt: now.subtract(const Duration(days: 2)),
    ));

    // Grocery (Debit)
    list.add(Transaction(
      id: 'tx-grocery-1',
      postedDate: now.subtract(const Duration(days: 3)),
      description: 'SAFEWAY GROCERY STORE #4839',
      amount: 142.50,
      direction: TransactionDirection.debit,
      merchant: 'Safeway',
      category: 'Groceries',
      notes: 'Weekly family groceries',
      tags: ['food', 'essential'],
      referenceNumber: 'REF-CARD-2234',
      balance: 5600.50,
      createdAt: now.subtract(const Duration(days: 3)),
      updatedAt: now.subtract(const Duration(days: 3)),
    ));

    // Coffee (Debit)
    list.add(Transaction(
      id: 'tx-coffee-1',
      postedDate: now.subtract(const Duration(days: 3, hours: 2)),
      description: 'STARBUCKS COFFEE #29938 SEATTLE WA',
      amount: 12.75,
      direction: TransactionDirection.debit,
      merchant: 'Starbucks',
      category: 'Cafes',
      notes: 'Cold brew and croissant',
      tags: ['leisure', 'coffee'],
      referenceNumber: 'REF-CARD-8839',
      balance: 5743.00,
      createdAt: now.subtract(const Duration(days: 3, hours: 2)),
      updatedAt: now.subtract(const Duration(days: 3, hours: 2)),
    ));

    // Ride (Debit)
    list.add(Transaction(
      id: 'tx-ride-1',
      postedDate: now.subtract(const Duration(days: 5)),
      description: 'UBER RIDE / HELP.UBER.COM / SAN FRANCISCO',
      amount: 24.50,
      direction: TransactionDirection.debit,
      merchant: 'Uber',
      category: 'Transport',
      notes: 'Ride to local airport',
      tags: ['commute', 'travel'],
      referenceNumber: 'REF-CARD-0912',
      balance: 5755.75,
      createdAt: now.subtract(const Duration(days: 5)),
      updatedAt: now.subtract(const Duration(days: 5)),
    ));

    // Dining (Debit)
    list.add(Transaction(
      id: 'tx-dining-1',
      postedDate: now.subtract(const Duration(days: 6)),
      description: 'CHIPOTLE MEXICAN GRILL #0983',
      amount: 18.25,
      direction: TransactionDirection.debit,
      merchant: 'Chipotle',
      category: 'Restaurants',
      notes: 'Burrito bowl lunch with guac',
      tags: ['food', 'quick-bite'],
      referenceNumber: 'REF-CARD-4493',
      balance: 5780.25,
      createdAt: now.subtract(const Duration(days: 6)),
      updatedAt: now.subtract(const Duration(days: 6)),
    ));

    // Subscription (Debit)
    list.add(Transaction(
      id: 'tx-sub-1',
      postedDate: now.subtract(const Duration(days: 10)),
      description: 'NETFLIX CARD BILLING / BEVERLY HILLS CA',
      amount: 15.99,
      direction: TransactionDirection.debit,
      merchant: 'Netflix',
      category: 'Subscriptions',
      notes: 'Premium plan subscription',
      tags: ['entertainment', 'recurring'],
      referenceNumber: 'REF-ACH-098234',
      balance: 5798.50,
      createdAt: now.subtract(const Duration(days: 10)),
      updatedAt: now.subtract(const Duration(days: 10)),
    ));

    // E-commerce (Debit)
    list.add(Transaction(
      id: 'tx-amazon-1',
      postedDate: now.subtract(const Duration(days: 12)),
      description: 'AMZN Mktp US*9E8A24J89 AMZN.COM/BILL WA',
      amount: 89.99,
      direction: TransactionDirection.debit,
      merchant: 'Amazon',
      category: 'Shopping',
      notes: 'Wireless charger and phone stand',
      tags: ['gadgets', 'shopping'],
      referenceNumber: 'REF-CARD-7739',
      balance: 5814.49,
      createdAt: now.subtract(const Duration(days: 12)),
      updatedAt: now.subtract(const Duration(days: 12)),
    ));

    // Gym Membership (Debit)
    list.add(Transaction(
      id: 'tx-gym-1',
      postedDate: now.subtract(const Duration(days: 15)),
      description: 'FITNESS FIRST GYM MEMBERSHIP ACH',
      amount: 60.00,
      direction: TransactionDirection.debit,
      merchant: 'Fitness First',
      category: 'Health',
      notes: 'Monthly gym membership',
      tags: ['health', 'recurring'],
      referenceNumber: 'REF-ACH-558231',
      balance: 5904.48,
      createdAt: now.subtract(const Duration(days: 15)),
      updatedAt: now.subtract(const Duration(days: 15)),
    ));

    // Refund (Credit)
    list.add(Transaction(
      id: 'tx-refund-1',
      postedDate: now.subtract(const Duration(days: 18)),
      description: 'CREDIT FROM AMAZON MARKETPLACE / RETURN REF',
      amount: 32.50,
      direction: TransactionDirection.credit,
      merchant: 'Amazon',
      category: 'Shopping',
      notes: 'Returned defective charger cable',
      tags: ['shopping', 'refund'],
      referenceNumber: 'REF-DEP-39281',
      balance: 5964.48,
      createdAt: now.subtract(const Duration(days: 18)),
      updatedAt: now.subtract(const Duration(days: 18)),
    ));

    // Groceries (Debit)
    list.add(Transaction(
      id: 'tx-grocery-2',
      postedDate: now.subtract(const Duration(days: 20)),
      description: 'WHOLE FOODS MARKET #8392',
      amount: 118.00,
      direction: TransactionDirection.debit,
      merchant: 'Whole Foods',
      category: 'Groceries',
      notes: 'Fresh vegetables and organic goods',
      tags: ['food', 'essential'],
      referenceNumber: 'REF-CARD-2893',
      balance: 5931.98,
      createdAt: now.subtract(const Duration(days: 20)),
      updatedAt: now.subtract(const Duration(days: 20)),
    ));

    // Coffee (Debit)
    list.add(Transaction(
      id: 'tx-coffee-2',
      postedDate: now.subtract(const Duration(days: 22)),
      description: 'STARBUCKS COFFEE #29938 SEATTLE WA',
      amount: 11.50,
      direction: TransactionDirection.debit,
      merchant: 'Starbucks',
      category: 'Cafes',
      notes: 'Flat white and muffin',
      tags: ['leisure', 'coffee'],
      referenceNumber: 'REF-CARD-8839',
      balance: 6049.98,
      createdAt: now.subtract(const Duration(days: 22)),
      updatedAt: now.subtract(const Duration(days: 22)),
    ));

    // Dining (Debit)
    list.add(Transaction(
      id: 'tx-dining-2',
      postedDate: now.subtract(const Duration(days: 25)),
      description: 'OLIVE GARDEN #08392 NEW YORK',
      amount: 82.40,
      direction: TransactionDirection.debit,
      merchant: 'Olive Garden',
      category: 'Restaurants',
      notes: 'Family dinner',
      tags: ['food', 'dining'],
      referenceNumber: 'REF-CARD-1193',
      balance: 6061.48,
      createdAt: now.subtract(const Duration(days: 25)),
      updatedAt: now.subtract(const Duration(days: 25)),
    ));

    return list;
  }

  /// Calculates Dashboard analytics dynamically over mock data.
  static DashboardAnalytics getMockDashboardAnalytics() {
    double totalIncome = 0.0;
    double totalExpense = 0.0;
    double currentMonthSpending = 0.0;
    final now = DateTime.now();

    final categoryMap = <String, double>{};
    final categoryCounts = <String, int>{};
    final merchantMap = <String, double>{};
    final merchantCounts = <String, int>{};
    final monthlyTrends = <String, Map<String, double>>{};

    for (final tx in transactions) {
      final period = DateFormat('yyyy-MM').format(tx.postedDate);
      monthlyTrends.putIfAbsent(period, () => {'income': 0.0, 'expense': 0.0});

      if (tx.direction == TransactionDirection.credit) {
        totalIncome += tx.amount;
        monthlyTrends[period]!['income'] = (monthlyTrends[period]!['income'] ?? 0.0) + tx.amount;
      } else {
        totalExpense += tx.amount;
        monthlyTrends[period]!['expense'] = (monthlyTrends[period]!['expense'] ?? 0.0) + tx.amount;

        final category = tx.category ?? 'Uncategorized';
        categoryMap[category] = (categoryMap[category] ?? 0.0) + tx.amount;
        categoryCounts[category] = (categoryCounts[category] ?? 0) + 1;

        final merchant = tx.merchant;
        merchantMap[merchant] = (merchantMap[merchant] ?? 0.0) + tx.amount;
        merchantCounts[merchant] = (merchantCounts[merchant] ?? 0) + 1;

        if (tx.postedDate.year == now.year && tx.postedDate.month == now.month) {
          currentMonthSpending += tx.amount;
        }
      }
    }

    final categoryList = categoryMap.entries.map((e) {
      return CategorySpend(
        category: e.key,
        totalSpent: e.value,
        transactionCount: categoryCounts[e.key] ?? 0,
        percentage: totalExpense > 0 ? (e.value / totalExpense) * 100 : 0.0,
      );
    }).toList()..sort((a, b) => b.totalSpent.compareTo(a.totalSpent));

    final merchantList = merchantMap.entries.map((e) {
      return MerchantSpend(
        merchant: e.key,
        totalSpent: e.value,
        transactionCount: merchantCounts[e.key] ?? 0,
      );
    }).toList()..sort((a, b) => b.totalSpent.compareTo(a.totalSpent));

    final sortedTrendKeys = monthlyTrends.keys.toList()..sort();
    final spendingTrend = sortedTrendKeys.map((key) {
      return TrendPoint(
        period: key,
        income: monthlyTrends[key]!['income'] ?? 0.0,
        expense: monthlyTrends[key]!['expense'] ?? 0.0,
        transactionCount: 0,
      );
    }).toList();

    final summary = DashboardSummary(
      totalIncome: totalIncome,
      totalExpense: totalExpense,
      netSavings: totalIncome - totalExpense,
      transactionCount: transactions.length,
      activeMerchants: merchantMap.keys.length,
      currentMonthSpending: currentMonthSpending,
    );

    final expenses = transactions.where((tx) => tx.direction == TransactionDirection.debit).toList()
      ..sort((a, b) => b.amount.compareTo(a.amount));
    final income = transactions.where((tx) => tx.direction == TransactionDirection.credit).toList()
      ..sort((a, b) => b.amount.compareTo(a.amount));

    return DashboardAnalytics(
      summary: summary,
      monthlySpendingTrend: spendingTrend,
      monthlyIncomeTrend: spendingTrend,
      categoryDistribution: categoryList,
      merchantSpending: merchantList,
      topCategories: categoryList.take(5).toList(),
      topMerchants: merchantList.take(5).toList(),
      largestExpenses: expenses.take(5).toList(),
      largestIncome: income.take(5).toList(),
    );
  }

  /// Calculates MerchantStats dynamically over mock data.
  static MerchantStats? getMockMerchantStats(String name) {
    final nameLower = name.trim().toLowerCase();
    final filtered = transactions.where((tx) => tx.merchant.trim().toLowerCase() == nameLower).toList();

    if (filtered.isEmpty) return null;

    final nameCanonical = filtered.first.merchant;
    final category = filtered.first.category;
    final debits = filtered.where((tx) => tx.direction == TransactionDirection.debit).toList();

    double totalSpent = 0.0;
    double highestTransaction = 0.0;
    double lowestTransaction = double.infinity;

    final monthlyMap = <String, double>{};
    for (final tx in filtered) {
      if (tx.direction == TransactionDirection.debit) {
        totalSpent += tx.amount;
        final period = DateFormat('yyyy-MM').format(tx.postedDate);
        monthlyMap[period] = (monthlyMap[period] ?? 0.0) + tx.amount;
      }
      if (tx.amount > highestTransaction) highestTransaction = tx.amount;
      if (tx.amount < lowestTransaction) lowestTransaction = tx.amount;
    }

    if (lowestTransaction == double.infinity) lowestTransaction = 0.0;

    final sortedDates = filtered.map((tx) => tx.postedDate).toList()..sort();

    final monthlySpending = monthlyMap.entries
        .map((e) => MapEntry(e.key, e.value))
        .toList()
      ..sort((a, b) => a.key.compareTo(b.key));

    return MerchantStats(
      merchant: nameCanonical,
      category: category,
      firstTransaction: sortedDates.first,
      lastTransaction: sortedDates.last,
      transactionCount: filtered.length,
      totalSpent: totalSpent,
      averageSpend: debits.isNotEmpty ? totalSpent / debits.length : 0.0,
      highestTransaction: highestTransaction,
      lowestTransaction: lowestTransaction,
      frequencyPerMonth: 1.2, // Stub frequency
      monthlySpending: monthlySpending,
    );
  }
}
