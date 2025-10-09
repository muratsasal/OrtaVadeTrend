import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

def send_telegram_message(bot_token, chat_id, message, parse_mode='HTML'):
    """
    Telegram bot üzerinden mesaj gönderme fonksiyonu
    
    Parameters:
    - bot_token: Telegram bot token (BotFather'dan alınan)
    - chat_id: Mesaj gönderilecek chat ID
    - message: Gönderilecek mesaj
    - parse_mode: Mesaj formatı ('HTML' veya 'Markdown')
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Mesaj çok uzunsa böl (Telegram limit: 4096 karakter)
    max_length = 4000
    messages = []
    
    if len(message) > max_length:
        parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
        messages = parts
    else:
        messages = [message]
    
    responses = []
    for msg in messages:
        payload = {
            'chat_id': chat_id,
            'text': msg,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload)
            responses.append(response.json())
            if response.status_code == 200:
                print(f"✅ Telegram mesajı başarıyla gönderildi!")
            else:
                print(f"❌ Telegram mesajı gönderilemedi: {response.text}")
        except Exception as e:
            print(f"❌ Hata: {e}")
            responses.append(None)
    
    return responses

def format_telegram_message(df_all, df_fresh):
    """
    DataFrame'leri Telegram için formatla
    """
    message = "📊 <b>BIST100 RSI Analizi</b>\n"
    message += f"📅 Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    message += "="*40 + "\n\n"
    
    # Bu hafta yukarı kesenler
    if not df_fresh.empty:
        message += "🔥 <b>BU HAFTA YUKARI KESENLER</b> 🔥\n"
        message += f"Toplam: {len(df_fresh)} hisse\n"
        message += "-"*40 + "\n\n"
        
        for idx, row in df_fresh.iterrows():
            message += f"<b>{row['Hisse']}</b>\n"
            message += f"  • Mor Çizgi (RSI): {row['Mor_Çizgi']}\n"
            message += f"  • Sarı Çizgi (SMA): {row['Sarı_Çizgi']}\n"
            message += f"  • Fark: +{row['Fark']}\n"
            message += f"  • Fiyat: {row['Fiyat']} TL\n"
            message += f"  • Min Sarı: {row['Min_Sarı']} ({row['Min_Tarih']})\n\n"
        
        message += "="*40 + "\n\n"
    
    # Tüm sonuçlar özeti
    if not df_all.empty:
        message += f"📈 <b>TÜM SONUÇLAR ÖZETİ</b>\n"
        message += f"Toplam: {len(df_all)} hisse\n"
        message += f"Bu hafta kesen: {len(df_fresh)} hisse\n"
        message += f"Daha önce kesen: {len(df_all) - len(df_fresh)} hisse\n\n"
        
        message += f"<b>İstatistikler:</b>\n"
        message += f"  • Ort. Mor Çizgi: {df_all['Mor_Çizgi'].mean():.2f}\n"
        message += f"  • Ort. Sarı Çizgi: {df_all['Sarı_Çizgi'].mean():.2f}\n"
        message += f"  • Ort. Fark: {df_all['Fark'].mean():.2f}\n\n"
        
        # En yüksek fark'a sahip 5 hisse
        message += "<b>En Güçlü 5 Hisse:</b>\n"
        top5 = df_all.head(5)
        for idx, row in top5.iterrows():
            message += f"  {row['Hisse']}: Fark +{row['Fark']} | Fiyat {row['Fiyat']} TL\n"
    
    return message

def calculate_rsi(data, period=31):
    """RSI hesaplama fonksiyonu"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# BIST100 hisse listesi (örnek - daha fazla eklenebilir)
bist100_stocks = [
    'AKBNK.IS', 'THYAO.IS', 'TUPRS.IS', 'EREGL.IS', 'SAHOL.IS',
    'KCHOL.IS', 'GARAN.IS', 'SISE.IS', 'PETKM.IS', 'ASELS.IS',
    'TTKOM.IS', 'KOZAL.IS', 'KOZAA.IS', 'TAVHL.IS', 'BIMAS.IS',
    'EKGYO.IS', 'TCELL.IS', 'ISCTR.IS', 'FROTO.IS', 'HEKTS.IS',
    'ENKAI.IS', 'PGSUS.IS', 'OYAKC.IS', 'SODA.IS', 'VESTL.IS',
    'TOASO.IS', 'KRDMD.IS', 'VAKBN.IS', 'DOHOL.IS', 'ARCLK.IS',
    'AEFES.IS', 'ODAS.IS', 'KONTR.IS', 'ENJSA.IS', 'HALKB.IS',
    'MGROS.IS', 'BTCIM.IS', 'SKBNK.IS', 'SOKM.IS', 'TTRAK.IS',
    'GUBRF.IS', 'AGHOL.IS', 'ULKER.IS', 'CCOLA.IS', 'AKSEN.IS',
    'ANACM.IS', 'GESAN.IS', 'GLYHO.IS', 'MAVI.IS', 'YATAS.IS',
    'ALARK.IS', 'PRKME.IS', 'LOGO.IS', 'BRSAN.IS', 'TKFEN.IS',
    'ISGYO.IS', 'TRILC.IS', 'CEMAS.IS', 'EGEEN.IS', 'ISCTR.IS'
]

