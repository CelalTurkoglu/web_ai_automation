import openai
import pdfplumber
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
import os

# .env dosyasını yükle
load_dotenv()

# OpenAI API Key'inizi .env dosyasından alın
openai.api_key = os.getenv("OPENAI_API_KEY")

# Form bilgilerini .env dosyasından alın
FORM_EMAIL = os.getenv("FORM_EMAIL")
FORM_PASSWORD = os.getenv("FORM_PASSWORD")


# PDF'i indirme fonksiyonu
def pdf_indir(url, kayit_yolu):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Hata kontrolü
        with open(kayit_yolu, "wb") as f:
            f.write(response.content)
        print(f"PDF başarıyla indirildi: {kayit_yolu}")
        return True
    except Exception as e:
        print(f"PDF indirilirken hata oluştu: {e}")
        return False


# PDF'den metin çıkarma fonksiyonu
def pdf_metnini_al(dosya_yolu):
    try:
        with pdfplumber.open(dosya_yolu) as pdf:
            metin = ""
            for sayfa in pdf.pages:
                metin += sayfa.extract_text()
            return metin
    except Exception as e:
        print(f"PDF'den metin çıkarılırken hata oluştu: {e}")
        return None


# GPT-4o-mini ile bilgi çıkarma
def bilgi_cikar(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # GPT-4o-mini kullanıyoruz
            messages=[
                {"role": "system",
                 "content": "Sen bir yardımcısın. Verilen metinden başlık, yazarlar, anahtar kelimeler ve kaynakça bilgilerini çıkarırsın."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"OpenAI API'den bilgi alınırken hata oluştu: {e}")
        return None


# Yazar ekleme fonksiyonu
def yazar_ekle(driver, yazar):
    try:
        # Yazar ekleme butonuna tıkla
        yazar_butonu = driver.find_element(By.XPATH,
                                           "//*[@id='main']/div/div/makale-giris/div/div/app-card/div/div[2]/form/app-card[3]/div/div[2]/div/div/div/pls-datatable/table/thead/tr/th[4]/button")
        yazar_butonu.click()
        time.sleep(1)

        # Yazar adını gir
        yazar_input = driver.find_element(By.XPATH,
                                          "/html/body/ngb-modal-window/div/div/form/div[2]/div[1]/div/p-autocomplete/span/input")
        yazar_input.send_keys(yazar)
        time.sleep(1)

        # Kaydet butonuna tıkla
        yazar_kaydet_butonu = driver.find_element(By.CLASS_NAME, "btn-outline-primary")
        yazar_kaydet_butonu.click()
        time.sleep(1)
    except Exception as e:
        print(f"Yazar eklenirken hata oluştu: {e}")


# Form doldurma fonksiyonu
def form_doldur(bilgiler):
    driver = None
    try:
        driver = webdriver.Safari()
        driver.maximize_window()

        # === 1. Giriş Yapma ===
        driver.get("https://aixadmin.ssteknoloji.com/academindex/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))

        # Mail adresi
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(FORM_EMAIL)  # .env dosyasından oku

        # Şifre
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(FORM_PASSWORD)  # .env dosyasından oku
        password_input.send_keys(Keys.ENTER)

        # === 2. Makaleler Sayfasına Git ===
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and @href='/academindex/acd/makaleler']")))
        a_etiketi = driver.find_element(By.XPATH, "//a[@class='nav-link' and @href='/academindex/acd/makaleler']")
        a_etiketi.click()
        time.sleep(1)

        # === 3. Formu Aç ===
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "btn-success")))
        form_ac_butonu = driver.find_element(By.CLASS_NAME, "btn-success")
        form_ac_butonu.click()
        time.sleep(1)

        # === 4. Form Alanlarını Doldur ===

        # Başlık
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "baslik")))
        baslik_input = driver.find_element(By.NAME, "baslik")
        baslik_input.send_keys(bilgiler["baslik"])

        # Yıl
        yil_input = driver.find_element(By.NAME, "yil")
        yil_input.send_keys("1996")

        # Sayı
        sayi_input = driver.find_element(By.NAME, "sayi")
        sayi_input.send_keys("20")

        # Cilt
        cilt_input = driver.find_element(By.NAME, "cilt")
        cilt_input.send_keys("7")

        # Anahtar Kelimeler
        anahtar_kelime = driver.find_element(By.XPATH,
                                             "//*[@id='main']/div/div/makale-giris/div/div/app-card/div/div[2]/form/app-card[1]/div/div[2]/div[10]/div/span/p-chips/div/ul/li/input")
        for kelime in bilgiler["anahtar_kelime"]:
            anahtar_kelime.send_keys(kelime)
            anahtar_kelime.send_keys(Keys.ENTER)

        # PDF Linki
        pdf_linki = driver.find_element(By.NAME, "url")
        pdf_linki.send_keys(bilgiler["link"])

        # Kaynakça
        kaynakca_butonu = driver.find_element(By.XPATH,
                                              "//*[@id='main']/div/div/makale-giris/div/div/app-card/div/div[2]/form/app-card[2]/div/div[2]/div/div/div/pls-datatable/table/thead/tr/th[4]/button[2]")
        kaynakca_butonu.click()
        time.sleep(1)

        kaynakca_formu = driver.find_element(By.NAME, "kaynakca")
        driver.execute_script(f"arguments[0].value = `{bilgiler['kaynakca']}`;", kaynakca_formu)

        kaynakca_formu.send_keys(Keys.SPACE)

        kaynakca_ekle_butonu = driver.find_element(By.CLASS_NAME, "btn-outline-primary")
        kaynakca_ekle_butonu.click()

        # Yazar Ekleme
        yazarlar = bilgiler["yazarlar"].split(", ")  # Yazarları virgülle ayır
        for yazar in yazarlar:
            yazar_ekle(driver, yazar)

        # Dergi Adı
        dergi_input = driver.find_element(By.XPATH,
                                          "//input[@class='ng-tns-c12-9 form-control ui-inputtext ui-widget ui-state-default ui-corner-all ui-autocomplete-input ng-star-inserted']")
        dergi_input.send_keys("Ekonomik Yaklaşım")  # Dergi adını yaz

        # Açılır listeyi bekle ve ilk öğeyi seç
        time.sleep(1.5)  # 2 saniye bekle
        liste_elemani = driver.find_element(By.XPATH, "//li[contains(@class, 'ui-autocomplete-list-item')]")
        liste_elemani.click()

        print("Form başarıyla dolduruldu.")
        input("Tarayıcıyı kapatmak için Enter'a basın...")

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        if driver:
            driver.quit()


