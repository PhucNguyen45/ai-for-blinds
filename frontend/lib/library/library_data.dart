import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

@immutable
class BookPage {
  const BookPage({required this.number, required this.title, required this.text});

  factory BookPage.fromJson(Map<String, dynamic> j) =>
      BookPage(number: (j['number'] as num).toInt(), title: j['title'] as String, text: j['text'] as String);

  final int number;
  final String title;

  /// Lời mô tả trang để đọc to.
  final String text;
}

@immutable
class Book {
  const Book({required this.id, required this.title, required this.subtitle, required this.color, required this.pages});

  factory Book.fromJson(Map<String, dynamic> j) => Book(
    id: j['id'] as String,
    title: j['title'] as String,
    subtitle: (j['subtitle'] as String?) ?? '',
    color: (j['color'] as String?) ?? 'lib',
    pages: [for (final p in j['pages'] as List) BookPage.fromJson(p as Map<String, dynamic>)],
  );

  final String id;
  final String title;
  final String subtitle;

  /// `lib`, `ask` hoặc `guide`: màu gáy sách trên danh sách.
  final String color;
  final List<BookPage> pages;
}

/// Nguồn sách cho màn hình Thư viện. Hiện là bản mẫu đóng gói trong app;
/// khi Mảng B xong `/v1/library` thì thêm một nguồn tải về máy (yêu cầu UI-44).
abstract class LibrarySource {
  Future<List<Book>> load();
}

class AssetLibrarySource implements LibrarySource {
  const AssetLibrarySource([this.asset = 'assets/library/sach_mau.json']);
  final String asset;

  @override
  Future<List<Book>> load() async {
    final j = jsonDecode(await rootBundle.loadString(asset)) as Map<String, dynamic>;
    return [for (final b in j['books'] as List) Book.fromJson(b as Map<String, dynamic>)];
  }
}
