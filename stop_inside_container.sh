#!/bin/bash
# AI 흡입기 분석 시스템 - 서버 정리 종료 스크립트
#
# start_inside_container.sh로 시작된 백엔드(8000)와 프론트엔드(8080) 서버를
# PID 파일, 프로세스 패턴, 포트 점유 순으로 안전하게 종료합니다.
#
# 사용법:
#   ./stop_inside_container.sh          # 정상 종료 (SIGTERM → SIGKILL 폴백)
#   ./stop_inside_container.sh --force  # 즉시 강제 종료 (SIGKILL)
#   ./stop_inside_container.sh --status # 서버 실행 상태만 확인

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="${PROJECT_ROOT}/.server_pids"
API_PID_FILE="${PROJECT_ROOT}/api_server.pid"

BACKEND_PORT=8000
FRONTEND_PORT=8080

# 색상 출력 (터미널 지원 시)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    NC='\033[0m'
else
    GREEN='' YELLOW='' RED='' NC=''
fi

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── 포트 점유 PID 조회 ──
get_pids_on_port() {
    local port=$1
    if command -v ss >/dev/null 2>&1; then
        ss -tlnp 2>/dev/null | grep ":${port} " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | sort -u
    elif command -v lsof >/dev/null 2>&1; then
        lsof -ti:${port} 2>/dev/null | sort -u
    elif command -v fuser >/dev/null 2>&1; then
        fuser ${port}/tcp 2>/dev/null | tr -s ' ' '\n' | grep -E '^[0-9]+$' | sort -u
    fi
}

# ── PID가 살아있는지 확인 ──
is_alive() {
    [ -n "$1" ] && kill -0 "$1" 2>/dev/null
}

# ── 단일 PID 종료 (SIGTERM → 대기 → SIGKILL) ──
kill_pid() {
    local pid=$1 label=$2 force=$3
    if ! is_alive "$pid"; then
        return 0
    fi

    if [ "$force" = "true" ]; then
        kill -9 "$pid" 2>/dev/null
        info "${label} (PID $pid) 강제 종료"
        return $?
    fi

    # SIGTERM 전송
    kill "$pid" 2>/dev/null
    # 최대 5초 대기
    local waited=0
    while [ $waited -lt 5 ]; do
        is_alive "$pid" || { info "${label} (PID $pid) 정상 종료"; return 0; }
        sleep 1
        waited=$((waited + 1))
    done

    # 아직 살아있으면 SIGKILL
    if is_alive "$pid"; then
        warn "${label} (PID $pid) SIGTERM 무응답 → SIGKILL"
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
    is_alive "$pid" && { error "${label} (PID $pid) 종료 실패"; return 1; }
    info "${label} (PID $pid) 종료 완료"
    return 0
}

# ── 패턴 매칭으로 프로세스 종료 ──
kill_by_pattern() {
    local pattern=$1 label=$2 force=$3 sig
    sig=$( [ "$force" = "true" ] && echo "-9" || echo "" )
    local pids
    pids=$(pgrep -f "$pattern" 2>/dev/null | grep -v "^$$\$" || true)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            kill_pid "$pid" "$label" "$force"
        done
    fi
}

# ── 포트 강제 해제 ──
release_port() {
    local port=$1 label=$2
    local pids
    pids=$(get_pids_on_port "$port")
    if [ -n "$pids" ]; then
        for pid in $pids; do
            warn "${label} 포트 ${port} 점유 프로세스 발견 (PID $pid) → 강제 종료"
            kill -9 "$pid" 2>/dev/null || true
        done
        sleep 1
    fi
}

# ── 상태 확인 ──
check_status() {
    echo "=========================================="
    echo "AI Inhaler 서버 상태"
    echo "=========================================="

    # PID 파일 기반
    if [ -f "$PID_FILE" ]; then
        info "PID 파일: $PID_FILE"
        local line_num=0
        while read -r pid; do
            line_num=$((line_num + 1))
            [ -z "$pid" ] && continue
            local label=$( [ $line_num -eq 1 ] && echo "백엔드" || echo "프론트엔드" )
            if is_alive "$pid"; then
                info "  ${label} PID $pid: 실행 중"
            else
                warn "  ${label} PID $pid: 종료됨 (stale)"
            fi
        done < "$PID_FILE"
    else
        warn "PID 파일 없음: $PID_FILE"
    fi

    echo ""

    # 포트 기반
    local be_pids fe_pids
    be_pids=$(get_pids_on_port $BACKEND_PORT)
    fe_pids=$(get_pids_on_port $FRONTEND_PORT)

    if [ -n "$be_pids" ]; then
        info "포트 ${BACKEND_PORT} (백엔드):  사용 중 (PID: $(echo $be_pids | tr '\n' ' '))"
    else
        warn "포트 ${BACKEND_PORT} (백엔드):  미사용"
    fi

    if [ -n "$fe_pids" ]; then
        info "포트 ${FRONTEND_PORT} (프론트엔드): 사용 중 (PID: $(echo $fe_pids | tr '\n' ' '))"
    else
        warn "포트 ${FRONTEND_PORT} (프론트엔드): 미사용"
    fi

    # HTTP 응답 확인
    echo ""
    local be_http fe_http
    be_http=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${BACKEND_PORT}/ 2>/dev/null || echo "000")
    fe_http=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT}/ 2>/dev/null || echo "000")

    [ "$be_http" != "000" ] && info "백엔드 HTTP 응답:  $be_http" || warn "백엔드 HTTP 응답:  연결 불가"
    [ "$fe_http" != "000" ] && info "프론트엔드 HTTP 응답: $fe_http" || warn "프론트엔드 HTTP 응답: 연결 불가"

    echo "=========================================="
}

