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


def determine_format_type(size):
    size_str = str(size).lower()
    if "ml" in size_str:
        return "LIQ"
    elif "g" in size_str:
        return "PWD"
    else:
        return "No format"


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


########################################################################################################

######################################## SECTION 1: Upload File ########################################

st.header(
    "Upload File",
    divider="gray",
)

upload_file = st.file_uploader("Choose your data file (CSV format)", type="csv")

if upload_file is None:
    st.info("Upload your data file to continue.")

elif upload_file is not None and not upload_file.name.endswith(".csv"):
    # Unsupported file format
    st.error("Unsupported file format. Please upload a CSV file.")
    st.stop()  # Stops Streamlit from processing further elements

else:
    # Process file through buffer for multiple read
    file_buffer = upload_file.read()

    # Read the original data
    df_original = pd.read_csv(io.BytesIO(file_buffer), low_memory=False)
    headers_list = df_original.columns.tolist()

    st.write("\n")
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df_original)

    ########################################################################################################

    ####################################### SECTION 2: Cast Columns ########################################

    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.header(
        "Cast Columns",
        divider="gray",
    )

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
            df_original.loc[:, "SKU Unit Original Price":"Order Refund Amount"].columns
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
            "COMBO 5 LỐC (30 CHAI) SỮA NƯỚC GLUCERNA HƯƠNG VANI",
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

        df.loc[
            df["Product Name"].isin(outliers_size) & df["Size"].isna(),
            "Size",
        ] = "220ml"

    st.write("\n")
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    st.divider()

    ##########################################################################################################

    ###################################### SECTION 5: Add FSP & FORMAT #######################################

    # Divide the layout
    col13, col23 = st.columns(2)

    with col13:
        st.subheader("**Calculated Columns**")

        FSP = st.checkbox("**ADD :red[FSP] COLUMN**", value=True)

        if FSP:
            # Calculate FSP
            df["FSP"] = (
                df["SKU Subtotal Before Discount"] - df["SKU Seller Discount"]
            ) / df["Quantity"]

        FORMAT = st.checkbox("**ADD :red[FORMAT] COLUMN**", value=True)

        df["Format"] = df["Size"].apply(determine_format_type)

    st.write("\n")
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    ##########################################################################################################

    ##################################### SECTION 6: Add KOL Extraction ######################################

    st.subheader("**KOL Extraction**")

    col14, col24 = st.columns(2)

    with col14:
        exclude_outliers = ["Hot Deal", "Deal Hè"]

        exclude_outliers_list = st.multiselect(
            label="**EXCLUDE OUTLIERS**",
            options=exclude_outliers,
            default=exclude_outliers,
        )

        # Add a text input for specifying new options
        exclude_outliers_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR EXCLUDE OUTLIERS (SEPARATE BY COMMAS):"
        )

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

        st.write("\n")
        st.write(
            "##### **Selected exclude outliers:**\n"
            + "\n".join(f"- {option}" for option in exclude_outliers_list)
        )

    with col24:
        kol_outliers = ["Quyền Leo", "Hằng Du Mục"]

        kol_outliers_list = st.multiselect(
            label="**KOL OUTLIERS**", options=kol_outliers, default=kol_outliers
        )

        # Add a text input for specifying new options
        kol_outliers_new_option = st.text_input(
            "OR SPECIFY NEW OPTIONS FOR KOL OUTLIERS (SEPARATE BY COMMAS):"
        )

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

        st.write("\n")
        st.write(
            "##### **Selected KOL outliers:**\n"
            + "\n".join(f"- {option}" for option in kol_outliers_list)
        )

    df["KOL"] = df["Product Name"].apply(
        lambda x: extract_deal_info(x, exclude_outliers_list, kol_outliers_list)
    )

    st.write("\n")
    with st.expander("**Dataframe Preview**"):
        st.dataframe(df)

    ##########################################################################################################

    ######################################## SECTION 5: Divide Periods #######################################

    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.header(
        "Divide Periods",
        divider="gray",
    )

    df["Created Time"] = pd.to_datetime(df["Created Time"], format="%d/%m/%Y %H:%M:%S")

    min_date = df["Created Time"].min().date()
    max_date = df["Created Time"].max().date()

    # Initialize periods in session state if not exists
    if "periods" not in st.session_state:
        st.session_state.periods = []

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
            st.stop()

        if submitted and start_date and end_date:
            if start_date <= end_date:
                period = (period_name, start_date, end_date)
                existing_names = [p[0] for p in st.session_state.periods]
                existing_dates = [(p[1], p[2]) for p in st.session_state.periods]

                if period in st.session_state.periods:
                    st.warning("This period already exists!")
                    # st.session_state.periods.pop()
                elif period_name in existing_names:
                    st.warning("This period name already exists!")
                    # st.session_state.periods.pop()
                elif (start_date, end_date) in existing_dates:
                    st.warning("This pair of start and end date already exists!")
                elif period not in st.session_state.periods:
                    st.session_state.periods.append(period)
                    st.success("Period added successfully!")

            else:
                st.error("End date must be after start date!")
                st.stop()

    print(st.session_state.periods)
    # Display and manage periods
    if st.session_state.periods:
        st.write("##### **Current Periods**")
        col16, col26 = st.columns([3, 1])
        for i, (name, start, end) in enumerate(st.session_state.periods):
            with col16:
                st.write(
                    f"- Period {i+1}: {name} ({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})"
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

                df["Period"] = "No Period"

                for name, start_date, end_date in st.session_state.periods:
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date) + pd.Timedelta(
                        hours=23, minutes=59, seconds=59
                    )
                    mask = (df["Created Time"] >= start_dt) & (
                        df["Created Time"] <= end_dt
                    )
                    df.loc[mask, "Period"] = name

            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
                # Add more detailed error information
                if "Created Time" in str(e):
                    st.error(
                        "Date format error detected. Please ensure your dates are in DD/MM/YYYY HH:MM:SS format"
                    )

            st.write("\n")
            with st.expander("**Dataframe Preview**"):
                st.dataframe(df)

        # Add clear all button
        with col26:
            if st.button("Clear All"):
                st.session_state.periods = []
                st.rerun()

    else:
        st.info("Add periods using the form above")

    ##########################################################################################################

    ########################################### SECTION 6: Download ##########################################

    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.header(
        "Download",
        divider="gray",
    )

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
