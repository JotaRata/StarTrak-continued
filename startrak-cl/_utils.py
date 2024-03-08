
def word_index(input_text : str, cursor : int, sep= ' ') -> tuple[list[str], int, int]:
	words = input_text.split(sep)
	current_idx = 0
	for word_idx, word in enumerate(words):
		if current_idx + len(word) >= cursor:
			break
		current_idx += len(word) + 1
	return words, word_idx, current_idx

def common_string(strings : list[str]):
	if not strings:
		return ''
	prefix = strings[0] 
	for string in strings[1:]:
		i = 0
		while i < len(prefix) and i < len(string) and prefix[i] == string[i]:
			i += 1
		prefix = prefix[:i] 
		if not prefix:
			break
	return prefix