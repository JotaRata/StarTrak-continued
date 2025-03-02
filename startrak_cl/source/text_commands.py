import startrak
from startrak_cl import Command, Parameter, Optional, get_active_console
import os
import re

class FindTextCommand(Command,
                    alias = 'grep',
                    description = 'Find patterns in text'):

    def init_params():
        return [
            Parameter('pattern')
                .with_type(str),

            Parameter('source')
                .with_type(str),

            Optional('regex', 'r'),
            Optional('ignore-case', 'i'),
        ]
    
    def execute(pattern, source, regex, ignore_case , printable = True, **kwargs):
        console = get_active_console();

        if ignore_case:
            pattern = pattern.lower()
        if not regex:
            pattern = re.escape(pattern).replace(r'\*', '.*')
        else:
            pattern = pattern

        matches = list()

        if os.path.exists(source) and os.path.isfile(source):
            matches = FindTextCommand.read_file(source, pattern)

        elif '*' in source:
            paths = glob.glob(source, root_dir= os.getcwd())
            if paths:
                for path in paths:
                    matches.append((f'{path}:', ()))
                    matches.extend(read_file(path, pattern))

        if not matches:
            source = console.remove_format(source)
            matches = FindTextCommand.read_text(source, pattern, ignore_case)

        if printable:
            buffer = console.buffer()
            
            for line, span in matches:
                if len(span) == 0:
                    buffer.write(line)
                else:
                    buffer.write(line[:span[0]])
                    buffer.write( console.format(line[span[0]:span[1]], 'red') )
                    buffer.write(line[span[1]:])
                buffer.write('\n')
            console.write(buffer.getvalue())

    def read_file(path, pattern):
            lines = list()
            file = open(path, 'r')
            
            for line in file:
                match =  re.search(pattern, line)
                if match:
                    lines.append((line, match.span()))
            file.close()
            return lines

    def read_text(source, pattern, no_case):
        lines = list()
        for line in source.split('\n'):
            match =  re.search(pattern, line.lower() if no_case else line)
            if match:
                lines.append((line, match.span()))
        return lines