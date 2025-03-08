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


class StarManageCommand(Command,
                        alias = 'star',
                        description = 'Command to manage the Stars associated with the images in the session',
                        author = 'JotaRata'):

    def init_params():
        return [
            Subcommand('add')
                .with_description('Adds a star to the current session.')
                .with_parameters([
                    Parameter('name')
                        .with_description('The name of the new element, it acts as a unique identifier for this object.')
                        .with_type(str),

                    Parameter('coords')
                        .with_description('The coordinates of the star in the image plane.')
                        .with_mapping(lambda x: [float(s) for s in x.split(',')])
                        .with_type(tuple)
                        .with_validation(lambda x: len(x) == 2),
                    
                    Optional('aperture', 'a')
                        .with_description('The size of the circular aperture that best fits the star PSF in pixels.')
                        .with_type(int)
                        .with_validation(lambda x: x > 0)
                        .with_default(16),

                    Optional('reference', 'r')
                        .with_description('Should this star be considered a reference star to compare brightness?')
                ]),

            Subcommand('remove')
                .with_description('Removes a star from the current session providing its name or index')
                .with_parameters([
                    Parameter('id')
                        .with_description('The name or index of the element')
                        .with_type(str),
                    
                    Optional('force-name')
                ]),
            Subcommand('info')
                .with_description('Prints the info for the star given its name or index')
                .with_parameters([
                    Parameter('id')
                        .with_description('The name or index of the element')
                        .with_type(str),
                    
                    Optional('force-name')
                ]),
        ]

    def execute(add, remove, info, **kwargs):
        if sum(x is not None for x in (add, remove, info)) != 1:
            raise STException("Exactly one of 'add', 'remove', or 'info' must be provided.")
        if add:
            star = startrak.Star(add['name'], add['coords'], add['aperture'])
            startrak.add_star(star)
            print('Added', repr(star))
        elif remove:
            if remove['force_name']:
                id = remove['id']
            else:
                try:
                    id = int(remove['id'])
                except:
                    id = remove['id']

            star = startrak.get_star(id)
            startrak.remove_star(star)
            print('Removed', repr(star))
        elif info:
            if info['force_name']:
                id = info['id']
            else:
                try:
                    id = int(info['id'])
                except:
                    id = info['id']

            star = startrak.get_star(id)
            print(star)
        else:
            raise STException('Missing subcommand for "star"')
