"""Offline URL inspection only: no destination is requested or resolved."""
import ipaddress
import re
from urllib.parse import urlsplit


def check_urls(text):
    candidates = re.findall(r"(?:https?://|www\.)[^\s<>\"']+", text, flags=re.I)
    checks = []
    for raw in dict.fromkeys(candidates):
        raw = raw.rstrip('.,;!?)]}।')
        if len(checks) >= 10:
            break
        url = raw if raw.lower().startswith(('http://', 'https://')) else 'https://' + raw
        flags = []
        try:
            parts = urlsplit(url)
            host = parts.hostname or ''
            if not host:
                raise ValueError('Missing host')
            if parts.scheme == 'http':
                flags.append('Uses unencrypted HTTP; this alone does not prove fraud.')
            if parts.username is not None:
                flags.append('Contains user information before @, which can obscure the destination.')
            try:
                ipaddress.ip_address(host)
                flags.append('Uses a numeric IP address instead of a domain name.')
            except ValueError:
                pass
            ascii_host = host.encode('idna').decode('ascii')
            if any(label.startswith('xn--') for label in ascii_host.split('.')):
                flags.append('Internationalized domain: check spelling carefully for lookalike characters.')
            if host.lower() in ('bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'shorturl.at'):
                flags.append('Shortened URL hides the final destination.')
            if host.count('.') >= 4:
                flags.append('Many subdomains can make the true domain harder to identify.')
            checks.append({'url': raw, 'host': host, 'indicators': flags,
                           'status': 'Pattern indicators found' if flags else 'No obvious pattern indicators',
                           'reputation': 'Not checked. Pattern analysis cannot establish whether a site is safe.'})
        except (ValueError, UnicodeError):
            checks.append({'url': raw, 'host': '', 'indicators': ['URL could not be parsed reliably.'],
                           'status': 'Invalid URL', 'reputation': 'Not checked.'})
    return checks