# Ana işlev
if __name__ == "__main__":
    # PDF linki
    pdf_url = "https://dergipark.org.tr/tr/download/article-file/3493120"  # Buraya PDF linkini yazın
    kayit_yolu = "/Users/celal/Desktop/aaa/indirilen_makale.pdf"  # PDF'in kaydedileceği yol

    # PDF'i indir
    if not pdf_indir(pdf_url, kayit_yolu):
        print("PDF indirilemedi. Program sonlandırılıyor.")
        exit()

    # PDF'den metni çıkar
    pdf_metni = pdf_metnini_al(kayit_yolu)
    if not pdf_metni:
        print("PDF'den metin çıkarılamadı. Program sonlandırılıyor.")
        exit()

    # GPT-4o-mini ile bilgi çıkar
    baslik_yazarlar_prompt = f"Aşağıdaki metinden başlık ve yazarları bul. Sadece başlık ve yazarları alt alta yaz:\n{pdf_metni}"
    baslik_yazarlar = bilgi_cikar(baslik_yazarlar_prompt)

    anahtar_kelimeler_prompt = f"Aşağıdaki metinden anahtar kelimeleri bul. Anahtar kelimeler 'anahtar kelimeler:' yazısından sonra gelir. Sadece anahtar kelimeleri yaz ve 'anahtar kelimeler:' ifadesini başına koyma:\n{pdf_metni}"
    anahtar_kelimeler = bilgi_cikar(anahtar_kelimeler_prompt)

    kaynakca_prompt = f"Aşağıdaki metinden kaynakça kısmını bul. Kaynakça 'kaynakça:' veya 'references:' yazısından sonra gelir. Tüm kaynakçayı yaz, başına başlık, anahtar kelimeler vs yazma:\n{pdf_metni}"
    kaynakca = bilgi_cikar(kaynakca_prompt)

    # Yazarları listeye çevir
    yazarlar = baslik_yazarlar.split("\n")[1]  # Başlık hariç yazarları al

    # Bilgileri birleştir
    bilgiler = {
        "baslik": baslik_yazarlar.split("\n")[0],  # İlk satır başlık
        "yazarlar": yazarlar,
        "anahtar_kelime": anahtar_kelimeler.split(", "),
        "kaynakca": kaynakca,
        "link": pdf_url  # Makale linki
    }

    # Formu doldur
    form_doldur(bilgiler)