/// Represents a "learning moment" — a captured image, text, or note
/// that the student wants to remember and retrieve later.
/// Supports vector embeddings for semantic search (Persistent Visual Memory).
class LearningMoment {
  final String id;
  final String title;
  final String description;
  final String? imagePath;
  final String? textContent;
  final String? audioPath;
  final String? sourceTextbook;
  final DateTime createdAt;
  final List<double>? embedding;

  LearningMoment({
    required this.id,
    required this.title,
    required this.description,
    this.imagePath,
    this.textContent,
    this.audioPath,
    this.sourceTextbook,
    DateTime? createdAt,
    this.embedding,
  }) : createdAt = createdAt ?? DateTime.now();

  /// Format date as a readable relative string (Vietnamese).
  String get formattedDate {
    final now = DateTime.now();
    final diff = now.difference(createdAt);

    if (diff.inSeconds < 60) return 'Vừa xong';
    if (diff.inMinutes < 60) return '${diff.inMinutes} phút trước';
    if (diff.inHours < 24) return '${diff.inHours} giờ trước';
    if (diff.inDays < 7) return '${diff.inDays} ngày trước';
    return '${createdAt.day}/${createdAt.month}/${createdAt.year}';
  }

  /// Preview text (first 100 chars).
  String get preview {
    if (description.length > 100) {
      return '${description.substring(0, 100)}...';
    }
    return description;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'description': description,
    'imagePath': imagePath,
    'textContent': textContent,
    'audioPath': audioPath,
    'sourceTextbook': sourceTextbook,
    'createdAt': createdAt.toIso8601String(),
    'embedding': embedding,
  };

  factory LearningMoment.fromJson(Map<String, dynamic> json) => LearningMoment(
    id: json['id'] as String,
    title: json['title'] as String? ?? '',
    description: json['description'] as String? ?? '',
    imagePath: json['imagePath'] as String?,
    textContent: json['textContent'] as String?,
    audioPath: json['audioPath'] as String?,
    sourceTextbook: json['sourceTextbook'] as String?,
    createdAt: json['createdAt'] != null
        ? DateTime.parse(json['createdAt'] as String)
        : null,
    embedding: json['embedding'] != null
        ? List<double>.from(json['embedding'] as List)
        : null,
  );

  /// Build a LearningMoment from the backend /moments API response shape.
  factory LearningMoment.fromApiMap(Map<String, dynamic> json) {
    final content = json['content'] as String? ?? '';
    final subject = json['subject'] as String?;
    final grade = json['grade'];
    final chapter = json['chapter'] as String?;
    final page = json['page_number'];

    final sourceParts = <String>[];
    if (subject != null && subject.isNotEmpty) {
      sourceParts.add(grade is num ? 'SGK $subject $grade' : 'SGK $subject');
    }
    if (chapter != null && chapter.isNotEmpty) sourceParts.add(chapter);
    if (page is num) sourceParts.add('trang $page');

    return LearningMoment(
      id: json['id'] as String,
      title: json['title'] as String? ?? '',
      description: content,
      textContent: content,
      sourceTextbook: sourceParts.isEmpty ? null : sourceParts.join(', '),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }
}
