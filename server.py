#GhamYar Project
#server.py
#author: Hossein Heari
#GitHub: https://github.com/Hossein-Hesari
#Kharazmi

import os
import json
import uuid
import logging
from flask import Flask, request, jsonify, render_template, make_response
import requests
from dotenv import load_dotenv

# --- پیکربندی اولیه ---
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = Flask(__name__)

# --- خواندن تنظیمات از متغیرهای محیطی ---
GAPGPT_API_KEY = os.environ.get("GAPGPT_API_KEY")
if not GAPGPT_API_KEY:
    logger.error("GAPGPT_API_KEY environment variable not set!")

GAPGPT_API_URL = os.environ.get("GAPGPT_API_URL", "https://api.gapgpt.app/v1/chat/completions")
APP_PORT = int(os.environ.get("PORT", 3000))

# --- مسیر فایل‌ها ---
ADDITIONAL_INFO_FILE = 'additional_info.txt'
HISTORY_FILE = 'chat_history.json'

additional_info_content = ""


# ─────────────────────────────────────────────
#         توابع مدیریت چت هیستوری
# ─────────────────────────────────────────────

def get_user_id():
    """شناسه کاربر از کوکی"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
    return user_id


def load_history():
    """بارگذاری هیستوری از فایل"""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading history: {e}")
        return {}


def save_history(history):
    """ذخیره هیستوری در فایل"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except IOError as e:
        logger.error(f"Error saving history: {e}")


def has_history(user_id):
    """آیا کاربر هیستوری دارد؟"""
    history = load_history()
    return user_id in history and len(history[user_id]) > 0


def get_history_context(user_id, limit=10):
    """
    هیستوری مکالمات را برای ارسال به AI آماده می‌کند.
    """
    history = load_history()
    if user_id not in history or not history[user_id]:
        return "", ""

    user_data = history[user_id][-limit:]

    # ساخت context text
    context_parts = []
    saved_interests = ""

    for entry in user_data:
        saved_interests = entry.get("interests", "")
        user_msg = entry.get("user", "")
        ai_msg = entry.get("assistant", "")

        context_parts.append(f"سوال: {user_msg}")
        context_parts.append(f"پاسخ: {ai_msg}")

    context_text = "\n".join(context_parts)
    return context_text, saved_interests


def add_to_history(user_id, interests, user_message, ai_response):
    """
    ذخیره یک مکالمه جدید.
    """
    history = load_history()

    if user_id not in history:
        history[user_id] = []

    entry = {
        "interests": interests,
        "user": user_message,
        "assistant": ai_response
    }
    history[user_id].append(entry)

    # حداکثر ۲۰ مکالمه آخر
    if len(history[user_id]) > 20:
        history[user_id] = history[user_id][-20:]

    save_history(history)
    logger.info(f"Chat saved for user {user_id}")


# ─────────────────────────────────────────────
#         خواندن فایل اطلاعات اضافی
# ─────────────────────────────────────────────

try:
    with open(ADDITIONAL_INFO_FILE, 'r', encoding='utf-8') as f:
        additional_info_content = f.read()
    logger.info(f"Successfully loaded additional info from {ADDITIONAL_INFO_FILE}")
except FileNotFoundError:
    logger.warning(f"'{ADDITIONAL_INFO_FILE}' not found.")
    additional_info_content = ""
except Exception as e:
    logger.error(f"Error loading {ADDITIONAL_INFO_FILE}: {e}")
    additional_info_content = ""


# ─────────────────────────────────────────────
#                   Route ها
# ─────────────────────────────────────────────

@app.route('/')
def introduction():
    """صفحه معرفی"""
    logger.info("Rendering index.html")
    try:
        return render_template('index.html')
    except FileNotFoundError:
        logger.error("index.html not found.")
        return "خطا در بارگذاری صفحه اصلی.", 500
    except Exception as e:
        logger.error(f"Error rendering index.html: {e}")
        return "خطا در بارگذاری صفحه اصلی.", 500


@app.route('/main')
def index():
    """صفحه اصلی"""
    logger.info("Rendering main.html")
    try:
        return render_template('main.html')
    except FileNotFoundError:
        logger.error("main.html not found.")
        return "خطا در بارگذاری صفحه اصلی.", 500
    except Exception as e:
        logger.error(f"Error rendering main.html: {e}")
        return "خطا در بارگذاری صفحه اصلی.", 500

