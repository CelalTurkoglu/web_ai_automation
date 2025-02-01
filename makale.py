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

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

# Get form login credentials from .env file
FORM_EMAIL = os.getenv("FORM_EMAIL")
FORM_PASSWORD = os.getenv("FORM_PASSWORD")


# Function to download a PDF from a given URL
def pdf_indir(url, kayit_yolu):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for errors
        with open(kayit_yolu, "wb") as f:
            f.write(response.content)
        print(f"PDF successfully downloaded: {kayit_yolu}")
        return True
    except Exception as e:
        print(f"Error while downloading PDF: {e}")
        return False


# Function to extract text from a PDF file
def pdf_metnini_al(dosya_yolu):
    try:
        with pdfplumber.open(dosya_yolu) as pdf:
            metin = ""
            for sayfa in pdf.pages:
                metin += sayfa.extract_text()
            return metin
    except Exception as e:
        print(f"Error while extracting text from PDF: {e}")
        return None


# Function to extract information using GPT-4o-mini
def bilgi_cikar(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Use GPT-4o-mini
            messages=[
                {"role": "system",
                 "content": "You are an assistant. Extract the title, authors, keywords, and references from the given text."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error while fetching information from OpenAI API: {e}")
        return None


# Function to add an author to the form
def yazar_ekle(driver, yazar):
    try:
        # Click the "Add Author" button
        yazar_butonu = driver.find_element(By.XPATH,
                                           "//*[@id='main']/div/div/makale-giris/div/div/app-card/div/div[2]/form/app-card[3]/div/div[2]/div/div/div/pls-datatable/table/thead/tr/th[4]/button")
        yazar_butonu.click()
        time.sleep(1)

        # Enter the author's name
        yazar_input = driver.find_element(By.XPATH,
                                          "/html/body/ngb-modal-window/div/div/form/div[2]/div[1]/div/p-autocomplete/span/input")
        yazar_input.send_keys(yazar)
        time.sleep(1)

        # Click the save button
        yazar_kaydet_butonu = driver.find_element(By.CLASS_NAME, "btn-outline-primary")
        yazar_kaydet_butonu.click()
        time.sleep(1)
    except Exception as e:
        print(f"Error while adding author: {e}")


# Function to fill out the form with extracted information
def form_doldur(bilgiler):
    driver = None
    try:
        driver = webdriver.Safari()
        driver.maximize_window()

        # === 1. Log in ===
        driver.get("https://aixadmin.ssteknoloji.com/academindex/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))

        # Enter email
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(FORM_EMAIL)  # Read from .env file

        # Enter password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(FORM_PASSWORD)  # Read from .env file
        password_input.send_keys(Keys.ENTER)

        # === 2. Navigate to the Articles Page ===
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and @href='/academindex/acd/makaleler']")))
        a_etiketi = driver.find_element(By.XPATH, "//a[@class='nav-link' and @href='/academindex/acd/makaleler']")
        a_etiketi.click()
        time.sleep(1)

        # === 3. Open the Form ===
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "btn-success")))
        form_ac_butonu = driver.find_element(By.CLASS_NAME, "btn-success")
        form_ac_butonu.click()
        time.sleep(1)

        # === 4. Fill Out the Form Fields ===

        # Title
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "baslik")))
        baslik_input = driver.find_element(By.NAME, "baslik")
        baslik_input.send_keys(bilgiler["baslik"])

        # Year
        yil_input = driver.find_element(By.NAME, "yil")
        yil_input.send_keys("1996")

        # Issue
        sayi_input = driver.find_element(By.NAME, "sayi")
        sayi_input.send_keys("20")

        # Volume
        cilt_input = driver.find_element(By.NAME, "cilt")
        cilt_input.send_keys("7")

        # Keywords
        anahtar_kelime = driver.find_element(By.XPATH,
                                             "//*[@id='main']/div/div/makale-giris/div/div/app-card/div/div[2]/form/app-card[1]/div/div[2]/div[10]/div/span/p-chips/div/ul/li/input")
        for kelime in bilgiler["anahtar_kelime"]:
            anahtar_kelime.send_keys(kelime)
            anahtar_kelime.send_keys(Keys.ENTER)

        # PDF Link
        pdf_linki = driver.find_element(By.NAME, "url")
        pdf_linki.send_keys(bilgiler["link"])

        # Bibliography
        kaynakca_butonu = driver.find_element(By.XPATH,
                                              "//*[@id='main']/div/div/makale-giris/div/div/app-card/div/div[2]/form/app-card[2]/div/div[2]/div/div/div/pls-datatable/table/thead/tr/th[4]/button[2]")
        kaynakca_butonu.click()
        time.sleep(1)

        kaynakca_formu = driver.find_element(By.NAME, "kaynakca")
        driver.execute_script(f"arguments[0].value = `{bilgiler['kaynakca']}`;", kaynakca_formu)

        kaynakca_formu.send_keys(Keys.SPACE)

        kaynakca_ekle_butonu = driver.find_element(By.CLASS_NAME, "btn-outline-primary")
        kaynakca_ekle_butonu.click()

        # Add Authors
        yazarlar = bilgiler["yazarlar"].split(", ")  # Split authors by comma
        for yazar in yazarlar:
            yazar_ekle(driver, yazar)

        # Journal Name
        dergi_input = driver.find_element(By.XPATH,
                                          "//input[@class='ng-tns-c12-9 form-control ui-inputtext ui-widget ui-state-default ui-corner-all ui-autocomplete-input ng-star-inserted']")
        dergi_input.send_keys("Ekonomik Yaklaşım")  # Enter journal name

        # Wait for the dropdown and select the first item
        time.sleep(1.5)  # Wait for 2 seconds
        liste_elemani = driver.find_element(By.XPATH, "//li[contains(@class, 'ui-autocomplete-list-item')]")
        liste_elemani.click()

        print("Form successfully filled out.")
        input("Press Enter to close the browser...")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()


