import pandas as pd
from PyPDF2 import PdfReader
import os

def read_company_list(file_path):
    """
    Reads the company list from an Excel file.

    Args:
        file_path (str): The absolute path to the Excel file.

    Returns:
        pandas.DataFrame: A DataFrame containing the company data, or None if an error occurs.
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Error: The file was not found at {file_path}")
            return None
        
        df = pd.read_excel(file_path)
        print("Successfully loaded company list.")
        return df
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        return None

def extract_cv_text(file_path):
    """
    Extracts text from a PDF file.

    Args:
        file_path (str): The absolute path to the PDF file.

    Returns:
        str: The extracted text from the PDF, or None if an error occurs.
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Error: The file was not found at {file_path}")
            return None

        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        print("Successfully extracted text from CV.")
        return text
    except Exception as e:
        print(f"An error occurred while reading the PDF file: {e}")
        return None

if __name__ == '__main__':
    # This is for testing purposes.
    # Replace with the actual paths to your files.
    # Make sure to use absolute paths.
    
    # Test reading the company list
    # Example: company_file = "/home/sourov/Documents/employment/unemploistablecestpartimisedispositiondeconse/260 Plus grosses entreprises 974 Filtre.xlsx"
    company_file = "path/to/your/260 Plus grosses entreprises 947 Filtre.xlsx"
    companies_df = read_company_list(company_file)
    if companies_df is not None:
        print("\nFirst 5 companies:")
        print(companies_df.head())

    # Test extracting text from the CV
    # Example: cv_file = "/home/sourov/Documents/employment/rerappelrdvfrancetravailuesaaxeressourceconseilst/Formateurd_Anglais_Certifié_CELTA_Cambridge_Spécialiste_IELTS_TOEIC_Business_English.pdf"
    cv_file = "path/to/your/cv.pdf"
    cv_text = extract_cv_text(cv_file)
    if cv_text is not None:
        print("\nCV Text (first 500 characters):")
        print(cv_text[:500])
