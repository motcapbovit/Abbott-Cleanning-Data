import pandas as pd
import streamlit as st
import re
import io
from datetime import datetime

##################################### SECTION 0: Define Functions ######################################


def extract_size(product_name):
    # Step 1: Replace special characters (except '.') with spaces
    cleaned_name = re.sub(r"[^\w\s\.]", " ", product_name)

    # Step 2: Split the cleaned name into individual words
    words = cleaned_name.split()

    # Step 3: Find any word that contains both digits and specified units
    for word in words:
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


########################################################################################################

######################################## SECTION 1: Upload File ########################################

st.header(
    "Upload File",
    divider="gray",
)

upload_file = st.file_uploader("Choose your data file (CSV format)", type="csv")

########################################################################################################

####################################### SECTION 2: Cast Columns ########################################

st.write("\n")
st.write("\n")
st.write("\n")
st.header(
    "Cast Columns",
    divider="gray",
)

if upload_file is not None:
    # Check the file format
    if not upload_file.name.endswith(".csv"):
        # Unsupported file format
        st.error("Unsupported file format. Please upload a CSV file.")
        st.stop()  # Stops Streamlit from processing further elements

    # Read headers
    file_buffer = upload_file.read()

    df_headers = pd.read_csv(io.BytesIO(file_buffer), nrows=0, low_memory=False)
    headers_list = df_headers.columns.tolist()

    # Divide the layout
    col11, col21 = st.columns(2)

    with col11:
        st.subheader("**String Format**")

        # Specified default columns
        default_string_columns = [
            "Order ID",
            "Seller SKU",
            "SKU ID",
            "Product Name",
            "Package ID",
        ]

        # Identify columns that need to be casted as string format
        columns_cast_string = st.multiselect(
            label="**CHOOSE COLUMNS THAT NEEDED TO BE CASTED AS :red[STRING] FORMAT**",
            options=headers_list,
            default=default_string_columns,
        )

        # Create a dictionary for dtype by setting each column in the list to str
        dtype_dict = {col: str for col in columns_cast_string}

    with col21:
        st.subheader("**Numeric Format**")

        # Specified default columns
        default_numeric_columns = list(
            df_headers.loc[:, "SKU Unit Original Price":"Order Refund Amount"].columns
        )

        # Identify columns that need to be casted as numeric format
        columns_cast_numeric = st.multiselect(
            label="**CHOOSE COLUMNS THAT NEEDED TO BE CASTED AS :red[NUMERIC] FORMAT**",
            options=headers_list,
            default=default_numeric_columns,
        )

    # Fully read data
    df = pd.read_csv(io.BytesIO(file_buffer), low_memory=False, dtype=dtype_dict)

    # Apply the cleaning transformation to each column in the list
    for col in columns_cast_numeric:
        if df[col].dtype != "Int64":  # Check if the column is not already Int64
            # Remove non-numeric characters and convert to Int64
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"\D", "", regex=True)
            ).astype("Int64")

    df[columns_cast_numeric] = df[columns_cast_numeric].fillna(0)

    # Remove special characters
    # - Tab
    df = df.apply(
        lambda x: x.str.replace("\t", "", regex=False) if x.dtype == "object" else x
    )

    st.write("\n")
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    ##########################################################################################################

    ####################################### SECTION 3: Extract Brands ########################################

    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.header(
        "Add Attributes",
        divider="gray",
    )

    # Divide the layout
    col12, col22 = st.columns(2)

    with col12:
        st.subheader("**Brand Names**")

        # Specified default brands
        brands_list = [
            "Abbott Grow",
            "PediaSure",
            "Ensure",
            "Similac",
            "Glucerna",
            "ProSure",
        ]
        default_brands = brands_list[:5]

        # Identify columns that need to be casted as string format
        extract_brands_list = st.multiselect(
            label="**CHOOSE BRAND NAME(S) THAT NEEDED TO BE EXTRACTED FROM PRODUCT NAMES**",
            options=brands_list,
            default=default_brands,
        )

        # Add a text input for specifying new options
        brand_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR BRAND NAMES (SEPARATE BY COMMAS):"
        )

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

        st.write("\n")
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

    ##########################################################################################################

    ######################################## SECTION 4: Extract Sizes ########################################

    with col22:
        st.subheader("**Product Sizes**")

        # Apply the function to the product_name column and save the result in a new column
        df["Size"] = df["Product Name"].apply(extract_size)

        # Specified default brands
        outliers_size = [
            "COMBO 4 LỐC (24 CHAI) SỮA NƯỚC GLUCERNA HƯƠNG VANI",
            "COMBO 5 LỐC (30 CH" "AI) SỮA NƯỚC GLUCERNA HƯƠNG VANI",
            "1 THÙNG 24 CHAI SỮA NƯỚC GLUCERNA HƯƠNG VANI",
            "[TẶNG BÌNH GIỮ NHIỆT] COMBO 24 CHAI SỮA NƯỚC GLUCERNA HƯƠNG VANI",
        ]

        # Identify columns that need to be casted as string format
        outliers_size_list = st.multiselect(
            label="**SPECIFY OUTLIERS FOR THE PROCESS OF EXTRACTING PRODUCT SIZE**",
            options=outliers_size,
            default=outliers_size,
        )

        # Add a text input for specifying new options
        size_new_options = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR SIZES (SEPARATE BY COMMAS):"
        )

        # Split and append each new option if provided
        if size_new_options:
            # Split new_option by commas and strip any extra whitespace around each part
            new_options_list = [
                option.strip()
                for option in size_new_options.split(",")
                if option.strip()
            ]
            # Append each new option to the selected_options list
            outliers_size_list.extend(new_options_list)

        st.write("\n")
        st.write(
            "##### **Selected size outliers:**\n"
            + "\n".join(f"- {option}" for option in outliers_size_list)
        )

        # INPUT ALLOW

        df.loc[
            df["Product Name"].isin(outliers_size) & df["Size"].isna(),
            "Size",
        ] = "220ml"

    st.write("\n")
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    st.divider()

    ##########################################################################################################

    ########################################### SECTION 5: Add FSP ###########################################

    # Divide the layout
    col13, col23 = st.columns(2)

    with col13:
        st.subheader("**Calculated Columns**")

        FSP = st.checkbox("**ADD :red[FSP] COLUMN**")

        if FSP:
            # Calculate FSP
            df["FSP"] = (
                df["SKU Subtotal Before Discount"] - df["SKU Seller Discount"]
            ) / df["Quantity"]

    st.write("\n")
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    ##########################################################################################################

    ########################################### SECTION 5: Download ##########################################

    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.header(
        "Download",
        divider="gray",
    )

    st.subheader("**Complete Dataset**")

    # Dummy code for prettier layout
    col15, col25, col35, col45, col55, col56 = st.columns(6)

    with col35:
        # CSV Download
        csv_data = convert_df_to_csv(df)
        timestamp = get_timestamp_string()
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
        timestamp = get_timestamp_string()
        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=f"data_export_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download-excel",
        )

    st.divider()
    st.subheader("**Period Datasets**")

    df["Created Time"] = pd.to_datetime(df["Created Time"], format="%d/%m/%Y %H:%M:%S")

    min_date = df["Created Time"].min().date()
    max_date = df["Created Time"].max().date()

    # Initialize periods in session state if not exists
    if "periods" not in st.session_state:
        st.session_state.periods = []

    # Add period form
    with st.form("add_period_form"):
        col15, col25 = st.columns(2)
        with col15:
            start_date = st.date_input(
                "Start Date", value=min_date, min_value=min_date, max_value=max_date
            )
        with col25:
            end_date = st.date_input(
                "End Date", value=max_date, min_value=min_date, max_value=max_date
            )

        submitted = st.form_submit_button("Add Period")
        if submitted and start_date and end_date:
            if start_date <= end_date:
                period = (start_date, end_date)
                if period not in st.session_state.periods:
                    st.session_state.periods.append(period)
                    st.success("Period added successfully!")
                else:
                    st.warning("This period already exists!")
            else:
                st.error("End date must be after start date!")

    # Display and manage periods
    if st.session_state.periods:
        st.write("##### **Current Periods**")
        col16, col26 = st.columns([3, 1])
        for i, (start, end) in enumerate(st.session_state.periods):
            with col16:
                st.write(
                    f"Period {i+1}: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
                )
            with col26:
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

                # Create tabs for CSV and Excel downloads
                tab1, tab2 = st.tabs(["CSV Downloads", "Excel Downloads"])

                with tab1:
                    st.write("### Download CSV Files")
                    for i, (start_date, end_date) in enumerate(
                        st.session_state.periods, start=1
                    ):
                        # Convert dates to datetime with time
                        start_dt = pd.to_datetime(start_date)
                        end_dt = pd.to_datetime(end_date) + pd.Timedelta(
                            hours=23, minutes=59, seconds=59
                        )

                        # Filter DataFrame
                        period_df = df[
                            (df["Created Time"] >= start_dt)
                            & (df["Created Time"] <= end_dt)
                        ].sort_values(by="Created Time")

                        # Create download button
                        if not period_df.empty:
                            csv_data = convert_df_to_csv(period_df)
                            file_name = f"Data_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
                            st.download_button(
                                label=f"📥 Download Period {i} ({len(period_df)} rows)",
                                data=csv_data,
                                file_name=file_name,
                                mime="text/csv",
                                key=f"csv_{i}",
                            )
                        else:
                            st.warning(f"No data found for period {i}")

                with tab2:
                    st.write("### Download Excel Files")
                    for i, (start_date, end_date) in enumerate(
                        st.session_state.periods, start=1
                    ):
                        # Convert dates to datetime with time
                        start_dt = pd.to_datetime(start_date)
                        end_dt = pd.to_datetime(end_date) + pd.Timedelta(
                            hours=23, minutes=59, seconds=59
                        )

                        # Filter DataFrame
                        period_df = df[
                            (df["Created Time"] >= start_dt)
                            & (df["Created Time"] <= end_dt)
                        ].sort_values(by="Created Time")

                        # Create download button
                        if not period_df.empty:
                            excel_data = convert_df_to_excel(period_df)
                            file_name = f"Data_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
                            st.download_button(
                                label=f"📥 Download Period {i} ({len(period_df)} rows)",
                                data=excel_data,
                                file_name=file_name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"excel_{i}",
                            )
                        else:
                            st.warning(f"No data found for period {i}")

            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
                # Add more detailed error information
                if "Created Time" in str(e):
                    st.error(
                        "Date format error detected. Please ensure your dates are in DD/MM/YYYY HH:MM:SS format"
                    )

        # Add clear all button
        with col26:
            if st.button("Clear All"):
                st.session_state.periods = []
                st.rerun()

    else:
        st.info("Add periods using the form above")


else:
    st.info("Upload your data file to continue.")