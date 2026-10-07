"""Alert channels. All open-source / stdlib: log file, SMTP email, webhook (Slack/Teams/any JSON)."""
from __future__ import annotations
import json, logging, smtplib, time, urllib.request
from email.message import EmailMessage

log = logging.getLogger(__name__)


class Notifier:
    name = "base"
    def send(self, alert: dict) -> bool:  # pragma: no cover
        raise NotImplementedError


class FileNotifier(Notifier):
    """Always-on audit trail (JSON lines). Also the safe fallback when SMTP isn't configured."""
    name = "file"
    def __init__(self, path="alerts.jsonl"):
        self.path = path
    def send(self, alert):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert, default=str) + "\n")
        return True


class EmailNotifier(Notifier):
    name = "email"
    def __init__(self, host, port=587, user=None, password=None, sender=None, recipients=None, use_tls=True):
        self.host, self.port, self.user, self.password = host, port, user, password
        self.sender = sender or user
        self.recipients = recipients or []
        self.use_tls = use_tls
    def send(self, alert):
        if not (self.host and self.recipients):
            return False
        msg = EmailMessage()
        msg["Subject"] = alert["subject"]
        msg["From"], msg["To"] = self.sender, ", ".join(self.recipients)
        msg.set_content(alert["message"])
        with smtplib.SMTP(self.host, self.port, timeout=15) as s:
            if self.use_tls:
                s.starttls()
            if self.user:
                s.login(self.user, self.password)
            s.send_message(msg)
        return True


class WebhookNotifier(Notifier):
    """POSTs {"text": ...} (Slack/Teams/Mattermost compatible) plus the full alert under "alert"."""
    name = "webhook"
    def __init__(self, url):
        self.url = url
    def send(self, alert):
        if not self.url:
            return False
        body = json.dumps({"text": f"*{alert['subject']}*\n{alert['message']}", "alert": alert}, default=str).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return 200 <= r.status < 300


def build_notifiers(cfg: dict) -> list[Notifier]:
    out: list[Notifier] = [FileNotifier(cfg.get("file", {}).get("path", "alerts.jsonl"))]
    e = cfg.get("email", {})
    if e.get("enabled"):
        out.append(EmailNotifier(e.get("host"), e.get("port", 587), e.get("user"), e.get("password"),
                                 e.get("sender"), e.get("recipients"), e.get("use_tls", True)))
    w = cfg.get("webhook", {})
    if w.get("enabled"):
        out.append(WebhookNotifier(w.get("url")))
    return out


def dispatch(notifiers: list[Notifier], alert: dict, retries: int = 2):
    """Send to every channel with retry; returns (channels_ok, any_external_ok)."""
    ok, external = [], False
    for n in notifiers:
        for attempt in range(retries + 1):
            try:
                if n.send(alert):
                    ok.append(n.name); external |= n.name != "file"
                break
            except Exception as ex:  # network/SMTP errors must never break the edit flow
                log.warning("notifier %s failed (attempt %d): %s", n.name, attempt + 1, ex)
                time.sleep(0.5 * (attempt + 1))
    return ok, external
