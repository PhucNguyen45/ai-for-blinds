import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_for_blinds/widgets/mode_selector.dart';

void main() {
  testWidgets('ModeSelector shows all scan modes',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ModeSelector(
            selectedMode: ScanMode.ocr,
            onModeChanged: (_) {},
          ),
        ),
      ),
    );

    expect(find.text('Đọc văn bản'), findsOneWidget);
    expect(find.text('Mô tả ảnh'), findsOneWidget);
    expect(find.text('Đọc biểu đồ'), findsOneWidget);
    expect(find.text('Phát hiện vật thể'), findsOneWidget);
  });

  testWidgets('ModeSelector calls onModeChanged when tapped',
      (WidgetTester tester) async {
    ScanMode? selected;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ModeSelector(
            selectedMode: ScanMode.ocr,
            onModeChanged: (mode) => selected = mode,
          ),
        ),
      ),
    );

    // Tap on "Mô tả ảnh" button
    await tester.tap(find.text('Mô tả ảnh'));
    expect(selected, ScanMode.describe);
  });
}
