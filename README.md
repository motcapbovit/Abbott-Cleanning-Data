## ***Abbott Cleaning Data: A repository for Cleanning and Manipulating Data from TikTok Seller Center***

## 🔆 Introduction
This repository is to clean data gather from tiktok seller center, in addition extracting features and add more necessary columns which facilitating the process of analyzing figures.

## 📝 Version log
- **[1.0.0]**: Launch the project.
- **[1.0.1]**: Add session state (i.e. cache memory), data visualization and enhance UI.
- **[1.0.2]**: Add demo cleaning province strings function.
- **[1.0.3]**: 🔥🔥 Enhance cleanning province function to official version & add function to divide period by upload period data file.

## 📄 Documentation
This tool currently contains 2 main page: Data Cleaning and Visualization.

### Data Cleaning
#### Section 1: Upload file
- Files accepted currently is with CSV format, in the near future it will develop to xlsx format
- It is crucial to upload the data file has the correct format with the data from tiktok seller center, strongly recommend to use the file has just been exported from tiktok seller center
- After uploading the file, user can view the raw data before processing in data preview expander tab

#### Section 2: Cast columns
- Multiple columns are not in their correct format or the user's desired format, therefore it should be casted either to string or numeric format
- You can only choose the columns that exists in the dataframe, several columns have been set as default to be casted

#### Section 3: Clean columns
- The columns 
