# llm/models/deepseek_model.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Dict, List, Any, Optional

class DeepSeekLLM:
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-6.7b-instruct", device: str = "cuda"):
        """
        DeepSeek LLM 모델 초기화
        
        Args:
            model_name: 사용할 DeepSeek 모델 이름
            device: 모델을 로드할 디바이스 (cuda, cpu)
        """
        self.device = "cuda" if torch.cuda.is_available() and device == "cuda" else "cpu"
        print(f"Loading DeepSeek model on {self.device}...")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            low_cpu_mem_usage=True
        ).to(self.device)
        
        print("DeepSeek model loaded successfully")
    
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """
        주어진 프롬프트에 대한 텍스트 생성
        
        Args:
            prompt: 프롬프트 텍스트
            max_tokens: 생성할 최대 토큰 수
            temperature: 생성 다양성 조절 파라미터
            
        Returns:
            생성된 텍스트
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            output = self.model.generate(
                inputs.input_ids,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # 입력 프롬프트 제외한 생성 텍스트만 반환
        generated_text = self.tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return generated_text