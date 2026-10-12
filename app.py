"""Tiny photo gallery: Flask on your laptop, photos stored in a private S3 bucket."""
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

REGION = os.environ["AWS_REGION"]
BUCKET = os.environ["S3_BUCKET"]

# boto3 reads AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from the environment (.env)
s3 = boto3.client(
    "s3",
    region_name=REGION,
    # Regional endpoint so photo links work immediately on a brand-new bucket.
    endpoint_url=f"https://s3.{REGION}.amazonaws.com",
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB per photo


def ensure_bucket():
    """Create the bucket on first run. New S3 buckets block public access by default."""
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        print(f"Created bucket {BUCKET} in {REGION}")


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/upload")
def upload():
    photo = request.files.get("photo")
    if not photo or not photo.mimetype.startswith("image/"):
        return jsonify(error="Send an image file in the 'photo' field"), 400

    ext = os.path.splitext(photo.filename or "")[1].lower() or ".jpg"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    key = f"photos/{stamp}-{uuid.uuid4().hex[:8]}{ext}"
    s3.upload_fileobj(photo, BUCKET, key, ExtraArgs={"ContentType": photo.mimetype})
    return jsonify(key=key)


@app.get("/api/photos")
def photos():
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="photos/")
    items = sorted(resp.get("Contents", []), key=lambda o: o["LastModified"], reverse=True)
    # The bucket is private, so give the browser short-lived links to each photo.
    return jsonify([
        {
            "key": o["Key"],
            "url": s3.generate_presigned_url(
                "get_object", Params={"Bucket": BUCKET, "Key": o["Key"]}, ExpiresIn=300
            ),
            "uploaded": o["LastModified"].isoformat(),
        }
        for o in items
    ])


if __name__ == "__main__":
    ensure_bucket()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)), debug=True)
