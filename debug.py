# TEST CASE

line1 = "tataśca tathābhūte tasminnavasthāntare maraṇaikaniścayā tattadbahu vila-"
line2 = "tataśca tathābhūte tasminnavasthāntare maraṇaikaniścayāttattadvaḍa vila-"


from app import extract_significant_differences

significant_differences = extract_significant_differences(
    (line1, line2)
)

print(significant_differences)

from app import is_roughly_equal

print(is_roughly_equal(
    s1='maraṇaikaniścayā' + 'tattadbahu',
    s2='maraṇaikaniścayāttattadvaḍa',
    threshold=0.15,
))