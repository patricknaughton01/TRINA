def parseCommand(command, *args):
	final_string = str(command) + '('
	for index, arg in enumerate(args):
		if(index != len(args)-1):
			final_string += '{},'
		else:
			final_string += '{}'
	final_string = (final_string + ')')
	final_string = final_string.format(*args)
	return final_string
