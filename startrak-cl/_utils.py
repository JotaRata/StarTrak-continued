
def word_index(input_text : str, cursor : int, sep= ' ') -> tuple[list[str], int, int]:
	words = input_text.split(sep)
	current_idx = 0
	for word_idx, word in enumerate(words):
		if current_idx + len(word) >= cursor:
			break
		current_idx += len(word) + 1
	return words, word_idx, current_idx