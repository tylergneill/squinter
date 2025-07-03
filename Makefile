FILE1="/Users/tyler/Dropbox/Docs/Projects/Computational/Digitizations/bāṇa_kādambarī/5_merge/2_Tylers_new.txt"
FILE2="/Users/tyler/Dropbox/Docs/Projects/Computational/Digitizations/bāṇa_kādambarī/5_merge/1_Andrew_derived.txt"
PDF="/Users/tyler/Library/CloudStorage/Dropbox/Docs/Projects/Computational/Digitizations/bāṇa_kādambarī/1_kadambari_pages.pdf"
NOTES="/Users/tyler/Library/CloudStorage/Dropbox/Docs/Projects/Computational/Digitizations/bāṇa_kādambarī/5_merge/notes.txt"

run:
	open $(FILE1) -a bbedit
	open $(FILE2) -a bbedit
	open $(PDF)
	open $(NOTES) -R
	python app.py --use-local-mode \
--local-filepath1 $(FILE2) \
--local-filepath2 $(FILE1) \
--start-percentage 50 \
--end-percentage 60
