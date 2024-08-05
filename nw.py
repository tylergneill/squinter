def needleman_wunsch(seq1, seq2, match=1, mismatch=-1, gap=-1):
    n = len(seq1)
    m = len(seq2)
    score = [[0 for j in range(m + 1)] for i in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = gap * i
    for j in range(1, m + 1):
        score[0][j] = gap * j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            match_score = score[i - 1][j - 1] + (match if seq1[i - 1] == seq2[j - 1] else mismatch)
            delete = score[i - 1][j] + gap
            insert = score[i][j - 1] + gap
            score[i][j] = max(match_score, delete, insert)
    align1, align2 = [], []
    i, j = n, m
    while i > 0 and j > 0:
        current_score = score[i][j]
        diagonal_score = score[i - 1][j - 1]
        up_score = score[i][j - 1]
        left_score = score[i - 1][j]
        if current_score == diagonal_score + (match if seq1[i - 1] == seq2[j - 1] else mismatch):
            align1.insert(0, seq1[i - 1])
            align2.insert(0, seq2[j - 1])
            i -= 1
            j -= 1
        elif current_score == left_score + gap:
            align1.insert(0, seq1[i - 1])
            align2.insert(0, "-")
            i -= 1
        elif current_score == up_score + gap:
            align1.insert(0, "-")
            align2.insert(0, seq2[j - 1])
            j -= 1
    while i > 0:
        align1.insert(0, seq1[i - 1])
        align2.insert(0, "-")
        i -= 1
    while j > 0:
        align1.insert(0, "-")
        align2.insert(0, seq2[j - 1])
        j -= 1
    return align1, align2
