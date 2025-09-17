# datadog-runner-load-generator

**Datadog Runner** 프로젝트의 **load-generator** 마이크로서비스입니다.

## 🔗 Multi-root Workspace
이 저장소는 Multi-root Workspace의 일부입니다:
- **🏠 워크스페이스**: /Users/kihyun.lee/workspace/datadog-runner-multiroot
- **🧠 개발 환경**: Cursor Multi-root로 통합 관리
- **🔄 Git 관리**: 각 서비스 독립적 버전 관리

## 🚀 개발 환경
```bash
# Multi-root Workspace에서 개발
cd /Users/kihyun.lee/workspace/datadog-runner-multiroot
cursor datadog-runner.code-workspace

# 또는 이 서비스만 단독 개발
cursor .
```

## 📁 기술 스택
- **Python**: HTTP 클라이언트 기반
- **Requests**: 합성 트래픽 생성
- **Custom Instrumentation**: 분산 트레이싱
- **Concurrent Testing**: 동시 요청 시나리오

## 📊 주요 기능
- 30명+ 동시 요청 테스트
- Connection Pool 고갈 시뮬레이션
- APM 성능 메트릭 수집
- 자동화된 성능 회귀 테스트

## 🔄 배포
```bash
# 개발 이미지 빌드 및 배포
../infra/scripts/update-dev-image.sh load-generator

# 또는 통합 배포
../infra/scripts/deploy-eks-complete.sh
```

## 📊 모니터링
- **Datadog APM**: 분산 트레이싱
- **JSON 로깅**: 구조화된 로그 분석
- **Dynamic Instrumentation**: 런타임 계측
- **Exception Replay**: 예외 상태 캡처

*마지막 업데이트: 2025-09-17*
