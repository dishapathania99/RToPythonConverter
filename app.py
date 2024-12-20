import os
import textwrap
import openai
from flask import Flask, render_template, request, url_for, send_from_directory

app = Flask(__name__)


# Folder paths for uploaded and converted files
UPLOAD_FOLDER = "UPLOAD_FOLDER"
PYTHON_FOLDER = "PYTHON_FOLDER"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PYTHON_FOLDER, exist_ok=True)

# Helper function to clear a folder
def clear_folder(folder_path):
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")


# Helper function to convert R code to Python
def convert_r_to_python(openai_key, r_code):
    """
    Converts R code to Python code using OpenAI API.
    Identifies if the input is valid R code and handles minor syntax errors.
    """
    prompt = f"""
    You are an expert programmer proficient in both R and Python. Your task is to:

    1. Identify whether the given input is valid R code.
    2. If the input is valid R code, or if it contains only minor syntax errors, convert it into equivalent Python 3.x code.
    3. Ensure the Python code generated is free of indentation errors or syntax issues and that all necessary libraries are imported at top.
    4. If the input is not valid R code (e.g., Python, Java, JavaScript, or any other non-R language), or if the input is gibberish, return the error message: 
    "Error: The provided input is not valid R code."

    Instructions:
    - **Only convert the input if it is valid R code or contains minor syntax errors that can be easily fixed.**
    - If the input includes code from other languages (e.g., Python, Java, JavaScript) or gibberish, **do not attempt to convert it**. Instead, return: "Error: The provided input is not valid R code."
    - The output should either be the converted Python code or the error message, without any explanations, comments, or additional text.

    Here is the input:
    {r_code}

    """
    try:
        openai.api_key = openai_key
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0,
            max_tokens=1500,
        )
        output = response.choices[0].text.strip()

        # If the response starts with "Error:", raise a ValueError
        if output.startswith("Error:"):
            raise ValueError(output)

        return output
    except Exception as e:
        raise Exception(f"Error during R to Python conversion: {e}")


@app.route('/', methods=['GET', 'POST'])
def RToPythonConverter():
    """
    Handles R to Python conversion, both from code snippets and file uploads.
    """
    if request.method == 'POST':
        openai_key = request.form.get('openai_key', '').strip()
        action = request.form.get('action')
        error_message = None
        python_code = ""
        download_link = None
        success_message = None

        # Validate OpenAI API Key
        if not openai_key:
            error_message = "The OpenAI API key is required for conversion. Please enter a valid key."
            return render_template(
                'RtoPythonConverter.html',
                error_message=error_message
            )

        # Handle R Code Snippet Conversion
        if action == 'convert':
            r_code = request.form.get('r_code', '').strip()
            if not r_code:
                error_message = "Please enter some R code to convert."
            else:
                try:
                    # Convert R code to Python
                    python_code = convert_r_to_python(openai_key, r_code)
                    # Clean up indentation
                    python_code = textwrap.dedent(python_code)
                    # Skip Python code validation
                    success_message = "Converted successfully!"
                except ValueError as ve:
                    error_message = str(ve)
                except Exception as e:
                    error_message = str(e)

            # Render response with either the Python code or error message
            return render_template(
                'RtoPythonConverter.html',
                r_code=r_code,
                python_code=python_code,
                error_message=error_message,
                success_message=success_message
            )

        # Handle R File Upload and Conversion
        elif action == 'upload_convert':
            uploaded_file = request.files.get('r_file')
            r_code = ""
            python_code = ""
            error_message = None
            success_message = None
            download_link = None

            if not uploaded_file or not (uploaded_file.filename.endswith('.R') or uploaded_file.filename.endswith('.r')):
                error_message = "The uploaded file must be a valid R file with the extension .R or .r."
            else:
                try:
                    # Clear the upload and Python folders
                    clear_folder(UPLOAD_FOLDER)
                    clear_folder(PYTHON_FOLDER)

                    # Save the uploaded R file
                    uploaded_file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
                    uploaded_file.save(uploaded_file_path)

                    # Read the R code from the file
                    with open(uploaded_file_path, 'r', encoding='utf-8') as file:
                        r_code = file.read()

                    # Convert R code to Python code
                    try:
                        python_code = convert_r_to_python(openai_key, r_code)

                        # Clean up indentation
                        python_code = textwrap.dedent(python_code)

                        # Skip Python code validation
                        success_message = "File converted successfully! You can download the Python file."
                    except ValueError as ve:
                        error_message = str(ve)  # This will handle the "not valid R code" case.

                    # Save the Python file regardless of validation status
                    python_file_name = os.path.splitext(uploaded_file.filename)[0] + ".py"
                    python_file_path = os.path.join(PYTHON_FOLDER, python_file_name)
                    with open(python_file_path, 'w', newline='\n', encoding='utf-8') as file:
                        file.write(python_code)

                    # Provide download link
                    download_link = url_for('download_file', filename=python_file_name)

                except Exception as e:
                    error_message = str(e)

            # Render the response based on the validation results
            return render_template(
                'RtoPythonConverter.html',
                error_message=error_message,
                download_link=download_link,
                success_message=success_message
            )
    # Render initial page (GET request)
    return render_template('RtoPythonConverter.html')


@app.route('/download/<filename>')
def download_file(filename):
    """
    Allows downloading of the converted Python file.
    """
    return send_from_directory(PYTHON_FOLDER, filename, as_attachment=True)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
