#!/bin/bash
# Renders the traditional Office (Divinum Officium, Rubrics 1960) to raw HTML.
#
#   tools/render.sh DO_DIR OUT_DIR START_YYYY-MM-DD DAYS [LANG...]
#
# DO_DIR is a checkout of github.com/DivinumOfficium/divinum-officium (MIT).
# Writes OUT_DIR/<lang>/<date>/<hour>.html, one language per column (lang1 = lang2).
# Only run this on CI: it executes the project's Perl engine.
set -euo pipefail

do_dir=$(cd "$1" && pwd)
out=$2
start=$3
days=$4
shift 4
langs=("$@")
[ ${#langs[@]} -gt 0 ] || langs=(English Latin)

hours=(Matutinum Laudes Prima Tertia Sexta Nona Vespera Completorium)
version="Rubrics 1960 - 1960"
engine="$do_dir/web/cgi-bin/horas"

render_day() {
    local day=$1 mdy lang dir hour
    mdy=$(date -u -d "$day" +%m-%d-%Y)
    for lang in "${langs[@]}"; do
        dir="$out/$lang/$day"
        mkdir -p "$dir"
        for hour in "${hours[@]}"; do
            (cd "$engine" && perl officium.pl \
                "date1=$mdy&command=pray$hour&version=$version&lang1=$lang&lang2=$lang&content=1") \
                >"$dir/$hour.html" 2>"$dir/$hour.err" || echo "failed: $lang $day $hour" >&2
            [ -s "$dir/$hour.err" ] || rm -f "$dir/$hour.err"
        done
    done
    echo "rendered $day"
}

# Days are independent; render a few at once.
parallel=${RENDER_JOBS:-4}
for ((i = 0; i < days; i++)); do
    render_day "$(date -u -d "$start + $i day" +%F)" &
    while [ "$(jobs -rp | wc -l)" -ge "$parallel" ]; do wait -n; done
done
wait
