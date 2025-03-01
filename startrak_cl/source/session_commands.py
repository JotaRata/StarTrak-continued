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
        ]
    
    
    def execute(subcommand : list = None, *args, **kwargs):
        console = get_active_console()

        if not subcommand:
            session = startrak.get_session()
            console.write(session.__pprint__(0, 4))
            console.write('\n')
            return

        match subcommand[0]:
            case 'new':
                session = startrak.new_session(subcommand[1], subcommand[2], *args)
                console.write(session.__pprint__(0, 0))
            case 'open':
                pass
        console.write('\n')

