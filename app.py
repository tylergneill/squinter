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
START_PERCENTAGE = args.start_percentage
END_PERCENTAGE = args.end_percentage

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

def is_roughly_equal(s1: str, s2: str, threshold: float = 0.1) -> bool:
    distance = Levenshtein.distance(s1, s2)
    max_len = max(len(s1), len(s2))
    proportional_distance = distance / max_len
    return proportional_distance <= threshold

def attempt_realignment(words1, words2):
    """
    Attempt to combine two elements of one list (the larger list, if applicable) to match other list
    """
    adjusted1 = []
    adjusted2 = []

    # identify which list is smaller
    if len(words1) < len(words2):
        smaller_list, smaller_result_list = words1, adjusted1
        larger_list, larger_result_list = words2, adjusted2
    else:
        smaller_list, smaller_result_list = words2, adjusted2
        larger_list, larger_result_list = words1, adjusted1
    min_len = min(len(words1), len(words2))

    for i in range(min_len):
        if is_roughly_equal(smaller_list[i], larger_list[i]):
            smaller_result_list.append(smaller_list[i])
            larger_result_list.append(larger_list[i])
        else:
            # if two words in larger list can be combined to match next one word in smaller list, combine and return
            combined_word_from_larger_list = larger_list[i]
            for j in range(i + 1, len(larger_list)):
                combined_word_from_larger_list += ' ' + larger_list[j]
                if is_roughly_equal(smaller_list[i], combined_word_from_larger_list):
                    smaller_result_list.append(smaller_list[i])
                    larger_result_list.append(combined_word_from_larger_list)

                    # extend by remainders of both input lists before returning
                    smaller_result_list.extend(smaller_list[i + 1:])
                    larger_result_list.extend(larger_list[j + 1:])
                    return adjusted1, adjusted2
            else:
                smaller_result_list.append(smaller_list[i])
                larger_result_list.append(larger_list[i])

    else:
        # extend by remainders of both input lists if end is reached, in case of unequal lengths
        smaller_result_list.extend(smaller_list[i + 1:])
        larger_result_list.extend(larger_list[i + 1:])

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

    template_name = 'index_hardcoded.html' if HARDCODED_MODE else 'index.html'
    return render_template(
        template_name,
        file1=highlighted1,
        file2=highlighted2,
        index=current_index,
        file1_path=file1_path,
        file2_path=file2_path
    )

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
