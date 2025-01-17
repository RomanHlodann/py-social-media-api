# Social media API

Social media API is used for managing posts and comments. Also it can generate response to comment and block profanity. Gives analytics about created and blocked comments in specified range of dates.

## Installation

```bash
git clone https://github.com/RomanHlodann/py-social-media-api.git
cd py-social-media-api
python -m venv venv
On mac: source venv/bin/activate Windows: venv/Scripts/activate
pip install -r requirements.txt
```

Create .env file with needed keys

To use ai for responses you shoud run redis in docker
```bash
docker run -d -p 6379:6379 redis
```
And start worker
```bash
celery -A social_media worker -P solo
```

Then, you can start project:
```bash
python manage.py migrate
python manage.py runserver
```

## Features
* JWT authenticated
* Django, Ninja
* Celery, Redis
* Usage of an ai model to generate fast reply
* Filtering comments on profanity

## Access the API endpoints via 
`http://localhost:8000/`
* **Posts crud** `api/posts/`
* **Comments crud** `api/posts/{post_id}/comments/`
* **Comments analytics** `api/posts/comments-daily-breakdown/?date_from=2023-07-11&date_to=2023-07-11`

To operate with tokens:
* **Get tokens** `api/users/token/pair/`
* **Refresh token** `api/users/token/refresh/`
* **Verify token** `api/users/token/verify/`
* **Register** `api/users/register/`

To use docs ui you can access by `http://localhost:8000/api/users/docs` or `http://localhost:8000/api/posts/docs`

## Testing
To run tests run this command
```bash
python manage.py test
``` 