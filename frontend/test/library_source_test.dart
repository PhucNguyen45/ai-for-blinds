// Thư viện của nhóm trên máy chủ (`/v1/library` của backend, kho data/library/).
// Fixture library_*.json là phản hồi THẬT của backend nhánh toan/tich-hop (25/11/2026).
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sgbe/api/api_client.dart';
import 'package:sgbe/api/models.dart';
import 'package:sgbe/library/library_data.dart';

import 'fakes.dart';

String fixture(String name) => File('test/fixtures/$name').readAsStringSync();

http.Response jsonResponse(String body, int status) =>
    http.Response.bytes(utf8.encode(body), status, headers: {'content-type': 'application/json; charset=utf-8'});

LibraryBookPages pages(String book, {bool reviewed = true}) => LibraryBookPages(
  book: book,
  title: 'Sách $book',
  pages: [
    LibraryPage(page: 4, pageType: 'chart', description: 'Biểu đồ cột về số sách.', reviewed: reviewed),
    LibraryPage(page: 5, pageType: 'map', description: 'Lược đồ.', reviewed: true, title: 'Lược đồ vùng núi'),
  ],
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('ApiClient thư viện', () {
    test('đọc danh sách sách và các trang từ phản hồi thật của backend', () async {
      final paths = <String>[];
      final api = ApiClient(
        'http://x',
        client: MockClient((req) async {
          paths.add(req.url.path);
          return jsonResponse(
            req.url.path.endsWith('/pages') ? fixture('library_pages_ok.json') : fixture('library_ok.json'),
            200,
          );
        }),
      );
      final list = (await api.library() as ApiOk<List<LibraryBookInfo>>).value;
      expect([for (final b in list) b.book], containsAll(['demo', 'tnxh3-mau', 'lsdl4-mau']));
      expect(list.firstWhere((b) => b.book == 'tnxh3-mau').pageCount, 3);

      final book = (await api.bookPages('tnxh3-mau') as ApiOk<LibraryBookPages>).value;
      expect(book.title, 'Tự nhiên và Xã hội 3');
      expect(book.pages, hasLength(3));
      expect(book.pages.first.description.length, greaterThan(40));
      expect(book.pages.first.title, isNotNull);
      expect(paths, ['/v1/library', '/v1/library/tnxh3-mau/pages']);
    });

    test('sách không có: lỗi BOOK_NOT_FOUND kèm câu tiếng Việt', () async {
      final api = ApiClient(
        'http://x',
        client: MockClient(
          (_) async => jsonResponse(
            '{"data":null,"error":{"code":"BOOK_NOT_FOUND","message":"Không tìm thấy cuốn sách này trong thư viện."}}',
            404,
          ),
        ),
      );
      final f = await api.bookPages('khong-co') as ApiFail<LibraryBookPages>;
      expect(f.code, 'BOOK_NOT_FOUND');
      expect(f.message, startsWith('Không tìm thấy'));
    });
  });

  group('ApiLibrarySource: máy chủ → bản đã lưu → sách mẫu', () {
    test('có máy chủ: lấy sách của nhóm và lưu lại để nghe khi mất mạng', () async {
      final api = FakeApi()..serverBooks = [pages('demo'), pages('tnxh3-mau', reviewed: false)];
      final cache = MemoryLibraryCache();
      final data = await ApiLibrarySource(api: () => api, cache: cache).load();
      expect(data.origin, LibraryOrigin.server);
      expect([for (final b in data.books) b.id], ['demo', 'tnxh3-mau']);
      expect(data.books[0].subtitle, '2 trang');
      expect(data.books[1].subtitle, '2 trang · chưa duyệt');
      expect(data.books[0].pages[0].title, 'Biểu đồ', reason: 'không có tiêu đề thì dùng tên loại hình');
      expect(data.books[0].pages[1].title, 'Lược đồ vùng núi');
      expect(cache.libraryCache, isNotNull);
    });

    test('mất mạng: đọc bản đã lưu lần trước', () async {
      final cache = MemoryLibraryCache();
      final online = FakeApi()..serverBooks = [pages('demo')];
      await ApiLibrarySource(api: () => online, cache: cache).load();

      final offline = FakeApi(); // serverBooks = null → lỗi mạng
      final data = await ApiLibrarySource(api: () => offline, cache: cache).load();
      expect(data.origin, LibraryOrigin.cache);
      expect(data.books.single.pages.first.text, 'Biểu đồ cột về số sách.');
    });

    test('chưa từng kết nối: dùng sách mẫu trong app', () async {
      final data = await ApiLibrarySource(
        api: () => FakeApi(),
        cache: MemoryLibraryCache(),
        fallback: const FakeLibrary(),
      ).load();
      expect(data.origin, LibraryOrigin.sample);
      expect(data.books.first.title, 'Sách A');
    });

    test('bản đã lưu hỏng thì bỏ qua, không treo', () async {
      final cache = MemoryLibraryCache()..libraryCache = '{không phải json';
      final data = await ApiLibrarySource(api: () => FakeApi(), cache: cache, fallback: const FakeLibrary()).load();
      expect(data.origin, LibraryOrigin.sample);
    });

    test('máy chủ có nhưng kho trống: không ghi đè bản đã lưu', () async {
      final cache = MemoryLibraryCache()..libraryCache = jsonEncode([Book.fromServer(pages('demo'), 0).toJson()]);
      final data = await ApiLibrarySource(api: () => FakeApi()..serverBooks = [], cache: cache).load();
      expect(data.origin, LibraryOrigin.cache);
    });
  });
}
