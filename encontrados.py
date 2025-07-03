from pathlib import Path

# Archivos
archivo_combinaciones = Path("combinaciones_cedula_contrato.txt")
archivo_resultados = Path("resultados_busqueda_alfresco.txt")
archivo_salida = Path("combinaciones_encontradas_tabla.txt")

# Cargar combinaciones con nombre
combinaciones_dict = {}
with archivo_combinaciones.open(encoding="utf-8") as f:
    for line in f:
        if "→" in line:
            clave, nombre = line.strip().split("→")
            combinaciones_dict[clave.strip()] = nombre.strip()

# Leer resultados encontrados
encontrados = []
with archivo_resultados.open(encoding="utf-8") as f:
    for line in f:
        if "→ FOUND" in line:
            clave = line.strip().split("→")[0].strip()
            nombre = combinaciones_dict.get(clave, "NOMBRE DESCONOCIDO")
            encontrados.append((clave, nombre, "FOUND ✅"))

# Calcular anchos
ancho_comb = max(len("Combinación"), max((len(e[0]) for e in encontrados), default=0))
ancho_nombre = max(len("Nombre"), max((len(e[1]) for e in encontrados), default=0))
ancho_estado = len("Estado")

# Crear tabla
linea_superior = f"╔{'═' * (ancho_comb + 2)}╦{'═' * (ancho_nombre + 2)}╦{'═' * (ancho_estado + 2)}╗"
linea_media =   f"╠{'═' * (ancho_comb + 2)}╬{'═' * (ancho_nombre + 2)}╬{'═' * (ancho_estado + 2)}╣"
linea_inferior =f"╚{'═' * (ancho_comb + 2)}╩{'═' * (ancho_nombre + 2)}╩{'═' * (ancho_estado + 2)}╝"

with archivo_salida.open("w", encoding="utf-8") as f:
    f.write(linea_superior + "\n")
    f.write(f"║ {'Combinación'.ljust(ancho_comb)} ║ {'Nombre'.ljust(ancho_nombre)} ║ {'Estado'} ║\n")
    f.write(linea_media + "\n")
    for comb, nombre, estado in encontrados:
        f.write(f"║ {comb.ljust(ancho_comb)} ║ {nombre.ljust(ancho_nombre)} ║ {estado} ║\n")
    f.write(linea_inferior + "\n")

print(f"✅ Archivo de tabla generado como: {archivo_salida}")