def get_rsi_crossover_stocks(rsi_period=31, sma_period=31, sma_threshold=51):
    """
    Mor Çizgi: 31 haftalık RSI
    Sarı Çizgi: 31 haftalık RSI SMA
    
    Koşullar:
    1) Son 2 yılda Sarı Çizgi < 51 görmüş olmalı
    2) Şu anda Mor Çizgi > Sarı Çizgi
    
    Ek: Bu hafta yukarı kesişme yapanları ayrıca listele
    (Geçen hafta Mor < Sarı, bu hafta Mor > Sarı)
    """
    
    all_results = []
    fresh_crossover_results = []
    
    # Son 2 yıl + ekstra veri için 3 yıl çekelim
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095)
    two_years_ago = end_date - timedelta(days=730)
    
    print(f"BIST100 hisseleri taranıyor...\n")
    print(f"📊 Tanımlamalar:")
    print(f"  • MOR ÇİZGİ = 31 Haftalık RSI")
    print(f"  • SARI ÇİZGİ = 31 Haftalık RSI SMA")
    print(f"\n🔍 Koşullar:")
    print(f"  1) Son 2 yılda SARI ÇİZGİ < {sma_threshold} seviyesini görmüş olmalı")
    print(f"  2) Şu anda: MOR ÇİZGİ > SARI ÇİZGİ")
    print(f"\n{'='*90}")
    
    for stock in bist100_stocks:
        try:
            # Haftalık veri çekme
            data = yf.download(stock, start=start_date, end=end_date, 
                             interval='1wk', progress=False)
            
            if len(data) < rsi_period + sma_period + 20:
                continue
            
            # RSI hesaplama (Mor Çizgi)
            data['RSI'] = calculate_rsi(data['Close'], period=rsi_period)
            
            # RSI'ın SMA'sını hesaplama (Sarı Çizgi)
            data['RSI_SMA'] = data['RSI'].rolling(window=sma_period).mean()
            
            # Son 2 yıllık veriyi filtrele
            recent_data = data[data.index >= two_years_ago].copy()
            
            if len(recent_data) < 10:
                continue
            
            # Koşul 1: Son 2 yılda RSI_SMA < 51 olmuş mu?
            has_been_below_threshold = (recent_data['RSI_SMA'] < sma_threshold).any()
            
            if not has_been_below_threshold:
                continue
            
            # En düşük RSI_SMA değerini bul
            min_rsi_sma = recent_data['RSI_SMA'].min()
            min_rsi_sma_date = recent_data['RSI_SMA'].idxmin()
            
            # Son değerler (bu hafta)
            current_rsi = data['RSI'].iloc[-1]
            current_rsi_sma = data['RSI_SMA'].iloc[-1]
            
            # Geçen hafta değerleri
            prev_rsi = data['RSI'].iloc[-2] if len(data) >= 2 else None
            prev_rsi_sma = data['RSI_SMA'].iloc[-2] if len(data) >= 2 else None
            
            # Koşul 2: Şu anda RSI > RSI_SMA mi?
            if (pd.notna(current_rsi) and pd.notna(current_rsi_sma) and 
                current_rsi > current_rsi_sma):
                
                stock_name = stock.replace('.IS', '')
                current_price = data['Close'].iloc[-1]
                rsi_diff = current_rsi - current_rsi_sma
                
                # RSI_SMA'nın 51'in altına son ne zaman düştüğünü bul
                below_threshold = recent_data[recent_data['RSI_SMA'] < sma_threshold]
                if len(below_threshold) > 0:
                    last_below_date = below_threshold.index[-1]
                    weeks_since = len(data[data.index > last_below_date])
                else:
                    last_below_date = None
                    weeks_since = None
                
                # Bu hafta yukarı kesişme kontrolü
                is_fresh_crossover = False
                if (pd.notna(prev_rsi) and pd.notna(prev_rsi_sma) and 
                    prev_rsi < prev_rsi_sma and current_rsi > current_rsi_sma):
                    is_fresh_crossover = True
                
                result_dict = {
                    'Hisse': stock_name,
                    'Mor_Çizgi': round(current_rsi, 2),
                    'Sarı_Çizgi': round(current_rsi_sma, 2),
                    'Fark': round(rsi_diff, 2),
                    'Min_Sarı': round(min_rsi_sma, 2),
                    'Min_Tarih': min_rsi_sma_date.strftime('%Y-%m-%d'),
                    'Son_<51': last_below_date.strftime('%Y-%m-%d') if last_below_date else 'N/A',
                    'Hafta_Önce': weeks_since if weeks_since else 'N/A',
                    'Fiyat': round(current_price, 2),
                    'Bu_Hafta_Kesti': '🔥 EVET' if is_fresh_crossover else 'Hayır'
                }
                
                all_results.append(result_dict)
                
                if is_fresh_crossover:
                    fresh_crossover_results.append(result_dict)
                    print(f"🔥 {stock_name:8} | Mor: {current_rsi:5.2f} | Sarı: {current_rsi_sma:5.2f} | "
                          f"Fark: +{rsi_diff:5.2f} | BU HAFTA YUKARI KESİŞME! | "
                          f"Fiyat: {current_price:8.2f} TL")
                else:
                    print(f"✓  {stock_name:8} | Mor: {current_rsi:5.2f} | Sarı: {current_rsi_sma:5.2f} | "
                          f"Fark: +{rsi_diff:5.2f} | Fiyat: {current_price:8.2f} TL")
        
        except Exception as e:
            continue
    
    print(f"{'='*90}")
    
    # TÜM SONUÇLAR
    if all_results:
        df_all = pd.DataFrame(all_results)
        df_all = df_all.sort_values('Fark', ascending=False)
        
        print(f"\n📊 TÜM SONUÇLAR - Toplam {len(all_results)} hisse bulundu:\n")
        print(df_all.to_string(index=False))
        
        # BU HAFTA YUKARI KESENLER
        if fresh_crossover_results:
            print(f"\n{'='*90}")
            print(f"🔥 BU HAFTA YUKARI KESENLER - Toplam {len(fresh_crossover_results)} hisse:\n")
            df_fresh = pd.DataFrame(fresh_crossover_results)
            df_fresh = df_fresh.sort_values('Fark', ascending=False)
            print(df_fresh.to_string(index=False))
        
        # İstatistikler
        print(f"\n{'='*90}")
        print("📈 İSTATİSTİKLER (Tüm Hisseler):")
        print(f"  • Ortalama Mor Çizgi (RSI): {df_all['Mor_Çizgi'].mean():.2f}")
        print(f"  • Ortalama Sarı Çizgi (RSI_SMA): {df_all['Sarı_Çizgi'].mean():.2f}")
        print(f"  • Ortalama Fark: {df_all['Fark'].mean():.2f}")
        print(f"  • Bu hafta yukarı kesen: {len(fresh_crossover_results)} hisse")
        print(f"  • Daha önce kesen: {len(all_results) - len(fresh_crossover_results)} hisse")
        
        return df_all, df_fresh if fresh_crossover_results else pd.DataFrame()
    else:
        print("\n❌ Belirtilen koşulları sağlayan hisse bulunamadı.")
        return pd.DataFrame(), pd.DataFrame()

