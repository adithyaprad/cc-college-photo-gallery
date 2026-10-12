# College Photo Gallery

A small web app that runs on your own computer. Take a photo (or pick a file) and it is
uploaded to a private Amazon S3 bucket. The page shows every photo in the bucket as a gallery.

## How it works

```
Browser (localhost:8000)  ──>  Flask server (app.py)  ──>  Amazon S3 bucket (private)
```

- **Flask server** (`app.py`) runs only on your machine. It holds the AWS keys and talks to S3.
- **S3** is the only AWS service used. The bucket blocks all public access.
- The browser never gets AWS keys. To show a photo, the server hands it a link that expires
  after 5 minutes (an S3 "presigned URL").
- No servers run on AWS, so there is no cost when the app is not in use. The only charge is
  storage: about $0.025 per GB per month in `ap-south-1` (Mumbai).

| Endpoint            | What it does                                  |
| ------------------- | --------------------------------------------- |
| `GET /`             | The gallery page (`templates/index.html`)     |
| `POST /api/upload`  | Saves the photo to `s3://<bucket>/photos/...` |
| `GET /api/photos`   | Lists photos, newest first, with short links  |

## Setup

You need Python 3.10+ and an AWS account with an access key that can use S3.

1. Install dependencies:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy the example config and fill in **your own** values:
   ```bash
   cp .env.example .env
   ```
   `S3_BUCKET` must be unique across all of AWS. The app creates it on first run.
3. Start the app:
   ```bash
   python app.py
   ```
4. Open http://localhost:8000

`.env` is in `.gitignore`. Never commit it.

## Removing everything from AWS

```bash
aws s3 rb s3://<your-bucket> --force --region ap-south-1
```
