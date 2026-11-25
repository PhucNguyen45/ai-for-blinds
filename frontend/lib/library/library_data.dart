import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../strings.dart';

@immutable
class BookPage {
  const BookPage({required this.number, required this.title, required this.text});

  factory BookPage.fromJson(Map<String, dynamic> j) =>
      BookPage(number: (j['number'] as num).toInt(), title: j['title'] as String, text: j['text'] as String);

  Map<String, dynamic> toJson() => {'number': number, 'title': title, 'text': text};

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

  /// Sách số hóa trên máy chủ (manifest của backend, `data/library/<mã>/manifest.json`).
  factory Book.fromServer(LibraryBookPages b, int index) {
    final unreviewed = b.pages.where((p) => !p.reviewed).length;
    return Book(
      id: b.book,
      title: b.title,
      subtitle: unreviewed == 0 ? '${b.pages.length} trang' : '${b.pages.length} trang · chưa duyệt',
      color: const ['lib', 'ask', 'guide'].elementAt(index % 3),
      pages: [
        for (final p in b.pages)
          BookPage(number: p.page, title: p.title ?? S.kindName(p.pageType) ?? 'Trang ${p.page}', text: p.description),
      ],
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'subtitle': subtitle,
    'color': color,
    'pages': [for (final p in pages) p.toJson()],
  };

  final String id;
  final String title;
  final String subtitle;

  /// `lib`, `ask` hoặc `guide`: màu gáy sách trên danh sách.
  final String color;
  final List<BookPage> pages;
}

/// Sách đang hiện lấy từ đâu (màn hình ghi rõ để người dùng và người hỗ trợ biết).
enum LibraryOrigin {
  /// Vừa tải từ máy chủ.
  server,

  /// Bản đã lưu trên máy từ lần tải trước (đang mất mạng): nghe được khi không có mạng.
  cache,

  /// Sách mẫu đóng gói trong app (chưa từng kết nối được máy chủ, hoặc chế độ demo).
  sample,
}

@immutable
class LibraryData {
  const LibraryData(this.books, this.origin);
  final List<Book> books;
  final LibraryOrigin origin;
}

abstract class LibrarySource {
  Future<LibraryData> load();
}

/// Sách mẫu đóng gói trong app.
class AssetLibrarySource implements LibrarySource {
  const AssetLibrarySource([this.asset = 'assets/library/sach_mau.json']);
  final String asset;

  @override
  Future<LibraryData> load() async {
    final j = jsonDecode(await rootBundle.loadString(asset)) as Map<String, dynamic>;
    return LibraryData([
      for (final b in j['books'] as List) Book.fromJson(b as Map<String, dynamic>),
    ], LibraryOrigin.sample);
  }
}

/// Nơi lưu bản thư viện đã tải (SettingsStore, trên SharedPreferences).
abstract class LibraryCache {
  String? get libraryCache;
  Future<void> setLibraryCache(String json);
}

/// Thư viện của nhóm trên máy chủ (`/v1/library`, kho `data/library/` của backend).
///
/// Ba tầng: máy chủ → bản đã lưu lần trước (nghe được khi mất mạng, yêu cầu UI-44) → sách mẫu trong app.
class ApiLibrarySource implements LibrarySource {
  ApiLibrarySource({required this.api, required this.cache, this.fallback = const AssetLibrarySource()});

  final SgbeApi Function() api;
  final LibraryCache cache;
  final LibrarySource fallback;

  @override
  Future<LibraryData> load() async {
    final fromServer = await _fromServer();
    if (fromServer != null && fromServer.isNotEmpty) {
      await cache.setLibraryCache(jsonEncode([for (final b in fromServer) b.toJson()]));
      return LibraryData(fromServer, LibraryOrigin.server);
    }
    final saved = _fromCache();
    if (saved != null && saved.isNotEmpty) return LibraryData(saved, LibraryOrigin.cache);
    return fallback.load();
  }

  Future<List<Book>?> _fromServer() async {
    final a = api();
    final list = await a.library();
    if (list is! ApiOk<List<LibraryBookInfo>>) return null;
    final books = <Book>[];
    for (final info in list.value) {
      final pages = await a.bookPages(info.book);
      if (pages is ApiOk<LibraryBookPages> && pages.value.pages.isNotEmpty) {
        books.add(Book.fromServer(pages.value, books.length));
      }
    }
    return books;
  }

  List<Book>? _fromCache() {
    final raw = cache.libraryCache;
    if (raw == null || raw.isEmpty) return null;
    try {
      return [for (final b in jsonDecode(raw) as List) Book.fromJson(b as Map<String, dynamic>)];
    } on FormatException {
      return null;
    } on TypeError {
      return null;
    }
  }
}
