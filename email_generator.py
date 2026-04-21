def generate_email_body(cv_text, company_info, company_research):
    """
    Generates a personalized email body.

    Args:
        cv_text (str): The text extracted from the user's CV.
        company_info (pandas.Series): A row from the company DataFrame.
        company_research (str): Text scraped from the company's website.

    Returns:
        str: A personalized email body.
    """
    company_name = company_info.get('NOM') # Assuming 'NOM' is the column name for the company name

    # Simple keyword matching from CV. This can be made more sophisticated.
    skills = []
    if "English" in cv_text and "CELTA" in cv_text:
        skills.append("a CELTA-certified English Trainer")
    if "management" in cv_text.lower():
        skills.append("experienced in project management")
    
    skills_str = " and ".join(skills) if skills else "a dedicated professional"

    # Extract a sentence from the company research
    opening_hook = ""
    if company_research:
        # Find a sentence that seems interesting. This is a very basic heuristic.
        sentences = company_research.split('.')
        for sentence in sentences:
            if "mission" in sentence.lower() or "value" in sentence.lower() or "innovative" in sentence.lower():
                opening_hook = sentence.strip() + "."
                break
        if not opening_hook: # fallback
            opening_hook = sentences[0].strip() + "." if sentences else ""
    
    if not opening_hook:
        opening_hook = f"I am writing to express my interest in potential opportunities at {company_name}."


    email_body = f"""
Dear Hiring Manager at {company_name},

I hope you are well. {opening_hook}

I am reaching out because my background as {skills_str} can support your team, especially in clear professional communication, learner progress, and practical outcomes.

I have attached my CV for quick review. If relevant, I would value a short conversation to understand your current needs and how I can contribute.

Thank you for your time and consideration.

Kind regards,
Sourov Deb
"""
    return email_body.strip()

if __name__ == '__main__':
    # This is for testing purposes
    
    # Mock CV text
    mock_cv = "Sourov Deb. An experienced and CELTA-certified English Trainer. Skilled in project management and business communication."
    
    # Mock company info (as a pandas Series)
    import pandas as pd
    mock_company = pd.Series({'NOM': 'Global Innovations Inc.'})
    
    # Mock company research
    mock_research = "Global Innovations Inc. is a leader in the tech industry. Our mission is to drive progress through innovative solutions. We value creativity and collaboration."

    email = generate_email_body(mock_cv, mock_company, mock_research)
    print(email)
