import 'package:flutter/material.dart';

/// Semantic color palette for Tally.
/// Provides central definitions for all theme states.
class AppColors {
  AppColors._();

  // Primary brand palette (Teal/Emerald)
  static const Color primaryLight = Color(0xFF0D9488); // Teal 600
  static const Color primaryDark = Color(0xFF14B8A6);  // Teal 500
  
  static const Color primaryContainerLight = Color(0xFFCCFBF1); // Teal 100
  static const Color primaryContainerDark = Color(0xFF115E59);  // Teal 800

  // Secondary brand palette (Indigo)
  static const Color secondaryLight = Color(0xFF4F46E5); // Indigo 600
  static const Color secondaryDark = Color(0xFF6366F1);  // Indigo 500

  // Background and Surface (Slate/Neutral)
  static const Color backgroundLight = Color(0xFFF8FAFC); // Slate 50
  static const Color backgroundDark = Color(0xFF0F172A);  // Slate 900

  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color surfaceDark = Color(0xFF1E293B);    // Slate 800

  static const Color cardLight = Color(0xFFFFFFFF);
  static const Color cardDark = Color(0xFF1E293B);      // Slate 800

  static const Color borderLight = Color(0xFFE2E8F0);    // Slate 200
  static const Color borderDark = Color(0xFF334155);     // Slate 700

  // Text colors
  static const Color textPrimaryLight = Color(0xFF0F172A);   // Slate 900
  static const Color textPrimaryDark = Color(0xFFF8FAFC);    // Slate 50

  static const Color textSecondaryLight = Color(0xFF475569); // Slate 600
  static const Color textSecondaryDark = Color(0xFF94A3B8);  // Slate 400

  static const Color textHintLight = Color(0xFF94A3B8);      // Slate 400
  static const Color textHintDark = Color(0xFF64748B);       // Slate 500

  // Semantic Status Colors
  static const Color success = Color(0xFF10B981); // Emerald 500
  static const Color warning = Color(0xFFF59E0B); // Amber 500
  static const Color error = Color(0xFFEF4444);   // Red 500
  static const Color info = Color(0xFF3B82F6);    // Blue 500

  // Shimmer
  static const Color shimmerBaseLight = Color(0xFFE2E8F0);
  static const Color shimmerHighlightLight = Color(0xFFF1F5F9);
  static const Color shimmerBaseDark = Color(0xFF334155);
  static const Color shimmerHighlightDark = Color(0xFF475569);

  // Gradient helpers for card glassmorphism and accents
  static const List<Color> primaryGradient = [
    Color(0xFF0D9488),
    Color(0xFF4F46E5),
  ];

  static const List<Color> darkBackgroundGradient = [
    Color(0xFF0F172A),
    Color(0xFF1E1E38),
  ];
}
