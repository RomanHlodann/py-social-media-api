import os

from celery import shared_task
from dotenv import load_dotenv
from openai import OpenAI

from comments.models import Comment


load_dotenv()

client = OpenAI(
    api_key=f"{os.getenv('AI_API_KEY')}",
    base_url="https://api.aimlapi.com",
)


@shared_task
def send_auto_reply(post_id: int, user_id: int, comment: str):
    response = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        messages=[
            {
                "role": "user",
                "content": f"Answer to this comment '{comment}' as it was me, in a positive way"
            },
        ],
    )
    message = response.choices[0].message.content
    Comment.objects.create(post_id=post_id, comment=message, user_id=user_id)
