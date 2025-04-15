import google.generativeai as genai

genai.configure(api_key="AIzaSyAQjrz2GIJSame8yuxg2IJ1nmt_6s3Ad5s")

def compare_answers(model_answer, user_answer):
    query = f"""
    Compare the given answers. Model Answer: '{model_answer}'. 
    User Answer: '{user_answer}'. If the user's answer captures the meaning 
    of the model answer upto some extent, respond with TRUE. Otherwise, respond with FALSE. 
    Respond strictly with TRUE or FALSE only, no explanations. 
    """

    try:
        response = genai.GenerativeModel("gemini-1.5-flash-latest").generate_content(query)
        result = response.text.strip().upper()
        return "TRUE" if result == "TRUE" else "FALSE"
    except Exception as e:
        return f"Error: {str(e)}"
    
def compare_numeric(model_answer, user_answer):
    query = f"""
    compare the both model answer and user answer which are as follows:
    model answer : '{model_answer}',
    user answer : '{user_answer}',
    and respond strictly in true or false while considering all possible unit conversions, 
    appropriate decimal round-off, etc if unit is missing in user answer then return false. 
    """

    try:
        response = genai.GenerativeModel("gemini-1.5-flash-latest").generate_content(query)
        result = response.text.strip().upper()
        return "TRUE" if result == "TRUE" else "FALSE"
    except Exception as e:
        return f"Error: {str(e)}"