@app.route('/document')
def document():
    """صفحه اصلی"""
    logger.info("Rendering doc.html")
    try:
        return render_template('doc.html')
    except FileNotFoundError:
        logger.error("doc.html not found.")
        return "خطا در بارگذاری صفحه اصلی.", 500
    except Exception as e:
        logger.error(f"Error rendering doc.html: {e}")
        return "خطا در بارگذاری صفحه اصلی.", 500


@app.route('/predict', methods=['POST'])
def predict():
    """پردازش درخواست - با چت هیستوری"""
    logger.info(f"Received request on /predict")

    if not GAPGPT_API_KEY:
        logger.error("GAPGPT_API_KEY not set.")
        return jsonify({"error": "Server configuration error"}), 500

    # دریافت شناسه کاربر
    user_id = get_user_id()

    try:
        data = request.get_json()
        if not data:
            raise ValueError("Invalid JSON data received")

        interests = data.get("interests", "")
        description = data.get("description", "")

        # ─── بررسی هیستوری ───
        # اگر بار اول است (هیستوری ندارد)، باید interests و description هر دو باشند
        # اگر قبلاً چت کرده، فقط description کافی است

        if not has_history(user_id):
            # بار اول - هر دو لازم است
            if not interests or not description:
                logger.warning("First chat: Missing 'interests' or 'description'.")
                return jsonify({
                    "error": "لطفا علایق و متن خود را کامل وارد نمایید.",
                    "details": "Missing 'interests' or 'description' field",
                    "is_first_chat": True
                }), 400
        else:
            if not description:
                logger.warning("Missing 'description' in request data.")
                return jsonify({
                    "error": "لطفاً متن خود را وارد نمایید.",
                    "details": "Missing 'description' field"
                }), 400
            if not interests:
                history_context, interests = get_history_context(user_id, limit=1)
                if not interests:
                    interests = "نامشخص"

    except ValueError as ve:
        logger.error(f"Error parsing JSON data: {ve}")
        return jsonify({"error": "Bad Request", "details": "Invalid JSON format"}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

    history_context, _ = get_history_context(user_id, limit=10)

    if history_context:
        history_section = f"""
## تاریخچه مکالمات اخیر:
{history_context}
"""
    else:
        history_section = "## تاریخچه: ندارد (این اولین مکالمه است)"

    final_prompt = f"""تو یک دستیار هوشمند هستی.

## اطلاعات کاربر
علایق کاربر: {interests}

## توضیحات کاربر (سوال جدید)
{description}

{history_section}

## اطلاعات تکمیلی
{additional_info_content}

لطفاً با توجه به تاریخچه مکالمات بالا، یک پاسخ مناسب و دقیق ارائه بده."""

    final_prompt = final_prompt.strip()
    logger.info(f"Constructed prompt for GapGPT API (user has history: {has_history(user_id)})")

    # ─── ارسال به API ───
    payload = {
        "model": "gpt-5.2",
        "messages": [
            {
                "role": "user",
                "content": final_prompt
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {GAPGPT_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Sending request to GapGPT API")
        response = requests.post(GAPGPT_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0 \
           and "message" in result["choices"][0] \
           and "content" in result["choices"][0]["message"]:

            answer = result["choices"][0]["message"]["content"]
            logger.info("Successfully received response from GapGPT API.")

            # ─── ذخیره در چت هیستوری ───
            add_to_history(user_id, interests, description, answer)

            response = make_response(jsonify({
                "response": answer,
                "is_first_chat": not has_history(user_id) or len(load_history().get(user_id, [])) == 1
            }))
            response.set_cookie('user_id', user_id, max_age=60 * 60 * 24 * 365)
            return response

        else:
            logger.error(f"Unexpected response format from GapGPT API.")
            return jsonify({"error": "API Response Error"}), 502

    except requests.exceptions.Timeout:
        logger.error("Request timed out.")
        return jsonify({"error": "Service Unavailable", "details": "زمان پاسخ سرور به پایان رسید."}), 503

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error: {http_err}")
        return jsonify({"error": "API Error", "details": f"خطای API: {response.status_code}"}), 502

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error: {req_err}")
        return jsonify({"error": "Service Unavailable", "details": "امکان اتصال وجود ندارد."}), 503

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


# ─── اجرای اپلیکیشن ───
if __name__ == '__main__':
    if not GAPGPT_API_KEY:
        logger.critical("GAPGPT_API_KEY is not set.")
    else:
        logger.info(f"Starting Flask server on port {APP_PORT}.")
        app.run(debug=True, host='0.0.0.0', port=APP_PORT)
        if os.path.exists("chat_history.json"):
            os.remove("chat_history.json")
