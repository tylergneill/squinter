from flask import Flask, render_template_string, request
import difflib

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    string1, string2 = '', ''
    if request.method == 'POST':
        string1 = request.form['string1']
        string2 = request.form['string2']
        string1, string2 = highlight_differences(string1, string2)
    return render_template_string(HTML_TEMPLATE, string1=string1, string2=string2)

def highlight_differences(s1, s2):
    differ = difflib.SequenceMatcher(None, s1, s2)
    highlighted1, highlighted2 = [], []
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'equal':
            highlighted1.append(s1[i1:i2])
            highlighted2.append(s2[j1:j2])
        else:
            highlighted1.append(f"<span style='background-color: yellow; font-weight: bold;'>{s1[i1:i2]}</span>")
            highlighted2.append(f"<span style='background-color: yellow; font-weight: bold;'>{s2[j1:j2]}</span>")
    return ''.join(highlighted1), ''.join(highlighted2)


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>String Difference Highlighter</title>
    <style>
        .container { max-width: 800px; margin: auto; padding: 20px; }
        .content-editable { width: 100%; min-height: 40px; margin-bottom: 10px; padding: 10px; border: 1px solid #ccc; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <form method="post" onsubmit="handleSubmit()">
            <div contenteditable="true" class="content-editable" id="input1">{{ string1|safe }}</div>
            <input type="hidden" name="string1" id="hiddenInput1">
            <div contenteditable="true" class="content-editable" id="input2">{{ string2|safe }}</div>
            <input type="hidden" name="string2" id="hiddenInput2">
            <button type="submit">Compare</button>
            <button type="button" onclick="clearFields()">Clear</button>
        </form>
    </div>
    <script>
        function handleSubmit() {
            document.getElementById('hiddenInput1').value = document.getElementById('input1').innerHTML;
            document.getElementById('hiddenInput2').value = document.getElementById('input2').innerHTML;
        }

        function clearFields() {
            document.getElementById('input1').innerHTML = '';
            document.getElementById('input2').innerHTML = '';
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
