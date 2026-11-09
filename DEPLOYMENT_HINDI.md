# TalkExpert ko online kaise karein (simple guide)

**Abhi link nahi bana hai.** Ye ZIP project files hain; public link tab milega jab hosting par deploy hoga.

1. ZIP ko computer par extract karein.
2. Python 3.11+ install karke project folder mein terminal kholein.
3. `pip install -r requirements.txt` chalayein.
4. `.env.example` ki copy `.env` banayein aur secret key set karein. Razorpay test keys sirf server environment mein rakhein.
5. `uvicorn app.main:app --host 0.0.0.0 --port 8000` chalayein.
6. Local test: `http://127.0.0.1:8000`.
7. Public hosting ke liye poora project kisi Python/FastAPI host par deploy karein. Host par persistent managed PostgreSQL database aur environment variables configure karna hoga. Host ka generated HTTPS URL hi website link hoga.

Mobile-only se deployment mushkil ho sakta hai; pehli baar kisi trusted adult ki madad se computer par setup karein. Hosting provider, database, environment variables aur payment merchant setup complete hone se pehle site ko public customers ke liye launch na karein.
