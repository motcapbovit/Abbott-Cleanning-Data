import streamlit as st
import re
import plotly.express as px
import unicodedata
import json
import time
from deep_translator import GoogleTranslator


# Extra utilities
from streamlit_extras.add_vertical_space import add_vertical_space

##################################### SECTION 0: Define Functions ######################################


def remove_vietnamese_accent(text, special_char_map):
    """
    Loại bỏ dấu tiếng Việt và xử lý các ký tự đặc biệt

    Args:
        text (str): Văn bản cần xử lý
        special_char_map (dict, optional): Bảng chuyển đổi ký tự đặc biệt.
            Mặc định xử lý chữ 'đ'/'Đ'
    """

    # Loại bỏ dấu
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    # Thay thế các ký tự đặc biệt
    for char, replacement in special_char_map.items():
        text = text.replace(char, replacement)

    return text


def remove_unnecessary_words(province, outlier_province_map, outlier_provinces):
    # Lowercase để chuẩn hóa
    province = province.lower()

    # Bước 1: Loại bỏ các từ không cần thiết
    province = re.sub(r"\b(thanh pho|pho|province|city)\b", "", province)

    # Bước 2: Xử lý các trường hợp đặc biệt Hà Tĩnh (ha tinh))
    for special_case in outlier_provinces:
        if special_case in province:
            province = special_case  # Case Ha Tinh
        else:
            province = re.sub(r"\btinh\b", "", province)

    # Bước 3: Xử lý các trường hợp Đắk Lắk (dac lak -> dak lak)
    for old_name, new_name in outlier_province_map.items():
        if old_name in province:
            province = new_name

    # Bước 4: Loại bỏ các ký tự đặc biệt và khoảng trắng
    province = re.sub(
        r"[-–]", " ", province
    )  # Case Thua Thien - Hue and Ba Ria - Vung Tau
    province = " ".join(province.split())

    return province.title()


def clean_province(province):
    # Bước 1: Loại bỏ dấu tiếng Việt
    outlier_char_map = {"đ": "d", "Đ": "D", "ð": "d", "Ð": "D"}

    province = remove_vietnamese_accent(province, outlier_char_map)

    # Bước 2: Loại bỏ các từ không cần thiết
    outlier_province_map = {
        "dac lak": "dak lak",
        "lau dai dac lac": "dak lak",
        "tan an": "long an",
    }
    outlier_provinces = ["ha tinh"]

    province = remove_unnecessary_words(
        province, outlier_province_map, outlier_provinces
    )

    return province


# Hàm kiểm tra chuỗi có chứa ký tự đặc biệt
def contains_special_chars(text, include_vietnamese=False):
    if include_vietnamese:
        vietnamese_chars = r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
        cleaned_text = re.sub(vietnamese_chars, "", text)
        return bool(re.search(r"[^a-zA-Z\s]", cleaned_text))
    return bool(re.search(r"[^a-zA-Z\s]", text))


# Hàm translate các province không phải tiếng việt
def translate_text(text, target_lang="vi"):
    translator = GoogleTranslator(target=target_lang)
    # Tự động phát hiện và dịch
    translated = translator.translate(text)
    time.sleep(0.5)

    return {"original": text, "translated": translated}


def process_province(text):
    if contains_special_chars(text, include_vietnamese=False):
        # Translate text with special characters
        result = translate_text(text)
        if isinstance(result, dict):
            translated = result["translated"]
            # Check if translated text still contains special characters
            return (
                "Others"
                if contains_special_chars(translated, include_vietnamese=True)
                else translated
            )
    return text


########################################################################################################

##################################### CHART 1: Bar Chart by Cities #####################################


is_data = False

if "df" not in st.session_state or st.session_state.df is None:
    st.info("Please upload data file in DataCleaning tab to continue.")
else:
    df = st.session_state.df
    is_data = True

if is_data:

    df["Province After"] = (
        df["Province"]
        .apply(clean_province)
        .apply(process_province)
        .apply(clean_province)
    )

    with open("province_mapping.json", "r", encoding="utf-8") as f:
        province_mapping = json.load(f)

    df["Province After"] = df["Province After"].map(province_mapping)

    # Calculate the count of each province
    province_counts = df["Province After"].value_counts().reset_index()
    province_counts.columns = ["Province", "Count"]

    # Tạo bar chart với Plotly
    fig = px.bar(
        province_counts,
        x="Province",
        y="Count",
        title="Distribution of Provinces",
        labels={"Province": "Province Name", "Count": "Number of Records"},
    )

    # Tùy chỉnh layout
    fig.update_layout(
        xaxis_tickangle=-45,
        height=600,
        margin=dict(b=100),  # Thêm margin bottom cho labels
        showlegend=False,
    )

    # Thêm text hiển thị số lượng trên mỗi cột
    fig.update_traces(
        texttemplate="%{y}",  # Hiển thị giá trị y
        textposition="outside",  # Đặt vị trí text ở trên cột
        textangle=0,  # Giữ text thẳng
    )

    # Hiển thị biểu đồ trong Streamlit
    st.plotly_chart(fig, use_container_width=True)
