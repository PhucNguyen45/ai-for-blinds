import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_for_blinds/widgets/big_button.dart';

void main() {
  testWidgets('BigButton displays label and responds to tap',
      (WidgetTester tester) async {
    bool tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: BigButton(
            icon: Icons.home,
            label: 'Test Button',
            onTap: () => tapped = true,
          ),
        ),
      ),
    );

    expect(find.text('Test Button'), findsOneWidget);
    expect(find.byIcon(Icons.home), findsOneWidget);

    await tester.tap(find.text('Test Button'));
    expect(tapped, true);
  });

  testWidgets('BigCircleButton displays label', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: BigCircleButton(
            icon: Icons.camera_alt_rounded,
            label: 'CHỤP ẢNH',
            color: Colors.blue,
            onTap: () {},
          ),
        ),
      ),
    );

    expect(find.bySemanticsLabel('CHỤP ẢNH'), findsOneWidget);
  });
}
