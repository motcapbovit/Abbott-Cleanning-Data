import pandas as pd
from pandas.api.types import is_numeric_dtype
import streamlit as st
import re
import io
import json
import unicodedata
from datetime import datetime
from calendar import monthrange
from deep_translator import GoogleTranslator
import time

# Extra utilities
from streamlit_extras.add_vertical_space import add_vertical_space


##################################### SECTION 0-1: Define Functions ######################################


## SECTION 1 ##
def split_dataframe(df, chunk_size=20000):
    return [df[i : i + chunk_size] for i in range(0, len(df), chunk_size)]


## SECTION 3 ##


def update_CleanProvince():
    st.session_state.is_CleanProvince = not st.session_state.is_CleanProvince


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


## SECTION 5 ##


def extract_size(product_name):
    # Step 1: Replace special characters (except '.') with spaces
    cleaned_name = re.sub(r"[^\w\s\.]", " ", product_name)

    # Step 2: Split the cleaned name into individual words
    words = cleaned_name.split()

    # Step 3: Find any word that contains both digits and specified units
    for word in words:
        # Dummy coding: just for the case of SIMILAC 5G
        if word.lower() == "5g":
            continue

        # Check if the word contains both digits and either 'g', 'kg', or 'ml'
        if re.search(r"\d", word) and re.search(r"(g|kg|ml)", word, re.IGNORECASE):
            return word.lower()  # Return the matched word as size info
    return None  # Return None if no match is found


## SECTION 6 ##


def update_FSP():
    st.session_state.is_FSP = not st.session_state.is_FSP


def update_FORMAT():
    st.session_state.is_FORMAT = not st.session_state.is_FORMAT


def update_SUBTOTAL_USD():
    st.session_state.is_SUBTOTAL_USD = not st.session_state.is_SUBTOTAL_USD


def update_DATE():
    st.session_state.is_DATE = not st.session_state.is_DATE


def update_CLP_REGION():
    st.session_state.is_CLP_REGION = not st.session_state.is_CLP_REGION


def update_VOUCHER():
    st.session_state.is_VOUCHER = not st.session_state.is_VOUCHER


def determine_format_type(size):
    return (
        "Liquid Milk"
        if "ml" in str(size).lower()
        else "Milk Powder" if "g" in str(size).lower() else "No format"
    )


def extract_clp_region(name):
    # Dictionary cho phần trong ngoặc
    exception_in_brackets = {
        "q6": "HCM",
        "củ chi": "HCM",
        "hcm": "HCM",
        "tuy hòa": "Phú Yên",
        "tuy hoà": "Phú Yên",
    }

    # Dictionary cho phần ngoài ngoặc
    exception_outside = {
        "hn": "Hà Nội",
        "đn": "Đà Nẵng",
        "hcm": "HCM",
        "bách hóa sữa bột 2": "HCM",
    }

    # Kiểm tra phần trong ngoặc
    match = re.search(r"\((.*?)\)", name)
    if match:
        region_hint = match.group(1).strip().lower()
        for key, value in exception_in_brackets.items():
            if key in region_hint:
                return value
        # Nếu không khớp key nào, trả về phần trong ngoặc (chữ hoa đầu từ)
        return match.group(1).strip().title()

    # Nếu không có ngoặc, kiểm tra tên trực tiếp
    name_lower = name.lower()
    for key, value in exception_outside.items():
        if key in name_lower:
            return value

    return name


## SECTION 7 ##


def extract_deal_info(product_name, exclude_outliers, kol_outliers):
    # Kiểm tra KOL trước
    special_phrases = [
        kol.upper() for kol in kol_outliers if kol.upper() in product_name.upper()
    ]

    # Nếu tìm thấy KOL thì trả về ngay
    if special_phrases:
        return special_phrases[0]

    # Nếu không tìm thấy KOL, tiếp tục xử lý DEAL
    brackets = re.findall(r"\[(.*?)\]", product_name)

    # Loại bỏ các từ trong exclude_outliers
    brackets = [
        b
        for b in brackets
        if all(excl.lower() not in b.lower() for excl in exclude_outliers)
    ]

    # Tìm các cụm từ chứa DEAL
    deal_phrases = [phrase for phrase in brackets if "DEAL" in phrase.upper()]

    if deal_phrases:
        # Lấy thông tin sau từ DEAL
        deal_info = deal_phrases[0].split("DEAL")[1].strip().upper()
        return deal_info

    # Nếu không tìm thấy cả KOL và DEAL
    return "No KOLs"


## SECTION 8 ##


def extract_gift_name(product_name, list_outliers):
    # Kiểm tra outliers trước
    for key, value in list_outliers:
        if key in product_name:
            if "THẺ QUÀ TẶNG" in key:
                return value

            result = value.upper().replace("TẶNG", "").strip()
            return result

    # Nếu không có outlier nào, tiếp tục xử lý bình thường
    brackets = re.findall(r"\[(.*?)\]", product_name)

    # Kiểm tra các cụm từ trong ngoặc vuông để tìm chữ "tặng"
    for bracket in brackets:
        if "TẶNG" in bracket.upper():
            gift_part = bracket.upper().split("TẶNG", 1)[1]  # Lấy phần sau "tặng"
            return gift_part.strip()

    # Nếu không tìm thấy trong ngoặc vuông, tìm trực tiếp trong product_name
    if "TẶNG" in product_name.upper():
        gift_part = product_name.upper().split("TẶNG", 1)[1]  # Lấy phần sau "tặng"
        return gift_part.strip()

    # Nếu không tìm thấy gift nào
    return "NO GIFT"


