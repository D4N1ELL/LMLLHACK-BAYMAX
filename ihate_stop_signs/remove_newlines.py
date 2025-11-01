# This script reads 'input.txt', removes all newlines, and writes the result to 'output.txt'.

def remove_newlines(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as infile:
        text = infile.read().replace('\n', '')
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(text)

if __name__ == '__main__':
    remove_newlines('input.txt', 'output.txt')
