import pandas as pd
import streamlit as st
import io
from itertools import combinations
from datetime import datetime

# Extra utilities
from streamlit_extras.add_vertical_space import add_vertical_space


##################################### SECTION 0-1: Define Functions ######################################


def find_best_combinations(list_value, target, num_combinations=10):
    # Dictionary lưu tổ hợp và tổng của chúng
    combinations_dict = {}

    # Xét tất cả độ dài có thể của tổ hợp
    for length in range(1, len(list_value) + 1):
        for combo in combinations(list_value, length):
            total = sum(combo)
            combinations_dict[combo] = total

    # Sắp xếp theo độ chênh lệch với target
    sorted_combinations = sorted(
        combinations_dict.items(), key=lambda x: (abs(target - x[1]), -x[1])
    )[:num_combinations]

    # Tạo DataFrame
    max_length = max(len(combo[0]) for combo in sorted_combinations)
    df_dict = {}

    for i, (combo, total) in enumerate(sorted_combinations, 1):
        col_name = f"Combination {i}"
        values = list(combo) + [None] * (max_length - len(combo))
        df_dict[col_name] = values

    return pd.DataFrame(df_dict)


# def find_combinations(values, target, top_n=10):
#     combinations = []
#     for r in range(1, len(values) + 1):
#         for combo in itertools.combinations(values, r):
#             total = sum(combo)
#             combinations.append((combo, abs(total - target), total))

#     # Sắp xếp theo khoảng cách tới target, sau đó theo tổng giảm dần
#     combinations.sort(key=lambda x: (x[1], -x[2]))

#     # Chỉ giữ lại top_n tổ hợp
#     top_combinations = combinations[:top_n]

#     # Chuyển đổi tổ hợp thành DataFrame
#     max_len = max(len(x[0]) for x in top_combinations)
#     data = {f"Combination {i+1}": list(x[0]) + [None] * (max_len - len(x[0]))
#             for i, x in enumerate(top_combinations)}
#     return pd.DataFrame(data)


@st.cache_data
def convert_df_to_excel(df):
    """Convert dataframe to Excel format"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        # Get workbook and worksheet
        worksheet = writer.sheets["Sheet1"]

        # Auto-adjust columns' width
        for i, col in enumerate(df.columns):
            # Find the maximum length of the column
            column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2

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
]

# Khởi tạo các components
for component in list_component_none:
    if component not in st.session_state:
        st.session_state[component] = None


########################################################################################################

######################################## SECTION 1: Upload File ########################################

# Title and description
st.title("Abbott Smart Calculator: A toolkit for  analytics")

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
        df = pd.read_csv(io.BytesIO(file_buffer), low_memory=False)
    else:  # xlsx or xls
        df = pd.read_excel(io.BytesIO(file_buffer))

    #######################################################################################################

    ################################## SECTION 2: Calculate Combinations ##################################

    list_value = df["Value"].iloc[:-2].tolist()
    target = df["Value"].iloc[-1]

    result_df = find_best_combinations(list_value, target)

    add_vertical_space(1)
    with st.expander("**Dataframe Preview**"):
        st.dataframe(result_df)

    #######################################################################################################

    ######################################### SECTION 3: Downloads ########################################

    timestamp = get_timestamp_string()

    excel_data = convert_df_to_excel(result_df)
    st.download_button(
        label="📥 Download as Excel",
        data=excel_data,
        file_name=f"data_export_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download-excel",
    )
