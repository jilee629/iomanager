import logging
import json
import re
import threading

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ALIGO_SEND_URL = "https://kakaoapi.aligo.in/akv10/alimtalk/send/"
ALIGO_VAR_PATTERN = re.compile(r"#\{([^}]+)\}")


def _render_template(template_text, context):
    def replace(match):
        key = match.group(1).strip()
        if key not in context:
            raise KeyError(key)
        return str(context[key])

    return ALIGO_VAR_PATTERN.sub(replace, template_text)


def send_alimtalk(template_key, receiver_phone, context):
    config = getattr(settings, "ALIGO", {}) or {}
    templates = config.get("templates") or {}
    template = templates.get(template_key)
    if not template:
        logger.info("Skip alimtalk: missing template key '%s'", template_key)
        return

    required = ("apikey", "userid", "senderkey", "sender")
    missing_fields = [field for field in required if not config.get(field)]
    if missing_fields:
        logger.info("Skip alimtalk: missing required config fields %s", ",".join(missing_fields))
        return

    try:
        rendered_message = _render_template(template.get("message", ""), context)
    except KeyError as error:
        logger.exception("Skip alimtalk: missing template variable '%s' for key '%s'", error, template_key)
        return

    payload = {
        "apikey": config["apikey"],
        "userid": config["userid"],
        "senderkey": config["senderkey"],
        "tpl_code": template.get("tpl_code", ""),
        "sender": config["sender"],
        "receiver_1": receiver_phone,
        "subject_1": template.get("subject", ""),
        "emtitle_1": "점핑몬스터 미사점",
        "message_1": rendered_message,
        "testMode": "Y" if config.get("test_mode") else "N",
    }
    buttons = template.get("buttons") or []
    if buttons:
        payload["button_1"] = json.dumps({"button": buttons}, ensure_ascii=False)
    if not payload["tpl_code"]:
        logger.info("Skip alimtalk: missing tpl_code for key '%s'", template_key)
        return

    def _request_send():
        try:
            response = requests.post(ALIGO_SEND_URL, data=payload, timeout=10)
            logger.info(
                "Alimtalk sent key=%s receiver=%s status=%s body=%s",
                template_key,
                receiver_phone,
                response.status_code,
                response.text[:300],
            )
        except Exception:
            logger.exception("Alimtalk request failed key=%s receiver=%s", template_key, receiver_phone)

    threading.Thread(target=_request_send, daemon=True).start()
