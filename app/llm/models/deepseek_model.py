import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import Dict, List, Any, Optional

class DeepSeekLLM:
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-1.3b-instruct", device: str = "cuda"):
        """
        DeepSeek LLM 모델 초기화
        
        Args:
            model_name: 사용할 DeepSeek 모델 이름
            device: 모델을 로드할 디바이스 (cuda, cpu)
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
            
        print("DeepSeek model loaded successfully")
    
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        # 토크나이저로 입력 인코딩 (attention_mask 포함)
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt",
            padding=True,
            truncation=True,
            return_attention_mask=True  # attention_mask 반환 명시
        ).to(self.device)
        
        # 추론 모드로 전환
        with torch.no_grad():
            output = self.model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,  # attention_mask 전달
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # 입력 프롬프트 제외한 생성 텍스트만 반환
        generated_text = self.tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return generated_text