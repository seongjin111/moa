"""
AI 서비스 연동 모듈
OpenAI, Claude 등 AI 서비스와의 통신 처리
"""

import os
import json
from django.conf import settings


class AIService:
    """
    AI 서비스 통합 클래스
    """
    
    @staticmethod
    def call_openai(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 1000):
        """
        OpenAI API 호출
        """
        try:
            from openai import OpenAI
            
            # API 키 확인
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
            
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return {
                'success': True,
                'response': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': model,
                'provider': 'openai'
            }
        except ImportError:
            return {
                'success': False,
                'error': 'openai 라이브러리가 설치되지 않았습니다. pip install openai를 실행하세요.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'OpenAI API 호출 중 오류가 발생했습니다: {str(e)}'
            }
    
    @staticmethod
    def call_claude(prompt: str, model: str = "claude-3-sonnet-20240229", max_tokens: int = 1000):
        """
        Claude (Anthropic) API 호출
        """
        try:
            import anthropic
            
            # API 키 확인
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            
            client = anthropic.Anthropic(api_key=api_key)
            
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                'success': True,
                'response': message.content[0].text,
                'tokens_used': message.usage.input_tokens + message.usage.output_tokens,
                'model': model,
                'provider': 'claude'
            }
        except ImportError:
            return {
                'success': False,
                'error': 'anthropic 라이브러리가 설치되지 않았습니다. pip install anthropic를 실행하세요.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Claude API 호출 중 오류가 발생했습니다: {str(e)}'
            }
    
    @staticmethod
    def call_ai(prompt: str, provider: str = 'openai', model: str = None, max_tokens: int = 1000):
        """
        통합 AI 호출 메서드
        provider: 'openai', 'claude'
        """
        if provider == 'openai':
            if not model:
                model = 'gpt-3.5-turbo'
            return AIService.call_openai(prompt, model, max_tokens)
        elif provider == 'claude':
            if not model:
                model = 'claude-3-sonnet-20240229'
            return AIService.call_claude(prompt, model, max_tokens)
        else:
            return {
                'success': False,
                'error': f'지원하지 않는 AI 제공자입니다: {provider}'
            }
    
    @staticmethod
    def estimate_cost(tokens: int, provider: str, model: str) -> float:
        """
        토큰 사용량으로 비용 추정 (USD)
        """
        # 간단한 비용 추정 (실제 비용은 API 제공자 문서 참조)
        cost_per_1k_tokens = {
            'openai': {
                'gpt-3.5-turbo': 0.002,  # $0.002 per 1K tokens
                'gpt-4': 0.03,  # $0.03 per 1K tokens
            },
            'claude': {
                'claude-3-sonnet-20240229': 0.003,  # $0.003 per 1K tokens
                'claude-3-opus-20240229': 0.015,  # $0.015 per 1K tokens
            }
        }
        
        if provider in cost_per_1k_tokens and model in cost_per_1k_tokens[provider]:
            return (tokens / 1000) * cost_per_1k_tokens[provider][model]
        
        return 0.0