# Kodu çalıştır
if __name__ == "__main__":
    # Telegram Bot Ayarları
    # BotFather'dan aldığınız token'ı buraya yazın
    TELEGRAM_BOT_TOKEN = "8256592463:AAHlJ3BQSvwUDOQuKCYAhKwAwMMWUFJXE4o"  # Örnek: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    
    # Chat ID'nizi buraya yazın (kendi chat ID'niz veya grup ID'si)
    TELEGRAM_CHAT_ID = "1008660822"  # Örnek: "123456789" veya "-100123456789" (grup için)
    
    # Telegram'a gönderilsin mi?
    SEND_TO_TELEGRAM = True  # True yapın telegram'a göndermek için
    
    print("🔄 Analiz başlatılıyor...\n")
    
    df_all, df_fresh = get_rsi_crossover_stocks(rsi_period=31, sma_period=31, sma_threshold=51)
    
    # CSV'ye kaydetme
    if not df_all.empty:
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Tüm sonuçlar
        filename_all = f'bist100_rsi_tum_sonuclar_{timestamp}.csv'
        df_all.to_csv(filename_all, index=False, encoding='utf-8-sig')
        print(f"\n💾 Tüm sonuçlar '{filename_all}' dosyasına kaydedildi.")
        
        # Bu hafta kesenler
        if not df_fresh.empty:
            filename_fresh = f'bist100_rsi_bu_hafta_kesenler_{timestamp}.csv'
            df_fresh.to_csv(filename_fresh, index=False, encoding='utf-8-sig')
            print(f"💾 Bu hafta kesenler '{filename_fresh}' dosyasına kaydedildi.")
        
        # Telegram'a gönder
        if SEND_TO_TELEGRAM:
            if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
                print("\n⚠️  UYARI: Telegram bot token ve chat ID'sini ayarlayın!")
                print("📝 Nasıl alınır:")
                print("   1. Bot Token: @BotFather'a /newbot komutu gönderin")
                print("   2. Chat ID: @userinfobot'a mesaj gönderin")
            else:
                print("\n📤 Telegram'a gönderiliyor...")
                telegram_message = format_telegram_message(df_all, df_fresh)
                send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, telegram_message)
        else:
            print("\n💡 Telegram'a göndermek için SEND_TO_TELEGRAM = True yapın")

            print("📝 Bot Token ve Chat ID'yi kod içinde ayarlamayı unutmayın!")
