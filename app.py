import Levenshtein
from flask import Flask, render_template, request
import difflib
import os
from typing import List

from nw import needleman_wunsch

app = Flask(__name__)

# Global variables to store file paths and differences
# TODO: generalize using session once actually using non-local mode
file1_path = ""
file2_path = ""
differing_line_pairs = []
current_index = 0

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--use-local-mode", help="Flag for using local mode", action='store_true')
parser.add_argument("--local-filepath1", type=str, help="Path to the first file", required=False)
parser.add_argument("--local-filepath2", type=str, help="Path to the second file", required=False)
parser.add_argument("--start-percentage", type=int, help="Percentage of the file to start from", required=False)
parser.add_argument("--end-percentage", type=int, help="Percentage of the file to end at", required=False)
args = parser.parse_args()

HARDCODED_MODE = args.use_local_mode
HARDCODED_FILE1_PATH = args.local_filepath1
HARDCODED_FILE2_PATH = args.local_filepath2
START_PERCENTAGE = args.start_percentage or 15
END_PERCENTAGE = args.end_percentage or 50

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def truncate_file(
    file_content: str,
    start_percentage: int = START_PERCENTAGE,
    end_percentage: int = END_PERCENTAGE,
) -> List[str]:
    lines = file_content.split("\n")
    truncated_lines = lines[ int(len(lines) * start_percentage / 100) : int(len(lines) * end_percentage / 100) ]
    return '\n'.join(truncated_lines)

def get_differing_line_pairs(file1, file2):
    lines1 = file1.split('\n')
    lines2 = file2.split('\n')
    differ = difflib.ndiff(lines1, lines2)
    line_diff_info = list(differ)
    differing_lines = [line for line in line_diff_info if not (line.startswith("  ") or line.startswith("? "))]
    text1 = [line[2:] for line in differing_lines[0::2]]
    text2 = [line[2:] for line in differing_lines[1::2]]
    return list(zip(text1, text2))

def is_roughly_equal(s1: str, s2: str, threshold: float = 0.15) -> bool:
    distance = Levenshtein.distance(s1, s2)
    max_len = max(len(s1), len(s2))
    proportional_distance = distance / max_len
    return proportional_distance <= threshold

def attempt_realignment(words1, words2, threshold=0.15):
    """
    Attempt to align two lists by combining adjacent words in both lists as needed.
    """
    adjusted1, adjusted2 = [], []
    i, j = 0, 0

    while i < len(words1) and j < len(words2):
        w1, w2 = words1[i], words2[j]

        if is_roughly_equal(w1, w2, threshold):  # Perfect match or roughly equal
            adjusted1.append(w1)
            adjusted2.append(w2)
            i += 1
            j += 1
        else:
            # Generate combinations for words1
            best_combined1, best_combined2, best_score = None, None, float("inf")

            for k in range(i + 1, len(words1) + 1):
                combined_w1 = " ".join(words1[i:k])  # Combine up to k words in words1
                for l in range(j + 1, len(words2) + 1):
                    combined_w2 = " ".join(words2[j:l])  # Combine up to l words in words2
                    score = Levenshtein.distance(combined_w1, combined_w2) / max(len(combined_w1), len(combined_w2))
                    if score < best_score and score <= threshold:
                        best_combined1, best_combined2, best_score = combined_w1, combined_w2, score

            if best_combined1 and best_combined2:
                # Use the best combination
                adjusted1.append(best_combined1)
                adjusted2.append(best_combined2)
                i += len(best_combined1.split())
                j += len(best_combined2.split())
            else:
                # No valid combination, align as-is
                adjusted1.append(w1)
                adjusted2.append(w2)
                i += 1
                j += 1

    # Append any remaining words
    adjusted1.extend(words1[i:])
    adjusted2.extend(words2[j:])

    return adjusted1, adjusted2

def realign(a, b):
    """
    Persist until no more realignment can be done
    """
    while True:
        res = attempt_realignment(a, b)
        if res == (a, b):
            break
        else:
            a, b = res
    return a, b

