# -*- coding: utf-8 -*-
"""p.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13gVq_rA6wH6B5QzpQ_v2u9eOWHs9x4q7
"""

import streamlit as st
import difflib
import requests
import re
from urllib.parse import urlparse
import nbformat
from nbconvert import PythonExporter
from tokenize import tokenize, untokenize, NUMBER, STRING, NAME, OP
from io import BytesIO
import openai

import os
import streamlit as st

secrets = st.secrets

# Set your OpenAI API key
openai.api_key = secrets["Op"]

# Set your GitHub API key
github_api_key = secrets["gitAPI"]

# Rest of your code goes here
# ...


# # Set your OpenAI API key
# openai.api_key = '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'

# # Set your GitHub API key
# github_api_key = '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'

MAX_TOKENS = 1000  # Set the maximum token limit for GPT

@st.cache
def preprocess_code(repository):
    if 'code' in repository:
        code = repository['code']

        # Remove comments and whitespace
        code = re.sub(r'\/\/.*', '', code)  # Remove single-line comments
        code = re.sub(r'\/\*(\*(?!\/)|[^*])*\*\/', '', code)  # Remove multi-line comments
        code = code.strip()  # Remove leading/trailing whitespace
        code = re.sub(r'\s+', ' ', code)  # Collapse multiple consecutive spaces

        # Normalize variable and function names
        code = normalize_variable_names(code)
        code = normalize_function_names(code)

        # Extract code snippets from Jupyter notebooks
        if code.startswith('%') or code.startswith('!'):
            notebook = nbformat.reads(code, nbformat.NO_CONVERT)
            python_exporter = PythonExporter()
            (python_code, _) = python_exporter.from_notebook_node(notebook)
            code = python_code.strip()

        # Handle large file sizes (e.g., split into smaller chunks)
        if len(code) > MAX_TOKENS:
            # Split the code into smaller chunks to fit within the token limit
            chunks = []
            current_chunk = ""
            for line in code.split('\n'):
                if len(current_chunk + line) < MAX_TOKENS:
                    current_chunk += line + '\n'
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
            if current_chunk:
                chunks.append(current_chunk.strip())
            code = chunks

        # Convert code to a suitable format for analysis (e.g., AST, tokenization)
        code = tokenize_code(code)

        # Apply preprocessing steps here
        preprocessed_code = code.strip()

        # Update the repository object or return the preprocessed code
        repository['code'] = preprocessed_code
        # Or return the preprocessed code directly: return preprocessed_code

    return repository

@st.cache
def normalize_variable_names(code):
    code = re.sub(r'\bvar\b', 'normalized_var', code)
    return code


@st.cache
def normalize_function_names(code):
    code = re.sub(r'\bfunc\b', 'normalized_func', code)
    return code


@st.cache
def tokenize_code(code):
    # Tokenize the code using Python's tokenize module
    tokens = tokenize(BytesIO(code.encode('utf-8')).readline)

    # Filter out tokens that are not relevant for analysis
    filtered_tokens = [
        token for token in tokens
        if token.type in (NUMBER, STRING, NAME, OP)
    ]

    # Untokenize the filtered tokens to obtain the transformed code
    transformed_code = untokenize(filtered_tokens).decode('utf-8')

    return transformed_code



@st.cache
def assess_repository(repository):
    # Implement prompt engineering when passing code through GPT for evaluation to determine its technical complexity

    # Extract the name and description from the repository
    name = repository['name'] or ""
    description = repository['description'] or ""

    # Generate a textual description/summary of the repository using GPT
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=name + "\n" + description,
        max_tokens=100
    )
    summary = response.choices[0].text.strip()

    # Assess the technical complexity of the repository based on the generated summary
    complexity_score = len(summary.split(' '))  # Placeholder value

    return complexity_score

@st.cache
def analyze_repository(repository):
    if 'code' in repository:
        code = repository['code']

        # Calculate code size
        lines_of_code = len(code.split('\n'))

        # Calculate code duplication impact
        duplication_impact = calculate_duplication_impact(code)

        # Calculate complexity score based on code size and duplication impact
        complexity_score = lines_of_code + duplication_impact

        return complexity_score
    else:
        return 0

@st.cache
def calculate_duplication_impact(code):
    # Identify duplicated code snippets and measure their impact
    duplicated_code = find_duplicated_code(code)

    # Calculate the impact of code duplication
    duplication_impact = len(duplicated_code) * 0.5  # Placeholder value

    return duplication_impact

@st.cache
def find_duplicated_code(code):
    # Example using difflib to find similar lines of code
    lines = code.split('\n')
    duplicated_code = []

    for i, line in enumerate(lines):
        for j in range(i + 1, len(lines)):
            similarity = difflib.SequenceMatcher(None, line, lines[j]).ratio()
            if similarity > 0.8:  # Adjust the similarity threshold as needed
                duplicated_code.append(line)

    return duplicated_code

def get_most_challenging_repository(profile_url):
    # Extract the username from the GitHub profile URL
    parsed_url = urlparse(profile_url)
    if parsed_url.netloc == 'github.com':
        path_parts = parsed_url.path.split('/')
        if len(path_parts) >= 2:
            username = path_parts[1]
        else:
            print("Invalid GitHub profile URL.")
            return None
    else:
        print("Invalid GitHub profile URL.")
        return None

    # Fetch user repositories from GitHub API
    headers = {
        'Authorization': f'token {github_api_key}'
    }
    response = requests.get(f'https://api.github.com/users/{username}/repos', headers=headers)
    repositories = response.json()

    most_challenging_repository = None
    highest_complexity_score = 0

    for repository in repositories:
        repository = preprocess_code(repository)
        complexity_score = analyze_repository(repository)
        complexity_challenge_score = assess_repository(repository)

        if complexity_challenge_score > highest_complexity_score:
            highest_complexity_score = complexity_challenge_score
            most_challenging_repository = repository

    return most_challenging_repository

# Set the title of the Streamlit app
st.title('Github Automated Analysis')

# Create an input box for the user to enter the GitHub profile URL
github_profile_url = st.text_input('Enter GitHub Profile URL')

# Check if the user has entered a URL and pressed Enter
if github_profile_url and st.button('Enter'):
    # Call the function to get the most challenging repository
    most_challenging_repo = get_most_challenging_repository(github_profile_url)

    # Check if a repository was found
    if most_challenging_repo:
        # Generate a GPT analysis justifying the selection
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=f"I selected [{most_challenging_repo['name']}]({most_challenging_repo['html_url']}) as the most complex repository because...",
            max_tokens=100
        )
        gpt_analysis = response.choices[0].text.strip()

        # Display the result
        st.write("Most challenging repository:", most_challenging_repo['name'])
        st.write("Most challenging repository:", most_challenging_repo['html_url'])
        st.write("GPT Analysis:", gpt_analysis)
    else:
        st.write("No repositories found.")
