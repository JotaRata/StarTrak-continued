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
                        .with_default('inspect'),

                    Optional('dir', 'd', implicit= True)
                        .with_type(casters.path)
                        .with_default('.')
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
    
    
    def execute(new, open, levels, **kwargs):
        console = get_active_console()

        if not new and not open:
            session = startrak.get_session()
            console.write(session.__pprint__(0, 4 if levels == -1 else levels))
        else:
            if new and open:
                raise STException('Invalid parameters for session')           

            if new:
                session = startrak.new_session(new['name'], new['mode'], *new['dir'])
                console.write(session.__pprint__(0, 0 if levels == -1 else levels))
            if open:
                session = startrak.load_session(open['path'])
                console.write(session.__pprint__(0, 1 if levels == -1 else levels))

        console.write('\n')

