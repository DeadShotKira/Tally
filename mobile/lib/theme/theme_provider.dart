import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Provider for managing and persisting the application ThemeMode (Light, Dark, System).
final themeNotifierProvider = StateNotifierProvider<ThemeNotifier, ThemeMode>((ref) {
  return ThemeNotifier();
});

class ThemeNotifier extends StateNotifier<ThemeMode> {
  static const String _themeKey = 'user_theme_mode';

  ThemeNotifier() : super(ThemeMode.system) {
    _loadTheme();
  }

  /// Loads the persisted theme mode from SharedPreferences.
  Future<void> _loadTheme() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final themeIndex = prefs.getInt(_themeKey);
      if (themeIndex != null) {
        state = ThemeMode.values[themeIndex];
      }
    } catch (_) {
      // Fallback to system theme in case of exception
      state = ThemeMode.system;
    }
  }

  /// Sets the application theme mode and persists it.
  Future<void> setThemeMode(ThemeMode mode) async {
    state = mode;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_themeKey, mode.index);
    } catch (_) {
      // Non-blocking fail
    }
  }

  /// Helper to toggle between light and dark modes (or system).
  Future<void> toggleTheme(BuildContext context) async {
    final currentBrightness = MediaQuery.platformBrightnessOf(context);
    final isDarkNow = state == ThemeMode.dark || 
        (state == ThemeMode.system && currentBrightness == Brightness.dark);
    
    await setThemeMode(isDarkNow ? ThemeMode.light : ThemeMode.dark);
  }
}
