# CRM Export Transformer

## Project Overview

This project automates the cleanup of a messy CRM export file and prepares the data for import into another sales or outreach platform.

The workflow is based on a common business process where customer records are exported from one CRM, cleaned manually in a spreadsheet, and then imported into another system. This project replaces much of that manual cleanup with a Python script.

All data used in this project is synthetic. No real customer, company, or private data is included. Email addresses and mobile numbers are masked in the public output files for privacy and security.

## Business Problem

Manual CRM data cleanup can be time-consuming and error-prone. Common issues include inconsistent formatting, duplicate records, missing contact information, invalid phone numbers, inconsistent state values, and lack of visibility into records that need review.

This project solves that problem by transforming a messy raw export into three organized outputs:

- A clean import-ready file
- A needs-review file for records that require human attention
- A duplicate records file for audit tracking

## Tools Used

- Python
- pandas
- CSV files
- Command Prompt
- Git/GitHub

## Cleaning Rules

The script performs the following cleanup steps:

- Deletes the `Billing State/Province` column
- Renames `Contact: Mobile` to `Mobile`
- Renames `Contact: Email` to `Email`
- Converts emails to lowercase
- Converts first and last names to title case
- Formats mobile numbers as `(xxx) xxx-xxxx`
- Standardizes state values to two-letter abbreviations
- Validates emails and phone numbers before masking sensitive fields
- Removes duplicate records by `CRM Id`
- Removes duplicate records by `Email`
- Sends incomplete or invalid records to a review file
- Masks email addresses and mobile numbers in public output files for privacy

## Required Fields

Rows are sent to review if any of these fields are missing or invalid:

- `CRM Id`
- `Contact: First Name`
- `Contact: Last Name`
- `Mobile`
- `Email`
- `Status`
- `State`

## Project Structure

```text
crm-export-transformer/
├── data/
│   ├── raw_export.csv
│   ├── close_import_ready.csv
│   ├── needs_review.csv
│   └── duplicate_records_removed.csv
├── scripts/
│   └── transform_data.py
├── README.md
└── requirements.txt
```

## Output Files

### close_import_ready.csv

Contains records that passed all validation rules and are ready for import. Email addresses and mobile numbers are masked in this public output file.

### needs_review.csv

Contains records that failed one or more validation rules. A `Review Reason` column explains what needs to be fixed. Email addresses and mobile numbers are masked in this public output file.

### duplicate_records_removed.csv

Contains records removed as duplicates, along with a `Duplicate Reason` column. Email addresses and mobile numbers are masked in this public output file.

## Results From Sample Run

```text
Rows loaded: 40
Duplicate CRM Id rows removed: 0
Duplicate Email rows removed: 1
Rows after duplicate removal: 39
Clean rows exported: 14
Review rows exported: 25
Duplicate rows exported: 1
Sensitive fields masked in output files: Email, Mobile
```

## How to Run This Project

Install the required package:

```bash
pip install -r requirements.txt
```

Run the script from the main project folder:

```bash
python scripts\transform_data.py
```

## What I Learned

This project helped me practice building a practical data automation workflow using Python and pandas. It reinforced the importance of data validation, duplicate handling, audit trails, and separating clean records from records that need human review.

I also added privacy-focused output masking so sensitive fields can be used for validation and duplicate detection without being exposed in public files.

## Future Improvements

Possible future improvements include:

- Add SQL validation queries
- Create a summary report
- Add automated tests
- Add Google Sheets integration
- Build a dashboard showing import readiness and data quality metrics
