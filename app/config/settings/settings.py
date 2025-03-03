# config/settings/settings.py
TRANSLATION_SETTINGS = {
    "enabled": True,
    "source_language": "ko",
    "target_language": "en",
    "translation_api": "google",  # google, microsoft, deepl 등
    "cache_translations": True    # 번역 결과 캐싱 여부
}

# 벡터 검색 관련 설정
VECTOR_SEARCH_SETTINGS = {
    "default_model": "paraphrase-multilingual-MiniLM-L12-v2",
    "default_threshold": 0.1,
    "max_results": 5,
    "cache_enabled": True
}

# LLM 관련 설정
LLM_SETTINGS = {
    "model_name": "deepseek-ai/deepseek-coder-1.3b-instruct",
    "temperature": 0.1,
    "max_tokens": 256,
    "repetition_penalty": 1.0
}