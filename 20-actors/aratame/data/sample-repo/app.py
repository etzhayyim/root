# aratame sample fixture — intentionally weak Python service.
# :representative. Weakness PATTERNS only (CWE), no exploit/PoC. Never executed
# by aratame (static AST inspection only — G3).
import hashlib
import subprocess
import pickle
import yaml


def run_report(user_cmd):
    # CWE-78: OS command injection — shell=True with untrusted input.
    return subprocess.call("report " + user_cmd, shell=True)


def evaluate(expr):
    # CWE-95: eval on caller-supplied expression.
    return eval(expr)


def load_profile(blob):
    # CWE-502: insecure deserialization.
    return pickle.loads(blob)


def parse_config(text):
    # CWE-20: yaml.load without SafeLoader.
    return yaml.load(text)


def fingerprint(token):
    # CWE-327: weak hash for a security-relevant value.
    return hashlib.md5(token.encode()).hexdigest()
