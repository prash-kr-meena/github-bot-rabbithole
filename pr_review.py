#!/usr/bin/env python3
"""
GitHub PR Review Module - Provides functionality for reviewing pull requests using AI.

This module handles repository cloning, diff analysis, and integration with the Anthropic API
to generate code reviews for pull requests.
"""

import os
import subprocess
import base64
import tempfile
import shutil
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.rabbithole.cred.club")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
GITHUB_PAT = os.getenv("GITHUB_PAT")

# Initialize Anthropic client
def initialize_anthropic_client():
    """Initialize the Anthropic client with configuration from environment variables."""
    try:
        # Try with just the required parameters
        return Anthropic(
            api_key=ANTHROPIC_API_KEY,
            base_url=ANTHROPIC_BASE_URL
        )
    except TypeError as e:
        # If there's a TypeError, it might be due to parameter issues
        print(f"Error initializing Anthropic client with base_url: {e}")
        # Try without base_url if that's causing issues
        return Anthropic(api_key=ANTHROPIC_API_KEY)

def clone_repository(repo_full_name, branch="main"):
    """Clone a GitHub repository to the local .repos directory.
    
    Args:
        repo_full_name (str): The full name of the repository (e.g., "username/repo")
        branch (str): The branch to checkout (default: "main")
        
    Returns:
        str: The path to the cloned repository
    """
    repo_dir = os.path.join(".repos", repo_full_name.replace("/", "_"))
    
    # Create .repos directory if it doesn't exist
    if not os.path.exists(".repos"):
        os.makedirs(".repos")
    
    if os.path.exists(repo_dir):
        # Update existing repository
        print(f"Updating existing repository: {repo_full_name}")
        subprocess.run(["git", "-C", repo_dir, "fetch", "--all"], check=True)
        subprocess.run(["git", "-C", repo_dir, "checkout", branch], check=True)
        subprocess.run(["git", "-C", repo_dir, "pull"], check=True)
    else:
        # Clone new repository
        print(f"Cloning repository: {repo_full_name}")
        clone_url = f"https://github.com/{repo_full_name}.git"
        subprocess.run(["git", "clone", clone_url, repo_dir], check=True)
        subprocess.run(["git", "-C", repo_dir, "checkout", branch], check=True)
    
    return repo_dir

