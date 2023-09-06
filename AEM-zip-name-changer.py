import glob
import xml.etree.ElementTree as ET
from zipfile import ZipFile

properties_xml = 'META-INF/vault/properties.xml'

# Obtiene lista de ficheros .zip que comiencen con 'DownloadedFormsPackage'
zip_files = glob.glob('DownloadedFormsPackage*.zip')

# Recorre todos los ficheros dentro del zip
for zip_file_path in zip_files:
    # Obtiene el nombre del fichero quitando la extensión .zip
    name_zip = zip_file_path[:-4]
    print(f'Abriendo fichero: {zip_file_path}')

    new_zip_name = 'None'

    # Obtiene el nombre original del formulario, abriendo el .zip y buscando dentro de los .content.xml
    with ZipFile(zip_file_path, 'r') as zip_file:
        # Buscar todas las rutas que empiecen por 'jcr_root/content' y terminen por '.content.xml'
        for file in zip_file.infolist():
            if file.filename.startswith('jcr_root/content') and file.filename.endswith('.content.xml'):
                # Abrir el archivo XML
                with zip_file.open(file) as xml_file:
                    # Analizar el contenido XML
                    content = xml_file.read()
                    root = ET.fromstring(content)
                    # Iterar sobre todos los elementos del XML
                    for element in root.iter():
                        # Obtener el valor de jcr:title
                        title = element.get('title')
                        if title is not None and '-' in title:
                            new_zip_name = title
                            break

    print(f'Obteniendo nombre: {new_zip_name}')

    # Crear un archivo ZIP nuevo con el nuevo nombre
    new_zip_path = f'{new_zip_name}.zip'

    # Abre el viejo .zip en modo lectura
    with ZipFile(zip_file_path, 'r') as zip_file:
        # Crea un nuevo .zip con el nombre del formulario original e inserta todo menos 'properties.xml'
        with ZipFile(new_zip_path, 'w') as new_zip:
            for file in zip_file.infolist():
                if file.filename != properties_xml:
                    new_zip.writestr(file, zip_file.read(file))

            # Obiene el contenido del archivo 'properties.xml'
            xml_content = zip_file.read(properties_xml)
            # Reemplaza el valor antiguo (DownloadedFormsPackage...) por el nombre del formulario original (ABC123-WXYZ-202301)
            modified_xml = xml_content.decode('utf-8').replace(name_zip, new_zip_name)
            print(f'Modificando name en {properties_xml}: {new_zip_name}')
            # Agrega el nuevo 'properties.xml' modificado al nuevo .zip
            new_zip.writestr(properties_xml, modified_xml)

    print(f'Archivo creado: {new_zip_path}\n')