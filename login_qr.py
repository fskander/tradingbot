import asyncio
import qrcode
import sys
from telethon import TelegramClient

# Load Config
try:
    import config
except ImportError:
    print("❌ Config not found.")
    sys.exit(1)

API_ID = config.TELEGRAM_API_ID
API_HASH = config.TELEGRAM_API_HASH

async def main():
    print("🔄 Initializing QR Login...")
    client = TelegramClient('session_main', API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        qr_login = await client.qr_login()
        print("\n" + "="*40)
        print("📱 SCAN THIS QR CODE WITH TELEGRAM APP")
        print("   (Settings > Devices > Link Desktop Device)")
        print("="*40 + "\n")
        
        # Generate and print QR
        qr = qrcode.QRCode()
        qr.add_data(qr_login.url)
        qr.print_ascii(invert=True)
        
        print("\n⏳ Waiting for you to scan...")
        await qr_login.wait()
        print("\n✅ SUCCESS! You are logged in.")
    else:
        print("\n✅ You were already logged in!")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
