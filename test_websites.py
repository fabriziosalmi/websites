import requests
import json
from datetime import datetime
import whois
import ssl
import socket

def check_domain_expiration(domain):
    try:
        w = whois.whois(domain)
        expiration_date = w.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]
        days_to_expire = (expiration_date - datetime.now()).days

        if days_to_expire < 15:
            return "🔴"
        elif days_to_expire < 30:
            return "🟠"
        else:
            return "🟢"
    except Exception as e:
        print(f"An error occurred while checking domain expiration for {domain}: {e}")
        return "🔴"

def check_ssl_cert(host, port=443):
    try:
        context = ssl.create_default_context()
        conn = socket.create_connection((host, port))
        sock = context.wrap_socket(conn, server_hostname=host)
        cert = sock.getpeercert()
        sock.close()

        cert_expiry = datetime.strptime(cert['notAfter'], r"%b %d %H:%M:%S %Y %Z")
        days_to_expire = (cert_expiry - datetime.utcnow()).days

        if days_to_expire <= 0:
            return "🔴"
        elif days_to_expire <= 30:
            return "🟠"
        else:
            return "🟢"
    except (ssl.SSLError, ssl.CertificateError):
        return "🔴"

def check_cdn(headers):
    cdn_headers = [
        ("Server", "cloudflare"),
        ("X-hello-human", "KeyCDN"),
        ("X-CDN", "stackpath"),
        ("X-Cache", "Fastly"),
        ("Via", "1.1 varnish"),  # Varnish, also used by Fastly
        ("Server", "ECS"),  # Amazon CloudFront
        ("Server", "AkamaiGHost"),  # Akamai
        ("Server", "nginx"),  # Could be a generic server, but commonly used in front of CDN
        ("X-CDN-Geo", "ovh"),  # OVH CDN
        ("Server", "CDN77-Turbo"),  # CDN77
        ("X-IPLB-Instance", "Incap"),  # Incapsula
        ("X-Powered-By", "Imperva")  # Imperva Incapsula
    ]
    for header, value in cdn_headers:
        if header in headers and value.lower() in headers[header].lower():
            return "🟢"
    return "🟠"

def check_pagespeed(website):
    pagespeed_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://{website}"
    pagespeed_response = requests.get(pagespeed_url)
    pagespeed_data = json.loads(pagespeed_response.text)
    return int(pagespeed_data["lighthouseResult"]["categories"]["performance"]["score"] * 100)

def check_security_headers(headers):
    csp_status = "🟢" if headers.get('Content-Security-Policy') else "🔴"
    revealing_status = "🟢" if not any(header in headers for header in ['Server', 'X-Powered-By', 'X-AspNet-Version']) else "🔴"
    return csp_status, revealing_status

def check_reachability(website):
    response = requests.get(f"https://{website}")
    return "🟢" if response.status_code == 200 else "🔴"

def write_report(websites):
    report_md = "# Websites monitor\n### Performances, headers, SSL/TLS, domain expiration, reachability and CDN enablement monitoring checks via Github action.\n| Site | Reachability | Performances | CSP | Headers | SSL | Expiration | CDN |\n|------|--------------|-----------------|--------------------------|------------------|-----|--------|-----|\n"
    
    for website in websites:
        reachability_status = check_reachability(website)
        pagespeed_score = check_pagespeed(website)
        security_response = requests.get(f"https://{website}")
        headers = security_response.headers
        csp_status, revealing_status = check_security_headers(headers)
        ssl_status = check_ssl_cert(website)
        domain_status = check_domain_expiration(website)
        cdn_status = check_cdn(headers)
        
        report_md += f"| {website} | {reachability_status} | {pagespeed_score} | {csp_status} | {revealing_status} | {ssl_status} | {domain_status} | {cdn_status} |\n"

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_md += f"\n---\nLast Updated: {current_time}"
    
    with open("README.md", "w") as f:
        f.write(report_md)

if __name__ == "__main__":
    websites = [
        'audiolibri.org',
        'get.domainsblacklists.com'
    ]
    write_report(websites)
