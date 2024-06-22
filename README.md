# Video Compression Script

This script compresses a video file to a target size using `ffmpeg`. It ensures that the output file size is within the specified limit by adjusting the bitrate. This is ideal for applications like sending game clips on Discord since there is a 25MB file limit.

## Features

- Compresses video files to a target size.
- Nvidia's NVENC support for hardware-accelerated video encoding.
- Automatically adjusts the bitrate to achieve best video quality while still being below the desired output size.
- Preserves the original audio track.

## Prerequisites

- ffmpeg must be installed and accessible in your system's PATH.
- ffprobe, which is part of the ffmpeg suite, must also be installed and accessible in your system's PATH.
- Python

## Installation

1. Clone this repository or download the script directly.

## Configuration

By default, the script will compress the video to fit into 25MB and will save the file to your downloads folder.

The configuration can be changed by modifying the following variables at the beginning of the script:

- `target_size_MB`: Initial target size for the compressed video in megabytes.
- `max_size_MB`: Maximum allowable size for the compressed video in megabytes.
- `output_folder`: Folder where the compressed video will be saved.
  - Must be a fill path
  - Must use double slashes for python to interperate it properly
  - Must end in a slash
  - Example: "C:\\\\Users\\\\Joe\\\\Downloads\\\\"

## Usage

The easiest method is to just drag and drop the video file you want to be compressed onto the compress.bat file.

For a more manual approach, run the script with the input video file as a command-line argument:

```bash
python compress_video.py <input_video_file>
```

For example:

```bash
python compress_video.py "C:\path\to\your\video.mp4"
```

The compressed video will be saved in the specified `output_folder`.

## Tips

1. For convinience, you can create a shortcut to the compress.bat file and put that anywhere you like. Dragging and dropping files onto the shortcut will still work.
