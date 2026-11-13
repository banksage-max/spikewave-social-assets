#!/usr/bin/env bash
# Re-render every clip that is still a Buffer draft, at the same paths (owner, 13 Nov 2026: new plain look).
# Run from tooling/:  bash rerender_all.sh
set -e
FF="/c/Users/vundl/anaconda3/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
M="../../clips-outbox/music/Back To The Start - Patrick Jordan Patrikios.mp3"
music() {  # $1 silent 8 s clip, $2 output with the YouTube-only music bed
  "$FF" -hide_banner -loglevel error -y -i "$1" -i "$M" -filter_complex \
    "[1:a]atrim=0:8,asetpts=N/SR/TB,volume=0.8,afade=t=in:st=0:d=0.3,afade=t=out:st=6.6:d=1.4[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart "$2"
}

# icon-motion clips
python motion.py stopby reveal "Now available" "Your reminder, when you arrive" "Free on Google Play" ../2026-11-07/stopby-now-available.mp4
python motion.py honest_km centred "Coming 23 November" "Every business km, logged as you drive" "Free during launch" ../2026-11-07/honestkm-coming-23-nov.mp4
python motion.py leave_by hero "Alerts you when it's time to leave" "For every appointment and event" "Free on Google Play" ../2026-11-07/leaveby-time-to-leave.mp4
python motion.py which_box hero "Know which box it's in" "Coming 12 January. A QR label for every box." "Pre-register on Google Play" ../2026-11-11/kistly/kistly-icon-motion.mp4
python motion.py honest_km reveal "Now available" "A km logbook that fills itself in. Free during launch." "Free on Google Play" ../2026-11-12/honestkm-now-available.mp4
music ../2026-11-07/stopby-now-available.mp4 ../2026-11-07/youtube/stopby-now-available-short.mp4
music ../2026-11-07/honestkm-coming-23-nov.mp4 ../2026-11-07/youtube/honestkm-coming-23-nov-short.mp4
music ../2026-11-07/leaveby-time-to-leave.mp4 ../2026-11-07/youtube/leaveby-time-to-leave-short.mp4
music ../2026-11-11/kistly/kistly-icon-motion.mp4 ../2026-11-11/kistly/kistly-icon-motion-short.mp4
echo "MOTION DONE"

# Shorts and explainers
python videos.py ../2026-11-07/youtube/specs.json ../2026-11-07/youtube-v2 \
  lb-short-countdown lb-short-flight-buffer lb-short-back-to-back lb-explainer \
  sb-short-tag-place sb-short-remind-me sb-short-arrive sb-short-on-device sb-explainer \
  hk-short-auto-trip hk-short-logbook hk-short-rental-limit hk-short-export hk-explainer
python videos.py ../2026-11-07/youtube/specs.json ../2026-11-11/kistly \
  wb-short-qr-label wb-short-move-item wb-short-arrival wb-short-leaving wb-explainer
for n in sb-explainer sb-short-arrive sb-short-on-device sb-short-remind-me sb-short-tag-place; do
  "$FF" -loglevel error -y -i ../2026-11-07/youtube-v2/$n.mp4 -an -c:v copy ../2026-11-09/$n-silent.mp4
done
echo "ALL DONE"
