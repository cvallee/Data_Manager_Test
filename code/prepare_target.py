import os
import typer
import time
from dm_job_utilities.dm_log import DmLog
import hippo # Need new release of HIPPO (probably xchem-hippo?)

cli = typer.Typer(add_completion=False)

def import_target(target, tas, stack, token, destination):
	from fragalysis.requests import download_target
	
	t0 = time.time()	
	if not os.path.isdir(f"{destination}"):
		os.makedirs(destination, exist_ok=True)

	if os.path.isfile(f"{destination}/{target}.tar.gz") and os.path.isfile(f"{destination}/{target}/metadata.csv") and os.path.isdir(f"{destination}/{target}/aligned_files"):
		DmLog.emit_event(f"Target '{target} ({tas})' has already been downloaded.")
		metadata = f"{destination}/{target}/metadata.csv"
		aligned_dir = f"{destination}/{target}/aligned_files"

		return metadata, aligned_dir

	download_target(name=target, tas=tas, stack=stack, token=token, destination=destination)

	assert os.path.isfile(f"{destination}/{target}.tar.gz")
	assert os.path.isfile(f"{destination}/{target}/metadata.csv")
	metadata = f"{destination}/{target}/metadata.csv"
	assert os.path.isdir(f"{destination}/{target}/aligned_files")
	aligned_dir = f"{destination}/{target}/aligned_files"
	
	t1 = time.time()
	DmLog.emit_event(f"Target '{target} ({tas})' successfully downloaded in {t1-t0}s.")
	
	return metadata, aligned_dir

def hits2db(name, db, target, metadata, aligned_dir, soakdb):
	t0 = time.time()
	DmLog.emit_event(f"Initiating HIPPO database '{name}' (path: {db})...")
	animal = hippo.HIPPO(name, db)

	DmLog.emit_event(f"Adding hits...")	
	animal.add_hits(
		target_name=target,
		metadata_csv=metadata,
		aligned_directory=aligned_dir,
		load_pose_mols=True # Optional, but keept true for now
		)

	if soakdb:
		DmLog.emit_event(f"Inserting compounds form SoakDB (file :{soakdb})...")
		animal.add_soakdb_compounds(soakdb)

	t1 = time.time()
	DmLog.emit_event(f"HIPPO database '{name}' (path: {db}) was generated in {t1-t0}s.")

	return animal

def exportSDF(animal, tag: str = "all", output: str | None = None, to_fragalysis=True, method="", submitter="", email="", institution=""):
	t0 = time.time()	

	if tag.lower() == "all": # Defaults write all poses
		poses = animal.poses[:]

	else:
		DmLog.emit_event(f"Selecting poses tagged '{tag}'...")
		poses = animal.poses(tag=tag)

	DmLog.emit_event(f"Writting {output}...")
	if not output:
		output = animal.db_path.replace(".sqlite", ".sdf")

	assert output.endswith(".sdf")

	if to_fragalysis:
		poses.to_fragalysis(output, method=method, submitter_name=submitter, submitter_email=email, submitter_institution=institution)

	else:
		poses.write_sdf(output)

	t1 = time.time()
	DmLog.emit_event(f"SDF file '{output}' was generated in {t1-t0}s.")

@cli.command(no_args_is_help=True, help="Download a target from Fragalysis using the python API and load it into a HIPPO database.")
def main(
	target: str = typer.Argument("", help="Name of the target to request as shown in Fragalysis (e.g. A71EV2A)."),
	tas: str = typer.Argument("", help="Name of the target access string (or TAS) as shown in Fragalysis (e.g. lb32627-66)."),
	stack: str = typer.Option("production", help="Name (either 'production', 'staging', 'matej-dev') or URL of the stack to download the data from."),
	token: str | None = typer.Option(None, help="Optional authentication token (can be obtain in Fragalysis using 'Get Token' from the HOME MENU)."),
	destination: str = typer.Option(".", help="Directory within which to place the download (default: current working directory)."),
	name: str | None = typer.Option(None, help="Optional name of the HIPPO database (defaut: '{target}-DB')."),
	db: str | None = typer.Option(None, help="Optional path of the HIPPO database file (defaut: '{destination}/{target.lower()}.sqlite')."),
	soakdb: str | None = typer.Option(None, help="Optional path to the SoakDB file."),
	tag: str = typer.Option("all", help="Optional tag to select the poses to write in the SDF file."),
	output: str | None = typer.Option(None, help="Optional path of the output SDF file (default: '{destination}/{target.lower()}.sdf')."),
	to_fragalysis: bool = typer.Option(True, help="Optional boolean to write SDF file to export into Fragalysis (True, default) or to write generic SDF file (False)."),
	method: str = typer.Option("", help="Required argument if --to-fragalysis True. Name of the method used to generate the compounds."),
	submitter: str = typer.Option("", help="Required argument if --to-fragalysis True. Name of the submitter."),
	email: str = typer.Option("", help="Required argument if --to-fragalysis True. Email of the submitter."),
	institution: str = typer.Option("", help="Required argument if --to-fragalysis True. Institution of the submitter."),
	):

	if name is None:
		name = f"{target}-DB"
	if db is None:
		db = f"{destination}/{target.lower()}.sqlite"
	if output is None:
		output = f"{destination}/{target.lower()}.sdf"
	DmLog.emit_event(f"Prepare target Args: (target: '{target}', tas: '{tas}', stack: '{stack}', token: '{token}', destination: '{destination}/', name: '{name}', db: '{db}', soakdb: '{soakdb}', tag: '{tag}', output: '{output}', to_fragalysis: '{to_fragalysis}')")

	DmLog.emit_event(f"Downloading target '{target} ({tas})' from Fragalysis {stack} stack to '{destination}'...")	
	metadata, aligned_dir = import_target(target=target, tas=tas, stack=stack, token=token, destination=destination)

	DmLog.emit_event(f"Adding hits from {target} to HIPPO database '{name}' (path: {db})...")	
	animal = hits2db(name=name, db=db, target=target, metadata=metadata, aligned_dir=aligned_dir, soakdb=soakdb)

	DmLog.emit_event(f"Writting SDF file from '{animal.name}' (path: {animal.db_path})...")
	exportSDF(animal=animal, tag=tag, output=output, to_fragalysis=to_fragalysis, method=method, submitter=submitter, email=email, institution=institution)

if __name__ == "__main__":
	cli()