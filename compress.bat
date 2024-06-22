:: Store the video file to be used in the script
set "videoFile=%~1"

:: Call the python script with the input file
python compress.py "%videoFile%"