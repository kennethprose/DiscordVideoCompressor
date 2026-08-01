import os
import subprocess
import sys

# ------ CONFIG ------
target_size_MB = 10
max_size_MB = 10
output_folder = ''
audio_bitrate_kbps = 128
safety_margin = 0.97
# ------ CONFIG ------

# Determine the Downloads folder dynamically
if output_folder == "" and sys.platform == 'win32':
    output_folder = os.path.join(os.environ['USERPROFILE'], 'Downloads') + '\\'

def probe_video(input_file):
    # Get height of the first video stream specifically
    height_result = subprocess.run(
        ['ffprobe', '-i', input_file, '-select_streams', 'v:0',
         '-show_entries', 'stream=height', '-v', 'quiet', '-of', 'csv=p=0'],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    height_output = height_result.stdout.strip()

    # Get duration from the format section specifically
    duration_result = subprocess.run(
        ['ffprobe', '-i', input_file,
         '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0'],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    duration_output = duration_result.stdout.strip()

    if not height_output:
        print(f"Could not detect a video stream in: {input_file}")
        sys.exit(1)
    if not duration_output:
        print(f"Could not detect duration for: {input_file}")
        sys.exit(1)

    try:
        height = int(height_output)
        duration = float(duration_output)
    except ValueError:
        print(f"Unexpected ffprobe output for: {input_file}")
        sys.exit(1)

    return height, duration

def count_audio_streams(input_file):
    result = subprocess.run(
        ['ffprobe', '-i', input_file, '-select_streams', 'a',
         '-show_entries', 'stream=index', '-v', 'quiet', '-of', 'csv=p=0'],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    return len([line for line in result.stdout.strip().splitlines() if line])

def get_encoder_args(encoder, target_video_bitrate):
    if encoder == 'nvenc':
        return [
            '-c:v', 'h264_nvenc',
            '-rc:v', 'cbr',
            '-b:v', str(int(target_video_bitrate)),
            '-bufsize', str(int(target_video_bitrate // 2)),
            '-maxrate', str(int(target_video_bitrate)),
        ]
    else:  # libx264 software fallback
        return [
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-b:v', str(int(target_video_bitrate)),
            '-minrate', str(int(target_video_bitrate)),
            '-maxrate', str(int(target_video_bitrate)),
            '-bufsize', str(int(target_video_bitrate // 2)),
        ]

def build_ffmpeg_cmd(encoder, input_file, temp_output, target_video_bitrate,
                      audio_track_count, height):
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', input_file]

    if audio_track_count > 1:
        filter_inputs = ''.join(f'[0:a:{i}]' for i in range(audio_track_count))
        cmd += ['-filter_complex',
                f'{filter_inputs}amix=inputs={audio_track_count}:duration=longest:normalize=0,alimiter=limit=0.95[aout]']
        cmd += ['-map', '0:v:0', '-map', '[aout]']
    elif audio_track_count == 1:
        cmd += ['-map', '0:v:0', '-map', '0:a:0']
    else:
        cmd += ['-map', '0:v:0']

    cmd += get_encoder_args(encoder, target_video_bitrate)

    if audio_track_count > 0:
        cmd += ['-c:a', 'aac', '-b:a', f'{audio_bitrate_kbps}k']

    if height > 1080:
        cmd += ['-vf', 'scale=-1:1080']

    cmd.append(temp_output)
    return cmd

def compress_video(input_file, target_size):
    output_file = output_folder + os.path.basename(input_file)
    temp_output = output_file + '.tmp.mp4'

    height, duration = probe_video(input_file)
    audio_track_count = count_audio_streams(input_file)

    # Calculate target bitrate in bits per second
    audio_bitrate = audio_bitrate_kbps * 1000
    total_bitrate = (target_size * 8) / duration
    target_video_bitrate = max((total_bitrate - audio_bitrate) * safety_margin, 100_000)

    cmd = build_ffmpeg_cmd('nvenc', input_file, temp_output, target_video_bitrate, audio_track_count, height)
    result = subprocess.run(cmd)

    if result.returncode != 0:                                            # NEW
        print("NVENC encoding failed (no GPU/driver?). Falling back to software encoding (libx264)...")
        cmd = build_ffmpeg_cmd('x264', input_file, temp_output, target_video_bitrate, audio_track_count, height)
        result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"ffmpeg failed to compress {input_file}")
        sys.exit(1)

    os.replace(temp_output, output_file)

    return output_file

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("You must pass an input file as the first command line argument.")
        sys.exit(1)

    # Iterate over arguments and compress each
    for x in range(1, len(sys.argv)):

        input_file = sys.argv[x]
        if not os.path.isfile(input_file):
            print(f"File not found: {input_file}")
            break

        print(f"{'-'*15} {input_file} {'-'*15}")

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
                target_size -= 0.25 * 1024 * 1024
            else:
                break

        print(f"Saved as: {output_file}\n")
