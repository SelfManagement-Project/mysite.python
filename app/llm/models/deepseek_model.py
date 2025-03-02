# llm/models/deepseek_model.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import Dict, List, Any, Optional
from llm.models.generation_params import GenerationParameters

class DeepSeekLLM:
    def __init__(self, 
                model_name: str = "deepseek-ai/deepseek-coder-1.3b-instruct", 
                device: str = "cuda",
                param_config: Optional[str] = None):
        """
        DeepSeek LLM 모델 초기화
        
        Args:
            model_name: 사용할 DeepSeek 모델 이름
            device: 모델을 로드할 디바이스 (cuda, cpu)
            param_config: 생성 파라미터 설정 파일 경로
        """
        # CUDA 사용 가능 여부 체크 및, 디바이스 설정 및 로그 출력
        self.device = "cuda" if torch.cuda.is_available() and device == "cuda" else "cpu"
        print(f"Loading DeepSeek model on {self.device}...")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA device: {torch.cuda.get_device_name(0)}")
            print(f"CUDA device count: {torch.cuda.device_count()}")
        
        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # 8비트 양자화 설정 생성
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )
        
        # 모델 로드 (8비트 양자화 및 CPU 오프로딩 적용)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # 생성 파라미터 관리자 초기화
        self.param_manager = GenerationParameters(config_path=param_config)
            
        print("DeepSeek model loaded successfully")
    
    def generate(self, 
                prompt: str, 
                max_tokens: int = 1024, 
                temperature: float = 0.7,
                preset: Optional[str] = None,
                param_overrides: Optional[Dict[str, Any]] = None,
                adaptive: bool = False,
                context_items: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        텍스트 생성 함수
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 생성 토큰 수
            temperature: 온도 (높을수록 다양한 출력)
            preset: 사용할 파라미터 프리셋 (creative, precise, balanced)
            param_overrides: 개별 파라미터 설정 (프리셋보다 우선)
            adaptive: 컨텍스트 기반 적응형 파라미터 사용 여부
            context_items: 적응형 파라미터 계산용 컨텍스트 항목
            
        Returns:
            생성된 텍스트
        """
        # 생성 파라미터 가져오기
        if adaptive and context_items:
            gen_params = self.param_manager.create_adaptive_params(prompt, context_items)
        else:
            gen_params = self.param_manager.get_params(preset, param_overrides)
        
        # 기본 파라미터 명시적 설정 (함수 파라미터 우선)
        if max_tokens is not None:
            gen_params['max_tokens'] = max_tokens
        if temperature is not None:
            gen_params['temperature'] = temperature
        
        # 토크나이저로 입력 인코딩
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt",
            padding=True,
            truncation=True,
            return_attention_mask=True
        ).to(self.device)
        
        # 추론 모드로 전환
        with torch.no_grad():
            output = self.model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=gen_params.get('max_tokens', 1024),
                temperature=gen_params.get('temperature', 0.7),
                top_p=gen_params.get('top_p', 0.9),
                top_k=gen_params.get('top_k', 40),
                repetition_penalty=gen_params.get('repetition_penalty', 1.05),
                do_sample=gen_params.get('do_sample', True),
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # 입력 프롬프트 제외한 생성 텍스트만 반환
        generated_text = self.tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return generated_text