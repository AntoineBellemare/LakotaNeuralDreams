#!/bin/bash
set -e  # Exit on error for debugging

echo "Using muselsl without conda activate" >> ~/muse_connection_debug.log

LOGFILE="$HOME/muse_connection.log"
MUSE_CMD="/c/Users/skite/miniconda3/envs/goofi-pipe/Scripts/muselsl"

while true; do
  echo "[$(/usr/bin/date '+%Y-%m-%d %H:%M:%S')] Attempting to start muselsl stream..." >> "$LOGFILE"
  "$MUSE_CMD" stream && echo "[$(/usr/bin/date '+%Y-%m-%d %H:%M:%S')] Muse connection established." >> "$LOGFILE"
  
  echo "[$(/usr/bin/date '+%Y-%m-%d %H:%M:%S')] Muselsl stream crashed or stopped. Restarting..." >> "$LOGFILE"
  /usr/bin/sleep 2
done
