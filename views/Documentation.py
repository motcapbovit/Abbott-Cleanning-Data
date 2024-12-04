import streamlit as st

# Title and description
st.title(
    "Abbott Cleaning Data: A data processing toolkit for TikTok Seller Center analytics"
)

# Core Features
st.header("🚀 Core Features")

st.markdown(
    """
- **Automated Data Cleaning**: Streamlined processing of TikTok Seller Center exports
- **Smart Feature Extraction**: Extract brands, sizes, and KOL information from product names
- **Advanced Period Division**: Flexible time-based data segmentation
- **Interactive Visualization**: Built-in data visualization capabilities
- **Caching System**: Session state management for improved performance
"""
)

# Detailed Modules
st.header("🛠 Module Details")

st.subheader("Data Cleaning Module")
st.markdown(
    """
#### 1. File Upload
- Supports CSV format (XLSX support coming soon)
- Direct integration with TikTok Seller Center exports
- Raw data preview functionality
"""
)

st.markdown(
    """
#### 2. Data Type Conversion
- Flexible column type casting (string/numeric)
- Pre-configured default column mappings
- Custom column selection
"""
)

st.markdown(
    """
#### 3. String Normalization
- Automated province name standardization
- Consistent string formatting
"""
)

st.markdown(
    """
#### 4. Feature Extraction
- Brand name extraction with custom brand list support
- Size extraction with exception handling
- KOL information extraction with customizable rules
"""
)

st.markdown(
    """
#### 5. Calculated Fields
- FSP calculation
- Format standardization
- Custom column generation
"""
)

st.subheader("Period Division System")
st.markdown(
    """
- Multiple period division methods:
    - Default templates
    - Manual period definition
    - Bulk import via file
- Non-overlapping period validation
- Flexible time-based segmentation
"""
)

# Latest Updates
st.header("📦 Latest Updates")

st.info(
    """
**Version 1.0.4**
- Added XLSX file support
- Updated documentation
"""
)

# Usage Notes
st.header("📝 Important Notes")
st.info("For best results, use data exported directly from TikTok Seller Center")
