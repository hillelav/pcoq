#!/usr/bin/env python3
"""
Real SLM Provider with API Integration
Fast, real-time STL generation using Groq, Together AI, and Ollama (local)
"""

import os
import time
import requests
from typing import Dict, Tuple, Optional
from stl_corrector import STLCorrector, STLPromptBuilder, STLTemplateLibrary


class RealSLMProvider:
    """Real SLM provider with actual API calls (optimized for speed)"""
    
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.api_key = self._get_api_key()
        
        # API endpoints (prioritize fast providers)
        self.api_configs = {
            "groq": {
                "base_url": "https://api.groq.com/openai/v1/chat/completions",
                "models": {
                    # Groq's PRODUCTION models (verified Jan 31, 2026)
                    "llama-3.2-3b": "llama-3.1-8b-instant",  # Map to Llama 3.1 8B (560 T/sec!)
                    "llama-3.3-70b": "llama-3.3-70b-versatile",  # Llama 3.3 70B (280 T/sec)
                    "codellama-7b": "llama-3.1-8b-instant",  # Use Llama 3.1 8B (no CodeLlama on Groq)
                    "llama-8b": "llama-3.1-8b-instant"  # Fast 8B model
                }
            },
            "together": {
                "base_url": "https://api.together.xyz/v1/chat/completions",
                "models": {
                    "qwen2.5-7b": "Qwen/Qwen2.5-7B-Instruct-Turbo",
                    "phi-3-mini-3.8b": "microsoft/phi-3-mini-128k-instruct",
                    "codellama-7b": "codellama/CodeLlama-7b-Instruct-hf"  # Real CodeLlama (needs TOGETHER_API_KEY)
                }
            },
            "ollama": {
                "base_url": "http://localhost:11434/api/chat",  # Local Ollama server
                "models": {
                    # Ollama models (100% FREE, no API key needed!)
                    "phi3": "phi3:latest",                    # Microsoft Phi-3 3.8B
                    "phi3-medium": "phi3:medium",             # Phi-3 Medium 14B
                    "qwen2.5-3b": "qwen2.5:3b",              # Alibaba Qwen 2.5 3B
                    "qwen2.5-7b": "qwen2.5:7b",              # Alibaba Qwen 2.5 7B
                    "gemma2-2b": "gemma2:2b",                # Google Gemma 2 2B
                    "llama3.2-3b": "llama3.2:3b",            # Meta Llama 3.2 3B
                    "mistral": "mistral:latest"               # Mistral 7B
                }
            }
        }
    
    def _get_api_key(self) -> str:
        """Get API key from environment"""
        key_map = {
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
            "openai": "OPENAI_API_KEY"
        }
        
        env_var = key_map.get(self.provider, f"{self.provider.upper()}_API_KEY")
        api_key = os.environ.get(env_var, "")
        
        if not api_key:
            print(f"⚠️  Warning: {env_var} not found in environment")
        
        return api_key
    
    def generate_stl_spec_with_retry(self, scenario: Dict, complexity: str, 
                                     max_retries: int = 10,
                                     allow_template_fallback: bool = False) -> Tuple[Optional[str], Dict]:
        """
        Generate STL with automatic retry - REAL SLM ONLY MODE
        
        Args:
            scenario: Test scenario
            complexity: 'easy', 'medium', or 'hard'
            max_retries: Number of attempts (default: 10 for high reliability)
            allow_template_fallback: If False, never use templates (REAL SLM ONLY!)
        
        Returns:
            (spec, metrics) - spec may be None if SLM fails and fallback disabled
        """
        
        last_error = None
        total_start = time.time()
        
        # Try real SLM (up to max_retries)
        for attempt in range(max_retries):
            spec, metrics = self._call_slm_api(scenario, complexity, feedback=last_error)
            
            if spec:
                # Auto-correct common errors
                corrected_spec = STLCorrector.fix_common_errors(spec)
                
                # Validate syntax
                is_valid, error = STLCorrector.validate_syntax(corrected_spec)
                
                if is_valid:
                    metrics['source'] = 'slm'
                    metrics['attempts'] = attempt + 1
                    metrics['corrected'] = (spec != corrected_spec)
                    if attempt > 0:
                        print(f"    [✓ Success on attempt {attempt + 1}]")
                    return corrected_spec, metrics
                else:
                    last_error = error
                    if attempt < max_retries - 1:
                        print(f"    [Attempt {attempt + 1}/{max_retries}] Validation failed: {error[:50]}...")
            else:
                last_error = metrics.get('error', 'Generation failed')
                if attempt < max_retries - 1:
                    print(f"    [Attempt {attempt + 1}/{max_retries}] API failed: {last_error[:50]}...")
        
        # REAL SLM ONLY MODE: Don't use templates
        if not allow_template_fallback:
            elapsed = time.time() - total_start
            print(f"    [❌ REAL SLM FAILED after {max_retries} attempts]")
            return None, {
                'llm_time': elapsed,
                'tokens_input': 0,
                'tokens_output': 0,
                'spec_length': 0,
                'source': 'failed',
                'attempts': max_retries,
                'error': f'Real SLM failed: {last_error}'
            }
        
        # Optional template fallback (only if explicitly allowed)
        print(f"    [⚠️  Fallback to template after {max_retries} failed attempts]")
        fallback_spec = STLTemplateLibrary.get_template(scenario['use_case'], complexity)
        
        elapsed = time.time() - total_start
        
        return fallback_spec, {
            'llm_time': elapsed,
            'tokens_input': 0,
            'tokens_output': 0,
            'spec_length': len(fallback_spec),
            'source': 'template',
            'attempts': max_retries,
            'error': last_error
        }
    
    def _call_slm_api(self, scenario: Dict, complexity: str, 
                     feedback: Optional[str] = None) -> Tuple[Optional[str], Dict]:
        """Call real SLM API (Groq, Together, or Ollama)"""
        
        # Ollama doesn't need API key (local server)
        if self.provider != "ollama" and not self.api_key:
            return None, {'error': f'No API key for {self.provider}', 'llm_time': 0}
        
        start_time = time.time()
        
        try:
            # Build prompt
            prompt = STLPromptBuilder.build_prompt(scenario, complexity)
            
            # Add feedback if retrying
            if feedback:
                prompt += f"\n\nPREVIOUS ATTEMPT FAILED WITH ERROR: {feedback}\nPlease fix the specification."
            
            # Get API config
            config = self.api_configs.get(self.provider)
            if not config:
                return None, {'error': f'Unknown provider: {self.provider}', 'llm_time': 0}
            
            # Get model name mapping
            model_name = config['models'].get(self.model, self.model)
            
            # Handle Ollama's different API format
            if self.provider == "ollama":
                return self._call_ollama_api(prompt, model_name, start_time)
            
            # Standard OpenAI-compatible API (Groq, Together)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are an STL specification generator. Output ONLY the raw STL formula. NO explanations. NO labels. NO colons. NO prefixes. Just the formula starting with 'always' or 'eventually'."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # Very low temperature for deterministic output
                "max_tokens": 150,   # STL specs are short
                "top_p": 0.8
            }
            
            # Call API (with timeout for real-time requirement)
            response = requests.post(
                config['base_url'],
                headers=headers,
                json=payload,
                timeout=5.0  # 5 second timeout for real-time
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                return None, {
                    'error': f'API error {response.status_code}: {response.text[:200]}',
                    'llm_time': elapsed
                }
            
            # Parse response
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                return None, {
                    'error': 'No choices in API response',
                    'llm_time': elapsed
                }
            
            spec = result['choices'][0]['message']['content'].strip()
            
            # Extract token counts
            usage = result.get('usage', {})
            
            return spec, {
                'llm_time': elapsed,
                'tokens_input': usage.get('prompt_tokens', 0),
                'tokens_output': usage.get('completion_tokens', 0),
                'spec_length': len(spec)
            }
        
        except requests.Timeout:
            elapsed = time.time() - start_time
            return None, {
                'error': f'API timeout after {elapsed:.2f}s',
                'llm_time': elapsed
            }
        
        except Exception as e:
            elapsed = time.time() - start_time
            return None, {
                'error': f'API call failed: {str(e)}',
                'llm_time': elapsed
            }
    
    def _call_ollama_api(self, prompt: str, model_name: str, start_time: float) -> Tuple[Optional[str], Dict]:
        """Call Ollama local API (different format than OpenAI-compatible)"""
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are an STL specification generator. Output ONLY the raw STL formula. NO explanations. NO labels. NO colons. NO prefixes. Just the formula starting with 'always' or 'eventually'."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 150
                }
            }
            
            response = requests.post(
                self.api_configs["ollama"]["base_url"],
                json=payload,
                timeout=60.0  # Ollama first run loads model into memory - can take 30-60s
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                return None, {
                    'error': f'Ollama API error {response.status_code}: {response.text[:200]}',
                    'llm_time': elapsed
                }
            
            result = response.json()
            
            # Ollama response format: {"message": {"content": "..."}}
            if 'message' not in result or 'content' not in result['message']:
                return None, {
                    'error': 'Invalid Ollama response format',
                    'llm_time': elapsed
                }
            
            spec = result['message']['content'].strip()
            
            return spec, {
                'llm_time': elapsed,
                'tokens_input': 0,  # Ollama doesn't return token counts
                'tokens_output': 0,
                'spec_length': len(spec)
            }
        
        except requests.ConnectionError:
            elapsed = time.time() - start_time
            return None, {
                'error': 'Ollama not running (start with: ollama serve)',
                'llm_time': elapsed
            }
        
        except Exception as e:
            elapsed = time.time() - start_time
            return None, {
                'error': f'Ollama call failed: {str(e)}',
                'llm_time': elapsed
            }


# Backward compatibility: map old names to new provider
def get_slm_provider(provider_name: str) -> Tuple[str, str]:
    """Map old provider names to real API providers (Cloud + Ollama)"""
    
    provider_map = {
        # Cloud APIs
        "llama": ("groq", "llama-3.2-3b"),
        "phi": ("together", "phi-3-mini-3.8b"),
        "qwen": ("together", "qwen2.5-7b"),
        "codellama": ("groq", "codellama-7b"),
        
        # Ollama (local - 100% FREE!)
        "ollama-phi3": ("ollama", "phi3"),
        "ollama-qwen2.5-3b": ("ollama", "qwen2.5-3b"),
        "ollama-gemma2": ("ollama", "gemma2-2b"),
        "ollama-llama3.2": ("ollama", "llama3.2-3b"),
    }
    
    return provider_map.get(provider_name, ("groq", "llama-3.2-3b"))
