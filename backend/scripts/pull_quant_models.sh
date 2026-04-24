#!/usr/bin/env bash
# 비교 실험용 Ollama 양자화 태그를 일괄 다운로드한다.
# 총 디스크 사용량은 약 28GB 이며, 실험 종료 후 `ollama rm <tag>` 로 정리 가능.
#
# 실제 Ollama 레지스트리의 태그 이름이 아래와 다를 경우,
# backend/app/config.py 의 ollama_model_name 프로퍼티(`-instruct-<tag>` 조합)를 함께 조정해야 한다.

set -euo pipefail

BASE_MODEL="${LLM_BASE_MODEL:-exaone3.5:7.8b}"
# Ollama 레지스트리에 실재하는 exaone3.5:7.8b 태그만 pull 한다.
# fp16 ≈ 15GB, q8_0 ≈ 8GB, q4_K_M ≈ 4.7GB (합계 약 28GB).
TAGS=(
  "q4_K_M"
  "q8_0"
  "fp16"
)

for tag in "${TAGS[@]}"; do
  full="${BASE_MODEL}-instruct-${tag}"
  echo "==> ollama pull ${full}"
  ollama pull "${full}"
done

echo "완료. 아래 명령으로 로컬 태그 목록을 확인하세요:"
echo "  ollama list"
