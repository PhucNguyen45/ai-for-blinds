"""
Vision-Language Model service — image description in Vietnamese.

Talks to any OpenAI-compatible endpoint (OpenRouter while developing, a local
vLLM / SGLang server once the model runs on-premise). Falls back to the Gemini
SDK only when no OpenRouter key is configured, so the old dev setup keeps
working during the migration.

The model is chosen with the VLM_MODEL environment variable; nothing in this
file is tied to one vendor.
"""

import base64
import hashlib
import time
from collections import OrderedDict
from typing import Optional

from backend.config import settings


class VlmService:
    """
    Vision-Language Model service.

    Generates detailed Vietnamese descriptions of images for blind students.
    """

    # Shared instruction block: every output is read aloud by TTS, so the
    # model must produce plain spoken Vietnamese — no markup, no visual deixis.
    SPEECH_RULES = (
        "Toàn bộ câu trả lời sẽ được đọc to bằng giọng nói tổng hợp. "
        "Vì vậy: không dùng markdown, không dùng dấu sao, dấu gạch đầu dòng, "
        "tiêu đề hay bất kỳ ký hiệu đặc biệt nào. "
        "Không dùng cụm chỉ thị thị giác như 'như bạn thấy', 'hình bên trái', "
        "'ở phía trên'. "
        "Giữ nguyên chữ số cho các con số, ví dụ viết 85,8 chứ không viết "
        "'tám mươi lăm phẩy tám' — máy đọc sẽ tự phát âm đúng. Dùng dấu phẩy "
        "thập phân kiểu Việt Nam, không dùng dấu chấm. "
        "Nhưng ký hiệu thì phải viết thành chữ: '%' viết là 'phần trăm', "
        "'°C' viết là 'độ C', 'm2' viết là 'mét vuông'. "
        "Tuyệt đối không chèn từ tiếng Anh nào vào câu trả lời. "
        "Viết câu ngắn, trình bày theo thứ tự tuyến tính, vì người nghe "
        "không tua lại được."
    )

    BASE_PROMPT = (
        "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
        "Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt một cách tự nhiên, "
        "dễ hiểu. Nếu ảnh có văn bản, hãy đọc nội dung văn bản đó. "
        "Nếu ảnh có biểu đồ, hãy mô tả số liệu và xu hướng. "
    )

    # Một trang đôi sách giáo khoa thường chứa bảy khối khác loại: tên bài,
    # đoạn văn, bản đồ, bảng số liệu, biểu đồ, sơ đồ các bước, ảnh chụp. Tả
    # tuôn một mạch thì người nghe mất phương hướng giữa chừng — nên bắt mô
    # hình nói trước trang có những gì, rồi mới đi vào từng phần, và quy định
    # cách đọc riêng cho từng loại khối.
    PAGE_PROMPT = (
        "Bạn là trợ lý cho học sinh khiếm thị Việt Nam đang học sách giáo "
        "khoa. Ảnh này là một trang sách. Hãy làm đúng hai bước. "
        "Bước một, mở đầu bằng một câu ngắn cho biết trang này gồm những phần "
        "nào, ví dụ tên bài, một bản đồ, một bảng số liệu, một biểu đồ. Nhờ "
        "câu đó người nghe biết trước sẽ được nghe những gì. "
        "Bước hai, lần lượt đọc từng phần theo thứ tự trên trang, trước mỗi "
        "phần nói rõ đang đọc phần nào. "
        "Cách đọc từng loại như sau. "
        "Đoạn văn thì đọc nguyên văn. "
        "Bảng số liệu thì đọc theo từng hàng, mỗi hàng nêu đủ tên và các số "
        "của hàng đó kèm đơn vị. "
        "Biểu đồ cột thì đọc lần lượt từng cột, nêu tên cột rồi giá trị. "
        "Bản đồ và lược đồ thì đọc tên bản đồ trước, rồi phần chú giải, rồi "
        "các địa danh và đối tượng chính, cuối cùng là hướng di chuyển nếu có. "
        "Trục thời gian thì đọc lần lượt từng mốc theo thứ tự thời gian, mỗi "
        "mốc nêu năm rồi đến sự kiện. "
        "Sơ đồ các bước thì đọc lần lượt bước một, bước hai, bước ba. "
        "Ảnh chụp và hiện vật thì nêu tên rồi tả nội dung. "
        "Câu hỏi trong bài thì đọc nguyên văn để học sinh biết phải làm gì. "
        "Đọc đủ mọi con số, không bỏ sót, không làm tròn. "
        # Prompt dài làm loãng quy tắc ký hiệu ở khối SPEECH_RULES phía sau,
        # nên nhắc lại đúng một lần ngay tại đây.
        "Nhắc lại một điều quan trọng: không được để lọt dấu phần trăm, phải "
        "viết chữ 'phần trăm'. "
    )

    # Chụp lại đúng trang sách là chuyện thường: học sinh nghe chưa kịp, chụp
    # lại. Nhớ kết quả cũ thì lần sau trả lời tức thì và không tốn thêm tiền.
    CACHE_SIZE = 64

    def __init__(self) -> None:
        self._client = None
        self._gemini = None
        self._cache: OrderedDict[str, str] = OrderedDict()

    # ── Cache ───────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(prompt: str, image_bytes: bytes) -> str:
        digest = hashlib.sha256(image_bytes).hexdigest()
        return f"{settings.vlm_model}|{hashlib.sha256(prompt.encode()).hexdigest()[:16]}|{digest}"

    def _cache_get(self, key: str) -> Optional[str]:
        value = self._cache.get(key)
        if value is not None:
            self._cache.move_to_end(key)
        return value

    def _cache_put(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self.CACHE_SIZE:
            self._cache.popitem(last=False)

    def clear_cache(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    # ── Client construction (lazy: importing this module needs no key) ──

    def _get_client(self):
        """Build the OpenAI-compatible client on first use."""
        if self._client is None:
            settings.validate()
            from openai import OpenAI

            self._client = OpenAI(
                api_key=settings.vlm_api_key,
                base_url=settings.vlm_base_url,
            )
        return self._client

    def _get_gemini(self):
        """Legacy path, used only when no OpenRouter key is set."""
        if self._gemini is None:
            settings.validate()
            import google.generativeai as genai

            genai.configure(api_key=settings.google_api_key)
            self._gemini = genai.GenerativeModel(settings.gemini_model)
        return self._gemini

    @property
    def model_name(self) -> str:
        """Model currently answering requests — surfaced by /health."""
        if settings.vlm_provider == "openai":
            return settings.vlm_model
        return settings.gemini_model

    # ── Internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _data_url(image_bytes: bytes, mime_type: str) -> str:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{b64}"

    def _chat(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        temperature: Optional[float] = None,
    ) -> str:
        """One vision turn against the OpenAI-compatible endpoint."""
        response = self._get_client().chat.completions.create(
            model=settings.vlm_model,
            max_tokens=settings.vlm_max_tokens,
            temperature=settings.vlm_temperature if temperature is None else temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self._data_url(image_bytes, mime_type)
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content

    def _generate(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        use_cache: bool = True,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        """
        Route to whichever provider is configured, with cache and retry.

        Providers return 429 often enough — free tiers share a pool — that a
        single failure would leave the student listening to silence. Retry a
        few times with growing waits before giving up.
        """
        key = self._cache_key(prompt, image_bytes)
        if use_cache:
            cached = self._cache_get(key)
            if cached is not None:
                return cached

        last_error: Optional[Exception] = None
        for attempt in range(settings.vlm_max_retries):
            try:
                if settings.vlm_provider == "openai":
                    text = self._chat(prompt, image_bytes, mime_type, temperature)
                else:
                    response = self._get_gemini().generate_content([
                        prompt,
                        {"mime_type": mime_type, "data": image_bytes},
                    ])
                    text = response.text

                if text:
                    self._cache_put(key, text)
                return text
            except Exception as e:
                last_error = e
                retryable = any(
                    code in str(e) for code in ("429", "500", "502", "503", "504")
                )
                if not retryable or attempt == settings.vlm_max_retries - 1:
                    break
                wait = 2**attempt
                print(f"VLM {self.model_name} lỗi tạm thời, thử lại sau {wait}s")
                time.sleep(wait)

        print(f"VLM error ({self.model_name}): {last_error}")
        return None

    # ── Public API ──────────────────────────────────────────────────────

    def describe(
        self,
        image_bytes: bytes,
        mime_type: str,
        textbook_page: bool = False,
    ) -> Optional[str]:
        """
        Describe an image in Vietnamese.

        Args:
            image_bytes: Raw image data.
            mime_type: MIME type of the image (e.g., 'image/jpeg').
            textbook_page: Ảnh chụp trang sách thì dùng prompt có cấu trúc,
                thay vì mô tả tuôn một mạch.

        Returns:
            Vietnamese description string, or None on failure.
        """
        prompt = self.PAGE_PROMPT if textbook_page else self.BASE_PROMPT
        return self._generate(prompt + self.SPEECH_RULES, image_bytes, mime_type)

    def describe_with_context(
        self, image_bytes: bytes, mime_type: str, context: str
    ) -> Optional[str]:
        """
        Describe an image with additional context (e.g., textbook chapter).

        Args:
            image_bytes: Raw image data.
            mime_type: MIME type of the image.
            context: Additional context about what the student is studying.

        Returns:
            Vietnamese description string, or None on failure.
        """
        prompt = (
            "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
            f"Học sinh đang học về: {context}. "
            "Hãy mô tả chi tiết bức ảnh này bằng tiếng Việt, liên hệ với nội "
            "dung đang học. " + self.SPEECH_RULES
        )
        return self._generate(prompt, image_bytes, mime_type)

    def transcribe(self, image_bytes: bytes, mime_type: str) -> Optional[str]:
        """
        Đọc nguyên văn chữ trong ảnh, không mô tả, không bình luận.

        Ràng buộc 2 của đề tài: một VLM gánh cả OCR lẫn mô tả. Nhờ vậy
        `/ocr` không cần PaddleOCR và không phải cài thêm vài GB thư viện.
        """
        prompt = (
            "Đọc toàn bộ chữ có trong ảnh này và chép lại chính xác bằng "
            "tiếng Việt, giữ nguyên thứ tự từ trên xuống dưới. "
            "Chỉ chép chữ, không mô tả hình ảnh, không thêm nhận xét, "
            "không thêm lời dẫn. Nếu ảnh không có chữ nào, trả lời đúng một "
            "câu: Ảnh này không có chữ."
        )
        return self._generate(prompt, image_bytes, mime_type, temperature=0.0)

    def answer_about_image(
        self, image_bytes: bytes, mime_type: str, question: str
    ) -> Optional[str]:
        """
        Trả lời một câu hỏi cụ thể về bức ảnh vừa chụp.

        Học sinh nghe mô tả xong thường hỏi tiếp: "cột năm hai nghìn mười chín
        bao nhiêu". Mô tả lại từ đầu vừa chậm vừa thừa, nên hỏi thẳng vào ảnh.
        """
        prompt = (
            "Bạn là trợ lý cho học sinh khiếm thị Việt Nam. "
            "Học sinh vừa chụp bức ảnh này và hỏi một câu về nó. "
            "Trả lời đúng trọng tâm câu hỏi, không mô tả lại toàn bộ ảnh. "
            "Nếu trong ảnh không có thông tin để trả lời, nói rõ là không thấy "
            "thông tin đó trong ảnh. "
            f"Câu hỏi: {question}. " + self.SPEECH_RULES
        )
        # Đọc số liệu trong ảnh là việc tra cứu. Nhiệt độ 0,3 làm cùng một câu
        # hỏi lúc trả lời đúng lúc bảo "không thấy thông tin".
        return self._generate(prompt, image_bytes, mime_type, temperature=0.0)

    def answer_from_context(self, question: str, passages: list[str]) -> Optional[str]:
        """
        Answer a student question grounded in retrieved textbook passages.

        Used by /rag/query so the endpoint returns spoken Vietnamese instead of
        a raw chunk of textbook.

        Args:
            question: The student's question.
            passages: Textbook passages retrieved from the vector store.

        Returns:
            Vietnamese answer, or None on failure.
        """
        joined = "\n\n".join(f"Đoạn {i + 1}: {p}" for i, p in enumerate(passages))
        prompt = (
            "Bạn là trợ lý học tập cho học sinh khiếm thị Việt Nam. "
            "Chỉ trả lời dựa trên các đoạn sách giáo khoa dưới đây. "
            "Nếu các đoạn này không đủ để trả lời, hãy nói rõ là chưa tìm thấy "
            "trong sách giáo khoa, đừng tự suy đoán.\n\n"
            f"{joined}\n\n"
            f"Câu hỏi của học sinh: {question}\n\n" + self.SPEECH_RULES
        )
        try:
            if settings.vlm_provider == "openai":
                response = self._get_client().chat.completions.create(
                    model=settings.vlm_model,
                    max_tokens=settings.vlm_max_tokens,
                    temperature=settings.vlm_temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content

            return self._get_gemini().generate_content(prompt).text
        except Exception as e:
            print(f"VLM answer error ({self.model_name}): {e}")
            return None


# Singleton instance
vlm_service = VlmService()