def get_file_diff(repo_dir, file_path, base_branch="main", head_branch="HEAD"):
    """Get the diff for a specific file between two branches.
    
    Args:
        repo_dir (str): Path to the repository
        file_path (str): Path to the file
        base_branch (str): Base branch for comparison
        head_branch (str): Head branch for comparison
        
    Returns:
        str: The diff output for the file
    """
    try:
        result = subprocess.run(
            ["git", "-C", repo_dir, "diff", f"{base_branch}..{head_branch}", "--", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting diff for {file_path}: {e}")
        return None

def identify_changed_sections(diff_output):
    """Parse a git diff output to identify changed sections of code.
    
    Args:
        diff_output (str): Git diff output
        
    Returns:
        list: List of dictionaries containing information about changed sections
    """
    if not diff_output:
        return []
    
    sections = []
    current_section = None
    current_line_number = 0
    
    for line in diff_output.split('\n'):
        if line.startswith('@@'):
            # Parse the @@ -a,b +c,d @@ line to get line numbers
            parts = line.split(' ')
            if len(parts) >= 3:
                # Extract the +c,d part
                added_info = parts[2]
                if added_info.startswith('+'):
                    line_info = added_info[1:].split(',')
                    start_line = int(line_info[0])
                    count = int(line_info[1]) if len(line_info) > 1 else 1
                    
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = {
                        'start_line': start_line,
                        'end_line': start_line + count - 1,
                        'content': [],
                        'header': line,
                        'changed_lines': []  # Track individual changed lines
                    }
                    current_line_number = start_line
        elif current_section is not None:
            if line.startswith('+') and not line.startswith('+++'):
                # This is an added line
                current_section['content'].append(line[1:])
                # Track the specific line with its content
                current_section['changed_lines'].append({
                    'line_number': current_line_number,
                    'content': line[1:],
                    'type': 'added'
                })
            elif line.startswith(' '):
                # This is an unchanged line
                pass
            elif not line.startswith('-'):
                # This is not a removed line, so increment the line counter
                pass
            
            # Increment line number for non-removed lines
            if not line.startswith('-'):
                current_line_number += 1
    
    if current_section:
        sections.append(current_section)
    
    return sections

def analyze_code_patterns(file_content, file_path):
    """Analyze code patterns to identify the technology stack and common patterns.
    
    Args:
        file_content (str): The content of the file
        file_path (str): The path of the file
        
    Returns:
        dict: Information about the technology and patterns
    """
    tech_info = {
        'language': 'unknown',
        'frameworks': [],
        'patterns': [],
        'imports': []
    }
    
    # Determine language based on file extension
    ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    if ext == 'py':
        tech_info['language'] = 'python'
        
        # Look for common Python frameworks
        if 'import flask' in file_content.lower() or 'from flask import' in file_content.lower():
            tech_info['frameworks'].append('flask')
        if 'import django' in file_content.lower() or 'from django import' in file_content.lower():
            tech_info['frameworks'].append('django')
        if 'import pandas' in file_content.lower() or 'from pandas import' in file_content.lower():
            tech_info['frameworks'].append('pandas')
        if 'import numpy' in file_content.lower() or 'from numpy import' in file_content.lower():
            tech_info['frameworks'].append('numpy')
        if 'import tensorflow' in file_content.lower() or 'from tensorflow import' in file_content.lower():
            tech_info['frameworks'].append('tensorflow')
        if 'import torch' in file_content.lower() or 'from torch import' in file_content.lower():
            tech_info['frameworks'].append('pytorch')
            
        # Extract imports
        import_lines = []
        for line in file_content.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                import_lines.append(line)
        tech_info['imports'] = import_lines
        
        # Identify common patterns
        if 'class ' in file_content and ('def __init__' in file_content or 'def __init__(self' in file_content):
            tech_info['patterns'].append('object_oriented')
        if 'async def ' in file_content:
            tech_info['patterns'].append('async')
        if '@app.route' in file_content:
            tech_info['patterns'].append('flask_routes')
        if '@dataclass' in file_content:
            tech_info['patterns'].append('dataclasses')
        
    elif ext in ['js', 'jsx', 'ts', 'tsx']:
        tech_info['language'] = 'javascript' if ext in ['js', 'jsx'] else 'typescript'
        
        # Look for common JS/TS frameworks
        if 'import React' in file_content or 'from "react"' in file_content:
            tech_info['frameworks'].append('react')
        if 'import { Component' in file_content:
            tech_info['frameworks'].append('angular')
        if 'import Vue' in file_content:
            tech_info['frameworks'].append('vue')
        if 'express' in file_content.lower():
            tech_info['frameworks'].append('express')
            
        # Identify common patterns
        if 'class ' in file_content and 'constructor' in file_content:
            tech_info['patterns'].append('object_oriented')
        if 'function*' in file_content or 'yield ' in file_content:
            tech_info['patterns'].append('generators')
        if '=>' in file_content:
            tech_info['patterns'].append('arrow_functions')
        if 'async ' in file_content:
            tech_info['patterns'].append('async')
            
    elif ext in ['java', 'kt']:
        tech_info['language'] = 'java' if ext == 'java' else 'kotlin'
        
        # Look for common Java frameworks
        if 'import org.springframework' in file_content:
            tech_info['frameworks'].append('spring')
        if 'import android' in file_content:
            tech_info['frameworks'].append('android')
            
    elif ext in ['rb']:
        tech_info['language'] = 'ruby'
        if 'Rails' in file_content:
            tech_info['frameworks'].append('rails')
            
    elif ext in ['go']:
        tech_info['language'] = 'go'
        
    elif ext in ['php']:
        tech_info['language'] = 'php'
        if 'Laravel' in file_content:
            tech_info['frameworks'].append('laravel')
            
    elif ext in ['cs']:
        tech_info['language'] = 'csharp'
        if 'using Microsoft.AspNetCore' in file_content:
            tech_info['frameworks'].append('aspnet')
            
    elif ext in ['html', 'htm']:
        tech_info['language'] = 'html'
        
    elif ext in ['css', 'scss', 'sass', 'less']:
        tech_info['language'] = ext
        
    return tech_info

def get_file_content_from_repo(repo_dir, file_path):
    """Get the content of a file from the local repository.
    
    Args:
        repo_dir (str): Path to the repository
        file_path (str): Path to the file
        
    Returns:
        str: The content of the file
    """
    full_path = os.path.join(repo_dir, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def generate_code_review_prompt(file_info, pr_info):
    """Generate a prompt for code review based on file and PR information.
    
    Args:
        file_info (dict): Information about the file being reviewed
        pr_info (dict): Information about the pull request
        
    Returns:
        str: The prompt for the AI code review
    """
    # Determine the language based on file extension
    file_path = file_info.get('path', '')
    ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    language_specific_guidelines = ""
    if ext == 'py':
        language_specific_guidelines = """
### Python-Specific Best Practices
- Does the code follow PEP 8 style guidelines?
- Are list comprehensions used instead of loops where appropriate?
- Are context managers (with statements) used properly?
- Are generator expressions used for large data?
- Is isinstance() preferred over type checking?
- Are f-strings used for formatting (Python 3.6+)?
- Is pathlib used instead of os.path?
- Are exceptions preferred over error codes?
- Are specific exceptions used instead of bare except clauses?
- Are type annotations added (PEP 484)?
- Are built-in functions/methods used effectively?
- Is string concatenation done efficiently?
- Are collections module data structures used appropriately?
- Is logging used instead of print()?
"""
    elif ext in ['js', 'jsx', 'ts', 'tsx']:
        language_specific_guidelines = """
### JavaScript/TypeScript-Specific Best Practices
- Is ES6+ syntax used appropriately?
- Are promises and async/await used correctly?
- Are const/let used instead of var?
- Is destructuring used for cleaner code?
- Are arrow functions used where appropriate?
- Are template literals used for string interpolation?
- Are spread/rest operators used effectively?
- Is proper error handling implemented for async operations?
- Are default parameters used where appropriate?
- Are optional chaining and nullish coalescing used for safer code?
- Is proper module import/export syntax used?
"""
    
    # Extract changed lines for more targeted review
    changed_lines = []
    for section in file_info.get('changed_sections', []):
        if 'changed_lines' in section:
            for line_info in section['changed_lines']:
                changed_lines.append(f"Line {line_info['line_number']}: {line_info['content']}")
    
    changed_lines_text = "\n".join(changed_lines) if changed_lines else "No specific changed lines identified."
    
    prompt = f"""
# Code Review Request

## Pull Request Information
- **Title**: {pr_info.get('title', 'N/A')}
- **Description**: {pr_info.get('description', 'N/A')}
- **Author**: {pr_info.get('author', 'N/A')}
- **File**: {file_info.get('path', 'N/A')}

## Review Task
You are a senior software engineer conducting a code review. I need you to provide a DETAILED and SPECIFIC code review with exact line numbers for each issue you identify. Focus on providing actionable feedback for each problematic line of code.

### File Context (Full File)
```
{file_info.get('full_content', 'No content available')}
```

### Changes Made (Diff)
```diff
{file_info.get('diff', 'No diff available')}
```

### Specific Changed Lines
{changed_lines_text}

## Review Guidelines
Please focus on the following aspects in your review:

### Code Quality
- Is the code self-documenting with meaningful names?
- Does it follow the DRY principle?
- Are functions/methods small and focused?
- Is there consistent indentation and formatting?
- Are magic numbers/strings avoided in favor of named constants?
- Does the code follow SOLID principles?
- Is there proper error handling?
- Are global variables avoided?
- Is cyclomatic complexity kept low?

### Security
- Is all external input validated?
- Is output properly sanitized to prevent injection?
- Are parameterized queries used for databases?
- Are secrets stored securely (not in code)?
- Is proper authentication/authorization implemented?
- Is HTTPS used for network communication?
- Are proper file permissions set?
- Is eval() or exec() avoided with user input?

{language_specific_guidelines}

### Critical Issues to Flag
- Mutating objects while iterating
- Using 'is' for value comparison (instead of just None/singletons)
- Mutable default arguments
- Missing context managers for resources
- Broad exception catching
- Ignoring exceptions silently

## Review Format
IMPORTANT: Your review MUST follow this exact format:

1. **Summary**: A brief overview of the code quality and main issues

2. **Line-by-Line Issues**: For EACH issue you find, include:
   - The exact line number
   - A description of the issue
   - A code example showing how to fix it
   - Format each issue as: "Line X: [Issue description] - [Suggested fix]"

3. **Positive Aspects**: Highlight good practices in the code with specific line references

Your review must be extremely specific with exact line numbers for each issue. Do not use vague references like "in this function" or "this section". Always specify the exact line number for each issue or positive aspect you mention.

Focus on being constructive and educational in your feedback. Prioritize the most important issues rather than listing every minor detail.
"""
    return prompt

def get_ai_code_review(file_info, pr_info):
    """Get an AI-generated code review for a file in a pull request.
    
    Args:
        file_info (dict): Information about the file being reviewed
        pr_info (dict): Information about the pull request
        
    Returns:
        str: The AI-generated code review
    """
    try:
        client = initialize_anthropic_client()
        prompt = generate_code_review_prompt(file_info, pr_info)
        
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as api_error:
            print(f"Error calling Anthropic API: {api_error}")
            # Fallback to a basic review
            return generate_fallback_review(file_info)
    except Exception as e:
        print(f"Error generating AI code review: {e}")
        return generate_fallback_review(file_info)

def generate_fallback_review(file_info):
    """Generate a basic fallback review when the AI review fails.
    
    Args:
        file_info (dict): Information about the file being reviewed
        
    Returns:
        str: A basic code review
    """
    file_path = file_info.get('path', 'Unknown file')
    changed_sections = file_info.get('changed_sections', [])
    num_sections = len(changed_sections)
    
    review = f"""
# Code Review for {file_path}

## Summary
This is an automated review of the changes in this file. The AI-powered review could not be generated, so this is a basic structural review.

## Changes Overview
- File: {file_path}
- Number of changed sections: {num_sections}
"""
    
    if num_sections > 0:
        review += "\n## Changed Sections\n"
        for i, section in enumerate(changed_sections):
            start_line = section.get('start_line', 'Unknown')
            end_line = section.get('end_line', 'Unknown')
            review += f"\n### Section {i+1} (Lines {start_line}-{end_line})\n"
            review += "Changes were made in this section. Please review for:\n"
            review += "- Code correctness\n"
            review += "- Potential bugs\n"
            review += "- Code style and best practices\n"
            review += "- Performance considerations\n"
    
    review += """
## Recommendations
1. Review the changes manually for any potential issues
2. Ensure proper error handling is in place
3. Check for consistent coding style
4. Verify that the changes meet the requirements

Note: This is a fallback review generated because the AI-powered review system encountered an error.
"""
    
    return review

def analyze_pr_file(repo_dir, file_info, base_branch, head_branch):
    """Analyze a file in a pull request and prepare it for review.
    
    Args:
        repo_dir (str): Path to the repository
        file_info (dict): Information about the file from GitHub API
        base_branch (str): Base branch for comparison
        head_branch (str): Head branch for comparison
        
    Returns:
        dict: Enhanced file information with content and diff
    """
    file_path = file_info.get('filename')
    
    # Get the full content of the file
    full_content = get_file_content_from_repo(repo_dir, file_path)
    
    # Get the diff for the file
    diff = get_file_diff(repo_dir, file_path, base_branch, head_branch)
    
    # Identify changed sections
    changed_sections = identify_changed_sections(diff)
    
    return {
        'path': file_path,
        'full_content': full_content,
        'diff': diff,
        'changed_sections': changed_sections,
        'status': file_info.get('status'),
        'additions': file_info.get('additions'),
        'deletions': file_info.get('deletions'),
        'changes': file_info.get('changes')
    }

def review_pr_files(repo_full_name, pr_number, pr_files, base_branch, head_branch, pr_info):
    """Review files in a pull request using AI.
    
    Args:
        repo_full_name (str): The full name of the repository
        pr_number (int): The pull request number
        pr_files (list): List of files in the pull request
        base_branch (str): Base branch for comparison
        head_branch (str): Head branch for comparison
        pr_info (dict): Information about the pull request
        
    Returns:
        list: List of reviews for each file
    """
    # Clone the repository
    repo_dir = clone_repository(repo_full_name, head_branch)
    
    reviews = []
    
    for file_info in pr_files:
        # Skip deleted files
        if file_info.get('status') == 'removed':
            continue
        
        # Analyze the file
        enhanced_file_info = analyze_pr_file(repo_dir, file_info, base_branch, head_branch)
        
        # Generate AI review
        review = get_ai_code_review(enhanced_file_info, pr_info)
        
        reviews.append({
            'file': enhanced_file_info,
            'review': review
        })
    
    return reviews

if __name__ == "__main__":
    # This can be used for testing the module independently
    pass
