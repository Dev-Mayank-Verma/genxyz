import re
from flask import Flask, request, jsonify
from .config import settings
from .db import init_db, get_session, upsert_session, create_order
from .telegram_api import send
from .registrar import RegistrarClient, RegistrarError

app=Flask(__name__)
DOMAIN_RE=re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)xyz$", re.I)

@app.get('/health')
def health():
    return jsonify(ok=True)

@app.post('/webhook')
def webhook():
    secret=request.headers.get('X-Telegram-Bot-Api-Secret-Token','')
    if settings.webhook_secret and secret != settings.webhook_secret:
        return jsonify(ok=False),403
    update=request.get_json(silent=True) or {}
    try:
        handle_update(update)
    except Exception as exc:
        app.logger.exception('update failed')
    return jsonify(ok=True)

def handle_update(update):
    msg=update.get('message')
    if not msg or not msg.get('chat'):
        return
    chat_id=msg['chat']['id']; text=(msg.get('text') or '').strip()
    if text.startswith('/start'):
        upsert_session(chat_id,state='search')
        send(chat_id,'👋 Welcome!\n\nSend the .xyz domain you want to check.\nExample: example.xyz')
        return
    session=get_session(chat_id) or {'state':'idle'}
    state=session.get('state','idle')
    if state=='search':
        domain=text.lower().strip()
        if not DOMAIN_RE.fullmatch(domain):
            send(chat_id,'Please enter a valid .xyz domain, for example: example.xyz')
            return
        try:
            client=RegistrarClient(); available, raw=client.availability(domain)
            if not available:
                send(chat_id,f'❌ {domain} is not available.\n\nSend another .xyz domain.')
                return
            upsert_session(chat_id,state='details',domain=domain,years=1)
            price=client.price(domain,1,settings.coupon_code or None)
            amount=price.get('final_price', price.get('price'))
            currency=price.get('currency','USD')
            coupon_note='\n🎟️ Promotion applied.' if settings.coupon_code else ''
            send(chat_id,f'✅ {domain} is available.\n\n1-year price: {amount} {currency}{coupon_note}\n\nReply with your email address to continue.')
        except RegistrarError as e:
            send(chat_id,'The domain service is not configured or is temporarily unavailable. Please try again later.')
        return
    if state=='details':
        email=text
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):
            send(chat_id,'Please enter a valid email address.')
            return
        upsert_session(chat_id,state='waiting_name',email=email)
        send(chat_id,'Enter your full name.')
        return
    if state=='waiting_name':
        parts=text.split()
        if len(parts)<2:
            send(chat_id,'Please enter first and last name.')
            return
        upsert_session(chat_id,state='waiting_address',first_name=parts[0],last_name=' '.join(parts[1:]))
        send(chat_id,'Enter your address, city, state and postal code in one message.')
        return
    if state=='waiting_address':
        upsert_session(chat_id,state='confirm',address=text)
        send(chat_id,'Details received.\n\nReply CONFIRM to submit the registration, or CANCEL to stop.')
        return
    if state=='confirm':
        if text.upper()=='CANCEL':
            upsert_session(chat_id,state='search')
            send(chat_id,'Cancelled. Send another .xyz domain when ready.')
            return
        if text.upper()!='CONFIRM':
            send(chat_id,'Reply CONFIRM to continue or CANCEL to stop.')
            return
        s=get_session(chat_id)
        try:
            client=RegistrarClient()
            contact={'email':s['email'],'first_name':s['first_name'],'last_name':s['last_name'],'address':s['address'] or ''}
            result=client.register(contact,s['domain'],1,settings.coupon_code or None)
            provider_id=str(result.get('order_id') or result.get('id') or '')
            price=result.get('final_price',result.get('price'))
            currency=result.get('currency','USD')
            create_order(chat_id,s['domain'],1,s['email'],provider_id,price,currency,'submitted')
            upsert_session(chat_id,state='verify',provider_order_id=provider_id)
            send(chat_id,'✅ Registration request submitted.\n\nCheck your email and complete the registrar verification link. Then send /status here.')
        except RegistrarError:
            send(chat_id,'Registration could not be submitted. No charge was attempted by this bot. Please try again later.')
        return
    if text.startswith('/status'):
        s=get_session(chat_id)
        if not s or not s.get('provider_order_id'):
            send(chat_id,'No active order found. Send /start to begin.')
            return
        try:
            result=RegistrarClient().status(s['provider_order_id'])
            send(chat_id,f"Order status: {result.get('status','unknown')}\nDomain: {s.get('domain','-')}")
        except RegistrarError:
            send(chat_id,'Unable to check status right now.')
        return
    send(chat_id,'Send /start to search for a .xyz domain.')

@app.post('/admin/init-db')
def admin_init_db():
    if request.headers.get('X-Admin-Secret') != settings.webhook_secret:
        return jsonify(ok=False),403
    init_db(); return jsonify(ok=True)

if __name__=='__main__':
    init_db(); app.run(host='0.0.0.0',port=8000)
