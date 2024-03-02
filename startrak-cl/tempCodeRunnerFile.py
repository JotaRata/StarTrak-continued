	self.output.write('\r' + ' ' * len(prompt + input_text) + '\r' + prompt + new_text) 
					self.output.flush()
					return