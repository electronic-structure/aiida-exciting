import click
@click.group()
lapwbasis():
   """commandline help for lapwbasis command"""

@lapwbasis.command('uploadfamily')
@click.option('--fmt', type=str, help='Format of the species: \"xml\" or \"json\""', required=True)
uploadfamily_command(fmt):
   """Upload a new family of LAPW basis"""
   print("Hello!")
