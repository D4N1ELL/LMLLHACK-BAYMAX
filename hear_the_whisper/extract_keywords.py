import re

def extract_keywords(transcript_path, output_path):
    pattern = re.compile(r"The (\d+)[a-z]{2} letter in keyword is ([A-Za-z]),")
    keywords = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_keyword = []
    last_index = 0
    for line in lines:
        match = pattern.search(line)
        if match:
            idx = int(match.group(1))
            letter = match.group(2)
            # If index is 1, start a new keyword
            if idx == 1 and current_keyword:
                keywords.append(''.join(current_keyword))
                current_keyword = []
            current_keyword.append(letter)
            last_index = idx
        else:
            # If we reach a non-matching line and have a partial keyword, finish it
            if current_keyword:
                keywords.append(''.join(current_keyword))
                current_keyword = []
    # Add last keyword if any
    if current_keyword:
        keywords.append(''.join(current_keyword))

    with open(output_path, 'w', encoding='utf-8') as f:
        for kw in keywords:
            f.write(kw + '\n')

if __name__ == "__main__":
    for i in range(16):
        input_file = f'output_{i:03d}.txt'
        output_file = f'keywords_{i:03d}.txt'
        print(f'Processing {input_file} -> {output_file}')
        extract_keywords(input_file, output_file)
