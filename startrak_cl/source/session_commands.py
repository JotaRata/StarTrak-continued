import startrak
from startrak_cl import Command, Parameter, Optional, casters, get_active_console, STException, Subcommand

class SessionCommands(Command,
        alias = 'session',
        description = 'Manage startrak sessions.',
        author = 'JotaRata'):
    
    def init_params():
        return [
            Subcommand('new')
                .with_parameters([
                    Parameter('name')
                        .with_type(str),
                    Optional('mode', 'm')
                        .with_type(str)
                        .with_validation(lambda x: x in ['inspect', 'scan'])
                        .with_default('inspect')
                ]),

            Subcommand('open')
                .with_parameters([
                    Parameter('path')
                        .with_type(casters.path),
                ]),
            
            Optional('levels', 'l')
                .with_type(int)
                .with_validation(lambda x: x >= 0 or x == -1)
                .with_default(-1)
        ]
    
    
    def execute(*args, **kwargs):
        console = get_active_console()
        
        levels = args[-1] if args else 4
        if not args or not args[0] or type(args[0]) is not list:
            session = startrak.get_session()
            console.write(session.__pprint__(0, 4 if levels == -1 else levels))
        else:
            subcommand = args[0]
            match subcommand[0]:
                case 'new':
                    session = startrak.new_session(subcommand[1], subcommand[2])
                    console.write(session.__pprint__(0, 0 if levels == -1 else levels))
                case 'open':
                    session = startrak.load_session(subcommand[1])
                    console.write(session.__pprint__(0, 1 if levels == -1 else levels))

        console.write('\n')

