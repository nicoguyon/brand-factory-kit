#!/bin/bash
# Montage : clips (ordre alphabétique) en fondus + carton final + musique baissée sous la voix + -14 LUFS.
# Usage : montage.sh <dossier_marque> [carton.png] [durée_clip=10]
set -euo pipefail
F="$1/film"; CARD="${2:-$F/endcard.png}"; D="${3:-10}"; OUT="$F/film.mp4"
CLIPS=("$F"/clips/*.mp4); N=${#CLIPS[@]}; X=0.8
IN=""; FC=""; for i in "${!CLIPS[@]}"; do IN="$IN -i ${CLIPS[$i]}"; FC="$FC[$i:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,setsar=1,format=yuv420p[v$i];"; done
IN="$IN -loop 1 -t 5 -i $CARD"; FC="$FC[$N:v]scale=1920:1080,fps=24,setsar=1,format=yuv420p[v$N];"
PREV="v0"; OFF=0
for i in $(seq 1 $N); do OFF=$(python3 -c "print($OFF+$D-$X)"); T=fade; [ $i -eq $N ] && T=fadewhite; FC="$FC[$PREV][v$i]xfade=transition=$T:duration=$X:offset=$OFF[x$i];"; PREV="x$i"; done
TOT=$(python3 -c "print($OFF+5)")
MUS=$(ls "$F"/music_*.mp3 | head -1); A=$((N+1))
IN="$IN -i $MUS"; FC="$FC[$PREV]fade=t=in:st=0:d=1,fade=t=out:st=$(python3 -c "print($TOT-0.8)"):d=0.8[vout];[$A:a]atrim=0:$TOT,asetpts=PTS-STARTPTS,afade=t=in:d=1.2,afade=t=out:st=$(python3 -c "print($TOT-3)"):d=3[m];"
if [ -f "$F/vo.mp3" ]; then IN="$IN -i $F/vo.mp3"; FC="$FC[$((A+1)):a]adelay=1500|1500,apad=whole_dur=$TOT[vo];[vo]asplit=2[v1][v2];[m][v1]sidechaincompress=threshold=0.04:ratio=4:attack=150:release=1000[md];[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"; else FC="$FC[m]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"; fi
ffmpeg -nostdin -y -hide_banner -loglevel error $IN -filter_complex "$FC" -map "[vout]" -map "[aout]" -t $TOT -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "✅ $OUT"
