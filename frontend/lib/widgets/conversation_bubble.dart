import 'package:flutter/material.dart';

import '../utils/responsive.dart';

/// A single Q&A message in the voice conversation UI.
class ConversationMessage {
  final String content;
  final bool isUser;
  final String? source;
  final String? timestamp;

  const ConversationMessage({
    required this.content,
    required this.isUser,
    this.source,
    this.timestamp,
  });
}

/// Chat bubble widget for the Neon Pulse voice conversation theme.
class ConversationBubble extends StatelessWidget {
  final String content;
  final bool isUser;
  final String? source;
  final String? timestamp;

  const ConversationBubble({
    super.key,
    required this.content,
    required this.isUser,
    this.source,
    this.timestamp,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Align(
        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          constraints: BoxConstraints(
            maxWidth: (MediaQuery.of(context).size.width * 0.85).clamp(200, 500),
          ),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isUser ? const Color(0xFF00F0FF) : const Color(0xFF141829),
            borderRadius: isUser
                ? const BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(4),
                    bottomLeft: Radius.circular(20),
                    bottomRight: Radius.circular(20),
                  )
                : const BorderRadius.only(
                    topLeft: Radius.circular(4),
                    topRight: Radius.circular(20),
                    bottomLeft: Radius.circular(20),
                    bottomRight: Radius.circular(20),
                  ),
            border: isUser
                ? null
                : Border.all(color: const Color(0xFF1E2A4A), width: 1),
          ),
          child: Semantics(
            label: isUser ? 'Bạn: $content' : 'Trợ lý: $content',
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  isUser ? Icons.person_rounded : Icons.auto_awesome_rounded,
                  size: 20,
                  color: isUser ? Colors.black : const Color(0xFF9D4EDD),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        content,
                        style: TextStyle(
                          fontSize: Responsive.textScale(context, 20, min: 14, max: 24),
                          fontWeight: FontWeight.w400,
                          height: 1.5,
                          color: isUser
                              ? Colors.black
                              : const Color(0xFFFFFFFF),
                        ),
                      ),
                      if (source != null && !isUser) ...[
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            const Icon(
                              Icons.menu_book_rounded,
                              size: 16,
                              color: Color(0xFF8892B0),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              source!,
                              style: TextStyle(
                                fontSize: Responsive.textScale(context, 14, min: 11, max: 17),
                                fontStyle: FontStyle.italic,
                                color: Color(0xFF8892B0),
                              ),
                            ),
                          ],
                        ),
                      ],
                      if (timestamp != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          timestamp!,
                          style: TextStyle(
                            fontSize: Responsive.textScale(context, 12, min: 10, max: 15),
                            color: Color(0xFF8892B0),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// A scrollable list of [ConversationBubble] items.
class ConversationList extends StatelessWidget {
  final List<ConversationMessage> messages;
  final ScrollController? controller;

  const ConversationList({
    super.key,
    required this.messages,
    this.controller,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: controller,
      padding: const EdgeInsets.all(16),
      itemCount: messages.length,
      itemBuilder: (context, index) {
        final msg = messages[index];
        return ConversationBubble(
          content: msg.content,
          isUser: msg.isUser,
          source: msg.source,
          timestamp: msg.timestamp,
        );
      },
    );
  }
}