# ── 메인 종료 로직 ──
stop_servers() {
    local force=$1

    echo "=========================================="
    echo "AI Inhaler 서버 종료"
    echo "=========================================="
    [ "$force" = "true" ] && warn "강제 종료 모드 (--force)"
    echo ""

    # 1단계: PID 파일 기반 종료
    if [ -f "$PID_FILE" ]; then
        info "PID 파일 기반 종료 ($PID_FILE)"
        local line_num=0
        while read -r pid; do
            line_num=$((line_num + 1))
            [ -z "$pid" ] && continue
            local label=$( [ $line_num -eq 1 ] && echo "백엔드 (api_server)" || echo "프론트엔드 (http.server)" )
            kill_pid "$pid" "$label" "$force"
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi

    if [ -f "$API_PID_FILE" ]; then
        local api_pid
        api_pid=$(cat "$API_PID_FILE" 2>/dev/null)
        if [ -n "$api_pid" ]; then
            kill_pid "$api_pid" "백엔드 (api_server.pid)" "$force"
        fi
        rm -f "$API_PID_FILE"
    fi

    # 2단계: 프로세스 패턴 매칭으로 잔여 프로세스 종료
    info "잔여 프로세스 패턴 검색..."
    kill_by_pattern "api_server.py"              "백엔드 (패턴)"   "$force"
    kill_by_pattern "uvicorn.*api_server"         "백엔드 uvicorn"  "$force"
    kill_by_pattern "python.*http\\.server.*8080" "프론트엔드 (패턴)" "$force"

    # 3단계: 포트 점유 확인 및 해제
    local be_pids fe_pids
    be_pids=$(get_pids_on_port $BACKEND_PORT)
    fe_pids=$(get_pids_on_port $FRONTEND_PORT)

    if [ -n "$be_pids" ] || [ -n "$fe_pids" ]; then
        warn "포트에 잔여 프로세스 발견 → 강제 해제"
        [ -n "$be_pids" ] && release_port $BACKEND_PORT "백엔드"
        [ -n "$fe_pids" ] && release_port $FRONTEND_PORT "프론트엔드"
    fi

    # 4단계: 최종 확인
    echo ""
    local ok=true
    be_pids=$(get_pids_on_port $BACKEND_PORT)
    fe_pids=$(get_pids_on_port $FRONTEND_PORT)

    if [ -z "$be_pids" ]; then
        info "포트 ${BACKEND_PORT} (백엔드):  해제 완료"
    else
        error "포트 ${BACKEND_PORT} (백엔드):  여전히 사용 중 (PID: $be_pids)"
        ok=false
    fi

    if [ -z "$fe_pids" ]; then
        info "포트 ${FRONTEND_PORT} (프론트엔드): 해제 완료"
    else
        error "포트 ${FRONTEND_PORT} (프론트엔드): 여전히 사용 중 (PID: $fe_pids)"
        ok=false
    fi

    echo ""
    if [ "$ok" = true ]; then
        info "모든 서버가 정상적으로 종료되었습니다."
    else
        error "일부 프로세스를 종료하지 못했습니다. 수동 확인이 필요합니다."
        echo "  확인: ss -tlnp | grep -E ':8000|:8080'"
    fi
    echo "=========================================="
}

# ── 엔트리포인트 ──
case "${1:-}" in
    --force|-f)
        stop_servers true
        ;;
    --status|-s)
        check_status
        ;;
    --help|-h)
        echo "사용법: $0 [옵션]"
        echo ""
        echo "옵션:"
        echo "  (없음)          정상 종료 (SIGTERM → 5초 대기 → SIGKILL)"
        echo "  --force, -f     즉시 강제 종료 (SIGKILL)"
        echo "  --status, -s    서버 실행 상태 확인"
        echo "  --help, -h      이 도움말 표시"
        ;;
    "")
        stop_servers false
        ;;
    *)
        error "알 수 없는 옵션: $1"
        echo "  사용법: $0 [--force|--status|--help]"
        exit 1
        ;;
esac
