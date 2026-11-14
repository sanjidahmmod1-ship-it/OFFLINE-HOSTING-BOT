OFFLINE HOST BOT
================

এটি Python দিয়ে তৈরি Telegram Bot management bot।

ফিচার:
- @BotFather থেকে তৈরি করা Bot Token যুক্ত করা
- Token যাচাই
- Token encrypted অবস্থায় SQLite-এ সংরক্ষণ
- My Bots তালিকা
- Bot Name, Description, About এবং Commands পরিবর্তন
- Bot Information দেখা
- নিজের Manager তালিকা থেকে Bot সরানো
- Admin stats, ban/unban এবং broadcast

গুরুত্বপূর্ণ সীমাবদ্ধতা:
- নতুন Telegram Bot তৈরি করতে Telegram-এর আসল @BotFather প্রয়োজন।
- এই প্রজেক্ট BotFather-এর internal system নয়; Telegram Bot API-তে অনুমোদিত সেটিংসই পরিবর্তন করতে পারে।
- "Remove from this manager" আসল Telegram Bot ডিলিট করে না।
- Token revoke/delete করতে আসল @BotFather ব্যবহার করতে হবে।
- Bot settings পরিবর্তনের সময় Telegram API-এর permission/limit প্রযোজ্য।

SETUP (Termux):
1. Python 3.10 বা নতুন সংস্করণ ইনস্টল করুন।
2. এই ফোল্ডারে প্রবেশ করুন।
3. pip install -r requirements.txt চালান।
4. .env.example কপি করে .env নামে রাখুন।
5. .env-এ Main Bot Token, নিজের Telegram numeric user ID এবং Fernet key দিন।

Fernet key তৈরি:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

চালু:
python main.py

সতর্কতা:
- .env ফাইল কাউকে দেবেন না।
- Bot Token কখনো চ্যাট/গ্রুপে প্রকাশ করবেন না।
- ENCRYPTION_KEY হারালে আগের encrypted token আর decrypt করা যাবে না।
- Production ব্যবহারের আগে VPS security, backup, rate limiting ও monitoring যোগ করুন।
