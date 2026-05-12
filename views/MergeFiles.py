import streamlit as st
import polars as pl
import uuid
import tempfile
from pathlib import Path
from streamlit_extras.add_vertical_space import add_vertical_space
from datetime import datetime
from io import BytesIO

# ===================== CONFIG =====================
allowed_types = ["csv", "xlsx"]

if "files_data" not in st.session_state:
    st.session_state.files_data = {}

if "last_uploaded_files" not in st.session_state:
    st.session_state.last_uploaded_files = []

if "default_string_columns" not in st.session_state:
    st.session_state.default_string_columns = None

if "default_numeric_columns" not in st.session_state:
    st.session_state.default_numeric_columns = None

# ===================== FUNCTION =====================
@st.cache_data
def get_timestamp_string(date_only=False):
    if date_only:
        return datetime.now().strftime("%Y%m%d")
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@st.cache_data
def convert_df_to_csv(df):
    # Cách nhanh và hiệu quả nhất
    return df.write_csv().encode("utf-8")


@st.cache_data
def convert_df_to_excel(df):
    output = BytesIO()
    
    # Polars hỗ trợ write_excel trực tiếp vào file-like object
    df.write_excel(
        workbook=output,
        worksheet="Sheet1",
        # Có thể thêm tùy chọn đẹp hơn nếu muốn:
        table_style="Table Style Light 13",
        autofit=True,
        float_precision=2,
    )
    
    # Reset pointer về đầu để Streamlit đọc
    output.seek(0)
    return output.getvalue()

########################################################################################################

######################################## SECTION 1: Upload File ########################################

st.title(
    "Raw Data File Combination from TikTok Seller Center"
)

st.header(
    "Upload File",
    divider="gray",
)

upload_files = st.file_uploader(
    "CHOOSE YOUR DATA FILE (CSV, XLSX)",
    type=allowed_types,
    accept_multiple_files=True
)

current_file_names = [f.name for f in upload_files] if upload_files else []

# Reset khi upload file mới
if current_file_names != st.session_state.last_uploaded_files:
    st.session_state.files_data = {}
    st.session_state.last_uploaded_files = current_file_names

