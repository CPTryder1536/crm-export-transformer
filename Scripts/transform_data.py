import pandas as pd
import re

INPUT_FILE = "data/raw_export.csv"
OUTPUT_FILE = "data/close_import_ready.csv"
REVIEW_FILE = "data/needs_review.csv"
DUPLICATES_FILE = "data/duplicate_records_removed.csv"


STATE_MAP = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
    "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
    "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
    "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI", "WYOMING": "WY", "DISTRICT OF COLUMBIA": "DC"
}

VALID_STATES = set(STATE_MAP.values())


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def title_case(value):
    value = clean_text(value)
    return value.title() if value else ""


def clean_email(value):
    value = clean_text(value).lower()
    return value


def is_valid_email(value):
    if not value:
        return False
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, value))


def clean_mobile(value):
    value = clean_text(value)
    digits = re.sub(r"\D", "", value)

    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    if len(digits) != 10:
        return ""

    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def clean_state(value):
    value = clean_text(value).upper()

    if not value:
        return ""

    if value in VALID_STATES:
        return value

    if value in STATE_MAP:
        return STATE_MAP[value]

    return ""


def remove_duplicates(df):
    duplicate_records = []

    # Remove duplicate CRM IDs.
    # Blank CRM IDs are kept so they can be reviewed instead of being treated as duplicates.
    crm_not_blank = df["CRM Id"].astype(str).str.strip() != ""

    crm_duplicates = df[crm_not_blank & df.duplicated(subset=["CRM Id"], keep="first")].copy()
    if not crm_duplicates.empty:
        crm_duplicates["Duplicate Reason"] = "Duplicate CRM Id"
        duplicate_records.append(crm_duplicates)

    df = df[~(crm_not_blank & df.duplicated(subset=["CRM Id"], keep="first"))].copy()

    # Remove duplicate emails.
    # Blank emails are kept so they can be reviewed instead of being treated as duplicates.
    email_not_blank = df["Email"].astype(str).str.strip() != ""

    email_duplicates = df[email_not_blank & df.duplicated(subset=["Email"], keep="first")].copy()
    if not email_duplicates.empty:
        email_duplicates["Duplicate Reason"] = "Duplicate Email"
        duplicate_records.append(email_duplicates)

    df = df[~(email_not_blank & df.duplicated(subset=["Email"], keep="first"))].copy()

    if duplicate_records:
        duplicates_df = pd.concat(duplicate_records, ignore_index=True)
    else:
        duplicates_df = pd.DataFrame(columns=list(df.columns) + ["Duplicate Reason"])

    crm_duplicates_removed = len(crm_duplicates)
    email_duplicates_removed = len(email_duplicates)

    return df.reset_index(drop=True), duplicates_df, crm_duplicates_removed, email_duplicates_removed


def main():
    df = pd.read_csv(INPUT_FILE)

    rows_loaded = len(df)

    # Drop unwanted column
    if "Billing State/Province" in df.columns:
        df = df.drop(columns=["Billing State/Province"])

    # Drop blank unnamed columns, if any exist
    unnamed_columns = [col for col in df.columns if str(col).startswith("Unnamed")]
    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    # Rename columns
    df = df.rename(columns={
        "Contact: Mobile": "Mobile",
        "Contact: Email": "Email"
    })

    # Strip whitespace from all object columns
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(clean_text)

    # Standardize fields
    df["Contact: First Name"] = df["Contact: First Name"].apply(title_case)
    df["Contact: Last Name"] = df["Contact: Last Name"].apply(title_case)
    df["Email"] = df["Email"].apply(clean_email)
    df["Mobile"] = df["Mobile"].apply(clean_mobile)
    df["State"] = df["State"].apply(clean_state)

    # Remove duplicates and save duplicate records for audit trail
    df, duplicates_df, crm_duplicates_removed, email_duplicates_removed = remove_duplicates(df)

    required_fields = [
        "CRM Id",
        "Contact: First Name",
        "Contact: Last Name",
        "Mobile",
        "Email",
        "Status",
        "State"
    ]

    review_reasons = []

    for _, row in df.iterrows():
        reasons = []

        for field in required_fields:
            if pd.isna(row[field]) or str(row[field]).strip() == "":
                reasons.append(f"Missing {field}")

        if row["Email"] and not is_valid_email(row["Email"]):
            reasons.append("Invalid Email")

        if str(row["Mobile"]).strip() == "":
            reasons.append("Invalid Mobile")

        if str(row["State"]).strip() == "":
            reasons.append("Invalid State")

        review_reasons.append("; ".join(reasons))

    df["Review Reason"] = review_reasons

    clean_df = df[df["Review Reason"] == ""].copy()
    review_df = df[df["Review Reason"] != ""].copy()

    clean_df.to_csv(OUTPUT_FILE, index=False)
    review_df.to_csv(REVIEW_FILE, index=False)
    duplicates_df.to_csv(DUPLICATES_FILE, index=False)

    print(f"Rows loaded: {rows_loaded}")
    print(f"Duplicate CRM Id rows removed: {crm_duplicates_removed}")
    print(f"Duplicate Email rows removed: {email_duplicates_removed}")
    print(f"Rows after duplicate removal: {len(df)}")
    print(f"Clean rows exported: {len(clean_df)}")
    print(f"Review rows exported: {len(review_df)}")
    print(f"Duplicate rows exported: {len(duplicates_df)}")


if __name__ == "__main__":
    main()