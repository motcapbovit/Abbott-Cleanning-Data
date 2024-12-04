import pandas as pd
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


def extract_size(product_name):
    # Step 1: Replace special characters (except '.') with spaces
    cleaned_name = re.sub(r"[^\w\s\.]", " ", product_name)

    # Step 2: Split the cleaned name into individual words
    words = cleaned_name.split()

    # Step 3: Find any word that contains both digits and specified units
    for word in words:
        if word.lower() == "5g":
            continue

        # Check if the word contains both digits and either 'g', 'kg', or 'ml'
        if re.search(r"\d", word) and re.search(r"(g|kg|ml)", word, re.IGNORECASE):
            return word.lower()  # Return the matched word as size info
    return None  # Return None if no match is found


@st.cache_data
def convert_df_to_csv(df):
    """Convert dataframe to CSV format"""
    return df.to_csv(index=False).encode("utf-8-sig")


@st.cache_data
def convert_df_to_excel(df):
    """Convert dataframe to Excel format"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)
        # Auto-adjust columns' width
        worksheet = writer.sheets["Sheet1"]
        for i, col in enumerate(df.columns):
            # Find the maximum length of the column
            column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)

    output.seek(0)
    return output.getvalue()


def get_timestamp_string():
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def determine_format_type(size):
    return (
        "LIQ"
        if "ml" in str(size).lower()
        else "PWD" if "g" in str(size).lower() else "No format"
    )


def extract_deal_info(product_name, exclude_outliers, kol_outliers):
    # Find all square brackets in product names
    brackets = re.findall(r"\[(.*?)\]", product_name)

    # Remove words that contain any word in exclude_outliers
    brackets = [
        b
        for b in brackets
        if all(excl.lower() not in b.lower() for excl in exclude_outliers)
    ]

    # Check whether any words in square bracket contain "DEAL"
    deal_phrases = [phrase for phrase in brackets if "DEAL" in phrase.upper()]

    if deal_phrases:
        # Get the words positioned after the "DEAL" word in the square bracket
        deal_info = deal_phrases[0].split("DEAL")[1].strip().upper()
        return deal_info
    else:
        # Check whether there are any KOLs in the product names
        special_phrases = [
            kol.upper() for kol in kol_outliers if kol.upper() in product_name.upper()
        ]
        return special_phrases[0] if special_phrases else "No KOLs"


def update_FSP():
    st.session_state.is_FSP = not st.session_state.is_FSP


def update_FORMAT():
    st.session_state.is_FORMAT = not st.session_state.is_FORMAT


def update_CleanProvince():
    st.session_state.is_CleanProvince = not st.session_state.is_CleanProvince


def get_default_periods(min_date, max_date):
    periods = []
    current_date = min_date.replace(day=1)  # Start from first day of min_date's month

    while current_date <= max_date:
        # Get the last day of current month
        _, last_day = monthrange(current_date.year, current_date.month)
        month_end = current_date.replace(day=last_day)

        # If we're in the last month and max_date is before month end
        if month_end > max_date:
            month_end = max_date

        # Calculate period end dates
        double_day_end = min(current_date.replace(day=13), month_end)
        mid_month_end = min(current_date.replace(day=20), month_end)

        # Only add periods if they fall within our date range
        if current_date <= double_day_end:
            periods.append((f"Double Day", current_date, double_day_end))

        mid_month_start = double_day_end.replace(day=14)
        if mid_month_start <= month_end and mid_month_start <= max_date:
            periods.append((f"Mid Month", mid_month_start, mid_month_end))

        pay_day_start = mid_month_end.replace(day=21)
        if pay_day_start <= month_end and pay_day_start <= max_date:
            periods.append((f"Pay Day", pay_day_start, month_end))

        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    return periods


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

list_component_bool_true = ["is_FORMAT", "is_FSP"]
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


########################################################################################################

######################################## SECTION 1: Upload File ########################################

# Title and description
st.title("Abbott Cleaning Data: A data processing toolkit for TikTok Seller Center analytics")

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
    st.session_state.df = df

    # Apply the cleaning transformation to each column in the list
    for col in columns_cast_numeric:
        if df[col].dtype != "Int64":  # Check if the column is not already Int64
            # Remove non-numeric characters and convert to Int64
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"\D", "", regex=True)
            ).astype("Int64")

    df[columns_cast_numeric] = df[columns_cast_numeric].fillna(0)

    # Store dataframe in session_state
    st.session_state.df = df

    # Remove special characters
    # - Tab
    df = df.apply(
        lambda x: x.str.replace("\t", "", regex=False) if x.dtype == "object" else x
    )

    # Store dataframe in session_state
    st.session_state.df = df

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

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
        # Clean province
        df["Clean Province"] = (
            df["Province"]
            .apply(clean_province)
            .apply(process_province)
            .apply(clean_province)
        )

        with open("province_mapping.json", "r", encoding="utf-8") as f:
            province_mapping = json.load(f)

        df["Clean Province"] = df["Clean Province"].map(province_mapping)

        # Store dataframe in session_state
        st.session_state.df = df

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

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
            "Abbott Grow",
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

        # Identify columns that need to be casted as string format
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

        # Add a text input for specifying new options
        brand_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR BRAND NAMES (SEPARATE BY COMMAS):",
            value=default_brand_new_option,
        )

        st.session_state.default_brand_new_option = brand_new_option

        # Split and append each new option if provided
        if brand_new_option:
            # Split new_option by commas and strip any extra whitespace around each part
            new_options_list = [
                option.strip()
                for option in brand_new_option.split(",")
                if option.strip()
            ]
            # Append each new option to the selected_options list
            extract_brands_list.extend(new_options_list)

        add_vertical_space(1)
        st.write(
            "##### **Selected brand names:**\n"
            + "\n".join(f"- {option}" for option in extract_brands_list)
        )
        brand_map = {
            brand.lower(): brand for brand in extract_brands_list
        }  # lowercase to original format mapping

        # Create a regex pattern from the lowercase versions of brands
        pattern = "|".join(brand_map.keys())

        # Convert product_name to lowercase, extract the brand in lowercase, and map back to original format
        df["Brand"] = (
            df["Product Name"]
            .str.lower()
            .str.extract(f"({pattern})", expand=False)  # Extract in lowercase
            .map(brand_map)  # Map to original format using brand_map
        )

        # Store dataframe in session_state
        st.session_state.df = df

    ####################################################################################################

    ##################################### SECTION 5: Extract Sizes #####################################

    with col22:
        st.subheader("**Product Sizes**")

        # Apply the function to the product_name column and save the result in a new column
        df["Size"] = df["Product Name"].apply(extract_size)

        # Store dataframe in session_state
        st.session_state.df = df

        # Specified default brands
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

        # Identify columns that need to be casted as string format
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

        # Add a text input for specifying new options
        size_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR SIZES (SEPARATE BY COMMAS):",
            value=default_size_new_option,
        )

        st.session_state.default_size_new_option = size_new_option

        # Split and append each new option if provided
        if size_new_option:
            # Split new_option by commas and strip any extra whitespace around each part
            new_options_list = [
                option.strip()
                for option in size_new_option.split(",")
                if option.strip()
            ]
            # Append each new option to the selected_options list
            outliers_size_list.extend(new_options_list)

        add_vertical_space(1)
        st.write(
            "##### **Selected size outliers:**\n"
            + "\n".join(f"- {option}" for option in outliers_size_list)
        )

        df.loc[
            df["Product Name"].isin(outliers_size) & df["Size"].isna(),
            "Size",
        ] = "220ml"
        # Store dataframe in session_state
        st.session_state.df = df

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    ####################################################################################################

    #################################### SECTION 6: Add NEW COLUMNS ####################################

    st.divider()

    # Divide the layout
    col13, col23 = st.columns(2)

    with col13:
        st.subheader("**Calculated Columns**")

        FSP = st.checkbox(
            "**ADD :red[FSP] COLUMN**",
            value=st.session_state.is_FSP,
            on_change=update_FSP,
        )

        if FSP:
            # Calculate FSP
            df["FSP"] = (
                df["SKU Subtotal Before Discount"] - df["SKU Seller Discount"]
            ) / df["Quantity"]

            # Store dataframe in session_state
            st.session_state.df = df

        FORMAT = st.checkbox(
            "**ADD :red[FORMAT] COLUMN**",
            value=st.session_state.is_FORMAT,
            on_change=update_FORMAT,
        )

        df["Format"] = df["Size"].apply(determine_format_type)

        # Store dataframe in session_state
        st.session_state.df = df

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

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

        exclude_outliers_list_copy = exclude_outliers_list.copy()
        st.session_state.default_exclude_outliers = exclude_outliers_list_copy

        default_exclude_new_option = (
            ""
            if st.session_state.default_exclude_new_option is None
            else st.session_state.default_exclude_new_option
        )

        # Add a text input for specifying new options
        exclude_outliers_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR EXCLUDE OUTLIERS (SEPARATE BY COMMAS):",
            value=default_exclude_new_option,
        )

        st.session_state.default_exclude_new_option = exclude_outliers_new_option

        # Split and append each new option if provided
        if exclude_outliers_new_option:
            # Split new_option by commas and strip any extra whitespace around each part
            new_options_list = [
                option.strip()
                for option in exclude_outliers_new_option.split(",")
                if option.strip()
            ]
            # Append each new option to the selected_options list
            exclude_outliers_list.extend(new_options_list)

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
            label="**KOL OUTLIERS**", options=kol_outliers, default=default_kol_outliers
        )

        kol_outliers_list_copy = kol_outliers_list.copy()
        st.session_state.default_kol_outliers = kol_outliers_list_copy

        default_kol_new_option = (
            ""
            if st.session_state.default_kol_new_option is None
            else st.session_state.default_kol_new_option
        )

        # Add a text input for specifying new options
        kol_outliers_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR KOL OUTLIERS (SEPARATE BY COMMAS):",
            value=default_kol_new_option,
        )

        st.session_state.default_kol_new_option = kol_outliers_new_option

        # Split and append each new option if provided
        if kol_outliers_new_option:
            # Split new_option by commas and strip any extra whitespace around each part
            new_options_list = [
                option.strip()
                for option in kol_outliers_new_option.split(",")
                if option.strip()
            ]
            # Append each new option to the selected_options list
            kol_outliers_list.extend(new_options_list)

        add_vertical_space(1)
        st.write(
            "##### **Selected KOL outliers:**\n"
            + "\n".join(f"- {option}" for option in kol_outliers_list)
        )

    df["KOL"] = df["Product Name"].apply(
        lambda x: extract_deal_info(x, exclude_outliers_list, kol_outliers_list)
    )

    # Store dataframe in session_state
    st.session_state.df = df

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    ####################################################################################################

    ##################################### SECTION 8: Divide Periods ####################################

    add_vertical_space(3)
    st.header(
        "Divide Periods",
        divider="gray",
    )

    df["Created Time"] = pd.to_datetime(df["Created Time"], format="%d/%m/%Y %H:%M:%S")

    # Store dataframe in session_state
    st.session_state.df = df

    min_date = df["Created Time"].min().date()
    max_date = df["Created Time"].max().date()

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
            col15, col25, col35 = st.columns(3)
            with col15:
                period_name = st.text_input("Period Name")
            with col25:
                start_date = st.date_input(
                    "Start Date", value=min_date, min_value=min_date, max_value=max_date
                )
            with col35:
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
                elif period not in st.session_state.periods:
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
                st.stop()

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
                if start_date < min_date or end_date > max_date:
                    st.warning(
                        f"Row {index + 1}: Dates must be between {min_date.strftime('%Y-%m-%d')} and {max_date.strftime('%Y-%m-%d')}!"
                    )
                    continue

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

    # # Display and manage periods
    if st.session_state.periods:
        st.write("##### Current Periods")

        # Tạo 2 cột chính
        col16, col26 = st.columns(2)

        # Tính số period cho mỗi cột
        total_periods = len(st.session_state.periods)
        periods_per_col = (total_periods + 1) // 2  # Làm tròn lên

        for i, (name, start, end) in enumerate(st.session_state.periods):
            # Xác định period này thuộc cột nào
            current_col = col16 if i < periods_per_col else col26

            # Tạo container cho period
            with current_col:
                period_container = st.container()
                with period_container:
                    col161, col261 = st.columns(
                        [3, 1]
                    )  # Chia container thành 2 phần cho nội dung và nút remove

                    with col161:
                        st.write(
                            f"- Period {i+1}: {name} ({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})"
                        )
                    with col261:
                        if st.button(f"Remove", key=f"remove_{i}"):
                            st.session_state.periods.pop(i)
                            st.rerun()

        # Process and download section
        if st.button("Process All Periods"):
            try:
                # Convert the 'Created Time' column to datetime format with the correct format
                df["Created Time"] = pd.to_datetime(
                    df["Created Time"], format="%d/%m/%Y %H:%M:%S"
                )

                # Store dataframe in session_state
                st.session_state.df = df

                df["Period"] = "No Period"

                # Store dataframe in session_state
                st.session_state.df = df

                for name, start_date, end_date in st.session_state.periods:
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date) + pd.Timedelta(
                        hours=23, minutes=59, seconds=59
                    )
                    mask = (df["Created Time"] >= start_dt) & (
                        df["Created Time"] <= end_dt
                    )
                    df.loc[mask, "Period"] = name

                    # Store dataframe in session_state
                    st.session_state.df = df

            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
                # Add more detailed error information
                if "Created Time" in str(e):
                    st.error(
                        "Date format error detected. Please ensure your dates are in DD/MM/YYYY HH:MM:SS format"
                    )

            add_vertical_space(1)
            with st.expander("**Dataframe Preview**"):
                st.dataframe(df)

        # Add clear all button
        if st.button("Clear All"):
            st.session_state.periods = []
            st.rerun()

    ####################################################################################################

    ######################################## SECTION 9: Download #######################################

    add_vertical_space(3)
    st.header(
        "Download",
        divider="gray",
    )

    # Dummy code for prettier layout
    col15, col25, col35, col45, col55, col65 = st.columns(6)
    timestamp = get_timestamp_string()

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