if upload_files:
    for upload_file in upload_files:
        file_name = upload_file.name

        # Tránh load lại file đã có
        if any(data["file_name"] == file_name for data in st.session_state.files_data.values()):
            continue

        file_id = str(uuid.uuid4())

        # Lưu file tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_name.split('.')[-1]}") as tmp:
            tmp.write(upload_file.read())
            tmp_path = tmp.name

        file_extension = file_name.split(".")[-1].lower()

        # Đọc file lần đầu để lấy schema (original)
        if file_extension == "csv":
            df_original = pl.read_csv(tmp_path, infer_schema_length=100_000, low_memory=True)
        else:
            df_original = pl.read_excel(tmp_path)

        st.session_state.files_data[file_id] = {
            "file_name": file_name,
            "file_path": tmp_path,
            "file_extension": file_extension,
            "df_original": df_original,
            "df_processed": df_original.clone(),
            "headers_list": df_original.columns
        }

    ####################################################################################################

    ###################################### SECTION 2: Cast Columns #####################################

    add_vertical_space(3)
    st.header("Cast Columns", divider="gray")

    all_headers = set()
    for data in st.session_state.files_data.values():
        all_headers.update(data["headers_list"])

    headers_list = sorted(list(all_headers))

    col11, col21 = st.columns(2)

    with col11:
        st.subheader("**String Format**")

        default_string = (
            st.session_state.default_string_columns 
            if st.session_state.default_string_columns is not None 
            else [
                "Order ID", "Seller SKU", "SKU ID", "Product Name", "Package ID"
            ]
        )

        columns_cast_string = st.multiselect(
            label="**CHOOSE COLUMNS THAT NEEDED TO BE CASTED AS :red[STRING] FORMAT**",
            options=headers_list,
            default=default_string,
        )
        st.session_state.default_string_columns = columns_cast_string

    with col21:
        st.subheader("**Numeric Format**")

        default_numeric = (
            st.session_state.default_numeric_columns 
            if st.session_state.default_numeric_columns is not None 
            else [
                "SKU Unit Original Price", "SKU Subtotal Before Discount",
                "SKU Platform Discount", "SKU Seller Discount",
                "SKU Subtotal After Discount", "Shipping Fee After Discount",
                "Original Shipping Fee", "Shipping Fee Seller Discount",
                "Shipping Fee Platform Discount", "Payment platform discount",
                "Taxes", "Order Amount", "Order Refund Amount"
            ]
        )

        columns_cast_numeric = st.multiselect(
            label="**CHOOSE COLUMNS THAT NEEDED TO BE CASTED AS :red[NUMERIC] FORMAT**",
            options=headers_list,
            default=default_numeric,
        )
        st.session_state.default_numeric_columns = columns_cast_numeric

    for file_id, data in st.session_state.files_data.items():
        file_path = data["file_path"]
        file_ext = data["file_extension"]

        # Đọc lại với tùy chỉnh dtype
        if file_ext == "csv":
            df = pl.read_csv(
                file_path,
                infer_schema_length=100_000,
                low_memory=True,
                # Cast string trước
                schema_overrides={col: pl.String for col in columns_cast_string}
            )
        else:
            df = pl.read_excel(file_path)

        # Cast string columns
        for col in columns_cast_string:
            if col in df.columns:
                df = df.with_columns(pl.col(col).cast(pl.String))

        # Cast numeric columns
        for col in columns_cast_numeric:
            if col in df.columns:
                # Chuyển sang numeric, lỗi thành null
                df = df.with_columns(
                    pl.col(col)
                    .cast(pl.String)  # đảm bảo là string trước khi parse
                    .str.replace_all(r"[^\d.-]", "")  # xóa ký tự không phải số (tùy chọn)
                    .cast(pl.Float64, strict=False)
                )

        # Fill null numeric = 0
        numeric_cols_in_df = [col for col in columns_cast_numeric if col in df.columns]
        if numeric_cols_in_df:
            df = df.with_columns(
                pl.col(numeric_cols_in_df).fill_null(0)
            )

        # Clean string columns (loại tab)
        string_cols_in_df = [col for col in columns_cast_string if col in df.columns]
        if string_cols_in_df:
            df = df.with_columns(
                pl.col(string_cols_in_df).str.replace_all(r"\t", "")
            )

        # Lưu processed DataFrame
        st.session_state.files_data[file_id]["df_processed"] = df

    # if st.session_state.files_data:
    #     for file_id, data in st.session_state.files_data.items():
    #         file_name = data["file_name"]
    #         df_original = data["df_original"]

    #         with st.expander(f"📄 Dataframe Preview - {file_name}"):
    #             st.dataframe(df_original)

    #####################################################################################################

    ###################################### SECTION 3: Combine Files #####################################

    add_vertical_space(3)
    st.header("Combine files", divider="gray")
    if st.session_state.files_data:
        # Lấy danh sách tất cả df_processed
        processed_dfs = [
            data["df_processed"] for data in st.session_state.files_data.values()
        ]

        df_concat = pl.DataFrame()

        if len(processed_dfs) > 1:
            try:
                # Vertical Relaxed: Cho phép các cột khác nhau (missing columns sẽ thành null)
                df_concat = pl.concat(processed_dfs, how="vertical_relaxed")
                
                st.success(f"✅ Successfully combined **{len(processed_dfs)} files** - Total rows: **{len(df_concat):,}**")

                # Hiển thị thông tin
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total rows", f"{len(df_concat):,}")
                with col2:
                    st.metric("Total columns", len(df_concat.columns))
                with col3:
                    st.metric("Total files", len(processed_dfs))

                with st.expander("🔎 Data Preview", expanded=False):
                    st.dataframe(df_concat, use_container_width=True)

                st.session_state.df_concat = df_concat

            except Exception as e:
                st.error(f"Lỗi khi concat: {e}")
                st.session_state.df_concat = None

        elif len(processed_dfs) == 1:
            df_concat = processed_dfs[0]
            
            st.success("✅ Only 1 upload file detected")

            # Hiển thị thông tin
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total rows", f"{len(df_concat):,}")
            with col2:
                st.metric("Total columns", len(df_concat.columns))
            with col3:
                st.metric("Total files", len(processed_dfs))

            with st.expander("🔎 Data Preview", expanded=False):
                st.dataframe(df_concat, use_container_width=True)

            st.session_state.df_concat = df_concat

        else:
            st.session_state.df_concat = None

    #####################################################################################################

    ###################################### SECTION 3: Download File #####################################

    add_vertical_space(3)
    st.header("Download", divider="gray")
    if st.session_state.files_data:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
        col1.markdown("**Custom Name**")
        col3.markdown("**CSV**")
        col4.markdown("**XLSX**")

        timestamp = get_timestamp_string(date_only=True)

        default_name = f"combined_order_{timestamp}"

        # Cột 1: input tên file
        with col1:
            custom_name = st.text_input(
                label="",
                value=default_name,
                key=f"name_{file_id}",
                label_visibility="collapsed"
            )

        # Cột 2: Download CSV
        with col3:
            st.download_button(
                label="📥 Download CSV",
                data=convert_df_to_csv(df),
                file_name=f"{custom_name}.csv",
                mime="text/csv",
                key=f"csv_{file_id}"
            )

        # Cột 3: Download XLSX
        with col4:
            st.download_button(
                label="📥 Download XLSX",
                data=convert_df_to_excel(df),
                file_name=f"{custom_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"xlsx_{file_id}"
            )