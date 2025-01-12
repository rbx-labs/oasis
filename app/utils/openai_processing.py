from openai import OpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def analyze_text(self, text: str) -> dict:
        prompt = """
        당신은 대화 내용을 분석하고 적절한 액션을 취하는 전문가입니다.
        주어진 대화 내용을 분석하여 다음 세 가지 액션 중 가장 적절한 것을 선택하여 수행해주세요:
        
        1. 피드백/어드바이스: 대화 내용에 대한 건설적인 피드백이나 조언이 필요한 경우
        2. 관련 정보제공: 대화 주제와 관련된 추가 정보나 컨텍스트가 도움될 경우
        3. 일처리: 구체적인 작업이나 문제 해결이 필요한 경우
        
        선택한 액션을 명시하고, 그에 따른 상세한 응답을 제공해주세요.
        """
        
        # Combine prompt and text into a single message
        combined_content = f"{prompt}\n\n분석할 대화 내용:\n{text}"
        
        try:
            response = self.client.chat.completions.create(
                model="o1-mini",
                messages=[
                    {"role": "user", "content": combined_content}
                ]
            )
            # response = self.client.chat.completions.create(
            #         model="gpt-4o",
            #         messages=[
            #             {"role": "system", "content": prompt},
            #             {"role": "user", "content": text}
            #         ]
            #     )
            return {
                "request_content": combined_content,
                "message_content": response.choices[0].message.content
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise 