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
        message += f"📈 <b>TÜM SONUÇLAR</b>\n"
        message += f"Toplam: {len(df_all)} hisse\n"
        message += f"Bu hafta kesen: {len(df_fresh)} hisse\n"
        message += f"Daha önce kesen: {len(df_all) - len(df_fresh)} hisse\n\n"
        
        # Tüm hisseleri listele (sadece sembol isimleri)
        for idx, row in df_all.iterrows():
            message += f"{row['Hisse']}\n"
    
    return message

def calculate_rsi(data, period=31):
    """RSI hesaplama fonksiyonu"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# BIST Hisse Sembolleri
SYMBOLS = [
    "A1CAP.IS", "ADEL.IS", "ADESE.IS", "ADGYO.IS", "AEFES.IS", "AFYON.IS",
    "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AHSGY.IS", "AKBNK.IS",
    "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFIS.IS", "AKFYE.IS", "AKGRT.IS",
    "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "AKSGY.IS", "ALARK.IS", "ALBRK.IS",
    "ALCAR.IS", "ALCTL.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS",
    "ALKLC.IS", "ALTNY.IS", "ALVES.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS",
    "ANSGR.IS", "ARASE.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARMGD.IS",
    "ARSAN.IS", "ARTMS.IS", "ASELS.IS", "ASGYO.IS", "ASTOR.IS", "ASUZU.IS",
    "ATAKP.IS", "ATATP.IS", "AVPGY.IS", "AYCES.IS", "AYDEM.IS", "AYEN.IS",
    "AYES.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAHKM.IS", "BAKAB.IS",
    "BALSU.IS", "BANVT.IS", "BARMA.IS", "BASCM.IS", "BASGZ.IS", "BEGYO.IS",
    "BERA.IS", "BESLR.IS", "BEYAZ.IS", "BFREN.IS", "BIENY.IS", "BIGCH.IS",
    "BIGEN.IS", "BIMAS.IS", "BINBN.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS",
    "BJKAS.IS", "BLCYT.IS", "BMSTL.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS",
    "BOSSA.IS", "BRISA.IS", "BRKVY.IS", "BRLSM.IS", "BRSAN.IS", "BRYAT.IS",
    "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BULGS.IS", "BVSAN.IS", "CANTE.IS",
    "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEMZY.IS",
    "CGCAM.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS",
    "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGI.IS", "DAPGM.IS",
    "DARDL.IS", "DCTTR.IS", "DERHL.IS", "DERIM.IS", "DESA.IS", "DEVA.IS",
    "DGATE.IS", "DGGYO.IS", "DGNMO.IS", "DITAS.IS", "DMRGD.IS", "DNISI.IS",
    "DOAS.IS", "DOBUR.IS", "DOCO.IS", "DOFER.IS", "DOHOL.IS", "DOKTA.IS",
    "DSTKF.IS", "DURKN.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS",
    "ECZYT.IS", "EDIP.IS", "EFORC.IS", "EGEEN.IS", "EGEGY.IS", "EGEPO.IS",
    "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKOS.IS", "EKSUN.IS",
    "ELITE.IS", "EMKEL.IS", "ENDAE.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS",
    "ENSRI.IS", "ENTRA.IS", "ERBOS.IS", "ERCB.IS", "EREGL.IS", "ESCAR.IS",
    "ESCOM.IS", "ESEN.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FENER.IS",
    "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FROTO.IS", "FZLGY.IS",
    "GARAN.IS", "GARFA.IS", "GEDIK.IS", "GENIL.IS", "GENTS.IS", "GEREL.IS",
    "GESAN.IS", "GIPTA.IS", "GLCVY.IS", "GLRMK.IS", "GLRYH.IS", "GLYHO.IS",
    "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRSEL.IS",
    "GRTHO.IS", "GSDHO.IS", "GSRAY.IS", "GUBRF.IS", "GUNDG.IS", "GWIND.IS",
    "GZNMI.IS", "HALKB.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HLGYO.IS",
    "HOROZ.IS", "HRKET.IS", "HTTBT.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS",
    "IEYHO.IS", "IHAAS.IS", "IHLAS.IS", "IHLGM.IS", "IMASM.IS", "INDES.IS",
    "INFO.IS", "INGRM.IS", "INTEK.IS", "INTEM.IS", "INVEO.IS", "INVES.IS",
    "IPEKE.IS", "ISBIR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS",
    "ISGSY.IS", "ISGYO.IS", "ISKPL.IS", "ISKUR.IS", "ISMEN.IS", "ISSEN.IS",
    "IZENR.IS", "IZFAS.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS",
    "KARSN.IS", "KARTN.IS", "KATMR.IS", "KAYSE.IS", "KBORU.IS", "KCAER.IS",
    "KCHOL.IS", "KENT.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLKIM.IS",
    "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSER.IS", "KLSYN.IS", "KLYPV.IS",
    "KMPUR.IS", "KNFRT.IS", "KOCMT.IS", "KONKA.IS", "KONTR.IS", "KONYA.IS",
    "KOPOL.IS", "KORDS.IS", "KOTON.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS",
    "KRDMB.IS", "KRDMD.IS", "KRONT.IS", "KRVGD.IS", "KSTUR.IS", "KTLEV.IS",
    "KTSKR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS",
    "LIDER.IS", "LIDFA.IS", "LILAK.IS", "LINK.IS", "LKMNH.IS", "LMKDC.IS",
    "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "LYDHO.IS", "LYDYE.IS", "MAALT.IS",
    "MACKO.IS", "MAGEN.IS", "MAKTK.IS", "MARBL.IS", "MARTI.IS", "MAVI.IS",
    "MEDTR.IS", "MEGMT.IS", "MEKAG.IS", "MERCN.IS", "MERIT.IS", "METUR.IS",
    "MGROS.IS", "MHRGY.IS", "MIATK.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS",
    "MOGAN.IS", "MOPAS.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS",
    "MTRKS.IS", "NATEN.IS", "NETAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS",
    "NUHCM.IS", "OBAMS.IS", "ODAS.IS", "ODINE.IS", "OFSYM.IS", "ONCSM.IS",
    "ONRYT.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OTKAR.IS", "OTTO.IS",
    "OYAKC.IS", "OYYAT.IS", "OZATD.IS", "OZKGY.IS", "OZSUB.IS", "OZYSR.IS",
    "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS",
    "PCILT.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS",
    "PINSU.IS", "PKENT.IS", "PLTUR.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS",
    "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PSGYO.IS", "QNBFK.IS", "QNBTR.IS",
    "QUAGR.IS", "RALYH.IS", "RAYSG.IS", "REEDR.IS", "RGYAS.IS", "RUZYE.IS",
    "RYGYO.IS", "RYSAS.IS", "SAFKR.IS", "SAHOL.IS", "SANFM.IS", "SANKO.IS",
    "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGMN.IS", "SEGYO.IS",
    "SELEC.IS", "SERNT.IS", "SISE.IS", "SKBNK.IS", "SKYMD.IS", "SMRTG.IS",
    "SMRVA.IS", "SNGYO.IS", "SNICA.IS", "SNPAM.IS", "SOKE.IS", "SOKM.IS",
    "SONME.IS", "SRVGY.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS",
    "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS",
    "TCKRC.IS", "TEHOL.IS", "TEKTU.IS", "TERA.IS", "TEZOL.IS", "TGSAS.IS",
    "THYAO.IS", "TKFEN.IS", "TKNSA.IS", "TMPOL.IS", "TMSN.IS", "TNZTP.IS",
    "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRHOL.IS", "TRILC.IS", "TSGYO.IS",
    "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUKAS.IS", "TUPRS.IS",
    "TUREX.IS", "TURGG.IS", "TURSG.IS", "UFUK.IS", "ULKER.IS", "ULUFA.IS",
    "ULUSE.IS", "ULUUN.IS", "UNLU.IS", "USAK.IS", "VAKBN.IS", "VAKFN.IS",
    "VAKKO.IS", "VBTYZ.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS",
    "VKGYO.IS", "VRGYO.IS", "VSNMD.IS", "YAPRK.IS", "YATAS.IS", "YBTAS.IS",
    "YEOTK.IS", "YGGYO.IS", "YIGIT.IS", "YKBNK.IS", "YUNSA.IS", "YYLGD.IS",
    "ZOREN.IS", "ZRGYO.IS"
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
    
    for stock in SYMBOLS:
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
    TELEGRAM_BOT_TOKEN = "8256592463:AAHlJ3BQSvwUDOQuKCYAhKwAwMMWUFJXE4o"
    TELEGRAM_CHAT_ID = "1008660822"
    SEND_TO_TELEGRAM = True
    
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
            print("\n📤 Telegram'a gönderiliyor...")
            telegram_message = format_telegram_message(df_all, df_fresh)
            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, telegram_message)

