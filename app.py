#!/usr/bin/env python3
"""
Synthetic Load Generator for Datadog Runner Services
30초마다 다양한 API 엔드포인트를 호출하여 지속적인 트래픽 생성
"""

# Datadog 트레이싱을 위한 설정 (다른 import보다 먼저!)
import ddtrace
from ddtrace import tracer
from ddtrace.propagation.http import HTTPPropagator

# 자동 계측 활성화 (다른 라이브러리 import 전에!)
ddtrace.patch_all()

import requests
import time
import random
import logging
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('load-generator')

@dataclass
class APICall:
    name: str
    method: str
    url: str
    headers: Optional[dict] = None
    data: Optional[dict] = None
    expected_status: int = 200

class LoadGenerator:
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'http://frontend-svc')
        self.interval = int(os.getenv('INTERVAL_SECONDS', '30'))
        self.session = requests.Session()
        self.session.timeout = 10
        
        # 로그인 세션 유지를 위한 쿠키 설정
        self.logged_in = False
        
        # API 호출 목록 정의
        self.api_calls = [
            # 인증 관련
            APICall(
                name="session_check",
                method="GET", 
                url=f"{self.base_url}/api/session/me"
            ),
            
            # 랭킹 조회 (실제 구현된 엔드포인트만)
            APICall(
                name="rankings_top",
                method="GET",
                url=f"{self.base_url}/rankings/top"
            ),
            APICall(
                name="rankings_top_limit",
                method="GET", 
                url=f"{self.base_url}/rankings/top?limit=5"
            ),
            
            # 점수 제출 (가상 데이터) - 올바른 엔드포인트 사용
            APICall(
                name="score_submit",
                method="POST",
                url=f"{self.base_url}/api/score",
                headers={"Content-Type": "application/json"},
                data={"score": lambda: random.randint(0, 1500)},
                expected_status=200
            ),
            
            # 로그아웃 (세션 테스트) - GET 메서드 사용
            APICall(
                name="logout",
                method="GET",
                url=f"{self.base_url}/api/auth/logout",
                expected_status=200
            ),
        ]
        
        logger.info(f"Load Generator 초기화 완료 - Base URL: {self.base_url}, Interval: {self.interval}s")

    def ensure_login(self) -> bool:
        """Demo 사용자로 로그인 시도"""
        # Custom instrumentation: trace the login operation
        with tracer.trace("load_generator.login", service="load-generator", resource="POST /api/auth/login") as login_span:
            try:
                # 기존 demo 사용자 사용 (평문 비밀번호 예외 처리됨)
                login_data = {"id": "demo", "pw": "demo"}
                
                # 헤더 준비 및 trace context 주입
                headers = {"Content-Type": "application/json"}
                propagator = HTTPPropagator()
                propagator.inject(login_span.context, headers)
                
                # Span에 로그인 메타데이터 추가
                login_span.set_tag("http.method", "POST")
                login_span.set_tag("http.url", f"{self.base_url}/api/auth/login")
                login_span.set_tag("component", "http")
                login_span.set_tag("span.kind", "client")
                login_span.set_tag("user.id", "demo")
                
                response = self.session.post(
                    f"{self.base_url}/api/auth/login",
                    json=login_data,
                    headers=headers,
                    timeout=5
                )
                
                login_span.set_tag("http.status_code", response.status_code)
                
                if response.status_code == 200:
                    self.logged_in = True
                    logger.info("로그인 성공! - demo")
                    login_span.set_tag("login.success", True)
                    return True
                else:
                    logger.warning(f"로그인 실패! - Status: {response.status_code}")
                    login_span.set_tag("login.success", False)
                    login_span.set_tag("error.message", f"Login failed with status {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.error(f"로그인 중 오류: {e}")
                login_span.set_tag("error", True)
                login_span.set_tag("error.message", str(e))
                login_span.set_tag("login.success", False)
                return False

    def call_api(self, api_call: APICall) -> dict:
        """단일 API 호출 실행"""
        # Custom instrumentation: trace the API call operation
        with tracer.trace("http.request", service="load-generator", resource=f"{api_call.method} {api_call.url}") as span:
            start_time = time.time()
            result = {
                "name": api_call.name,
                "method": api_call.method,
                "url": api_call.url,
                "success": False,
                "status_code": None,
                "response_time_ms": 0,
                "error": None
            }
            
            try:
                # 동적 데이터 처리 (점수 등)
                data = api_call.data
                if data and callable(data.get("score")):
                    data = {**data, "score": data["score"]()}
                
                # 헤더 준비 및 trace context 주입
                headers = api_call.headers.copy() if api_call.headers else {}
                
                # HTTP propagator를 사용해 현재 span context를 headers에 주입
                propagator = HTTPPropagator()
                propagator.inject(span.context, headers)
                
                # Span에 HTTP 메타데이터 추가
                span.set_tag("http.method", api_call.method)
                span.set_tag("http.url", api_call.url)
                span.set_tag("component", "http")
                span.set_tag("span.kind", "client")
                
                # API 호출
                response = self.session.request(
                    method=api_call.method,
                    url=api_call.url,
                    headers=headers,
                    json=data,
                    timeout=5
                )
            
                result["status_code"] = response.status_code
                result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
                
                # Span에 HTTP response 메타데이터 추가
                span.set_tag("http.status_code", response.status_code)
                span.set_tag("http.response_time_ms", result["response_time_ms"])
                
                # 성공 여부 판단
                if response.status_code == api_call.expected_status:
                    result["success"] = True
                    span.set_tag("http.success", True)
                    logger.info(f"✅ {api_call.name}: {response.status_code} ({result['response_time_ms']}ms)")
                else:
                    result["error"] = f"Unexpected status: {response.status_code}"
                    span.set_tag("http.success", False)
                    span.set_tag("error.message", result["error"])
                    logger.warning(f"⚠️ {api_call.name}: {response.status_code} (expected {api_call.expected_status})")
                    
            except requests.exceptions.Timeout:
                result["error"] = "Timeout"
                result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
                span.set_tag("error", True)
                span.set_tag("error.message", "Timeout")
                span.set_tag("http.response_time_ms", result["response_time_ms"])
                logger.error(f"❌ {api_call.name}: Timeout after 5s")
                
            except Exception as e:
                result["error"] = str(e)
                result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
                span.set_tag("error", True) 
                span.set_tag("error.message", str(e))
                span.set_tag("http.response_time_ms", result["response_time_ms"])
                logger.error(f"❌ {api_call.name}: {e}")
            
            return result

    def run_cycle(self) -> List[dict]:
        """한 사이클의 API 호출 실행 (span 없음 - 너무 길어서)"""
        cycle_start = time.time()
        logger.info(f"🔄 Load generation cycle 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 로그인이 안되어 있으면 시도
        if not self.logged_in:
            self.ensure_login()
        
        results = []
        
        # 각 API 순서대로 호출 (랜덤 딜레이 추가)
        for i, api_call in enumerate(self.api_calls):
            if i > 0:  # 첫 번째 호출 제외하고 간격 두기
                delay = random.uniform(1, 3)  # 1-3초 랜덤 딜레이
                time.sleep(delay)
            
            result = self.call_api(api_call)
            results.append(result)
            
            # 로그아웃 호출 후에는 로그인 상태 리셋
            if api_call.name == "logout":
                self.logged_in = False
        
        cycle_time = round(time.time() - cycle_start, 2)
        success_count = sum(1 for r in results if r["success"])
        
        logger.info(f"📊 Cycle 완료: {success_count}/{len(results)} 성공, 소요시간: {cycle_time}s")
        
        return results

    def run(self):
        """메인 실행 루프"""
        logger.info(f"🚀 Load Generator 시작 - {self.interval}초마다 API 호출")
        
        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n{'='*50}")
                logger.info(f"🔢 Cycle #{cycle_count}")
                
                # API 호출 사이클 실행
                results = self.run_cycle()
                
                # 다음 사이클까지 대기
                logger.info(f"⏰ {self.interval}초 대기 중...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Load Generator 중지 요청됨")
        except Exception as e:
            logger.error(f"💥 예상치 못한 오류: {e}")
        finally:
            logger.info(f"📋 총 {cycle_count} 사이클 완료")

if __name__ == "__main__":
    # Datadog 트레이싱 초기화
    ddtrace.config.django.instrument_databases = False
    
    generator = LoadGenerator()
    generator.run()
