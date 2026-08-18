# pdf_metadata.py
"""
Extrae metadata de PDFs encontrados durante el rastreo (ej: "instrucciones
de pago" de una estafa). La metadata puede delatar al autor real, el
software usado, o la fecha real de creación — y alimenta el módulo de
correlación si el mismo autor/software aparece en varias campañas.
Requiere: pip install pypdf   (puro Python, instala rápido en Termux)
"""
import io
from pypdf import PdfReader


class PDFMetadataExtractor:
    def extraer(self, contenido_bytes, origen="desconocido"):
        """
        contenido_bytes: el PDF descargado (resp.content, no resp.text).
        Devuelve un dict con los campos de metadata más reveladores.
        """
        try:
            reader = PdfReader(io.BytesIO(contenido_bytes))
            info = reader.metadata
            if not info:
                return {}
            meta = {
                "origen": origen,
                "autor": info.get("/Author") or None,
                "creador": info.get("/Creator") or None,
                "productor": info.get("/Producer") or None,
                "fecha_creacion": info.get("/CreationDate") or None,
                "fecha_modificacion": info.get("/ModDate") or None,
                "titulo": info.get("/Title") or None,
            }
            return {k: v for k, v in meta.items() if v}
        except Exception as e:
            print(f"⚠️ Error leyendo metadata de PDF ({origen[:50]}): {e}")
            return {}
