## ***Abbott Cleaning Data: A repository for Cleanning and Manipulating Data from TikTok Seller Center***

A robust data processing tool for TikTok Seller Center analytics, focusing on cleaning, feature extraction, and enhanced data visualization.

## 🚀 Features

- **Automated Data Cleaning**: Streamlined processing of TikTok Seller Center exports
- **Smart Feature Extraction**: Extract brands, sizes, and KOL information from product names
- **Advanced Period Division**: Flexible time-based data segmentation
- **Interactive Visualization**: Built-in data visualization capabilities
- **Caching System**: Session state management for improved performance

## 📦 Latest Updates

### Version 1.0.3 🔥🔥
- Enhanced province name cleaning algorithm
- Added period division via file upload
- Improved data processing efficiency

### Version 1.0.2
- Introduced province string cleaning functionality

### Version 1.0.1
- Added session state caching
- Implemented data visualization
- Enhanced user interface

### Version 1.0.0
- Initial release

## 🛠 Core Functionalities

### Data Cleaning Module

1. **File Upload**
   - Supports CSV format (XLSX support coming soon)
   - Direct integration with TikTok Seller Center exports
   - Raw data preview functionality

2. **Data Type Conversion**
   - Flexible column type casting (string/numeric)
   - Pre-configured default column mappings
   - Custom column selection

3. **String Normalization**
   - Automated province name standardization
   - Consistent string formatting

4. **Feature Extraction**
   - Brand name extraction with custom brand list support
   - Size extraction with exception handling
   - KOL information extraction with customizable rules

5. **Calculated Fields**
   - FSP calculation
   - Format standardization
   - Custom column generation

### Period Division System

- Multiple period division methods:
  - Default templates
  - Manual period definition
  - Bulk import via file
- Non-overlapping period validation
- Flexible time-based segmentation

## 🔜 Roadmap

- XLSX file format support
- Enhanced visualization capabilities
- Additional data cleaning algorithms
- Expanded feature extraction options

## 📝 Note

For optimal results, use data directly exported from TikTok Seller Center. This ensures compatibility and accurate processing of all features.