#!/usr/bin/env bash
# Instala las tareas automáticas en el crontab de esta máquina (PC siempre prendida o servidor/VPS).
#   03:00 → busca reels, escribe guiones y genera los videos del día
#   cada 15 min → publica los videos aprobados cuyo horario ya llegó
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3)"
mkdir -p "$DIR/salida"
( crontab -l 2>/dev/null | grep -v "maquina " ; cat <<EOF
CRON_TZ=America/Argentina/Cordoba
0 3 * * * cd "$DIR" && "$PY" -m maquina diario >> salida/registro.log 2>&1
*/15 * * * * cd "$DIR" && "$PY" -m maquina publicar >> salida/registro.log 2>&1
EOF
) | crontab -
echo "Listo. Tareas instaladas:"; crontab -l | grep maquina
