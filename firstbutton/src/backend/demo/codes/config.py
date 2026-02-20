"""
AWS Secrets Manager에서 시크릿을 로드하여 환경변수에 세팅.
로컬 개발 시에는 .env 파일을 fallback으로 사용.
"""
import os
import json
from dotenv import load_dotenv

# .env 파일 먼저 로드 (로컬 개발용 fallback)
load_dotenv()


def load_secrets():
    """AWS Secrets Manager에서 시크릿을 로드하여 os.environ에 세팅"""
    region = os.getenv("AWS_REGION", "us-east-1")

    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=region)

        # first_button_google 시크릿 로드
        google_secret = client.get_secret_value(SecretId="first_button_google")
        google_data = json.loads(google_secret["SecretString"])
        for key, value in google_data.items():
            os.environ.setdefault(key, str(value))

        # first_button_db 시크릿 로드
        db_secret = client.get_secret_value(SecretId="first_button_db")
        db_data = json.loads(db_secret["SecretString"])
        for key, value in db_data.items():
            os.environ.setdefault(key, str(value))

        print("AWS Secrets Manager에서 시크릿 로드 완료")

    except Exception as e:
        print(f"Secrets Manager 로드 실패 (로컬 .env 사용): {e}")


load_secrets()