# Main function
if __name__ == "__main__":
    # PDF URL
    pdf_url = "https://dergipark.org.tr/tr/download/article-file/3493120"  # Enter the PDF URL here
    kayit_yolu = "/Users/celal/Desktop/aaa/indirilen_makale.pdf"  # Path to save the downloaded PDF

    # Download the PDF
    if not pdf_indir(pdf_url, kayit_yolu):
        print("Failed to download PDF. Exiting program.")
        exit()

    # Extract text from the PDF
    pdf_metni = pdf_metnini_al(kayit_yolu)
    if not pdf_metni:
        print("Failed to extract text from PDF. Exiting program.")
        exit()

    # Extract information using GPT-4o-mini
    baslik_yazarlar_prompt = f"Extract the title and authors from the following text. Write only the title and authors, one per line, and separate multiple authors with a comma ',':\n{pdf_metni}"
    baslik_yazarlar = bilgi_cikar(baslik_yazarlar_prompt)

    anahtar_kelimeler_prompt = f"Extract the keywords from the following text. Keywords usually appear after 'anahtar kelimeler:' or 'keywords:'. Write only the keywords, without any labels:\n{pdf_metni}"
    anahtar_kelimeler = bilgi_cikar(anahtar_kelimeler_prompt)

    kaynakca_prompt = f"Extract the bibliography from the following text. The bibliography usually appears after 'kaynakça:' or 'references:'. Write the entire bibliography, without any additional text:\n{pdf_metni}"
    kaynakca = bilgi_cikar(kaynakca_prompt)

    # Convert authors to a list
    yazarlar = baslik_yazarlar.split("\n")[1]  # Exclude the title line

    # Combine extracted information
    bilgiler = {
        "baslik": baslik_yazarlar.split("\n")[0],  # First line is the title
        "yazarlar": yazarlar,
        "anahtar_kelime": anahtar_kelimeler.split(", "),
        "kaynakca": kaynakca,
        "link": pdf_url  # PDF link
    }

    # Fill out the form
    form_doldur(bilgiler)