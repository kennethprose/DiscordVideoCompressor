import os
import subprocess
import sys

# ------ CONFIG ------
target_size_MB = 25
max_size_MB = 25
output_folder = ''
# ------ CONFIG ------

# Determine the Downloads folder dynamically
if output_folder == "" and sys.platform == 'win32':
    output_folder = os.path.join(os.environ['USERPROFILE'], 'Downloads') + '\\'

def compress_video(input_file, target_size):
    output_file = output_folder + os.path.basename(input_file)

    # Get the duration of the video in seconds
    result = subprocess.run(
        ['ffprobe', '-i', input_file, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0'],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    duration = float(result.stdout.splitlines()[0])

    # Calculate target bitrate in bits per second
    target_bitrate = (target_size * 8) / duration

    # ffmpeg command to compress video
    cmd = [
        'ffmpeg',
        '-y', 
        '-hide_banner', '-loglevel', 'error',
        '-i', input_file,
        '-c:v', 'h264_nvenc',
        '-b:v', str(int(target_bitrate)),
        '-bufsize', str(int(target_bitrate)),
        '-maxrate', str(int(target_bitrate)),
        '-c:a', 'copy',
        output_file
    ]

    subprocess.run(cmd)

    return output_file

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("You must pass an input file as the first command line argument.")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"File not found: {input_file}")
        sys.exit(1)

    # Set initial target size
    target_size = target_size_MB * 1024 * 1024
    while True:
        # Compress the file
        output_file = compress_video(input_file, target_size=target_size)

        # Check the size of the output file
        output_file_size = os.path.getsize(output_file)
        print(f'Output File Size: {round(output_file_size / (1024 * 1024), 2)}MB')

        # If file is over absolute max, lower target and run again
        if output_file_size > max_size_MB * 1024 * 1024:
            print(f'Output size too large. Recompressing...')
            target_size -= 1024 * 1024
        else:
            break

    print(f"Compressed video saved as: {output_file}")