def extract_significant_differences(line_pair):
    if not line_pair:
        return "", ""
    words1 = line_pair[0].split()
    words2 = line_pair[1].split()

    words_adjusted1, words_adjusted2 = realign(words1, words2)

    word_pairs = []
    for i, (word1, word2) in enumerate(zip(words_adjusted1, words_adjusted2)):
        if word1 == word2 and i != 0:
            blank_word = '_' * (len(word1)//2)
            word_pairs.append((blank_word, blank_word))
        else:
            word_pairs.append((word1, word2))

    # perform final check in case list lengths weren't equal
    if len(words_adjusted1) != len(words_adjusted2):
        for word in words_adjusted1[i + 1:]:
            word_pairs.append((word, "-"))
        for word in words_adjusted2[i + 1:]:
            word_pairs.append(("-", word))

    return word_pairs

def highlight_character_differences(word_pair):
    """
    Use Needleman-Wunsch to align characters and highlight differences
    """
    if word_pair == ("", ""):
        return "", ""
    highlighted1, highlighted2 = [], []
    for word1, word2 in word_pair:
        if word1 == word2:
            highlighted1.append(word1)
            highlighted2.append(word2)
        else:
            aligned_chars1, aligned_chars2 = needleman_wunsch(word1, word2)
            highlighted_word1, highlighted_word2 = [], []
            for char1, char2 in zip(aligned_chars1, aligned_chars2):
                if char1 == char2:
                    highlighted_word1.append(char1)
                    highlighted_word2.append(char2)
                else:
                    highlighted_word1.append(f"<span style='background-color: yellow; font-weight: bold;'>{char1}</span>")
                    highlighted_word2.append(f"<span style='background-color: yellow; font-weight: bold;'>{char2}</span>")
            highlighted1.append(''.join(highlighted_word1))
            highlighted2.append(''.join(highlighted_word2))
    return ' '.join(highlighted1), ' '.join(highlighted2)

def initialize(file1_path, file2_path):
    truncated_file1 = truncate_file(read_file(file1_path))
    truncated_file2 = truncate_file(read_file(file2_path))
    differing_line_pairs = get_differing_line_pairs(truncated_file1, truncated_file2)
    current_index = 0

    return differing_line_pairs, current_index


def get_current_percentage(differing_line_pairs, current_index):
    # Compute progress through the truncated slice
    if differing_line_pairs:
        total_pairs = len(differing_line_pairs)
        # avoid division by zero
        if total_pairs > 1:
            frac = current_index / (total_pairs - 1)
        else:
            frac = 0.0
        pct = START_PERCENTAGE + (END_PERCENTAGE - START_PERCENTAGE) * frac
        # format with up to two decimals, dropping any trailing zero
        return f"{pct:.2f}".rstrip('0').rstrip('.') + '%'
    else:
        return '0%'


@app.route('/', methods=['GET', 'POST'])
def index():
    global file1_path, file2_path, differing_line_pairs, current_index

    if request.method == 'GET' and HARDCODED_MODE:

        # file selection
        file1_path = HARDCODED_FILE1_PATH
        file2_path = HARDCODED_FILE2_PATH

        differing_line_pairs, current_index = initialize(file1_path, file2_path)

    elif request.method == 'POST':

        if 'file1' in request.files and 'file2' in request.files:

            # file selection
            file1 = request.files['file1']
            file2 = request.files['file2']
            file1_path = os.path.join('uploads', file1.filename)
            file2_path = os.path.join('uploads', file2.filename)
            file1.save(file1_path)
            file2.save(file2_path)

            differing_line_pairs, current_index = initialize(file1_path, file2_path)

        # Handle navigation
        elif 'action' in request.form:
            if request.form['action'] == 'Next':
                current_index = min(current_index + 1, len(differing_line_pairs) - 1)
            elif request.form['action'] == 'Previous':
                current_index = max(current_index - 1, 0)

    current_pair = differing_line_pairs[current_index] if differing_line_pairs else []
    significant_differences = extract_significant_differences(current_pair)
    highlighted1, highlighted2 = highlight_character_differences(significant_differences)
    current_percentage = get_current_percentage(differing_line_pairs, current_index)

    template_name = 'index_hardcoded.html' if HARDCODED_MODE else 'index.html'
    return render_template(
        template_name,
        file1_text=highlighted1,
        file2_text=highlighted2,
        index=current_index,
        file1_label=os.path.basename(file1_path),
        file2_label=os.path.basename(file2_path),
        current_percentage=current_percentage,
    )

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True, port=5040)
