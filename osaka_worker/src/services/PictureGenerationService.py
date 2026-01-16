import boto3
import io
import requests

from PIL import Image, ImageDraw, ImageFont
from aws_lambda_powertools import Logger
from dto.PictureRequest import PictureRequest

logger = Logger()

S3_CLIENT = boto3.client('s3')
BUCKET_NAME = 'email-templates-picture-bucket'
FONT_PATH = 'IMPACT.TTF'

def generate_picture(data: PictureRequest, request_id: str) -> str:
    img = _fetch_picture(str(data.image_url))
    img_with_text = _draw_impact(img, data.top_text, data.bottom_text)
    return _upload_result_to_s3(img_with_text, request_id)

def _fetch_picture(url: str) -> Image:
    response = requests.get(url, timeout=10)
    logger.info(f"Fetched picture for url: {url}")
    return Image.open(io.BytesIO(response.content))

def _get_fitted_font(draw: ImageDraw, text: str, max_width: float, start_size: int) -> ImageFont:
    if not text:
        return None
    
    current_size = start_size
    text_upper = text.upper()

    while current_size > 10:
        try:
            font = ImageFont.truetype(FONT_PATH, current_size)
        except:
            return ImageFont.load_default()
        
        if draw.textlength(text_upper, font=font) <= max_width:
            return font
        current_size -= 2
    
    return ImageFont.load_default()

def _draw_impact(img: Image, top: str, bottom: str) -> Image:
    draw = ImageDraw.Draw(img)
    w, h = img.size

    max_w = w * 0.9
    initial_size = int(h + 0.12)

    top_font = _get_fitted_font(draw, top, max_w, initial_size)
    bottom_font = _get_fitted_font(draw, bottom, max_w, initial_size)

    if top_font:
        _draw_single_line(draw, top.upper(), h * 0.05, top_font, w)
    if bottom_font:
        y_pos = h - bottom_font.size - (h * 0.05)
        _draw_single_line(draw, bottom.upper(),y_pos, bottom_font, w)

    logger.info("Text was overlaid to picture")
    return img

def _draw_single_line(draw, text, y, font, img_w):
    text_w = draw.textlength(text, font=font)
    x = (img_w - text_w) / 2
    
    stroke_radius = 2

    for offset_x in range(-stroke_radius, stroke_radius + 1):
        for offset_y in range(-stroke_radius, stroke_radius + 1):
            if offset_x == 0 and offset_y == 0:
                continue
            draw.text(
                (x + offset_x, y + offset_y), 
                text, 
                font=font, 
                fill="black"
            )

    draw.text((x, y), text, font=font, fill="white")

    logger.info("Single line was drawn")

def _upload_result_to_s3(img: Image, request_id: str) -> str:
    logger.info("Uploading image")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    logger.info("Creating key")
    key = f"generated/{request_id}.jpg"
    S3_CLIENT.upload_fileobj(
        buffer, BUCKET_NAME, key,
        ExtraArgs={'ContentType': 'image/jpeg'}
    )

    logger.info("Retrieving S3 url")
    return f'https://{BUCKET_NAME}.s3.amazonaws.com/{key}'