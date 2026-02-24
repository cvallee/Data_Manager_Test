import argparse
import time
from dm_job_utilities.dm_log import DmLog

def write_file(prompt, output, encoding):
	text_to_write = list(prompt.split("\n"))
	DmLog.emit_event(f"Writting '{prompt}' into {output} with {encoding.upper()} encoding")
	t0 = time.time()
	with open(output, 'w', encoding=encoding) as f:
		for line in text_to_write:
			f.write(f"{line}\n")
	t1 = time.time()
	DmLog.emit_event(f"Prompt '{prompt}' was written in {output} in {t1-t0}s")

def main():
	parser = argparse.ArgumentParser(description="Simple module that writes a prompt into a file.")

	parser.add_argument("-i", "--input_prompt", type=str, required=True, default="Hello World!", help="Prompt to be written in the output file (--output). Default: 'Hello World!'")
	parser.add_argument("-o", "--output", type=str, required=True, default="prompt.txt", help="Name of the output file in which the prompt will be written inside. Default: 'prompt.txt'")
	parser.add_argument("-e", "--encoding", type=str, default="utf-8", help="Encoding used to decode or encode the file. Default: 'utf-8'")

	args = parser.parse_args()
	DmLog.emit_event("Hello World Args: ", args)
	write_file(args.input_prompt, args.output, args.encoding)

if __name__ == "__main__":
	main()