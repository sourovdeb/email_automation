import pandas as pd
from PyPDF2 import PdfReader
import os

COMPANY_NAME_COLUMNS = ['Raison sociale', 'NOM', 'Company', 'Entreprise', 'Name', 'ENTREPRISE', 'Société']
EMAIL_COLUMNS = ['Email', 'email', 'E-mail', 'Mail', 'Courriel', 'MAIL', 'EMAIL']


def detect_company_name_column(df):
    for col in COMPANY_NAME_COLUMNS:
        if col in df.columns:
            return col
    return df.columns[0]


def detect_email_column(df):
    for col in EMAIL_COLUMNS:
        if col in df.columns:
            return col
    for col in df.columns:
        sample = df[col].dropna().astype(str)
        if sample.str.contains('@').mean() > 0.3:
            return col
    return None


def read_company_list(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return None
        df = pd.read_excel(file_path)
        name_col = detect_company_name_column(df)
        email_col = detect_email_column(df)
        print(f"Company list loaded: {len(df)} rows | name column='{name_col}' | email column={email_col!r}")
        return df, name_col, email_col
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None


def extract_cv_text(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"Error: CV not found at {file_path}")
            return None
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        print(f"CV extracted: {len(text)} characters")
        return text
    except Exception as e:
        print(f"Error reading CV PDF: {e}")
        return None


def extract_motivation_letter(file_path):
    try:
        if not os.path.exists(file_path):
            return None
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        print(f"Motivation letter extracted: {len(text)} characters")
        return text
    except Exception as e:
        print(f"Error reading motivation letter: {e}")
        return None


if __name__ == '__main__':
    result = read_company_list("/home/sourov/Documents/employment/unemploistablecestpartimisedispositiondeconse/260 Plus grosses entreprises 974 Filtre.xlsx")
    if result:
        df, name_col, email_col = result
        print(f"\nFirst 5 companies (column: {name_col}):")
        print(df[[name_col]].head())

    cv = extract_cv_text("/home/sourov/Documents/employment/rerappelrdvfrancetravailuesaaxeressourceconseilst/Formateurd_Anglais_Certifié_CELTA_Cambridge_Spécialiste_IELTS_TOEIC_Business_English.pdf")
    if cv:
        print("\nCV excerpt:", cv[:300])
