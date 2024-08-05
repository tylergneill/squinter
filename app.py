from flask import Flask, render_template, request
import difflib
import os
from typing import List

from nw import needleman_wunsch

app = Flask(__name__)

# Global variables to store file paths and differences
file1_path = ""
file2_path = ""
first_tier_chunks = []
current_index = 0

EXCERPT_PERCENTAGE = 10  # Set this to the desired percentage for truncation

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def get_first_x_percent_lines(content: str, excerpt_percentage: int) -> List[str]:
    lines = content.split("\n")
    return lines[:int(len(lines) * excerpt_percentage / 100)]

def compute_first_tier_differences(file1, file2):
    differ = difflib.ndiff(file1, file2)
    return list(differ)

def get_first_tier_chunks(differences):
    chunks = []
    chunk = []
    for line in differences:
        if line.startswith("  "):  # Unchanged line
            if chunk:
                chunks.append(chunk)
                chunk = []
        else:
            chunk.append(line)
    if chunk:
        chunks.append(chunk)
    return chunks

def highlight_character_differences(word_pairs):
    highlighted1, highlighted2 = [], []
    for word1, word2 in word_pairs:
        if word1 == word2:
            highlighted1.append(word1)
            highlighted2.append(word2)
        else:
            aligned1, aligned2 = needleman_wunsch(word1, word2)
            highlighted_word1, highlighted_word2 = [], []
            for char1, char2 in zip(aligned1, aligned2):
                if char1 == char2:
                    highlighted_word1.append(char1)
                    highlighted_word2.append(char2)
                else:
                    highlighted_word1.append(f"<span style='background-color: yellow; font-weight: bold;'>{char1}</span>")
                    highlighted_word2.append(f"<span style='background-color: yellow; font-weight: bold;'>{char2}</span>")
            highlighted1.append(''.join(highlighted_word1))
            highlighted2.append(''.join(highlighted_word2))
    return ' '.join(highlighted1), ' '.join(highlighted2)

def compute_second_tier_differences(text1, text2):
    words1 = text1.split()
    words2 = text2.split()
    aligned1, aligned2 = needleman_wunsch(words1, words2)
    word_pairs = []
    for i, (word1, word2) in enumerate(zip(aligned1, aligned2)):
        if word1 == word2 and i != 0:
            blank_word = '_' * (len(word1)//2)
            word_pairs.append((blank_word, blank_word))
        else:
            word_pairs.append((word1, word2))
    return word_pairs

@app.route('/', methods=['GET', 'POST'])
def index():
    global file1_path, file2_path, first_tier_chunks, current_index
    if request.method == 'POST':
        # Handle file selection
        if 'file1' in request.files and 'file2' in request.files:
            file1 = request.files['file1']
            file2 = request.files['file2']
            file1_path = os.path.join('uploads', file1.filename)
            file2_path = os.path.join('uploads', file2.filename)
            file1.save(file1_path)
            file2.save(file2_path)
            file1_excerpt = get_first_x_percent_lines(read_file(file1_path), EXCERPT_PERCENTAGE)
            file2_excerpt = get_first_x_percent_lines(read_file(file2_path), EXCERPT_PERCENTAGE)
            first_tier_differences = compute_first_tier_differences(file1_excerpt, file2_excerpt)
            first_tier_chunks = get_first_tier_chunks(first_tier_differences)
            current_index = 0
        # Handle navigation
        elif 'action' in request.form:
            if request.form['action'] == 'Next':
                current_index = min(current_index + 1, len(first_tier_chunks) - 1)
            elif request.form['action'] == 'Previous':
                current_index = max(current_index - 1, 0)
            elif request.form['action'] == 'Refresh':
                file1_excerpt = get_first_x_percent_lines(read_file(file1_path), EXCERPT_PERCENTAGE)
                file2_excerpt = get_first_x_percent_lines(read_file(file2_path), EXCERPT_PERCENTAGE)
                first_tier_differences = compute_first_tier_differences(file1_excerpt, file2_excerpt)
                first_tier_chunks = get_first_tier_chunks(first_tier_differences)
                current_index = 0

    chunk = first_tier_chunks[current_index] if first_tier_chunks else []
    text1, text2 = ''.join(line[2:] for line in chunk if line.startswith('- ')), ''.join(line[2:] for line in chunk if line.startswith('+ '))
    second_tier_word_pairs = compute_second_tier_differences(text1, text2)
    highlighted1, highlighted2 = highlight_character_differences(second_tier_word_pairs)
    return render_template('index.html', file1=highlighted1, file2=highlighted2, index=current_index, file1_path=file1_path, file2_path=file2_path)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
