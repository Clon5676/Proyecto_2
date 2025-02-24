import requests
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urljoin
import urllib3
import warnings
import os
# from datetime import datetime

# Suprimir advertencias SSL y otras advertencias
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

def extract_property_details(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        }
        
        session = requests.Session()
        response = session.get(url, headers=headers, verify=False, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Inicializar diccionario de detalles
        details = {
            'habitaciones': 'No especificado',
            'baños': 'No especificado',
            'metros_cuadrados': 'No especificado',
            'parqueos': 'No especificado',

        }
        
        # Buscar todos los detalles de la propiedad
        detail_containers = soup.select('div.listing_detail')
        
        # Buscar el ID de la propiedad específicamente
        # id_container = soup.select_one('div.property_id')
        

        for container in detail_containers:
            text = container.text.strip().lower()
            # Extraer el texto sin la etiqueta strong
            # strong_tag = container.find('strong')
            # if strong_tag:
            #     label = strong_tag.text.strip().lower()
            #     value = text.replace(label, '').strip()
                
                # Identificar el tipo de detalle
            if 'habitacion' in text or 'dormitor' in text:
                details['habitaciones'] = container.text.strip()
            elif 'baño' in text or 'bath' in text:
                details['baños'] = container.text.strip()
            elif 'metro' in text or 'm²' in text or 'm2' in text:
                details['metros_cuadrados'] = container.text.strip()
            elif 'parqueo' in text or 'garage' in text or 'estacionamiento' in text:
                if 'visita' not in text:
                    details['parqueos'] = container.text.strip()
        
        return details
        
    except Exception as e:
        print(f"Error al obtener detalles de {url}: {str(e)}")
        return None
    

def extract_properties_info(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    property_containers = soup.find_all('div', class_='property_listing')
    
    properties = []
    for container in property_containers:
        # Extraer información básica
        title = container.find('h4')
        if title and title.find('a'):
            property_name = title.find('a').text.strip()
            link = title.find('a')['href']
            full_link = urljoin(base_url, link)
        else:
            continue
        
        price_div = container.find('div', class_='listing_unit_price_wrapper')
        price = price_div.text.strip() if price_div else "No se encontró el precio"
        
        location_tags = container.select('div.property_location_image a')
        location = ', '.join([tag.text.strip() for tag in location_tags]) if location_tags else "No se encontró la ubicación"
        
        print(f"Obteniendo detalles de: {property_name}")
        details = extract_property_details(full_link)
        
        if details:
            property_info = {
                'nombre': property_name,
                'precio': price,
                'ubicacion': location,
                'enlace': full_link,
                'habitaciones': details['habitaciones'],
                'baños': details['baños'],
                'metros_cuadrados': details['metros_cuadrados'],
                'parqueos': details['parqueos']
            }
            properties.append(property_info)
            
        time.sleep(2)
    
    return properties

def get_page_content(page_number):
    # Crear nombre de carpeta con la fecha actual
    folder_name = f"html_files"
    
    # Crear la carpeta si no existe
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Carpeta creada: {folder_name}")
    
    base_url = "https://mapainmueble.com/apartamentos-en-alquiler-zona-14/"
    if page_number > 1:
        url = f"{base_url}page/{page_number-1}/"
    else:
        url = base_url
    
    # Ruta del archivo HTML dentro de la nueva carpeta
    file_path = os.path.join(folder_name, f'pagina_{page_number}.html')
    
    try:
        # Intentar leer el archivo si existe
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read(), base_url
    except FileNotFoundError:
        print(f"Descargando página {page_number}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            # Guardar el archivo en la nueva carpeta
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(response.text)
            return response.text, base_url
        else:
            return None, None

def main():
    all_properties = []
    num_pages = 4
    
    for page in range(2, num_pages + 1):
        print(f"\nProcesando página {page}...")
        html_content, base_url = get_page_content(page)
        
        if html_content and base_url:
            properties = extract_properties_info(html_content, base_url)
            all_properties.extend(properties)
            print(f"Se encontraron {len(properties)} propiedades en la página {page}")
            
            if page < num_pages:
                time.sleep(2)
    
    if all_properties:
        # Guardar en CSV con los nuevos campos
        with open('propiedades_detalladas.csv', 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['nombre', 'precio', 'ubicacion', 'enlace', 'habitaciones', 'baños', 'metros_cuadrados', 'parqueos']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_properties)
        
        print(f"\nSe guardaron {len(all_properties)} propiedades con detalles en 'propiedades_detalladas.csv'")
        
        # Imprimir resultados
        for i, prop in enumerate(all_properties, 1):
            print(f"\nPropiedad {i}:")
            for key, value in prop.items():
                print(f"{key}: {value}")
    else:
        print("No se encontraron propiedades")

if __name__ == "__main__":
    main()