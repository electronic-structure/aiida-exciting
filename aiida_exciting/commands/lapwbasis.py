import click
@click.group()
def lapwbasis():
    """Help for lapwbasis command"""

@lapwbasis.command('upload')
@click.option('--fmt', type=str, help='Format of the species: \"xml\" or \"json\""', required=True)
@click.option('--name', type=str, help='Name of the LAPW basis set', required=True)
@click.option('--description', type=str, help='Description of the set', required=False)
@click.argument('path', type=str, required=True)
def upload_command(path, fmt, name, description):
    """Upload a new set of LAPW basis files"""
    import os.path

    stop_if_existing = False

    if not fmt in ["xml", "json"]:
        print >> sys.stderr, ("wrong species format: %s"%parsed_args.fmt)
        sys.exit(1)
    
    folder = os.path.abspath(path)

    if (not os.path.isdir(folder)):
        print >> sys.stderr, 'Cannot find directory: ' + folder
        sys.exit(1)

    from aiida import load_dbenv
    load_dbenv()
    import aiida_exciting.data.lapwbasis as lapwbasis

    if not description: description=""

    files_found, files_uploaded = lapwbasis.upload_family(folder, name, description, fmt, stop_if_existing)

    print "Species files found: {}. New files uploaded: {}".format(files_found, files_uploaded)

@lapwbasis.command('list')
def list_command():
    """List the uploaded sets of LAPW basis files"""
    
    with_description = True

    from aiida import load_dbenv
    load_dbenv()
    from aiida.orm import DataFactory

    LapwbasisData = DataFactory('exciting.lapwbasis')
    groups = LapwbasisData.get_lapwbasis_groups()

    if groups:
        for g in groups:
            sp = LapwbasisData.query(dbgroups=g.dbgroup).distinct()
            num_sp = sp.count()

            if with_description:
                description_string = ": {}".format(g.description)
            else:
                description_string = ""

            print "* {} [{} species]{}".format(g.name, num_sp, description_string)
    else:
        print "No LAPW basis sets were found."
