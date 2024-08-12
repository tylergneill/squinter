# squinter
a small utility for comparing strings at the level of individual characters, made by a philologist, for philologists or anyone else 

squinter takes the strain out of comparing near-exact versions of text with long or otherwise difficult-to-read segments, by helping identify what actually needs attention and freeing you to ignore the rest

![mascot](starch_mascot.jpg)
(English lexicographer Samuel Johnson, expert squinter)

# example usage
```bash
python app.py --use-local-mode \
--local-filepath1 "/path/to/file1.txt" \
--local-filepath2 "/path/to/file2.txt" \
--start-percentage 10 \
--end-percentage 20
```