## SECTION 9 ##


def get_default_periods(min_date, max_date):
    # Định nghĩa cấu hình cho từng period
    period_configs = {
        "Double Day": {"start_day": 1, "end_day": 13},  # Từ ngày 1 đến ngày 13
        "Mid Month": {"start_day": 14, "end_day": 20},  # Từ ngày 14 đến ngày 20
        "Pay Day": {"start_day": 21, "end_day": None},  # Từ ngày 21 đến cuối tháng
    }

    periods = []
    current_date = min_date.replace(
        day=1
    )  # Bắt đầu từ ngày đầu tiên của tháng min_date

    while current_date <= max_date:
        # Lấy ngày cuối cùng của tháng hiện tại
        _, last_day = monthrange(current_date.year, current_date.month)
        month_end = current_date.replace(day=last_day)

        # Nếu tháng hiện tại vượt quá max_date, điều chỉnh month_end
        if month_end > max_date:
            month_end = max_date

        # Duyệt qua từng period trong cấu hình
        for period_name, config in period_configs.items():
            start_day = config["start_day"]
            end_day = (
                config["end_day"] if config["end_day"] else last_day
            )  # Nếu end_day là None, lấy cuối tháng

            # Tính ngày bắt đầu và kết thúc của period
            period_start = current_date.replace(day=start_day)
            period_end = current_date.replace(day=min(end_day, month_end.day))

            # Chỉ thêm period nếu nó nằm trong khoảng min_date và max_date
            if (
                period_start <= max_date
                and period_end >= min_date
                and period_start <= period_end
            ):
                periods.append((period_name, period_start, period_end))

        # Chuyển sang tháng tiếp theo
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    return periods


## SECTION 10 ##


@st.cache_data
def convert_df_to_csv(df):
    """Convert dataframe to CSV format"""
    return df.to_csv(index=False).encode("utf-8-sig")


# @st.cache_data
# def convert_df_to_excel(df):
#     """Convert dataframe to Excel format"""
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
#         df.to_excel(writer, sheet_name="Sheet1", index=False)
#         # Auto-adjust columns' width
#         worksheet = writer.sheets["Sheet1"]
#         for i, col in enumerate(df.columns):
#             # Find the maximum length of the column
#             column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
#             worksheet.set_column(i, i, column_len)

#     output.seek(0)
#     return output.getvalue()


