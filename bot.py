import os
import asyncio
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

# আপনার টেলিগ্রাম বট টোকেন এখানে দিন
TOKEN = '8515561351:AAHdfsdy7ShGoCWShwTwU6XbWSdRb_TZXq8'

async def clean_and_format_html(raw_html):
    """ডিক্রিপ্ট হওয়া কোড থেকে ময়লা পরিষ্কার করা"""
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # এনক্রিপ্টরের বাড়তি স্ক্রিপ্ট ট্যাগগুলো রিমুভ করা (ঐচ্ছিক)
    # অনেক সময় ডিক্রিপ্ট হওয়ার পর এনক্রিপ্টরের স্ক্রিপ্ট থেকে যায় যা আর দরকার নেই
    scripts_to_remove = soup.find_all("script")
    for script in scripts_to_remove:
        # যদি স্ক্রিপ্টের ভেতরে এনক্রিপশন লজিক থাকে তবে তা বাদ দিতে পারেন
        if len(script.text) > 500: # বড় স্ক্রিপ্টগুলো সাধারণত এনক্রিপশন মেকানিজম হয়
            script.decompose()

    return soup.prettify()

async def decrypt_html_logic(file_path):
    """ব্রাউজারের মেমোরি থেকে ডাটা বের করার আসল লজিক"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # ফাইল পাথ সেট করা
        abs_path = f"file://{os.path.abspath(file_path)}"
        
        # ব্রাউজারে ফাইলটি ওপেন করা
        await page.goto(abs_path, wait_until="networkidle")
        
        # জাভাস্ক্রিপ্ট ডিক্রিপ্ট হওয়ার জন্য ৩ সেকেন্ড সময় দিন
        await asyncio.sleep(7) 

        # ব্রাউজারের বর্তমান রেন্ডার করা কন্টেন্ট নেওয়া
        content = await page.content()
        
        await browser.close()
        return content

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_name = update.message.document.file_name

    if file_name.endswith(".html"):
        status_msg = await update.message.reply_text("🔍 ফাইলটি এনালাইজ করা হচ্ছে...")
        
        download_path = f"temp_{file_name}"
        await file.download_to_drive(download_path)

        try:
            await status_msg.edit_text("🔓 ডিক্রিপ্ট করা হচ্ছে (Virtual Browser-এ রান হচ্ছে)...")
            
            # স্টেপ ১: ব্রাউজার থেকে রেন্ডার করা কোড আনা
            raw_decrypted = await decrypt_html_logic(download_path)
            
            # স্টেপ ২: কোড ক্লিন করা
            await status_msg.edit_text("✨ কোড বিউটিফাই করা হচ্ছে...")
            clean_html = await clean_and_format_html(raw_decrypted)
            
            # স্টেপ ৩: ফাইল সেভ করা
            output_file = f"decrypted_{file_name}"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(clean_html)

            # ইউজারকে পাঠানো
            await update.message.reply_document(
                document=open(output_file, "rb"), 
                caption="✅ সফলভাবে ডিক্রিপ্ট করা হয়েছে!\n\nবটটি ব্রাউজার রেন্ডারিং মেথড ব্যবহার করেছে।"
            )
            
            # ডিলিট করা
            os.remove(download_path)
            os.remove(output_file)
            await status_msg.delete()

        except Exception as e:
            await update.message.reply_text(f"❌ এরর: {str(e)}")
    else:
        await update.message.reply_text("❌ দয়া করে একটি HTML ফাইল পাঠান।")

def main():
    print("বট স্টার্ট হচ্ছে...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()

if __name__ == '__main__':
    main()