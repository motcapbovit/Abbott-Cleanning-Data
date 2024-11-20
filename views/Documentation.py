from deep_translator import GoogleTranslator
import time
import streamlit as st


def translate_text(text, target_lang="vi"):
    """
    Dịch văn bản sang tiếng Việt sử dụng deep-translator
    """
    translator = GoogleTranslator(target=target_lang)
    try:
        # Tự động phát hiện và dịch
        translated = translator.translate(text)
        time.sleep(0.5)

        return {"original": text, "translated": translated}
    except Exception as e:
        return f"Lỗi khi dịch: {str(e)}"


texts = [
    "베트남",
    "ベトナム",
    "越南",
    "វៀតណាម",
    "វៀតណាម",
    "ダナン市",
    "岘港",
    "닥락 성",
    "ダナン市",
    "グーハインソン",
    "第十一郡",
    "胡志明市",
]
st.write(texts)

for text in texts:
    result = translate_text(text)

    if isinstance(result, dict):
        st.write(f"Văn bản gốc: {result['original']}")
        st.write(f"Bản dịch: {result['translated']}\n")
    else:
        st.write(result + "\n")