@st.cache_data
def convert_df_to_excel(df):
    """Convert dataframe to Excel format"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        # Create center alignment format
        center_format = workbook.add_format({"align": "center"})

        # Find Brand column index
        brand_col_idx = list(df.columns).index("Brand")

        # Auto-adjust columns' width
        for i, col in enumerate(df.columns):
            # Find the maximum length of the column
            column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2

            # Apply center format to Brand column, normal width adjustment for others
            if i == brand_col_idx:
                worksheet.set_column(i, i, column_len, center_format)
            else:
                worksheet.set_column(i, i, column_len)

    # Reset pointer to the start of BytesIO object
    output.seek(0)
    return output.getvalue()


def get_timestamp_string():
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


########################################################################################################

#################################### SECTION 0-2: Define Session State ###################################


list_component_none = [
    "upload_file",
    "upload_file_name",
    "df",
    "default_numeric_columns",
    "default_string_columns",
    "default_brand_names",
    "default_brand_new_option",
    "default_outliers_size",
    "default_size_new_option",
    "default_exclude_outliers",
    "default_exclude_new_option",
    "default_kol_outliers",
    "default_kol_new_option",
]

list_component_bool_true = [
    "is_FORMAT",
    "is_FSP",
    "is_SUBTOTAL_USD",
    "is_DATE",
    "is_CLP_REGION",
    "is_VOUCHER",
]
list_component_bool_false = ["is_CleanProvince"]

list_component_list = ["periods"]

# Khởi tạo các components
for component in list_component_none:
    if component not in st.session_state:
        st.session_state[component] = None

for component in list_component_bool_true:
    if component not in st.session_state:
        st.session_state[component] = True

for component in list_component_bool_false:
    if component not in st.session_state:
        st.session_state[component] = False

for component in list_component_list:
    if component not in st.session_state:
        st.session_state[component] = []

if "gifts" not in st.session_state:
    st.session_state["gifts"] = [
        ("TĂNG KHĂN CHOÀNG TẮM", "TẶNG KHĂN CHOÀNG TẮM"),
        ("TẶNG GHÉ SOFA HƯƠU VÀNG", "TẶNG GHẾ SOFA HƯƠU VÀNG"),
        (
            "TẶNG LY THUỶ TINH ENSURE GOLD MỚI CẢI TIẾN DẠNG BỘT HƯƠNG VANI 400G",
            "TẶNG LY THUỶ TINH",
        ),
        (
            "TẶNG ẤM ĐUN COMBO 3 LON SỮA ENSURE GOLD CẢI TIẾN MỚI DẠNG BỘT HƯƠNG VANI 850G",
            "TẶNG ẤM ĐUN",
        ),
        (
            "TẶNG LY THỦY TINH LON ENSURE GOLD CẢI TIẾN MỚI DẠNG BỘT HƯƠNG VANI 400G",
            "TẶNG LY THỦY TINH",
        ),
        (
            "TẶNG CÂN COMBO 2 LON SỮA ENSURE GOLD CẢI TIẾN MỚI DẠNG BỘT HƯƠNG VANI 850G",
            "TẶNG CÂN",
        ),
        (
            "TẶNG BÌNH GIỮ NHIỆT LON ENSURE GOLD CẢI TIẾN MỚI DẠNG BỘT HƯƠNG VANI 850G",
            "TẶNG BÌNH GIỮ NHIỆT",
        ),
        (
            "[DEAL HÈ] [DATE TỪ 01.01.2025 TRỞ ĐI] 1 Lon Thực phẩm Dinh Dưỡng Sữa Bột PediaSure 400g, Túi Đeo Chéo",
            "TÚI ĐEO CHÉO",
        ),
        ("THẺ QUÀ TẶNG", "THẺ QUÀ TẶNG"),
    ]


########################################################################################################

######################################## SECTION 1: Upload File ########################################

# Title and description
st.title(
    "Abbott Cleaning Data: A data processing toolkit for TikTok Seller Center analytics"
)

st.header(
    "Upload File",
    divider="gray",
)

is_data = False

allowed_types = ["csv", "xlsx"]
upload_file = st.file_uploader("CHOOSE YOUR DATA FILE (CSV FORMAT)", type=allowed_types)

if upload_file is None and st.session_state.upload_file is None:
    st.info("Upload your data file to continue.")
    print("upload_file is None and st.session_state.upload_file is None")

elif upload_file is None and st.session_state.upload_file is not None:
    file_buffer = st.session_state.upload_file

    st.info("Processing File: " + st.session_state.upload_file_name)
    print("upload_file is None and st.session_state.upload_file is not None")
    is_data = True

elif upload_file is not None and st.session_state.upload_file is None:
    file_name = upload_file.name
    file_buffer = upload_file.read()

    st.session_state.upload_file_name = file_name
    st.session_state.upload_file = file_buffer

    st.info("Processing File: " + st.session_state.upload_file_name)
    print("upload_file is not None and st.session_state.upload_file is None")
    is_data = True

elif upload_file is not None and st.session_state.upload_file is not None:
    st.session_state.upload_file = None
    st.session_state.upload_file_name = None

    file_name = upload_file.name
    file_buffer = upload_file.read()

    st.session_state.upload_file_name = file_name
    st.session_state.upload_file = file_buffer

    st.info("Processing File: " + st.session_state.upload_file_name)
    print("upload_file is not None and st.session_state.upload_file is not None")
    is_data = True

if is_data:
    # Read the original data
    file_extension = st.session_state.upload_file_name.split(".")[-1].lower()

    if file_extension == "csv":
        df_original = pd.read_csv(io.BytesIO(file_buffer), low_memory=False)
    else:  # xlsx or xls
        df_original = pd.read_excel(io.BytesIO(file_buffer))

    headers_list = df_original.columns.tolist()

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df_original)

    ####################################################################################################

    ###################################### SECTION 2: Cast Columns #####################################

    add_vertical_space(3)
    st.header(
        "Cast Columns",
        divider="gray",
    )

    # Divide the layout
    col11, col21 = st.columns(2)

    with col11:
        st.subheader("**String Format**")

        # Specified default columns
        string_columns = [
            "Order ID",
            "Seller SKU",
            "SKU ID",
            "Product Name",
            "Package ID",
        ]

        # Khởi tạo session state trước
        default_string_columns = (
            string_columns
            if st.session_state.default_string_columns is None
            else st.session_state.default_string_columns
        )

        # Identify columns that need to be casted as string format
        columns_cast_string = st.multiselect(
            label="**CHOOSE COLUMNS THAT NEEDED TO BE CASTED AS :red[STRING] FORMAT**",
            options=headers_list,
            default=default_string_columns,
        )

        st.session_state.default_string_columns = columns_cast_string

        # Create a dictionary for dtype by setting each column in the list to str
        dtype_dict = {col: str for col in columns_cast_string}

    with col21:
        st.subheader("**Numeric Format**")

        # Specified default columns
        numeric_columns = list(
            df_original.loc[:, "SKU Unit Original Price":"Order Refund Amount"].columns
        )

        # Khởi tạo session state trước
        default_numeric_columns = (
            numeric_columns
            if st.session_state.default_numeric_columns is None
            else st.session_state.default_numeric_columns
        )

        # Identify columns that need to be casted as numeric format
        columns_cast_numeric = st.multiselect(
            label="**CHOOSE COLUMNS THAT NEEDED TO BE CASTED AS :red[NUMERIC] FORMAT**",
            options=headers_list,
            default=default_numeric_columns,
        )

        # Cập nhật session state
        st.session_state.default_numeric_columns = columns_cast_numeric

    # Fully read data
    file_extension = st.session_state.upload_file_name.split(".")[-1].lower()

    if file_extension == "csv":
        df = pd.read_csv(io.BytesIO(file_buffer), low_memory=False, dtype=dtype_dict)
    else:  # xlsx or xls
        df = pd.read_excel(io.BytesIO(file_buffer), dtype=dtype_dict)

    df_chunks = split_dataframe(df)

    st.session_state.df_chunks = df_chunks
    st.session_state.total_chunks = len(df_chunks)

    # Apply the cleaning transformation to each chunk
    cast_type_chunks = st.session_state.df_chunks

    for chunk in cast_type_chunks:
        # Cast numeric columns
        for col in columns_cast_numeric:
            if not is_numeric_dtype(chunk[col]):
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

        # Fill NaN with 0 in numeric columns
        chunk[columns_cast_numeric] = chunk[columns_cast_numeric].fillna(0)

        # Remove special characters in string columns (e.g., tab characters)
        chunk = chunk.apply(
            lambda x: x.str.replace("\t", "", regex=False) if x.dtype == "object" else x
        )

    # Update processed chunks to session_state
    st.session_state.df_chunks = cast_type_chunks

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(st.session_state.df_chunks[0])

    ####################################################################################################

    ##################################### SECTION 3: Clean Columns ####################################

    add_vertical_space(3)
    st.header(
        "Clean Columns",
        divider="gray",
    )

    CleanProvince = st.checkbox(
        "**CLEAN :red[PROVINCE] COLUMN**",
        value=st.session_state.is_CleanProvince,
        on_change=update_CleanProvince,
    )

    if CleanProvince:
        # Load mapping once
        with open("province_mapping.json", "r", encoding="utf-8") as f:
            province_mapping = json.load(f)

        cleaned_chunks = st.session_state.df_chunks

        for chunk in cleaned_chunks:
            # Clean Province column step-by-step
            cleaned_province = (
                chunk["Province"]
                .apply(clean_province)
                .apply(process_province)
                .apply(clean_province)
            )

            # Map using external mapping
            chunk["Clean Province"] = cleaned_province.map(province_mapping)

        # Update session state
        st.session_state.df_chunks = cleaned_chunks

    # Preview chunk đầu tiên
    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(st.session_state.df_chunks[0])

    ####################################################################################################

    ##################################### SECTION 4: Extract Brands ####################################

    add_vertical_space(3)
    st.header(
        "Add Attributes",
        divider="gray",
    )

    # Divide the layout
    col12, col22 = st.columns(2)

    with col12:
        st.subheader("**Brand Names**")

        # Specified default brands
        brand_names = [
            "Grow",
            "PediaSure",
            "Ensure",
            "Similac",
            "Glucerna",
            "ProSure",
        ]

        default_brand_names = (
            brand_names[:5]
            if st.session_state.default_brand_names is None
            else st.session_state.default_brand_names
        )

        extract_brands_list = st.multiselect(
            label="**CHOOSE BRAND NAME(S) THAT NEEDED TO BE EXTRACTED FROM PRODUCT NAMES**",
            options=brand_names,
            default=default_brand_names,
        )

        extract_brands_list_copy = extract_brands_list.copy()
        st.session_state.default_brand_names = extract_brands_list_copy

        default_brand_new_option = (
            ""
            if st.session_state.default_brand_new_option is None
            else st.session_state.default_brand_new_option
        )

        brand_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR BRAND NAMES (SEPARATE BY COMMAS):",
            value=default_brand_new_option,
        )
        st.session_state.default_brand_new_option = brand_new_option

        if brand_new_option:
            new_options_list = [
                option.strip()
                for option in brand_new_option.split(",")
                if option.strip()
            ]
            extract_brands_list.extend(new_options_list)

        add_vertical_space(1)
        st.write(
            "##### **Selected brand names:**\n"
            + "\n".join(f"- {option}" for option in extract_brands_list)
        )

        # Brand map: lowercase to original
        brand_map = {brand.lower(): brand for brand in extract_brands_list}
        pattern = "|".join(brand_map.keys())  # e.g., "grow|ensure|glucerna"

        # Process each chunk
        brand_extract_chunks = st.session_state.df_chunks

        for chunk in brand_extract_chunks:
            chunk["Brand"] = (
                chunk["Product Name"]
                .str.lower()
                .str.extract(f"({pattern})", expand=False)
                .map(brand_map)
            )

        # Update chunks and full df
        st.session_state.df_chunks = brand_extract_chunks

    # Preview chunk đầu tiên
    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(st.session_state.df_chunks[0])

    ####################################################################################################

    ##################################### SECTION 5: Extract Sizes #####################################

    with col22:
        st.subheader("**Product Sizes**")

        # Default outliers
        outliers_size = [
            "COMBO 4 LỐC (24 CHAI) SỮA NƯỚC GLUCERNA HƯƠNG VANI",
            "COMBO 5 LỐC (30 CHAI) SỮA NƯỚC GLUCERNA HƯƠNG VANI",
            "1 THÙNG 24 CHAI SỮA NƯỚC GLUCERNA HƯƠNG VANI",
            "[TẶNG BÌNH GIỮ NHIỆT] COMBO 24 CHAI SỮA NƯỚC GLUCERNA HƯƠNG VANI",
        ]

        default_outliers_size = (
            outliers_size
            if st.session_state.default_outliers_size is None
            else st.session_state.default_outliers_size
        )

        outliers_size_list = st.multiselect(
            label="**SPECIFY OUTLIERS FOR THE PROCESS OF EXTRACTING PRODUCT SIZE**",
            options=outliers_size,
            default=default_outliers_size,
        )

        outliers_size_list_copy = outliers_size_list.copy()
        st.session_state.default_outliers_size = outliers_size_list_copy

        default_size_new_option = (
            ""
            if st.session_state.default_size_new_option is None
            else st.session_state.default_size_new_option
        )

        size_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR SIZES (SEPARATE BY COMMAS):",
            value=default_size_new_option,
        )

        st.session_state.default_size_new_option = size_new_option

        if size_new_option:
            new_options_list = [
                option.strip()
                for option in size_new_option.split(",")
                if option.strip()
            ]
            outliers_size_list.extend(new_options_list)

        add_vertical_space(1)
        st.write(
            "##### **Selected size outliers:**\n"
            + "\n".join(f"- {option}" for option in outliers_size_list)
        )

        # Apply to each chunk
        updated_chunks = st.session_state.df_chunks

        for chunk in updated_chunks:
            # Extract size from Product Name
            chunk["Size"] = chunk["Product Name"].apply(extract_size)

            # Override missing sizes for outliers
            chunk.loc[
                chunk["Product Name"].isin(outliers_size_list) & chunk["Size"].isna(),
                "Size",
            ] = "220ml"

        # Cập nhật session_state
        st.session_state.df_chunks = updated_chunks

    # Preview chunk đầu tiên
    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(st.session_state.df_chunks[0])

    ####################################################################################################

    #################################### SECTION 6: Add NEW COLUMNS ####################################

    st.divider()

    # Divide the layout
    col13, col23 = st.columns(2)

    with col13:
        st.subheader("**Calculated Columns**")

        updated_chunks = st.session_state.df_chunks

        FSP = st.checkbox(
            "**ADD :red[FSP] COLUMN**",
            value=st.session_state.is_FSP,
            on_change=update_FSP,
        )

        if FSP:
            for i, chunk in enumerate(updated_chunks):
                chunk["FSP"] = (
                    chunk["SKU Subtotal Before Discount"] - chunk["SKU Seller Discount"]
                ) / chunk["Quantity"]

            # Cập nhật vào session_state
            st.session_state.df_chunks = updated_chunks

        FORMAT = st.checkbox(
            "**ADD :red[FORMAT] COLUMN**",
            value=st.session_state.is_FORMAT,
            on_change=update_FORMAT,
        )

        if FORMAT:
            for i, chunk in enumerate(updated_chunks):
                chunk["Format"] = chunk["Size"].apply(determine_format_type)

            # Cập nhật vào session_state
            st.session_state.df_chunks = updated_chunks

        SUBTOTAL_USD = st.checkbox(
            "**ADD :red[SKU SUBTOTAL AFTER DISCOUNT (USD)] COLUMN**",
            value=st.session_state.is_SUBTOTAL_USD,
            on_change=update_SUBTOTAL_USD,
        )

        if SUBTOTAL_USD:
            for i, chunk in enumerate(updated_chunks):
                chunk["SKU Subtotal After Discount (USD)"] = (
                    chunk["SKU Subtotal After Discount"] / 25800
                ).round(2)

            # Cập nhật vào session_state
            st.session_state.df_chunks = updated_chunks

        DATE = st.checkbox(
            "**ADD :red[DATE TIME] COLUMNS**",
            value=st.session_state.is_DATE,
            on_change=update_DATE,
        )

        if DATE:
            for i, chunk in enumerate(updated_chunks):
                chunk["Created Time"] = pd.to_datetime(
                    chunk["Created Time"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
                )
                chunk["Created Date"] = chunk["Created Time"].dt.date
                chunk["Created Year Month"] = chunk["Created Time"].dt.strftime("%Y-%m")

            # Cập nhật vào session_state
            st.session_state.df_chunks = updated_chunks

        CLP_REGION = st.checkbox(
            "**ADD :red[CLP REGION] COLUMNS**",
            value=st.session_state.is_CLP_REGION,
            on_change=update_CLP_REGION,
        )

        if CLP_REGION:
            for i, chunk in enumerate(updated_chunks):
                chunk["Warehouse Region"] = chunk["Warehouse Name"].apply(
                    extract_clp_region
                )

            # Cập nhật vào session_state
            st.session_state.df_chunks = updated_chunks

        VOUCHER = st.checkbox(
            "**ADD :red[VOUCHER] COLUMN**",
            value=st.session_state.is_VOUCHER,
            on_change=update_VOUCHER,
        )

        if VOUCHER:
            for i, chunk in enumerate(updated_chunks):
                chunk["Voucher"] = chunk["SKU Platform Discount"] / (
                    chunk["SKU Subtotal Before Discount"] - chunk["SKU Seller Discount"]
                )

            # Cập nhật vào session_state
            st.session_state.df_chunks = updated_chunks

        # Cập nhật vào session_state
        st.session_state.df_chunks = updated_chunks

    # Preview chunk đầu tiên
    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(st.session_state.df_chunks[0])

    ####################################################################################################

    ################################### SECTION 7: Add KOL Extraction ##################################

    st.divider()
    st.subheader("**KOL Extraction**")

    col14, col24 = st.columns(2)

    with col14:
        exclude_outliers = ["Hot Deal", "Deal Hè", "Deal E2E"]

        default_exclude_outliers = (
            exclude_outliers
            if st.session_state.default_exclude_outliers is None
            else st.session_state.default_exclude_outliers
        )

        exclude_outliers_list = st.multiselect(
            label="**EXCLUDE OUTLIERS**",
            options=exclude_outliers,
            default=default_exclude_outliers,
        )

        st.session_state.default_exclude_outliers = exclude_outliers_list.copy()

        default_exclude_new_option = (
            ""
            if st.session_state.default_exclude_new_option is None
            else st.session_state.default_exclude_new_option
        )

        exclude_outliers_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR EXCLUDE OUTLIERS (SEPARATE BY COMMAS):",
            value=default_exclude_new_option,
        )

        st.session_state.default_exclude_new_option = exclude_outliers_new_option

        if exclude_outliers_new_option:
            new_options = [
                x.strip() for x in exclude_outliers_new_option.split(",") if x.strip()
            ]
            exclude_outliers_list.extend(new_options)

        add_vertical_space(1)
        st.write(
            "##### **Selected exclude outliers:**\n"
            + "\n".join(f"- {option}" for option in exclude_outliers_list)
        )

    with col24:
        kol_outliers = ["Quyền Leo", "Hằng Du Mục"]

        default_kol_outliers = (
            kol_outliers
            if st.session_state.default_kol_outliers is None
            else st.session_state.default_kol_outliers
        )

        kol_outliers_list = st.multiselect(
            label="**KOL OUTLIERS**",
            options=kol_outliers,
            default=default_kol_outliers,
        )

        st.session_state.default_kol_outliers = kol_outliers_list.copy()

        default_kol_new_option = (
            ""
            if st.session_state.default_kol_new_option is None
            else st.session_state.default_kol_new_option
        )

        kol_outliers_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR KOL OUTLIERS (SEPARATE BY COMMAS):",
            value=default_kol_new_option,
        )

        st.session_state.default_kol_new_option = kol_outliers_new_option

        if kol_outliers_new_option:
            new_options = [
                x.strip() for x in kol_outliers_new_option.split(",") if x.strip()
            ]
            kol_outliers_list.extend(new_options)

        add_vertical_space(1)
        st.write(
            "##### **Selected KOL outliers:**\n"
            + "\n".join(f"- {option}" for option in kol_outliers_list)
        )

    # Áp dụng xử lý lên từng chunk
    kol_chunks = st.session_state.df_chunks

    for chunk in kol_chunks:
        chunk["KOL"] = chunk["Product Name"].apply(
            lambda x: extract_deal_info(x, exclude_outliers_list, kol_outliers_list)
        )
        updated_chunks.append(chunk)

    # Cập nhật lại session state
    st.session_state.df_chunks = updated_chunks

    # Preview chunk đầu tiên
    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(st.session_state.df_chunks[0])

    ####################################################################################################

    ################################### SECTION 8: Add Gift Extraction ##################################

    st.divider()
    st.subheader("**Gift Extraction**")

    form_submitted = False

    # Add period form
    with st.form("add_gift_form"):
        col15, col25 = st.columns(2)
        with col15:
            gift_key = st.text_input("Gift Outlier Key")
        with col25:
            gift_value = st.text_input("Gift Outlier Value")

        submitted = st.form_submit_button("Add Gift Outlier")

        if submitted and not gift_key:
            st.error("Please enter gift outlier key!")
        elif submitted and not gift_value:
            st.error("Please enter gift outlier value!")
        elif submitted and gift_key and gift_value:
            form_submitted = True

    if form_submitted:
        gift = (gift_key, gift_value)
        existing_gift_keys = [g[0] for g in st.session_state.gifts]

        if gift in st.session_state.gifts:
            st.warning("This gift outlier already exists!")
        elif gift[0] in existing_gift_keys:
            st.warning("This gift outlier key already exists!")
        else:
            st.session_state.gifts.append(gift)
            st.success("Gift outlier added successfully!")

    ## Display and manage gifts
    if st.session_state.gifts:
        st.write("##### Current Gift Outliers")

        col16, col26 = st.columns(2)
        total_gifts = len(st.session_state.gifts)
        gifts_per_col = (total_gifts + 1) // 2

        for i, (key, value) in enumerate(st.session_state.gifts):
            current_col = col16 if i < gifts_per_col else col26
            with current_col:
                gift_container = st.container()
                with gift_container:
                    col161, col261 = st.columns([3, 1])
                    with col161:
                        st.write(f"Gift {i+1}\n- Key : {key}\n- Value: {value}")
                    with col261:
                        if st.button(f"Remove", key=f"remove_gift_{i}"):
                            st.session_state.gifts.pop(i)
                            st.rerun()

        ## Process and download section
        if st.button("Process All Gifts"):
            gift_chunks = st.session_state.df_chunks

            for chunk in gift_chunks:
                chunk["Gift"] = chunk["Product Name"].apply(
                    lambda x: extract_gift_name(x, st.session_state.gifts)
                )

            # Cập nhật lại session state
            st.session_state.df_chunks = gift_chunks

            add_vertical_space(1)
            with st.expander("**Dataframe Preview**"):
                st.dataframe(st.session_state.df_chunks[0])

        if st.button("Clear All", key="remove_all_gifts"):
            st.session_state.gifts = []
            st.rerun()

    ####################################################################################################

    ##################################### SECTION 9: Divide Periods ####################################

    add_vertical_space(3)
    st.header(
        "Divide Periods",
        divider="gray",
    )

    create_time_chunks = st.session_state.df_chunks

    for i, chunk in enumerate(create_time_chunks):
        chunk["Created Time"] = pd.to_datetime(
            df["Created Time"], format="%d/%m/%Y %H:%M:%S"
        )

    st.session_state.df_chunks = create_time_chunks

    # Tính min và max date toàn bộ chunks
    all_created_times = pd.concat(
        [chunk["Created Time"] for chunk in st.session_state.df_chunks],
        ignore_index=True,
    )
    min_date = all_created_times.min().date()
    max_date = all_created_times.max().date()

    tab1, tab2, tab3 = st.tabs(["Add Default", "Add Manually", "Add by File"])

    with tab1:
        add_defaults = st.button("Add Default Periods")

        if add_defaults:
            default_periods = get_default_periods(min_date, max_date)
            new_periods_added = 0

            for period in default_periods:
                if period not in st.session_state.periods:
                    # existing_names = [p[0] for p in st.session_state.periods]
                    existing_dates = [(p[1], p[2]) for p in st.session_state.periods]

                    if period in st.session_state.periods:
                        st.warning(
                            f"Period ({period[1].strftime('%Y-%m-%d')} to {period[2].strftime('%Y-%m-%d')}) already exists!"
                        )
                    elif (period[1], period[2]) in existing_dates:
                        st.warning(
                            f"Period ({period[1].strftime('%Y-%m-%d')} to {period[2].strftime('%Y-%m-%d')}) already exists!"
                        )
                    elif period not in st.session_state.periods:
                        # Check for overlapping periods
                        has_overlap = False
                        for existing_start, existing_end in existing_dates:
                            if not (
                                period[2] < pd.Timestamp(existing_start).date()
                                or period[1] > pd.Timestamp(existing_end).date()
                            ):
                                has_overlap = True
                                break

                        if has_overlap:
                            st.warning(
                                f"Period ({period[1].strftime('%Y-%m-%d')} to {period[2].strftime('%Y-%m-%d')}) overlaps with an existing period!"
                            )
                        else:
                            st.session_state.periods.append(period)
                            new_periods_added += 1

            if new_periods_added > 0:
                st.success(f"Added {new_periods_added} default periods successfully!")

    with tab2:

        form_submitted = False

        # Add period form
        with st.form("add_period_form"):
            col17, col27, col37 = st.columns(3)
            with col17:
                period_name = st.text_input("Period Name")
            with col27:
                start_date = st.date_input(
                    "Start Date", value=min_date, min_value=min_date, max_value=max_date
                )
            with col37:
                end_date = st.date_input(
                    "End Date", value=max_date, min_value=min_date, max_value=max_date
                )

            submitted = st.form_submit_button("Add Period")

            if submitted and not period_name:
                st.error("Please enter period name!")
                print(st.session_state.periods)
            elif submitted and start_date and end_date:
                form_submitted = True

        if form_submitted:
            if start_date <= end_date:
                period = (period_name, start_date, end_date)
                # existing_names = [p[0] for p in st.session_state.periods]
                existing_dates = [(p[1], p[2]) for p in st.session_state.periods]

                if period in st.session_state.periods:
                    st.warning("This period already exists!")
                elif (start_date, end_date) in existing_dates:
                    st.warning("This pair of start and end date already exists!")
                else:
                    # Check for overlapping periods
                    has_overlap = False
                    for existing_start, existing_end in existing_dates:
                        if not (
                            end_date < pd.Timestamp(existing_start).date()
                            or start_date > pd.Timestamp(existing_end).date()
                        ):
                            has_overlap = True
                            break

                    if has_overlap:
                        st.warning("This period overlaps with an existing period!")
                    else:
                        st.session_state.periods.append(period)
                        st.success("Period added successfully!")

            else:
                st.error("End date must be after start date!")

    with tab3:
        upload_file = st.file_uploader(
            "CHOOSE YOUR PERIOD DATA FILE (XLSX FORMAT)", type="xlsx"
        )
        is_period_data = False

        st.markdown(
            "You can download a sample file [here](https://docs.google.com/spreadsheets/u/0/d/1BJ2DSfOU1p75r1lF7RWB0QBs6UL9ln28W56UB-fT2oM/export?format=xlsx)"
        )

        if upload_file:
            period_df = pd.read_excel(upload_file)

            period_df["start_date"] = pd.to_datetime(
                period_df["start_date"], format="%d/%m/%Y"
            )
            period_df["end_date"] = pd.to_datetime(
                period_df["end_date"], format="%d/%m/%Y"
            )
            min_date = pd.Timestamp(min_date)
            max_date = pd.Timestamp(max_date)

            # Add new periods
            new_periods_added = 0

            for index, row in period_df.iterrows():
                # Phase 1: Check for null values first
                if row.isnull().any():
                    st.warning(f"Row {index + 1} contains null values - skipping")
                    continue

                start_date = pd.to_datetime(row["start_date"], format="%d/%m/%Y")
                end_date = pd.to_datetime(row["end_date"], format="%d/%m/%Y")
                min_date = pd.Timestamp(min_date)
                max_date = pd.Timestamp(max_date)

                # Phase 2: Check start_date before end_date
                if start_date > end_date:
                    st.warning(f"Row {index + 1}: End date must be after start date!")
                    continue

                # Phase 3: Check date range
                # if start_date < min_date or end_date > max_date:
                #     st.warning(
                #         f"Row {index + 1}: Dates must be between {min_date.strftime('%Y-%m-%d')} and {max_date.strftime('%Y-%m-%d')}!"
                #     )
                #     continue

                # Process valid period
                period = (row["period_name"], start_date, end_date)
                if period not in st.session_state.periods:
                    existing_dates = [(p[1], p[2]) for p in st.session_state.periods]

                    if period in st.session_state.periods:
                        st.warning(
                            f"Period ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}) already exists!"
                        )
                    elif (start_date, end_date) in existing_dates:
                        st.warning(
                            f"Period ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}) already exists!"
                        )
                    else:
                        # Check for overlapping periods
                        has_overlap = False
                        for existing_start, existing_end in existing_dates:
                            if not (
                                end_date < pd.Timestamp(existing_start)
                                or start_date > pd.Timestamp(existing_end)
                            ):
                                has_overlap = True
                                break

                        if has_overlap:
                            st.warning(
                                f"Period ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}) overlaps with an existing period!"
                            )
                        else:
                            st.session_state.periods.append(period)
                            new_periods_added += 1

            if new_periods_added > 0:
                st.success(f"Added {new_periods_added} periods successfully!")

    ## Display and manage periods
    if st.session_state.periods:
        st.write("##### Current Periods")

        # Tạo 2 cột chính
        col18, col28 = st.columns(2)

        # Tính số period cho mỗi cột
        total_periods = len(st.session_state.periods)
        periods_per_col = (total_periods + 1) // 2  # Làm tròn lên

        for i, (name, start, end) in enumerate(st.session_state.periods):
            # Xác định period này thuộc cột nào
            current_col = col18 if i < periods_per_col else col28

            # Tạo container cho period
            with current_col:
                period_container = st.container()
                with period_container:
                    col181, col281 = st.columns(
                        [3, 1]
                    )  # Chia container thành 2 phần cho nội dung và nút remove

                    with col181:
                        st.write(
                            f"- Period {i+1}: {name} ({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})"
                        )
                    with col281:
                        if st.button(f"Remove", key=f"remove_period_{i}"):
                            st.session_state.periods.pop(i)
                            st.rerun()

        if st.button("Process All Periods"):
            try:
                updated_chunks = st.session_state.df_chunks

                for chunk in updated_chunks:
                    chunk["Period"] = "No Period"

                    for name, start_date, end_date in st.session_state.periods:
                        start_dt = pd.to_datetime(start_date).date()
                        end_dt = pd.to_datetime(end_date).date()

                        mask = (chunk["Created Date"] >= start_dt) & (
                            chunk["Created Date"] <= end_dt
                        )
                        chunk.loc[mask, "Period"] = name

                # Update session state
                st.session_state.df_chunks = updated_chunks

            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
                if "Created Time" in str(e):
                    st.error(
                        "Date format error detected. Please ensure your dates are in DD/MM/YYYY HH:MM:SS format"
                    )

            add_vertical_space(1)
            with st.expander("**Dataframe Preview**"):
                st.dataframe(st.session_state.df_chunks[0])

        # Add clear all button
        if st.button("Clear All", key="remove_all_periods"):
            st.session_state.periods = []
            st.rerun()

    ####################################################################################################

    ######################################## SECTION 10: Download #######################################

    add_vertical_space(3)
    st.header(
        "Download",
        divider="gray",
    )

    # Dummy code for prettier layout
    col15, col25, col35, col45, col55, col65 = st.columns(6)
    timestamp = get_timestamp_string()

    chunks = st.session_state.df_chunks
    df = pd.concat(chunks, ignore_index=True)

    with col35:
        # CSV Download
        csv_data = convert_df_to_csv(df)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"data_export_{timestamp}.csv",
            mime="text/csv",
            key="download-csv",
        )

    with col45:
        # Excel Download
        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=f"data_export_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download-excel",
        )


# # Create tabs for CSV and Excel downloads
# tab1, tab2 = st.tabs(["CSV Downloads", "Excel Downloads"])

# with tab1:
#     st.write("### Download CSV Files")
#     for i, (start_date, end_date) in enumerate(
#         st.session_state.periods, start=1
#     ):
#         # Convert dates to datetime with time
#         start_dt = pd.to_datetime(start_date)
#         end_dt = pd.to_datetime(end_date) + pd.Timedelta(
#             hours=23, minutes=59, seconds=59
#         )

#         # Filter DataFrame
#         period_df = df[
#             (df["Created Time"] >= start_dt)
#             & (df["Created Time"] <= end_dt)
#         ].sort_values(by="Created Time")

#         # Create download button
#         if not period_df.empty:
#             csv_data = convert_df_to_csv(period_df)
#             file_name = f"Data_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
#             st.download_button(
#                 label=f"📥 Download Period {i} ({len(period_df)} rows)",
#                 data=csv_data,
#                 file_name=file_name,
#                 mime="text/csv",
#                 key=f"csv_{i}",
#             )
#         else:
#             st.warning(f"No data found for period {i}")

# with tab2:
#     st.write("### Download Excel Files")
#     for i, (start_date, end_date) in enumerate(
#         st.session_state.periods, start=1
#     ):
#         # Convert dates to datetime with time
#         start_dt = pd.to_datetime(start_date)
#         end_dt = pd.to_datetime(end_date) + pd.Timedelta(
#             hours=23, minutes=59, seconds=59
#         )

#         # Filter DataFrame
#         period_df = df[
#             (df["Created Time"] >= start_dt)
#             & (df["Created Time"] <= end_dt)
#         ].sort_values(by="Created Time")

#         # Create download button
#         if not period_df.empty:
#             excel_data = convert_df_to_excel(period_df)
#             file_name = f"Data_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
#             st.download_button(
#                 label=f"📥 Download Period {i} ({len(period_df)} rows)",
#                 data=excel_data,
#                 file_name=file_name,
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 key=f"excel_{i}",
#             )
#         else:
#             st.warning(f"No data found for period {i}")
